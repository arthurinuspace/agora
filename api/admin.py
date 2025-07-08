"""
Admin API endpoints.
Separated from dashboard_api.py to follow Single Responsibility Principle.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from services import (
    PollRepository, ExportService, MonitoringService, 
    ConfigurationService, get_service
)
from .auth import require_admin

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/admin", tags=["admin"])


class ExportRequest(BaseModel):
    poll_ids: List[int]
    format: str = "csv"
    include_voter_ids: bool = False
    include_analytics: bool = True
    anonymize: bool = True


class SystemConfigRequest(BaseModel):
    key: str
    value: Any


# Dashboard overview
@router.get("/overview/stats")
async def get_overview_stats(
    period: str = Query("30d"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Get dashboard overview statistics."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Calculate date range
        date_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90
        }
        days = date_map.get(period, 30)
        date_from = datetime.now() - timedelta(days=days)
        
        # Get polls for the period
        filters = {"date_from": date_from}
        polls = poll_repo.get_polls(admin_user['team_id'], filters)
        
        # Calculate statistics
        total_polls = len(polls)
        active_polls = len([p for p in polls if p['status'] == 'active'])
        total_votes = sum(p.get('total_votes', 0) for p in polls)
        
        # Calculate unique voters (simplified)
        active_users = len(set(p['creator_id'] for p in polls))
        
        return {
            "total_polls": total_polls,
            "total_votes": total_votes,
            "active_users": active_users,
            "active_polls": active_polls,
            "period": period
        }
    
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get overview statistics")


@router.get("/overview/activity")
async def get_activity_chart(
    period: str = Query("7d"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Get activity chart data."""
    try:
        # Mock data for demonstration
        # In a real implementation, this would query actual activity data
        if period == "7d":
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            polls_created = [5, 8, 12, 7, 15, 3, 9]
            votes_cast = [45, 67, 89, 54, 123, 34, 78]
        elif period == "30d":
            labels = [f"Day {i}" for i in range(1, 31)]
            polls_created = [i % 10 + 2 for i in range(30)]
            votes_cast = [i % 50 + 20 for i in range(30)]
        else:
            labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
            polls_created = [25, 32, 28, 35]
            votes_cast = [234, 312, 287, 356]
        
        return {
            "labels": labels,
            "polls_created": polls_created,
            "votes_cast": votes_cast
        }
    
    except Exception as e:
        logger.error(f"Error getting activity chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to get activity data")


@router.get("/overview/recent")
async def get_recent_activity(
    limit: int = Query(10),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Get recent activity."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Get recent polls
        polls = poll_repo.get_polls(admin_user['team_id'])[:limit]
        
        activities = []
        for poll in polls:
            activities.append({
                "type": "poll_created",
                "title": "New poll created",
                "description": f'"{poll["question"]}" by @{poll["creator_id"]}',
                "time": f"{(datetime.now() - poll['created_at']).days} days ago",
                "icon": "fas fa-plus",
                "color": "bg-success"
            })
        
        return activities
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent activity")


# Export functionality
@router.post("/export")
async def export_polls(
    export_request: ExportRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Export polls to file."""
    try:
        export_service = get_service(ExportService)
        
        if len(export_request.poll_ids) == 1:
            # Single poll export
            file_data = export_service.export_poll(
                poll_id=export_request.poll_ids[0],
                format_type=export_request.format,
                options={
                    'include_voter_ids': export_request.include_voter_ids,
                    'include_analytics': export_request.include_analytics,
                    'anonymize': export_request.anonymize
                }
            )
        else:
            # Multiple polls export
            file_data = export_service.export_multiple_polls(
                poll_ids=export_request.poll_ids,
                format_type=export_request.format,
                options={
                    'include_analytics': export_request.include_analytics,
                    'anonymize': export_request.anonymize
                }
            )
        
        if not file_data:
            raise HTTPException(status_code=400, detail="Failed to export polls")
        
        # Create response with appropriate headers
        filename = f"polls_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"
        
        return FileResponse(
            path=None,
            filename=filename,
            content=file_data,
            media_type="application/octet-stream"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting polls: {e}")
        raise HTTPException(status_code=500, detail="Failed to export polls")


# System management
@router.get("/system/health")
async def get_system_health(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Get system health status."""
    try:
        monitoring_service = get_service(MonitoringService)
        health_data = monitoring_service.health_check()
        return health_data
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")


@router.get("/system/metrics")
async def get_system_metrics(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Get system metrics."""
    try:
        monitoring_service = get_service(MonitoringService)
        metrics_data = monitoring_service.get_metrics()
        return {"metrics": metrics_data}
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/system/config")
async def get_system_config(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Get system configuration."""
    try:
        config_service = get_service(ConfigurationService)
        validation_result = config_service.validate_config()
        
        return {
            "configuration_status": validation_result,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system configuration")


@router.post("/system/config")
async def update_system_config(
    config_request: SystemConfigRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Update system configuration."""
    try:
        config_service = get_service(ConfigurationService)
        
        success = config_service.set_config(config_request.key, config_request.value)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update configuration")
        
        return {
            "message": "Configuration updated successfully",
            "key": config_request.key,
            "updated_by": admin_user['user_id']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")


# User management
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    team_id: str = Query(None),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """List users."""
    try:
        # In a real implementation, this would query user database
        # For now, return mock data
        users = [
            {
                "user_id": f"user_{i}",
                "team_id": team_id or admin_user['team_id'],
                "role": "user" if i > 0 else "admin",
                "created_at": datetime.now() - timedelta(days=i),
                "last_active": datetime.now() - timedelta(hours=i)
            }
            for i in range(10)
        ]
        
        # Apply pagination
        total_count = len(users)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_users = users[start_idx:end_idx]
        
        return {
            "users": paginated_users,
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: Dict[str, Any],
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Update user role."""
    try:
        # In a real implementation, this would update user role in database
        return {
            "message": "User role updated successfully",
            "user_id": user_id,
            "new_role": role_data.get('role'),
            "updated_by": admin_user['user_id']
        }
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user role")


# Analytics
@router.get("/analytics/polls")
async def get_poll_analytics(
    period: str = Query("30d"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """Get poll analytics."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Get polls for analysis
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        date_from = datetime.now() - timedelta(days=days)
        
        filters = {"date_from": date_from}
        polls = poll_repo.get_polls(admin_user['team_id'], filters)
        
        # Calculate analytics
        total_polls = len(polls)
        avg_votes_per_poll = sum(p.get('total_votes', 0) for p in polls) / max(total_polls, 1)
        
        # Poll type distribution
        vote_types = {}
        for poll in polls:
            vote_type = poll.get('vote_type', 'single')
            vote_types[vote_type] = vote_types.get(vote_type, 0) + 1
        
        return {
            "period": period,
            "total_polls": total_polls,
            "avg_votes_per_poll": round(avg_votes_per_poll, 2),
            "vote_type_distribution": vote_types,
            "poll_status_distribution": {
                "active": len([p for p in polls if p['status'] == 'active']),
                "ended": len([p for p in polls if p['status'] == 'ended'])
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting poll analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get poll analytics")


# Note: Exception handlers should be added to the main FastAPI app, not the router
# These would be added in the main application factory