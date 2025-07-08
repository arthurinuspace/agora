"""
Authentication API endpoints.
Separated from dashboard_api.py to follow Single Responsibility Principle.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import AuthenticationService, get_service

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router
router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    token: str
    team_id: str


class UserInfo(BaseModel):
    user_id: str
    team_id: str
    role: str
    permissions: List[str] = []


class PermissionCheckRequest(BaseModel):
    resource: str
    action: str


# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    auth_service = get_service(AuthenticationService)
    
    user = auth_service.authenticate_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    
    return user


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role."""
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return current_user


# Authentication endpoints
@router.post("/login")
async def login(login_request: LoginRequest):
    """Authenticate user and return user info."""
    try:
        auth_service = get_service(AuthenticationService)
        
        user = auth_service.authenticate_user(login_request.token)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        # Get user roles
        roles = auth_service.get_user_roles(user['user_id'], login_request.team_id)
        
        return {
            "user_id": user['user_id'],
            "team_id": login_request.team_id,
            "role": user.get('role', 'user'),
            "roles": roles,
            "authenticated": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    try:
        auth_service = get_service(AuthenticationService)
        
        roles = auth_service.get_user_roles(
            current_user['user_id'],
            current_user['team_id']
        )
        
        return {
            "user_id": current_user['user_id'],
            "team_id": current_user['team_id'],
            "role": current_user.get('role', 'user'),
            "roles": roles,
            "authenticated": True
        }
    
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")


@router.post("/check-permission")
async def check_permission(
    permission_request: PermissionCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check if user has permission for specific resource and action."""
    try:
        auth_service = get_service(AuthenticationService)
        
        has_permission = auth_service.check_permissions(
            current_user['user_id'],
            permission_request.resource,
            permission_request.action
        )
        
        return {
            "has_permission": has_permission,
            "user_id": current_user['user_id'],
            "resource": permission_request.resource,
            "action": permission_request.action
        }
    
    except Exception as e:
        logger.error(f"Permission check error: {e}")
        raise HTTPException(status_code=500, detail="Permission check failed")


@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Refresh authentication token."""
    try:
        # In a real implementation, this would generate a new token
        return {
            "message": "Token refreshed successfully",
            "user_id": current_user['user_id'],
            "team_id": current_user['team_id']
        }
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout user."""
    try:
        # In a real implementation, this would invalidate the token
        return {
            "message": "Logged out successfully",
            "user_id": current_user['user_id']
        }
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


# Admin endpoints
@router.get("/admin/users")
async def list_users(
    team_id: str = None,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """List users (admin only)."""
    try:
        # In a real implementation, this would query user database
        return {
            "users": [],
            "total": 0,
            "team_id": team_id or admin_user['team_id']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.post("/admin/users/{user_id}/roles")
async def assign_role(
    user_id: str,
    role_data: Dict[str, Any],
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Assign role to user (admin only)."""
    try:
        # In a real implementation, this would update user roles
        return {
            "message": "Role assigned successfully",
            "user_id": user_id,
            "role": role_data.get('role'),
            "assigned_by": admin_user['user_id']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign role error: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign role")


# Note: Exception handlers should be added to the main FastAPI app, not the router
# These would be added in the main application factory