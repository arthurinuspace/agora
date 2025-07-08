"""
Poll search and history utilities for Agora Slack app.
Provides search functionality and poll history management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from models import Poll, PollOption, VotedUser, UserVote, SessionLocal
from performance import OptimizedQueries

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Types of search queries."""
    QUESTION = "question"
    OPTION = "option"
    CREATOR = "creator"
    CHANNEL = "channel"
    ALL = "all"

class SortOrder(Enum):
    """Sort order options."""
    CREATED_ASC = "created_asc"
    CREATED_DESC = "created_desc"
    VOTES_ASC = "votes_asc"
    VOTES_DESC = "votes_desc"
    ALPHABETICAL = "alphabetical"

class PollStatus(Enum):
    """Poll status filter options."""
    ALL = "all"
    ACTIVE = "active"
    ENDED = "ended"

@dataclass
class SearchFilters:
    """Search filter configuration."""
    status: PollStatus = PollStatus.ALL
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    vote_type: Optional[str] = None
    min_votes: Optional[int] = None
    max_votes: Optional[int] = None
    creator_id: Optional[str] = None
    channel_id: Optional[str] = None
    has_voted: Optional[bool] = None
    user_id_for_voted_filter: Optional[str] = None

@dataclass
class SearchResult:
    """Search result data structure."""
    poll_id: int
    question: str
    vote_type: str
    status: str
    total_votes: int
    option_count: int
    created_at: datetime
    ended_at: Optional[datetime]
    creator_id: str
    channel_id: str
    team_id: str
    relevance_score: float = 0.0

class PollSearchEngine:
    """Handles poll search and history functionality."""
    
    def __init__(self):
        self.max_results = 100
    
    def search_polls(self, 
                    team_id: str,
                    query: str = "",
                    search_type: SearchType = SearchType.ALL,
                    filters: SearchFilters = None,
                    sort_order: SortOrder = SortOrder.CREATED_DESC,
                    limit: int = 50,
                    offset: int = 0) -> Tuple[List[SearchResult], int]:
        """Search polls with various filters and sorting options."""
        try:
            db = SessionLocal()
            filters = filters or SearchFilters()
            
            # Base query
            base_query = db.query(Poll).filter(Poll.team_id == team_id)
            
            # Apply text search
            if query.strip():
                search_conditions = []
                
                if search_type in [SearchType.QUESTION, SearchType.ALL]:
                    search_conditions.append(Poll.question.ilike(f"%{query}%"))
                
                if search_type in [SearchType.CREATOR, SearchType.ALL]:
                    search_conditions.append(Poll.creator_id.ilike(f"%{query}%"))
                
                if search_type in [SearchType.CHANNEL, SearchType.ALL]:
                    search_conditions.append(Poll.channel_id.ilike(f"%{query}%"))
                
                if search_type in [SearchType.OPTION, SearchType.ALL]:
                    # Search in poll options
                    option_subquery = db.query(PollOption.poll_id).filter(
                        PollOption.text.ilike(f"%{query}%")
                    ).subquery()
                    search_conditions.append(Poll.id.in_(option_subquery))
                
                if search_conditions:
                    base_query = base_query.filter(or_(*search_conditions))
            
            # Apply filters
            base_query = self._apply_filters(base_query, filters, db)
            
            # Get total count
            total_count = base_query.count()
            
            # Apply sorting
            base_query = self._apply_sorting(base_query, sort_order, db)
            
            # Apply pagination
            base_query = base_query.offset(offset).limit(min(limit, self.max_results))
            
            # Execute query
            polls = base_query.all()
            
            # Convert to search results
            results = []
            for poll in polls:
                total_votes = sum(option.vote_count for option in poll.options)
                
                result = SearchResult(
                    poll_id=poll.id,
                    question=poll.question,
                    vote_type=poll.vote_type,
                    status=poll.status,
                    total_votes=total_votes,
                    option_count=len(poll.options),
                    created_at=poll.created_at,
                    ended_at=poll.ended_at,
                    creator_id=poll.creator_id,
                    channel_id=poll.channel_id,
                    team_id=poll.team_id,
                    relevance_score=self._calculate_relevance(poll, query, search_type)
                )
                results.append(result)
            
            # Sort by relevance if text search was performed
            if query.strip() and search_type != SearchType.ALL:
                results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results, total_count
        
        except Exception as e:
            logger.error(f"Error searching polls: {e}")
            return [], 0
        
        finally:
            db.close()
    
    def get_poll_history(self,
                        team_id: str,
                        user_id: str = None,
                        channel_id: str = None,
                        days: int = 30,
                        include_voted_only: bool = False) -> List[SearchResult]:
        """Get poll history for a team, user, or channel."""
        try:
            db = SessionLocal()
            
            # Date filter
            date_from = datetime.now() - timedelta(days=days)
            
            # Base query
            base_query = db.query(Poll).filter(
                and_(
                    Poll.team_id == team_id,
                    Poll.created_at >= date_from
                )
            )
            
            # Filter by channel if specified
            if channel_id:
                base_query = base_query.filter(Poll.channel_id == channel_id)
            
            # Filter by user involvement if specified
            if user_id:
                if include_voted_only:
                    # Only polls where user voted
                    voted_poll_ids = db.query(VotedUser.poll_id).filter(
                        VotedUser.user_id == user_id
                    ).subquery()
                    base_query = base_query.filter(Poll.id.in_(voted_poll_ids))
                else:
                    # Polls created by user or where user voted
                    voted_poll_ids = db.query(VotedUser.poll_id).filter(
                        VotedUser.user_id == user_id
                    ).subquery()
                    base_query = base_query.filter(
                        or_(
                            Poll.creator_id == user_id,
                            Poll.id.in_(voted_poll_ids)
                        )
                    )
            
            # Order by creation date (newest first)
            base_query = base_query.order_by(desc(Poll.created_at))
            
            # Execute query
            polls = base_query.all()
            
            # Convert to search results
            results = []
            for poll in polls:
                total_votes = sum(option.vote_count for option in poll.options)
                
                result = SearchResult(
                    poll_id=poll.id,
                    question=poll.question,
                    vote_type=poll.vote_type,
                    status=poll.status,
                    total_votes=total_votes,
                    option_count=len(poll.options),
                    created_at=poll.created_at,
                    ended_at=poll.ended_at,
                    creator_id=poll.creator_id,
                    channel_id=poll.channel_id,
                    team_id=poll.team_id
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting poll history: {e}")
            return []
        
        finally:
            db.close()
    
    def get_popular_polls(self,
                         team_id: str,
                         days: int = 30,
                         limit: int = 10) -> List[SearchResult]:
        """Get most popular polls by vote count."""
        try:
            db = SessionLocal()
            
            # Date filter
            date_from = datetime.now() - timedelta(days=days)
            
            # Get polls with vote counts
            polls_with_votes = db.query(
                Poll,
                func.sum(PollOption.vote_count).label('total_votes')
            ).join(
                PollOption, Poll.id == PollOption.poll_id
            ).filter(
                and_(
                    Poll.team_id == team_id,
                    Poll.created_at >= date_from
                )
            ).group_by(
                Poll.id
            ).order_by(
                desc('total_votes')
            ).limit(limit).all()
            
            # Convert to search results
            results = []
            for poll, total_votes in polls_with_votes:
                result = SearchResult(
                    poll_id=poll.id,
                    question=poll.question,
                    vote_type=poll.vote_type,
                    status=poll.status,
                    total_votes=total_votes or 0,
                    option_count=len(poll.options),
                    created_at=poll.created_at,
                    ended_at=poll.ended_at,
                    creator_id=poll.creator_id,
                    channel_id=poll.channel_id,
                    team_id=poll.team_id
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting popular polls: {e}")
            return []
        
        finally:
            db.close()
    
    def get_recent_polls(self,
                        team_id: str,
                        channel_id: str = None,
                        limit: int = 10) -> List[SearchResult]:
        """Get most recent polls."""
        try:
            db = SessionLocal()
            
            # Base query
            base_query = db.query(Poll).filter(Poll.team_id == team_id)
            
            # Filter by channel if specified
            if channel_id:
                base_query = base_query.filter(Poll.channel_id == channel_id)
            
            # Order by creation date (newest first)
            polls = base_query.order_by(desc(Poll.created_at)).limit(limit).all()
            
            # Convert to search results
            results = []
            for poll in polls:
                total_votes = sum(option.vote_count for option in poll.options)
                
                result = SearchResult(
                    poll_id=poll.id,
                    question=poll.question,
                    vote_type=poll.vote_type,
                    status=poll.status,
                    total_votes=total_votes,
                    option_count=len(poll.options),
                    created_at=poll.created_at,
                    ended_at=poll.ended_at,
                    creator_id=poll.creator_id,
                    channel_id=poll.channel_id,
                    team_id=poll.team_id
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting recent polls: {e}")
            return []
        
        finally:
            db.close()
    
    def get_user_participation_stats(self, team_id: str, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user participation statistics."""
        try:
            db = SessionLocal()
            
            # Date filter
            date_from = datetime.now() - timedelta(days=days)
            
            # Polls created by user
            created_polls = db.query(Poll).filter(
                and_(
                    Poll.team_id == team_id,
                    Poll.creator_id == user_id,
                    Poll.created_at >= date_from
                )
            ).count()
            
            # Polls voted in
            voted_polls = db.query(VotedUser).join(
                Poll, VotedUser.poll_id == Poll.id
            ).filter(
                and_(
                    Poll.team_id == team_id,
                    VotedUser.user_id == user_id,
                    Poll.created_at >= date_from
                )
            ).count()
            
            # Total votes cast
            votes_cast = db.query(UserVote).join(
                Poll, UserVote.poll_id == Poll.id
            ).filter(
                and_(
                    Poll.team_id == team_id,
                    UserVote.user_id == user_id,
                    Poll.created_at >= date_from
                )
            ).count()
            
            # Most active day of week
            vote_days = db.query(
                func.strftime('%w', VotedUser.voted_at).label('day_of_week'),
                func.count(VotedUser.id).label('vote_count')
            ).join(
                Poll, VotedUser.poll_id == Poll.id
            ).filter(
                and_(
                    Poll.team_id == team_id,
                    VotedUser.user_id == user_id,
                    VotedUser.voted_at >= date_from
                )
            ).group_by('day_of_week').order_by(desc('vote_count')).first()
            
            most_active_day = None
            if vote_days:
                days_map = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                most_active_day = days_map[int(vote_days[0])]
            
            return {
                'polls_created': created_polls,
                'polls_voted_in': voted_polls,
                'total_votes_cast': votes_cast,
                'most_active_day': most_active_day,
                'participation_rate': round((voted_polls / max(created_polls + voted_polls, 1)) * 100, 2)
            }
        
        except Exception as e:
            logger.error(f"Error getting user participation stats: {e}")
            return {}
        
        finally:
            db.close()
    
    def _apply_filters(self, query, filters: SearchFilters, db: Session):
        """Apply search filters to query."""
        # Status filter
        if filters.status != PollStatus.ALL:
            query = query.filter(Poll.status == filters.status.value)
        
        # Date range filter
        if filters.date_from:
            query = query.filter(Poll.created_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(Poll.created_at <= filters.date_to)
        
        # Vote type filter
        if filters.vote_type:
            query = query.filter(Poll.vote_type == filters.vote_type)
        
        # Creator filter
        if filters.creator_id:
            query = query.filter(Poll.creator_id == filters.creator_id)
        
        # Channel filter
        if filters.channel_id:
            query = query.filter(Poll.channel_id == filters.channel_id)
        
        # Vote count filters
        if filters.min_votes is not None or filters.max_votes is not None:
            # Subquery to calculate total votes per poll
            vote_counts = db.query(
                PollOption.poll_id,
                func.sum(PollOption.vote_count).label('total_votes')
            ).group_by(PollOption.poll_id).subquery()
            
            query = query.join(vote_counts, Poll.id == vote_counts.c.poll_id)
            
            if filters.min_votes is not None:
                query = query.filter(vote_counts.c.total_votes >= filters.min_votes)
            if filters.max_votes is not None:
                query = query.filter(vote_counts.c.total_votes <= filters.max_votes)
        
        # Has voted filter
        if filters.has_voted is not None and filters.user_id_for_voted_filter:
            voted_poll_ids = db.query(VotedUser.poll_id).filter(
                VotedUser.user_id == filters.user_id_for_voted_filter
            ).subquery()
            
            if filters.has_voted:
                query = query.filter(Poll.id.in_(voted_poll_ids))
            else:
                query = query.filter(~Poll.id.in_(voted_poll_ids))
        
        return query
    
    def _apply_sorting(self, query, sort_order: SortOrder, db: Session):
        """Apply sorting to query."""
        if sort_order == SortOrder.CREATED_ASC:
            return query.order_by(asc(Poll.created_at))
        elif sort_order == SortOrder.CREATED_DESC:
            return query.order_by(desc(Poll.created_at))
        elif sort_order == SortOrder.ALPHABETICAL:
            return query.order_by(asc(Poll.question))
        elif sort_order in [SortOrder.VOTES_ASC, SortOrder.VOTES_DESC]:
            # Join with vote counts
            vote_counts = db.query(
                PollOption.poll_id,
                func.sum(PollOption.vote_count).label('total_votes')
            ).group_by(PollOption.poll_id).subquery()
            
            query = query.outerjoin(vote_counts, Poll.id == vote_counts.c.poll_id)
            
            if sort_order == SortOrder.VOTES_ASC:
                return query.order_by(asc(vote_counts.c.total_votes))
            else:
                return query.order_by(desc(vote_counts.c.total_votes))
        
        return query.order_by(desc(Poll.created_at))  # Default
    
    def _calculate_relevance(self, poll: Poll, query: str, search_type: SearchType) -> float:
        """Calculate relevance score for search results."""
        if not query.strip():
            return 0.0
        
        score = 0.0
        query_lower = query.lower()
        
        # Question relevance
        if search_type in [SearchType.QUESTION, SearchType.ALL]:
            question_lower = poll.question.lower()
            if query_lower in question_lower:
                # Exact match gets higher score
                if query_lower == question_lower:
                    score += 100
                # Starts with query gets medium score
                elif question_lower.startswith(query_lower):
                    score += 75
                # Contains query gets lower score
                else:
                    score += 50
        
        # Creator relevance
        if search_type in [SearchType.CREATOR, SearchType.ALL]:
            if query_lower in poll.creator_id.lower():
                score += 25
        
        # Channel relevance
        if search_type in [SearchType.CHANNEL, SearchType.ALL]:
            if query_lower in poll.channel_id.lower():
                score += 25
        
        # Option relevance
        if search_type in [SearchType.OPTION, SearchType.ALL]:
            for option in poll.options:
                if query_lower in option.text.lower():
                    score += 30
                    break
        
        # Boost score for recent polls
        days_old = (datetime.now() - poll.created_at).days
        if days_old < 7:
            score += 10
        elif days_old < 30:
            score += 5
        
        # Boost score for active polls
        if poll.status == 'active':
            score += 15
        
        return score

# Global search engine instance
search_engine = PollSearchEngine()

# Utility functions
def search_polls(team_id: str, query: str = "", search_type: str = "all",
                filters: Dict[str, Any] = None, sort_order: str = "created_desc",
                limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    """Search polls and return results."""
    try:
        search_type_enum = SearchType(search_type)
        sort_order_enum = SortOrder(sort_order)
        
        # Convert filters dict to SearchFilters object
        search_filters = SearchFilters()
        if filters:
            if 'status' in filters:
                search_filters.status = PollStatus(filters['status'])
            if 'date_from' in filters and filters['date_from']:
                search_filters.date_from = datetime.fromisoformat(filters['date_from'])
            if 'date_to' in filters and filters['date_to']:
                search_filters.date_to = datetime.fromisoformat(filters['date_to'])
            if 'vote_type' in filters:
                search_filters.vote_type = filters['vote_type']
            if 'creator_id' in filters:
                search_filters.creator_id = filters['creator_id']
            if 'channel_id' in filters:
                search_filters.channel_id = filters['channel_id']
        
        results, total = search_engine.search_polls(
            team_id, query, search_type_enum, search_filters, sort_order_enum, limit, offset
        )
        
        # Convert to dict format
        results_dict = []
        for result in results:
            results_dict.append({
                'poll_id': result.poll_id,
                'question': result.question,
                'vote_type': result.vote_type,
                'status': result.status,
                'total_votes': result.total_votes,
                'option_count': result.option_count,
                'created_at': result.created_at.isoformat(),
                'ended_at': result.ended_at.isoformat() if result.ended_at else None,
                'creator_id': result.creator_id,
                'channel_id': result.channel_id,
                'team_id': result.team_id,
                'relevance_score': result.relevance_score
            })
        
        return results_dict, total
    
    except ValueError as e:
        logger.error(f"Invalid search parameters: {e}")
        return [], 0

def get_poll_history(team_id: str, user_id: str = None, channel_id: str = None,
                    days: int = 30, include_voted_only: bool = False) -> List[Dict[str, Any]]:
    """Get poll history."""
    results = search_engine.get_poll_history(team_id, user_id, channel_id, days, include_voted_only)
    
    return [{
        'poll_id': result.poll_id,
        'question': result.question,
        'vote_type': result.vote_type,
        'status': result.status,
        'total_votes': result.total_votes,
        'option_count': result.option_count,
        'created_at': result.created_at.isoformat(),
        'ended_at': result.ended_at.isoformat() if result.ended_at else None,
        'creator_id': result.creator_id,
        'channel_id': result.channel_id,
        'team_id': result.team_id
    } for result in results]

def get_popular_polls(team_id: str, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
    """Get popular polls."""
    results = search_engine.get_popular_polls(team_id, days, limit)
    
    return [{
        'poll_id': result.poll_id,
        'question': result.question,
        'vote_type': result.vote_type,
        'status': result.status,
        'total_votes': result.total_votes,
        'option_count': result.option_count,
        'created_at': result.created_at.isoformat(),
        'ended_at': result.ended_at.isoformat() if result.ended_at else None,
        'creator_id': result.creator_id,
        'channel_id': result.channel_id,
        'team_id': result.team_id
    } for result in results]

def get_user_participation_stats(team_id: str, user_id: str, days: int = 30) -> Dict[str, Any]:
    """Get user participation statistics."""
    return search_engine.get_user_participation_stats(team_id, user_id, days)