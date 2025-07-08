"""
Poll management API endpoints.
Separated from dashboard_api.py to follow Single Responsibility Principle.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import PollRepository, ValidationService, EventPublisher, get_service
from .auth import get_current_user

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/polls", tags=["polls"])


class PollCreateRequest(BaseModel):
    question: str
    options: List[str]
    vote_type: str = "single"
    team_id: str
    channel_id: str


class PollUpdateRequest(BaseModel):
    question: Optional[str] = None
    status: Optional[str] = None


class PollSearchRequest(BaseModel):
    query: str = ""
    team_id: str = ""
    search_type: str = "all"
    status: Optional[str] = None


# Poll CRUD operations
@router.get("")
async def get_polls(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    creator: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get polls with filtering and pagination."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if creator:
            filters['creator_id'] = creator
        if date_from:
            filters['date_from'] = datetime.fromisoformat(date_from)
        if date_to:
            filters['date_to'] = datetime.fromisoformat(date_to)
        
        # Get polls
        polls = poll_repo.get_polls(current_user['team_id'], filters)
        
        # Apply pagination
        total_count = len(polls)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_polls = polls[start_idx:end_idx]
        
        return {
            "polls": paginated_polls,
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Error getting polls: {e}")
        raise HTTPException(status_code=500, detail="Failed to get polls")


@router.get("/{poll_id}")
async def get_poll(
    poll_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get poll details."""
    try:
        poll_repo = get_service(PollRepository)
        
        poll = poll_repo.get_poll(poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Check if user has access to this poll
        if poll['team_id'] != current_user['team_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return poll
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get poll")


@router.post("")
async def create_poll(
    poll_request: PollCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create new poll."""
    try:
        # Validate request
        validation_service = get_service(ValidationService)
        validation_result = validation_service.validate({
            'question': poll_request.question,
            'options': poll_request.options,
            'vote_type': poll_request.vote_type
        })
        
        if not validation_result['valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {', '.join(validation_result['errors'])}"
            )
        
        # Create poll
        poll_repo = get_service(PollRepository)
        poll_data = {
            'question': poll_request.question,
            'options': poll_request.options,
            'vote_type': poll_request.vote_type,
            'team_id': poll_request.team_id,
            'channel_id': poll_request.channel_id,
            'creator_id': current_user['user_id']
        }
        
        poll_id = poll_repo.create_poll(poll_data)
        
        # Publish event
        event_publisher = get_service(EventPublisher)
        event_publisher.publish('poll_created', {
            'poll_id': poll_id,
            'creator_id': current_user['user_id'],
            'team_id': poll_request.team_id,
            'question': poll_request.question
        })
        
        return {
            "message": "Poll created successfully",
            "poll_id": poll_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating poll: {e}")
        raise HTTPException(status_code=500, detail="Failed to create poll")


@router.put("/{poll_id}")
async def update_poll(
    poll_id: int,
    update_request: PollUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update poll."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Check if poll exists and user has permission
        poll = poll_repo.get_poll(poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        if poll['creator_id'] != current_user['user_id'] and current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Prepare updates
        updates = {}
        if update_request.question:
            updates['question'] = update_request.question
        if update_request.status:
            updates['status'] = update_request.status
            if update_request.status == 'ended':
                updates['ended_at'] = datetime.now()
        
        # Update poll
        success = poll_repo.update_poll(poll_id, updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update poll")
        
        # Publish event
        event_publisher = get_service(EventPublisher)
        event_publisher.publish('poll_updated', {
            'poll_id': poll_id,
            'updated_by': current_user['user_id'],
            'updates': updates
        })
        
        return {"message": "Poll updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update poll")


@router.delete("/{poll_id}")
async def delete_poll(
    poll_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete poll."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Check if poll exists and user has permission
        poll = poll_repo.get_poll(poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        if poll['creator_id'] != current_user['user_id'] and current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Delete poll
        success = poll_repo.delete_poll(poll_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete poll")
        
        # Publish event
        event_publisher = get_service(EventPublisher)
        event_publisher.publish('poll_deleted', {
            'poll_id': poll_id,
            'deleted_by': current_user['user_id'],
            'team_id': poll['team_id']
        })
        
        return {"message": "Poll deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete poll")


@router.post("/{poll_id}/duplicate")
async def duplicate_poll(
    poll_id: int,
    options: Dict[str, Any] = {},
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Duplicate poll."""
    try:
        poll_repo = get_service(PollRepository)
        
        # Get original poll
        original_poll = poll_repo.get_poll(poll_id)
        if not original_poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Check permission
        if original_poll['team_id'] != current_user['team_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create duplicate poll data
        duplicate_data = {
            'question': options.get('new_question', f"Copy of {original_poll['question']}"),
            'options': [opt['text'] for opt in original_poll['options']],
            'vote_type': original_poll['vote_type'],
            'team_id': options.get('team_id', original_poll['team_id']),
            'channel_id': options.get('channel_id', original_poll['channel_id']),
            'creator_id': current_user['user_id']
        }
        
        new_poll_id = poll_repo.create_poll(duplicate_data)
        
        # Publish event
        event_publisher = get_service(EventPublisher)
        event_publisher.publish('poll_duplicated', {
            'original_poll_id': poll_id,
            'new_poll_id': new_poll_id,
            'duplicated_by': current_user['user_id']
        })
        
        return {
            "message": "Poll duplicated successfully",
            "new_poll_id": new_poll_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating poll {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate poll")


@router.post("/search")
async def search_polls(
    search_request: PollSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search polls."""
    try:
        # This would use the search service
        # For now, return basic search using poll repository
        poll_repo = get_service(PollRepository)
        
        filters = {}
        if search_request.status:
            filters['status'] = search_request.status
        
        polls = poll_repo.get_polls(
            search_request.team_id or current_user['team_id'],
            filters
        )
        
        # Simple text search
        if search_request.query:
            query_lower = search_request.query.lower()
            polls = [
                poll for poll in polls
                if query_lower in poll['question'].lower()
            ]
        
        return {
            "results": polls,
            "total": len(polls),
            "query": search_request.query
        }
    
    except Exception as e:
        logger.error(f"Error searching polls: {e}")
        raise HTTPException(status_code=500, detail="Failed to search polls")


# Poll statistics
@router.get("/{poll_id}/stats")
async def get_poll_stats(
    poll_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get poll statistics."""
    try:
        poll_repo = get_service(PollRepository)
        
        poll = poll_repo.get_poll(poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        # Check permission
        if poll['team_id'] != current_user['team_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate statistics
        total_votes = sum(opt['vote_count'] for opt in poll['options'])
        
        stats = {
            'poll_id': poll_id,
            'total_votes': total_votes,
            'option_stats': [
                {
                    'option_id': opt['id'],
                    'text': opt['text'],
                    'votes': opt['vote_count'],
                    'percentage': (opt['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                }
                for opt in poll['options']
            ],
            'status': poll['status'],
            'created_at': poll['created_at'],
            'ended_at': poll.get('ended_at')
        }
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll stats {poll_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get poll statistics")


# Note: Exception handlers should be added to the main FastAPI app, not the router
# These would be added in the main application factory