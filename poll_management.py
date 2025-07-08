"""
Poll duplication and editing utilities for Agora Slack app.
Handles poll copying, editing, and management operations.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from models import Poll, PollOption, SessionLocal
from performance import OptimizedQueries

logger = logging.getLogger(__name__)

@dataclass
class PollEditRequest:
    """Poll edit request data structure."""
    poll_id: int
    question: Optional[str] = None
    options: Optional[List[str]] = None
    vote_type: Optional[str] = None
    user_id: str = ""
    team_id: str = ""

class PollManager:
    """Handles poll duplication and editing operations."""
    
    def __init__(self):
        self.max_options = 20
        self.max_question_length = 500
    
    def duplicate_poll(self, 
                      poll_id: int, 
                      new_question: str = None,
                      team_id: str = None,
                      channel_id: str = None,
                      creator_id: str = None,
                      copy_votes: bool = False) -> Optional[int]:
        """Create a duplicate of an existing poll."""
        try:
            db = SessionLocal()
            
            # Get original poll
            original_poll = OptimizedQueries.get_poll_with_details(db, poll_id)
            if not original_poll:
                logger.error(f"Poll {poll_id} not found for duplication")
                return None
            
            # Create new poll with duplicated data
            new_poll = Poll(
                question=new_question or original_poll.question,
                team_id=team_id or original_poll.team_id,
                channel_id=channel_id or original_poll.channel_id,
                creator_id=creator_id or original_poll.creator_id,
                vote_type=original_poll.vote_type,
                status='active',
                created_at=datetime.now()
            )
            
            db.add(new_poll)
            db.flush()  # Get the new poll ID
            
            # Duplicate options
            for original_option in original_poll.options:
                new_option = PollOption(
                    poll_id=new_poll.id,
                    text=original_option.text,
                    vote_count=original_option.vote_count if copy_votes else 0,
                    order_index=original_option.order_index
                )
                db.add(new_option)
            
            db.commit()
            
            logger.info(f"Successfully duplicated poll {poll_id} as poll {new_poll.id}")
            return new_poll.id
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error duplicating poll {poll_id}: {e}")
            return None
        
        finally:
            db.close()
    
    def edit_poll_question(self, poll_id: int, new_question: str, user_id: str) -> bool:
        """Edit poll question (only for active polls)."""
        try:
            if len(new_question.strip()) == 0:
                logger.error("Question cannot be empty")
                return False
            
            if len(new_question) > self.max_question_length:
                logger.error(f"Question too long (max {self.max_question_length} characters)")
                return False
            
            db = SessionLocal()
            
            # Get poll
            poll = db.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                logger.error(f"Poll {poll_id} not found")
                return False
            
            # Check if poll is still active
            if poll.status != 'active':
                logger.error(f"Cannot edit ended poll {poll_id}")
                return False
            
            # Check if user has permission (creator or admin)
            user_role = OptimizedQueries.get_user_role(db, user_id, poll.team_id)
            if poll.creator_id != user_id and user_role != 'admin':
                logger.error(f"User {user_id} does not have permission to edit poll {poll_id}")
                return False
            
            # Update question
            old_question = poll.question
            poll.question = new_question.strip()
            db.commit()
            
            logger.info(f"Updated poll {poll_id} question from '{old_question}' to '{new_question}'")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error editing poll question: {e}")
            return False
        
        finally:
            db.close()
    
    def add_poll_option(self, poll_id: int, option_text: str, user_id: str) -> bool:
        """Add a new option to an active poll."""
        try:
            if len(option_text.strip()) == 0:
                logger.error("Option text cannot be empty")
                return False
            
            db = SessionLocal()
            
            # Get poll
            poll = OptimizedQueries.get_poll_with_details(db, poll_id)
            if not poll:
                logger.error(f"Poll {poll_id} not found")
                return False
            
            # Check if poll is still active
            if poll.status != 'active':
                logger.error(f"Cannot add option to ended poll {poll_id}")
                return False
            
            # Check if user has permission
            user_role = OptimizedQueries.get_user_role(db, user_id, poll.team_id)
            if poll.creator_id != user_id and user_role != 'admin':
                logger.error(f"User {user_id} does not have permission to edit poll {poll_id}")
                return False
            
            # Check option limit
            if len(poll.options) >= self.max_options:
                logger.error(f"Cannot add more options (max {self.max_options})")
                return False
            
            # Check for duplicate option
            option_text_clean = option_text.strip()
            existing_options = [opt.text.lower().strip() for opt in poll.options]
            if option_text_clean.lower() in existing_options:
                logger.error(f"Option '{option_text_clean}' already exists")
                return False
            
            # Get next order index
            max_order = max([opt.order_index for opt in poll.options], default=0)
            
            # Add new option
            new_option = PollOption(
                poll_id=poll_id,
                text=option_text_clean,
                vote_count=0,
                order_index=max_order + 1
            )
            
            db.add(new_option)
            db.commit()
            
            logger.info(f"Added option '{option_text_clean}' to poll {poll_id}")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding poll option: {e}")
            return False
        
        finally:
            db.close()
    
    def remove_poll_option(self, poll_id: int, option_id: int, user_id: str) -> bool:
        """Remove an option from an active poll (if no votes)."""
        try:
            db = SessionLocal()
            
            # Get poll and option
            poll = OptimizedQueries.get_poll_with_details(db, poll_id)
            if not poll:
                logger.error(f"Poll {poll_id} not found")
                return False
            
            option = db.query(PollOption).filter(
                PollOption.id == option_id,
                PollOption.poll_id == poll_id
            ).first()
            
            if not option:
                logger.error(f"Option {option_id} not found in poll {poll_id}")
                return False
            
            # Check if poll is still active
            if poll.status != 'active':
                logger.error(f"Cannot remove option from ended poll {poll_id}")
                return False
            
            # Check if user has permission
            user_role = OptimizedQueries.get_user_role(db, user_id, poll.team_id)
            if poll.creator_id != user_id and user_role != 'admin':
                logger.error(f"User {user_id} does not have permission to edit poll {poll_id}")
                return False
            
            # Check if option has votes
            if option.vote_count > 0:
                logger.error(f"Cannot remove option {option_id} because it has votes")
                return False
            
            # Check minimum options (must have at least 2)
            if len(poll.options) <= 2:
                logger.error("Cannot remove option - poll must have at least 2 options")
                return False
            
            # Remove option
            option_text = option.text
            db.delete(option)
            db.commit()
            
            logger.info(f"Removed option '{option_text}' from poll {poll_id}")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing poll option: {e}")
            return False
        
        finally:
            db.close()
    
    def edit_poll_option(self, poll_id: int, option_id: int, new_text: str, user_id: str) -> bool:
        """Edit an existing poll option (if no votes)."""
        try:
            if len(new_text.strip()) == 0:
                logger.error("Option text cannot be empty")
                return False
            
            db = SessionLocal()
            
            # Get poll and option
            poll = OptimizedQueries.get_poll_with_details(db, poll_id)
            if not poll:
                logger.error(f"Poll {poll_id} not found")
                return False
            
            option = db.query(PollOption).filter(
                PollOption.id == option_id,
                PollOption.poll_id == poll_id
            ).first()
            
            if not option:
                logger.error(f"Option {option_id} not found in poll {poll_id}")
                return False
            
            # Check if poll is still active
            if poll.status != 'active':
                logger.error(f"Cannot edit option in ended poll {poll_id}")
                return False
            
            # Check if user has permission
            user_role = OptimizedQueries.get_user_role(db, user_id, poll.team_id)
            if poll.creator_id != user_id and user_role != 'admin':
                logger.error(f"User {user_id} does not have permission to edit poll {poll_id}")
                return False
            
            # Check if option has votes (allow editing with warning)
            if option.vote_count > 0:
                logger.warning(f"Editing option {option_id} that has {option.vote_count} votes")
            
            # Check for duplicate option text
            new_text_clean = new_text.strip()
            existing_options = [opt.text.lower().strip() for opt in poll.options if opt.id != option_id]
            if new_text_clean.lower() in existing_options:
                logger.error(f"Option '{new_text_clean}' already exists")
                return False
            
            # Update option
            old_text = option.text
            option.text = new_text_clean
            db.commit()
            
            logger.info(f"Updated option {option_id} from '{old_text}' to '{new_text_clean}'")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error editing poll option: {e}")
            return False
        
        finally:
            db.close()
    
    def reorder_poll_options(self, poll_id: int, option_order: List[int], user_id: str) -> bool:
        """Reorder poll options."""
        try:
            db = SessionLocal()
            
            # Get poll
            poll = OptimizedQueries.get_poll_with_details(db, poll_id)
            if not poll:
                logger.error(f"Poll {poll_id} not found")
                return False
            
            # Check if poll is still active
            if poll.status != 'active':
                logger.error(f"Cannot reorder options in ended poll {poll_id}")
                return False
            
            # Check if user has permission
            user_role = OptimizedQueries.get_user_role(db, user_id, poll.team_id)
            if poll.creator_id != user_id and user_role != 'admin':
                logger.error(f"User {user_id} does not have permission to edit poll {poll_id}")
                return False
            
            # Validate option order
            existing_option_ids = [opt.id for opt in poll.options]
            if set(option_order) != set(existing_option_ids):
                logger.error("Option order list does not match existing options")
                return False
            
            # Update order indexes
            for new_index, option_id in enumerate(option_order):
                option = db.query(PollOption).filter(
                    PollOption.id == option_id,
                    PollOption.poll_id == poll_id
                ).first()
                
                if option:
                    option.order_index = new_index
            
            db.commit()
            
            logger.info(f"Reordered options for poll {poll_id}")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error reordering poll options: {e}")
            return False
        
        finally:
            db.close()
    
    def clone_poll_template(self, poll_id: int, team_id: str, channel_id: str, creator_id: str) -> Optional[int]:
        """Clone a poll as a template (without votes)."""
        return self.duplicate_poll(
            poll_id=poll_id,
            team_id=team_id,
            channel_id=channel_id,
            creator_id=creator_id,
            copy_votes=False
        )
    
    def get_poll_edit_permissions(self, poll_id: int, user_id: str) -> Dict[str, bool]:
        """Get what editing permissions a user has for a poll."""
        try:
            db = SessionLocal()
            
            poll = db.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                return {'can_edit': False, 'reason': 'Poll not found'}
            
            # Check if poll is active
            if poll.status != 'active':
                return {'can_edit': False, 'reason': 'Poll has ended'}
            
            # Check user role
            user_role = OptimizedQueries.get_user_role(db, user_id, poll.team_id)
            is_creator = poll.creator_id == user_id
            is_admin = user_role == 'admin'
            
            can_edit = is_creator or is_admin
            
            permissions = {
                'can_edit': can_edit,
                'can_edit_question': can_edit,
                'can_add_options': can_edit,
                'can_remove_options': can_edit,
                'can_edit_options': can_edit,
                'can_reorder_options': can_edit,
                'is_creator': is_creator,
                'is_admin': is_admin,
                'poll_status': poll.status
            }
            
            if not can_edit:
                if poll.status != 'active':
                    permissions['reason'] = 'Poll has ended'
                else:
                    permissions['reason'] = 'Insufficient permissions'
            
            return permissions
        
        except Exception as e:
            logger.error(f"Error checking poll edit permissions: {e}")
            return {'can_edit': False, 'reason': 'Error checking permissions'}
        
        finally:
            db.close()

# Global poll manager instance
poll_manager = PollManager()

# Utility functions
def duplicate_poll(poll_id: int, new_question: str = None, team_id: str = None,
                  channel_id: str = None, creator_id: str = None, copy_votes: bool = False) -> Optional[int]:
    """Duplicate a poll."""
    return poll_manager.duplicate_poll(poll_id, new_question, team_id, channel_id, creator_id, copy_votes)

def edit_poll_question(poll_id: int, new_question: str, user_id: str) -> bool:
    """Edit poll question."""
    return poll_manager.edit_poll_question(poll_id, new_question, user_id)

def add_poll_option(poll_id: int, option_text: str, user_id: str) -> bool:
    """Add poll option."""
    return poll_manager.add_poll_option(poll_id, option_text, user_id)

def remove_poll_option(poll_id: int, option_id: int, user_id: str) -> bool:
    """Remove poll option."""
    return poll_manager.remove_poll_option(poll_id, option_id, user_id)

def edit_poll_option(poll_id: int, option_id: int, new_text: str, user_id: str) -> bool:
    """Edit poll option."""
    return poll_manager.edit_poll_option(poll_id, option_id, new_text, user_id)

def reorder_poll_options(poll_id: int, option_order: List[int], user_id: str) -> bool:
    """Reorder poll options."""
    return poll_manager.reorder_poll_options(poll_id, option_order, user_id)

def clone_poll_template(poll_id: int, team_id: str, channel_id: str, creator_id: str) -> Optional[int]:
    """Clone poll as template."""
    return poll_manager.clone_poll_template(poll_id, team_id, channel_id, creator_id)

def get_poll_edit_permissions(poll_id: int, user_id: str) -> Dict[str, bool]:
    """Get poll edit permissions."""
    return poll_manager.get_poll_edit_permissions(poll_id, user_id)