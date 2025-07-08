"""
Performance optimization module for Agora Slack app.
Provides database query optimizations, caching, and performance monitoring.
"""

import time
import functools
import logging
from typing import Any, Dict, List, Optional, Callable
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, text
from contextlib import contextmanager
import redis
import json
from datetime import datetime, timedelta
from models import Poll, PollOption, VotedUser, UserVote, PollAnalytics, UserRole, Notification
from config import Config

logger = logging.getLogger(__name__)

# Redis client for caching
redis_client = None
try:
    if hasattr(Config, 'REDIS_URL') and Config.REDIS_URL:
        redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    else:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching disabled.")
    redis_client = None

class PerformanceMonitor:
    """Context manager for monitoring query performance."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if duration > 1.0:  # Log slow queries (> 1 second)
            logger.warning(f"Slow operation: {self.operation_name} took {duration:.2f}s")
        elif duration > 0.1:  # Log medium queries (> 100ms)
            logger.info(f"Medium operation: {self.operation_name} took {duration:.2f}s")
        else:
            logger.debug(f"Fast operation: {self.operation_name} took {duration:.2f}s")

def performance_monitor(operation_name: str = None):
    """Decorator for monitoring function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with PerformanceMonitor(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

class CacheManager:
    """Manages Redis caching with automatic serialization."""
    
    @staticmethod
    def get_key(prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments."""
        return f"agora:{prefix}:{':'.join(map(str, args))}"
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not redis_client:
            return default
        
        try:
            value = redis_client.get(key)
            if value is None:
                return default
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        if not redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            return redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache."""
        if not redis_client:
            return False
        
        try:
            return redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not redis_client:
            return 0
        
        try:
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

class OptimizedQueries:
    """Optimized database queries with caching and performance monitoring."""
    
    @staticmethod
    @performance_monitor("get_active_polls")
    def get_active_polls(db: Session, team_id: str, limit: int = 50) -> List[Poll]:
        """Get active polls for a team with optimized loading."""
        cache_key = CacheManager.get_key("active_polls", team_id, limit)
        
        # Try cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Query with eager loading
        polls = db.query(Poll).filter(
            and_(
                Poll.team_id == team_id,
                Poll.status == "active"
            )
        ).options(
            joinedload(Poll.options),
            selectinload(Poll.voted_users)
        ).order_by(Poll.created_at.desc()).limit(limit).all()
        
        # Cache result
        poll_data = [{
            'id': poll.id,
            'question': poll.question,
            'team_id': poll.team_id,
            'channel_id': poll.channel_id,
            'creator_id': poll.creator_id,
            'vote_type': poll.vote_type,
            'status': poll.status,
            'created_at': poll.created_at.isoformat(),
            'message_ts': poll.message_ts,
            'options': [{'id': opt.id, 'text': opt.text, 'vote_count': opt.vote_count} for opt in poll.options],
            'voter_count': len(poll.voted_users)
        } for poll in polls]
        
        CacheManager.set(cache_key, poll_data, ttl=60)  # Cache for 1 minute
        return polls
    
    @staticmethod
    @performance_monitor("get_poll_with_details")
    def get_poll_with_details(db: Session, poll_id: int) -> Optional[Poll]:
        """Get poll with all related data in a single query."""
        cache_key = CacheManager.get_key("poll_details", poll_id)
        
        # Try cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            # Convert back to Poll object if needed
            pass
        
        # Query with all related data
        poll = db.query(Poll).filter(Poll.id == poll_id).options(
            joinedload(Poll.options),
            joinedload(Poll.voted_users),
            joinedload(Poll.analytics),
            joinedload(Poll.shares)
        ).first()
        
        if poll:
            # Cache the result
            CacheManager.set(cache_key, {
                'id': poll.id,
                'question': poll.question,
                'team_id': poll.team_id,
                'channel_id': poll.channel_id,
                'creator_id': poll.creator_id,
                'vote_type': poll.vote_type,
                'status': poll.status,
                'created_at': poll.created_at.isoformat(),
                'ended_at': poll.ended_at.isoformat() if poll.ended_at else None,
                'message_ts': poll.message_ts,
                'options': [{'id': opt.id, 'text': opt.text, 'vote_count': opt.vote_count} for opt in poll.options],
                'voter_count': len(poll.voted_users)
            }, ttl=300)  # Cache for 5 minutes
        
        return poll
    
    @staticmethod
    @performance_monitor("check_user_voted")
    def check_user_voted(db: Session, poll_id: int, user_id: str) -> bool:
        """Check if user has voted on a poll (optimized)."""
        cache_key = CacheManager.get_key("user_voted", poll_id, user_id)
        
        # Try cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Use exists() for better performance
        voted = db.query(VotedUser).filter(
            and_(
                VotedUser.poll_id == poll_id,
                VotedUser.user_id == user_id
            )
        ).first() is not None
        
        # Cache result
        CacheManager.set(cache_key, voted, ttl=3600)  # Cache for 1 hour
        return voted
    
    @staticmethod
    @performance_monitor("get_user_role")
    def get_user_role(db: Session, user_id: str, team_id: str) -> str:
        """Get user role with caching."""
        cache_key = CacheManager.get_key("user_role", user_id, team_id)
        
        # Try cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Query user role
        user_role = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.team_id == team_id,
                UserRole.is_active == True
            )
        ).first()
        
        role = user_role.role if user_role else "user"
        
        # Cache result
        CacheManager.set(cache_key, role, ttl=1800)  # Cache for 30 minutes
        return role
    
    @staticmethod
    @performance_monitor("get_poll_analytics")
    def get_poll_analytics(db: Session, poll_id: int) -> Dict[str, Any]:
        """Get comprehensive poll analytics."""
        cache_key = CacheManager.get_key("poll_analytics", poll_id)
        
        # Try cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Use subqueries for better performance
        total_votes = db.query(func.count(UserVote.id)).filter(UserVote.poll_id == poll_id).scalar()
        unique_voters = db.query(func.count(VotedUser.id)).filter(VotedUser.poll_id == poll_id).scalar()
        
        # Get vote distribution
        vote_distribution = db.query(
            PollOption.text,
            PollOption.vote_count,
            func.round(PollOption.vote_count * 100.0 / func.nullif(total_votes, 0), 2).label('percentage')
        ).join(Poll).filter(Poll.id == poll_id).all()
        
        # Get voting timeline (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        hourly_votes = db.query(
            func.date_trunc('hour', UserVote.voted_at).label('hour'),
            func.count(UserVote.id).label('votes')
        ).filter(
            and_(
                UserVote.poll_id == poll_id,
                UserVote.voted_at >= yesterday
            )
        ).group_by('hour').order_by('hour').all()
        
        analytics = {
            'total_votes': total_votes,
            'unique_voters': unique_voters,
            'vote_distribution': [
                {'option': dist.text, 'votes': dist.vote_count, 'percentage': float(dist.percentage or 0)}
                for dist in vote_distribution
            ],
            'hourly_votes': [
                {'hour': hour.isoformat(), 'votes': votes}
                for hour, votes in hourly_votes
            ]
        }
        
        # Cache result
        CacheManager.set(cache_key, analytics, ttl=300)  # Cache for 5 minutes
        return analytics
    
    @staticmethod
    @performance_monitor("bulk_update_vote_counts")
    def bulk_update_vote_counts(db: Session, poll_id: int):
        """Bulk update vote counts for all options in a poll."""
        # Use raw SQL for better performance
        db.execute(text("""
            UPDATE poll_options 
            SET vote_count = (
                SELECT COUNT(*) 
                FROM user_votes 
                WHERE user_votes.option_id = poll_options.id
            )
            WHERE poll_id = :poll_id
        """), {'poll_id': poll_id})
        
        # Clear related caches
        CacheManager.clear_pattern(f"agora:poll_*:{poll_id}:*")
        CacheManager.clear_pattern(f"agora:active_polls:*")
    
    @staticmethod
    @performance_monitor("get_user_notifications")
    def get_user_notifications(db: Session, user_id: str, team_id: str, limit: int = 20) -> List[Notification]:
        """Get user notifications with pagination."""
        cache_key = CacheManager.get_key("user_notifications", user_id, team_id, limit)
        
        # Try cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            return cached_result
        
        notifications = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.team_id == team_id
            )
        ).order_by(Notification.sent_at.desc()).limit(limit).all()
        
        # Cache result
        notification_data = [{
            'id': notif.id,
            'poll_id': notif.poll_id,
            'notification_type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'sent_at': notif.sent_at.isoformat(),
            'read_at': notif.read_at.isoformat() if notif.read_at else None
        } for notif in notifications]
        
        CacheManager.set(cache_key, notification_data, ttl=300)  # Cache for 5 minutes
        return notifications

@contextmanager
def db_transaction(db: Session):
    """Context manager for database transactions with automatic rollback."""
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        db.close()

def invalidate_poll_cache(poll_id: int):
    """Invalidate all cache entries related to a poll."""
    patterns = [
        f"agora:poll_*:{poll_id}:*",
        f"agora:active_polls:*",
        f"agora:poll_analytics:{poll_id}",
        f"agora:user_voted:{poll_id}:*"
    ]
    
    for pattern in patterns:
        CacheManager.clear_pattern(pattern)

def invalidate_user_cache(user_id: str, team_id: str):
    """Invalidate all cache entries related to a user."""
    patterns = [
        f"agora:user_role:{user_id}:{team_id}",
        f"agora:user_notifications:{user_id}:{team_id}:*",
        f"agora:user_voted:*:{user_id}"
    ]
    
    for pattern in patterns:
        CacheManager.clear_pattern(pattern)

# Performance monitoring decorator for external use
def monitor_performance(operation_name: str = None):
    """Decorator for monitoring external function performance."""
    return performance_monitor(operation_name)