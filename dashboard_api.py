"""
Admin dashboard API endpoints for Agora Slack app.
Provides REST API for the web-based admin dashboard.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import SessionLocal, Poll, PollOption, UserVote, VotedUser, UserRole, TeamSettings
from performance import OptimizedQueries
from search_utils import search_polls, get_poll_history, get_popular_polls, get_user_participation_stats
from export_utils import export_poll_data, export_multiple_polls_data
from templates import get_template_by_id, get_templates_by_category, get_popular_templates
from scheduler import get_scheduled_polls, schedule_poll_creation, cancel_scheduled_poll
from poll_management import duplicate_poll, edit_poll_question, get_poll_edit_permissions
from config_validator import validate_configuration, get_configuration_status
from security import generate_security_report
from monitoring import get_health, get_metrics

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Pydantic models
class PollCreateRequest(BaseModel):
    question: str
    options: List[str]
    vote_type: str = "single"
    team_id: str
    channel_id: str
    creator_id: str

class PollUpdateRequest(BaseModel):
    question: Optional[str] = None
    status: Optional[str] = None

class UserRoleUpdateRequest(BaseModel):
    team_id: str
    role: str

class TemplateCreateRequest(BaseModel):
    name: str
    description: str
    category: str
    question: str
    options: List[str]
    vote_type: str = "single"
    tags: List[str] = []

class ScheduledPollRequest(BaseModel):
    team_id: str
    channel_id: str
    creator_id: str
    poll_data: Dict[str, Any]
    schedule_type: str
    scheduled_time: str
    cron_expression: Optional[str] = None

class ExportRequest(BaseModel):
    poll_ids: List[int]
    format: str = "csv"
    include_voter_ids: bool = False
    include_analytics: bool = True
    anonymize: bool = True

# Router
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token."""
    # In a real implementation, verify JWT token and check admin permissions
    # For now, we'll skip actual verification
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Extract user info from token (mock implementation)
    return {
        "user_id": "admin_user",
        "team_id": "admin_team",
        "role": "admin"
    }

# Dashboard Overview
@router.get("/overview/stats")
async def get_overview_stats(
    period: str = Query("30d"),
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get dashboard overview statistics."""
    try:
        # Calculate date range
        if period == "7d":
            date_from = datetime.now() - timedelta(days=7)
        elif period == "30d":
            date_from = datetime.now() - timedelta(days=30)
        elif period == "90d":
            date_from = datetime.now() - timedelta(days=90)
        else:
            date_from = datetime.now() - timedelta(days=30)

        # Get statistics
        total_polls = db.query(Poll).count()
        active_polls = db.query(Poll).filter(Poll.status == "active").count()
        
        # Calculate total votes
        total_votes = db.query(VotedUser).count()
        
        # Calculate active users (users who voted in the period)
        active_users = db.query(VotedUser).filter(
            VotedUser.voted_at >= date_from
        ).distinct(VotedUser.user_id).count()
        
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
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get activity chart data."""
    try:
        # This would calculate actual activity data
        # For now, return mock data
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
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get recent activity."""
    try:
        # Get recent polls
        recent_polls = db.query(Poll).order_by(Poll.created_at.desc()).limit(limit).all()
        
        activities = []
        for poll in recent_polls:
            activities.append({
                "type": "poll_created",
                "title": "New poll created",
                "description": f'"{poll.question}" by @{poll.creator_id}',
                "time": f"{(datetime.now() - poll.created_at).days} days ago",
                "icon": "fas fa-plus",
                "color": "bg-success"
            })
        
        return activities
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent activity")

# Poll Management
@router.get("/polls")
async def get_polls(
    page: int = Query(1),
    limit: int = Query(20),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    creator: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get polls with filtering and pagination."""
    try:
        # Build query
        query = db.query(Poll)
        
        # Apply filters
        if status:
            query = query.filter(Poll.status == status)
        if type:
            query = query.filter(Poll.vote_type == type)
        if creator:
            query = query.filter(Poll.creator_id.ilike(f"%{creator}%"))
        if date_from:
            query = query.filter(Poll.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Poll.created_at <= datetime.fromisoformat(date_to))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        polls = query.order_by(Poll.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # Format response
        poll_data = []
        for poll in polls:
            total_votes = sum(option.vote_count for option in poll.options)
            poll_data.append({
                "id": poll.id,
                "question": poll.question,
                "vote_type": poll.vote_type,
                "status": poll.status,
                "votes": total_votes,
                "created": poll.created_at.isoformat(),
                "ended": poll.ended_at.isoformat() if poll.ended_at else None,
                "creator": poll.creator_id,
                "team_id": poll.team_id,
                "channel_id": poll.channel_id
            })
        
        return {
            "polls": poll_data,
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Error getting polls: {e}")
        raise HTTPException(status_code=500, detail="Failed to get polls")

@router.get("/polls/{poll_id}")
async def get_poll(
    poll_id: int,
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Get poll details."""
    try:
        poll = OptimizedQueries.get_poll_with_details(db, poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        total_votes = sum(option.vote_count for option in poll.options)
        
        return {
            "id": poll.id,
            "question": poll.question,
            "vote_type": poll.vote_type,
            "status": poll.status,
            "total_votes": total_votes,
            "created_at": poll.created_at.isoformat(),
            "ended_at": poll.ended_at.isoformat() if poll.ended_at else None,
            "creator_id": poll.creator_id,
            "team_id": poll.team_id,
            "channel_id": poll.channel_id,
            "message_ts": poll.message_ts,
            "options": [
                {
                    "id": option.id,
                    "text": option.text,
                    "vote_count": option.vote_count,
                    "order_index": option.order_index
                }
                for option in poll.options
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get poll")

@router.put("/polls/{poll_id}")
async def update_poll(
    poll_id: int,
    update_data: PollUpdateRequest,
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Update poll."""
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Update fields
        if update_data.question:
            success = edit_poll_question(poll_id, update_data.question, admin_user["user_id"])
            if not success:
                raise HTTPException(status_code=400, detail="Failed to update question")
        
        if update_data.status:
            poll.status = update_data.status
            if update_data.status == "ended":
                poll.ended_at = datetime.now()
        
        db.commit()
        
        return {"message": "Poll updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update poll")

@router.delete("/polls/{poll_id}")
async def delete_poll(
    poll_id: int,
    admin_user: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """Delete poll."""
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Delete related data
        db.query(UserVote).filter(UserVote.poll_id == poll_id).delete()
        db.query(VotedUser).filter(VotedUser.poll_id == poll_id).delete()
        db.query(PollOption).filter(PollOption.poll_id == poll_id).delete()
        db.delete(poll)
        db.commit()
        
        return {"message": "Poll deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete poll")

@router.post("/polls/{poll_id}/duplicate")
async def duplicate_poll_endpoint(
    poll_id: int,
    options: Dict[str, Any] = {},
    admin_user: dict = Depends(verify_admin_token)
):
    """Duplicate poll."""
    try:
        new_poll_id = duplicate_poll(
            poll_id=poll_id,
            new_question=options.get("new_question"),
            team_id=options.get("team_id"),
            channel_id=options.get("channel_id"),
            creator_id=admin_user["user_id"]
        )
        
        if not new_poll_id:
            raise HTTPException(status_code=400, detail="Failed to duplicate poll")
        
        return {"message": "Poll duplicated successfully", "new_poll_id": new_poll_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate poll")

@router.post("/polls/export")
async def export_polls(
    export_request: ExportRequest,
    admin_user: dict = Depends(verify_admin_token)
):
    """Export polls to file."""
    try:
        if len(export_request.poll_ids) == 1:
            # Single poll export
            file_data = export_poll_data(
                poll_id=export_request.poll_ids[0],
                format_type=export_request.format,
                include_voter_ids=export_request.include_voter_ids,
                include_analytics=export_request.include_analytics,
                anonymize=export_request.anonymize
            )
        else:
            # Multiple polls export
            file_data = export_multiple_polls_data(
                poll_ids=export_request.poll_ids,
                format_type=export_request.format,
                include_analytics=export_request.include_analytics,
                anonymize=export_request.anonymize
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

# Search
@router.get("/search/polls")
async def search_polls_endpoint(
    q: str = Query(""),
    team_id: str = Query(""),
    search_type: str = Query("all"),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(20),
    admin_user: dict = Depends(verify_admin_token)
):
    """Search polls."""
    try:
        filters = {}
        if status:
            filters["status"] = status
        
        results, total = search_polls(
            team_id=team_id or admin_user["team_id"],
            query=q,
            search_type=search_type,
            filters=filters,
            limit=limit,
            offset=(page - 1) * limit
        )
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Error searching polls: {e}")
        raise HTTPException(status_code=500, detail="Failed to search polls")

# Templates
@router.get("/templates")
async def get_templates(
    category: str = Query(""),
    admin_user: dict = Depends(verify_admin_token)
):
    """Get poll templates."""
    try:
        if category:
            templates = get_templates_by_category(category)
        else:
            from templates import template_manager
            templates = template_manager.get_all_templates()
        
        return {
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category.value,
                    "question": template.question,
                    "options": template.options,
                    "vote_type": template.vote_type,
                    "tags": template.tags,
                    "usage_count": template.usage_count
                }
                for template in templates
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")

# System Health
@router.get("/system/health")
async def get_system_health(admin_user: dict = Depends(verify_admin_token)):
    """Get system health status."""
    try:
        health_data = get_health()
        return health_data
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@router.get("/system/metrics")
async def get_system_metrics(admin_user: dict = Depends(verify_admin_token)):
    """Get system metrics."""
    try:
        metrics_data = get_metrics()
        return {"metrics": metrics_data}
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

# Security
@router.get("/security/report")
async def get_security_report(admin_user: dict = Depends(verify_admin_token)):
    """Get security audit report."""
    try:
        report = generate_security_report()
        return report
    except Exception as e:
        logger.error(f"Error getting security report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get security report")

@router.get("/security/config/validate")
async def validate_config(admin_user: dict = Depends(verify_admin_token)):
    """Validate configuration."""
    try:
        is_valid, report = validate_configuration()
        return {
            "valid": is_valid,
            "report": report,
            "status": get_configuration_status()
        }
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate configuration")

# Error handlers are handled by main app middleware