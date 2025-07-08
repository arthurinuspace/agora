"""
API middleware for rate limiting, error handling, and request/response processing.
"""

import time
import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
import redis
import json
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

# Redis client for rate limiting
redis_client = None
try:
    if hasattr(Config, 'REDIS_URL') and Config.REDIS_URL:
        redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    else:
        redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed for rate limiting: {e}")
    redis_client = None

class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded."""
    def __init__(self, message: str, retry_after: int):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(self, max_requests: int, time_window: int, identifier: str):
        self.max_requests = max_requests
        self.time_window = time_window
        self.identifier = identifier
        self.key = f"rate_limit:{identifier}"
    
    def is_allowed(self) -> Tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, retry_after)."""
        if not redis_client:
            return True, 0
        
        try:
            current_time = int(time.time())
            window_start = current_time - self.time_window
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(self.key, 0, window_start)
            
            # Count current requests
            pipe.zcard(self.key)
            
            # Add current request
            pipe.zadd(self.key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(self.key, self.time_window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            if current_requests >= self.max_requests:
                # Calculate retry after
                oldest_request = redis_client.zrange(self.key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = int(oldest_request[0][1]) + self.time_window - current_time
                    return False, max(retry_after, 1)
                return False, self.time_window
            
            return True, 0
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True, 0  # Allow request on error

class APIMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting, logging, and error handling."""
    
    def __init__(self, app, enable_rate_limiting: bool = True, enable_logging: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_logging = enable_logging
        
        # Rate limit configurations
        self.rate_limits = {
            '/slack/events': {'max_requests': 100, 'time_window': 60},  # 100 requests per minute
            '/health': {'max_requests': 30, 'time_window': 60},  # 30 requests per minute
            'default': {'max_requests': 60, 'time_window': 60}  # 60 requests per minute
        }
    
    async def dispatch(self, request: StarletteRequest, call_next) -> StarletteResponse:
        """Process request through middleware."""
        start_time = time.time()
        
        # Extract client identifier
        client_id = self._get_client_id(request)
        
        # Apply rate limiting
        if self.enable_rate_limiting:
            try:
                self._check_rate_limit(request, client_id)
            except RateLimitExceeded as e:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "message": e.message},
                    headers={"Retry-After": str(e.retry_after)}
                )
        
        # Log request
        if self.enable_logging:
            logger.info(f"Request: {request.method} {request.url.path} from {client_id}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            if self.enable_logging:
                duration = time.time() - start_time
                logger.info(f"Response: {response.status_code} in {duration:.3f}s")
            
            # Add custom headers
            response.headers["X-Response-Time"] = f"{time.time() - start_time:.3f}s"
            response.headers["X-Rate-Limit-Remaining"] = str(self._get_remaining_requests(request, client_id))
            
            return response
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": "An unexpected error occurred"}
            )
    
    def _get_client_id(self, request: StarletteRequest) -> str:
        """Extract client identifier from request."""
        # Try to get real IP from headers
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP", "") or
            request.client.host if request.client else "unknown"
        )
        
        # Include user agent for more specific identification
        user_agent = request.headers.get("User-Agent", "unknown")
        
        return f"{client_ip}:{hash(user_agent) % 10000}"
    
    def _check_rate_limit(self, request: StarletteRequest, client_id: str):
        """Check if request should be rate limited."""
        path = request.url.path
        
        # Get rate limit config for this endpoint
        config = self.rate_limits.get(path, self.rate_limits['default'])
        
        # Create rate limiter
        limiter = RateLimiter(
            max_requests=config['max_requests'],
            time_window=config['time_window'],
            identifier=f"{path}:{client_id}"
        )
        
        # Check if request is allowed
        allowed, retry_after = limiter.is_allowed()
        
        if not allowed:
            raise RateLimitExceeded(
                f"Rate limit exceeded for {path}. Max {config['max_requests']} requests per {config['time_window']} seconds.",
                retry_after
            )
    
    def _get_remaining_requests(self, request: StarletteRequest, client_id: str) -> int:
        """Get remaining requests for client."""
        if not redis_client:
            return 999
        
        try:
            path = request.url.path
            config = self.rate_limits.get(path, self.rate_limits['default'])
            key = f"rate_limit:{path}:{client_id}"
            
            current_requests = redis_client.zcard(key)
            return max(0, config['max_requests'] - current_requests)
            
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return 999

def handle_api_errors(func):
    """Decorator for handling API errors gracefully."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionError as e:
            # Handle permission errors
            logger.warning(f"Permission error: {e}")
            raise HTTPException(status_code=403, detail=str(e))
        except FileNotFoundError as e:
            # Handle not found errors
            logger.warning(f"Not found error: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return wrapper

class ErrorTracker:
    """Track and analyze API errors."""
    
    def __init__(self):
        self.error_key = "api_errors"
    
    def track_error(self, error_type: str, endpoint: str, details: Dict[str, Any]):
        """Track an API error."""
        if not redis_client:
            return
        
        try:
            error_data = {
                'error_type': error_type,
                'endpoint': endpoint,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                'count': 1
            }
            
            # Create unique key for this error
            error_hash = hash(f"{error_type}:{endpoint}:{str(details)}")
            key = f"{self.error_key}:{error_hash}"
            
            # Increment counter or create new entry
            if redis_client.exists(key):
                existing_data = json.loads(redis_client.get(key))
                existing_data['count'] += 1
                existing_data['last_seen'] = datetime.now().isoformat()
                redis_client.setex(key, 86400, json.dumps(existing_data))  # 24 hours
            else:
                redis_client.setex(key, 86400, json.dumps(error_data))  # 24 hours
                
        except Exception as e:
            logger.error(f"Error tracking failed: {e}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        if not redis_client:
            return {}
        
        try:
            keys = redis_client.keys(f"{self.error_key}:*")
            errors = []
            
            for key in keys:
                data = json.loads(redis_client.get(key))
                errors.append(data)
            
            # Sort by count (most frequent first)
            errors.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'total_errors': len(errors),
                'most_frequent': errors[:10],
                'recent_errors': sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

# Global error tracker instance
error_tracker = ErrorTracker()

def track_api_error(error_type: str, endpoint: str, **details):
    """Track an API error globally."""
    error_tracker.track_error(error_type, endpoint, details)

def get_api_error_stats() -> Dict[str, Any]:
    """Get API error statistics."""
    return error_tracker.get_error_stats()

class RequestValidator:
    """Validate API requests."""
    
    @staticmethod
    def validate_slack_signature(request: Request) -> bool:
        """Validate Slack request signature."""
        try:
            # This would be implemented with actual Slack signature validation
            # For now, we'll just check if the signature header exists
            signature = request.headers.get("X-Slack-Signature")
            timestamp = request.headers.get("X-Slack-Request-Timestamp")
            
            if not signature or not timestamp:
                return False
            
            # Check timestamp (request should be recent)
            try:
                request_time = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - request_time) > 300:  # 5 minutes
                    return False
            except ValueError:
                return False
            
            # In production, you would validate the actual signature here
            return True
            
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False
    
    @staticmethod
    def validate_poll_data(poll_data: Dict[str, Any]) -> bool:
        """Validate poll creation data."""
        required_fields = ['question', 'options', 'vote_type']
        
        for field in required_fields:
            if field not in poll_data:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(poll_data['options'], list) or len(poll_data['options']) < 2:
            raise ValueError("Poll must have at least 2 options")
        
        if len(poll_data['options']) > 10:
            raise ValueError("Poll cannot have more than 10 options")
        
        if poll_data['vote_type'] not in ['single', 'multiple']:
            raise ValueError("Vote type must be 'single' or 'multiple'")
        
        return True
    
    @staticmethod
    def validate_user_role(role: str) -> bool:
        """Validate user role."""
        valid_roles = ['admin', 'user', 'viewer']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return True