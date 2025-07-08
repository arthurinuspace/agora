"""
Scheduled polls system for Agora Slack app.
Handles poll scheduling, auto-creation, and auto-ending.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from models import SessionLocal, Poll, ScheduledPoll

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    """Types of poll scheduling."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_CRON = "custom_cron"

class PollAction(Enum):
    """Actions that can be scheduled."""
    CREATE = "create"
    END = "end"
    REMIND = "remind"
    NOTIFY = "notify"

@dataclass
class ScheduledPollData:
    """Scheduled poll data structure."""
    id: str
    poll_id: Optional[int]
    team_id: str
    channel_id: str
    creator_id: str
    action: PollAction
    schedule_type: ScheduleType
    scheduled_time: datetime
    cron_expression: Optional[str]
    poll_data: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0

class PollScheduler:
    """Manages scheduled polls and automatic actions."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduled_polls: Dict[str, ScheduledPollData] = {}
        self.poll_handlers: Dict[PollAction, Callable] = {}
        self.is_running = False
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Poll scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Poll scheduler stopped")
    
    def register_handler(self, action: PollAction, handler: Callable):
        """Register a handler for poll actions."""
        self.poll_handlers[action] = handler
        logger.info(f"Registered handler for action: {action.value}")
    
    def schedule_poll_creation(self, 
                             schedule_id: str,
                             team_id: str,
                             channel_id: str,
                             creator_id: str,
                             poll_data: Dict[str, Any],
                             schedule_type: ScheduleType,
                             scheduled_time: datetime,
                             cron_expression: Optional[str] = None) -> bool:
        """Schedule a poll creation."""
        try:
            scheduled_poll = ScheduledPollData(
                id=schedule_id,
                poll_id=None,
                team_id=team_id,
                channel_id=channel_id,
                creator_id=creator_id,
                action=PollAction.CREATE,
                schedule_type=schedule_type,
                scheduled_time=scheduled_time,
                cron_expression=cron_expression,
                poll_data=poll_data,
                created_at=datetime.now()
            )
            
            # Add to scheduler
            if schedule_type == ScheduleType.ONCE:
                self.scheduler.add_job(
                    self._execute_scheduled_action,
                    trigger=DateTrigger(run_date=scheduled_time),
                    args=[schedule_id],
                    id=schedule_id,
                    replace_existing=True
                )
            elif schedule_type == ScheduleType.DAILY:
                self.scheduler.add_job(
                    self._execute_scheduled_action,
                    trigger=CronTrigger(hour=scheduled_time.hour, minute=scheduled_time.minute),
                    args=[schedule_id],
                    id=schedule_id,
                    replace_existing=True
                )
            elif schedule_type == ScheduleType.WEEKLY:
                self.scheduler.add_job(
                    self._execute_scheduled_action,
                    trigger=CronTrigger(
                        day_of_week=scheduled_time.weekday(),
                        hour=scheduled_time.hour,
                        minute=scheduled_time.minute
                    ),
                    args=[schedule_id],
                    id=schedule_id,
                    replace_existing=True
                )
            elif schedule_type == ScheduleType.MONTHLY:
                self.scheduler.add_job(
                    self._execute_scheduled_action,
                    trigger=CronTrigger(
                        day=scheduled_time.day,
                        hour=scheduled_time.hour,
                        minute=scheduled_time.minute
                    ),
                    args=[schedule_id],
                    id=schedule_id,
                    replace_existing=True
                )
            elif schedule_type == ScheduleType.CUSTOM_CRON and cron_expression:
                self.scheduler.add_job(
                    self._execute_scheduled_action,
                    trigger=CronTrigger.from_crontab(cron_expression),
                    args=[schedule_id],
                    id=schedule_id,
                    replace_existing=True
                )
            
            # Store scheduled poll data
            self.scheduled_polls[schedule_id] = scheduled_poll
            
            # Save to database
            self._save_scheduled_poll_to_db(scheduled_poll)
            
            logger.info(f"Scheduled poll creation: {schedule_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error scheduling poll creation: {e}")
            return False
    
    def schedule_poll_ending(self, 
                           schedule_id: str,
                           poll_id: int,
                           team_id: str,
                           channel_id: str,
                           end_time: datetime) -> bool:
        """Schedule a poll to end automatically."""
        try:
            scheduled_poll = ScheduledPollData(
                id=schedule_id,
                poll_id=poll_id,
                team_id=team_id,
                channel_id=channel_id,
                creator_id="",
                action=PollAction.END,
                schedule_type=ScheduleType.ONCE,
                scheduled_time=end_time,
                cron_expression=None,
                poll_data={},
                created_at=datetime.now()
            )
            
            # Add to scheduler
            self.scheduler.add_job(
                self._execute_scheduled_action,
                trigger=DateTrigger(run_date=end_time),
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )
            
            # Store scheduled poll data
            self.scheduled_polls[schedule_id] = scheduled_poll
            
            # Save to database
            self._save_scheduled_poll_to_db(scheduled_poll)
            
            logger.info(f"Scheduled poll ending: {schedule_id} at {end_time}")
            return True
        
        except Exception as e:
            logger.error(f"Error scheduling poll ending: {e}")
            return False
    
    def schedule_poll_reminder(self, 
                             schedule_id: str,
                             poll_id: int,
                             team_id: str,
                             channel_id: str,
                             remind_time: datetime,
                             reminder_message: str) -> bool:
        """Schedule a poll reminder."""
        try:
            scheduled_poll = ScheduledPollData(
                id=schedule_id,
                poll_id=poll_id,
                team_id=team_id,
                channel_id=channel_id,
                creator_id="",
                action=PollAction.REMIND,
                schedule_type=ScheduleType.ONCE,
                scheduled_time=remind_time,
                cron_expression=None,
                poll_data={"reminder_message": reminder_message},
                created_at=datetime.now()
            )
            
            # Add to scheduler
            self.scheduler.add_job(
                self._execute_scheduled_action,
                trigger=DateTrigger(run_date=remind_time),
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )
            
            # Store scheduled poll data
            self.scheduled_polls[schedule_id] = scheduled_poll
            
            # Save to database
            self._save_scheduled_poll_to_db(scheduled_poll)
            
            logger.info(f"Scheduled poll reminder: {schedule_id} at {remind_time}")
            return True
        
        except Exception as e:
            logger.error(f"Error scheduling poll reminder: {e}")
            return False
    
    def cancel_scheduled_poll(self, schedule_id: str) -> bool:
        """Cancel a scheduled poll."""
        try:
            # Remove from scheduler
            self.scheduler.remove_job(schedule_id)
            
            # Remove from memory
            if schedule_id in self.scheduled_polls:
                self.scheduled_polls[schedule_id].is_active = False
                del self.scheduled_polls[schedule_id]
            
            # Update database
            self._update_scheduled_poll_status(schedule_id, False)
            
            logger.info(f"Cancelled scheduled poll: {schedule_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling scheduled poll: {e}")
            return False
    
    def get_scheduled_polls(self, team_id: str = None) -> List[ScheduledPollData]:
        """Get all scheduled polls, optionally filtered by team."""
        if team_id:
            return [p for p in self.scheduled_polls.values() if p.team_id == team_id and p.is_active]
        return [p for p in self.scheduled_polls.values() if p.is_active]
    
    def get_scheduled_poll(self, schedule_id: str) -> Optional[ScheduledPollData]:
        """Get a specific scheduled poll."""
        return self.scheduled_polls.get(schedule_id)
    
    async def _execute_scheduled_action(self, schedule_id: str):
        """Execute a scheduled poll action."""
        try:
            scheduled_poll = self.scheduled_polls.get(schedule_id)
            if not scheduled_poll or not scheduled_poll.is_active:
                logger.warning(f"Scheduled poll not found or inactive: {schedule_id}")
                return
            
            logger.info(f"Executing scheduled action: {scheduled_poll.action.value} for {schedule_id}")
            
            # Update run statistics
            scheduled_poll.last_run = datetime.now()
            scheduled_poll.run_count += 1
            
            # Execute the appropriate handler
            handler = self.poll_handlers.get(scheduled_poll.action)
            if handler:
                await handler(scheduled_poll)
            else:
                logger.error(f"No handler registered for action: {scheduled_poll.action.value}")
            
            # If it's a one-time action, deactivate it
            if scheduled_poll.schedule_type == ScheduleType.ONCE:
                scheduled_poll.is_active = False
                self._update_scheduled_poll_status(schedule_id, False)
            
            # Update database
            self._update_scheduled_poll_stats(schedule_id, scheduled_poll.last_run, scheduled_poll.run_count)
            
        except Exception as e:
            logger.error(f"Error executing scheduled action {schedule_id}: {e}")
    
    def _save_scheduled_poll_to_db(self, scheduled_poll: ScheduledPollData):
        """Save scheduled poll to database."""
        try:
            db = SessionLocal()
            
            db_scheduled_poll = ScheduledPoll(
                id=scheduled_poll.id,
                poll_id=scheduled_poll.poll_id,
                team_id=scheduled_poll.team_id,
                channel_id=scheduled_poll.channel_id,
                creator_id=scheduled_poll.creator_id,
                action=scheduled_poll.action.value,
                schedule_type=scheduled_poll.schedule_type.value,
                scheduled_time=scheduled_poll.scheduled_time,
                cron_expression=scheduled_poll.cron_expression,
                poll_data=scheduled_poll.poll_data,
                is_active=scheduled_poll.is_active,
                created_at=scheduled_poll.created_at,
                last_run=scheduled_poll.last_run,
                run_count=scheduled_poll.run_count
            )
            
            db.add(db_scheduled_poll)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving scheduled poll to database: {e}")
        finally:
            db.close()
    
    def _update_scheduled_poll_status(self, schedule_id: str, is_active: bool):
        """Update scheduled poll status in database."""
        try:
            db = SessionLocal()
            
            db_scheduled_poll = db.query(ScheduledPoll).filter(
                ScheduledPoll.id == schedule_id
            ).first()
            
            if db_scheduled_poll:
                db_scheduled_poll.is_active = is_active
                db.commit()
            
        except Exception as e:
            logger.error(f"Error updating scheduled poll status: {e}")
        finally:
            db.close()
    
    def _update_scheduled_poll_stats(self, schedule_id: str, last_run: datetime, run_count: int):
        """Update scheduled poll statistics in database."""
        try:
            db = SessionLocal()
            
            db_scheduled_poll = db.query(ScheduledPoll).filter(
                ScheduledPoll.id == schedule_id
            ).first()
            
            if db_scheduled_poll:
                db_scheduled_poll.last_run = last_run
                db_scheduled_poll.run_count = run_count
                db.commit()
            
        except Exception as e:
            logger.error(f"Error updating scheduled poll stats: {e}")
        finally:
            db.close()
    
    def load_scheduled_polls_from_db(self):
        """Load scheduled polls from database on startup."""
        try:
            db = SessionLocal()
            
            db_scheduled_polls = db.query(ScheduledPoll).filter(
                ScheduledPoll.is_active == True
            ).all()
            
            for db_poll in db_scheduled_polls:
                scheduled_poll = ScheduledPollData(
                    id=db_poll.id,
                    poll_id=db_poll.poll_id,
                    team_id=db_poll.team_id,
                    channel_id=db_poll.channel_id,
                    creator_id=db_poll.creator_id,
                    action=PollAction(db_poll.action),
                    schedule_type=ScheduleType(db_poll.schedule_type),
                    scheduled_time=db_poll.scheduled_time,
                    cron_expression=db_poll.cron_expression,
                    poll_data=db_poll.poll_data,
                    is_active=db_poll.is_active,
                    created_at=db_poll.created_at,
                    last_run=db_poll.last_run,
                    run_count=db_poll.run_count
                )
                
                self.scheduled_polls[db_poll.id] = scheduled_poll
                
                # Re-add to scheduler if still valid
                if scheduled_poll.scheduled_time > datetime.now():
                    self._reschedule_poll(scheduled_poll)
            
            logger.info(f"Loaded {len(db_scheduled_polls)} scheduled polls from database")
            
        except Exception as e:
            logger.error(f"Error loading scheduled polls from database: {e}")
        finally:
            db.close()
    
    def _reschedule_poll(self, scheduled_poll: ScheduledPollData):
        """Re-add a scheduled poll to the scheduler."""
        try:
            if scheduled_poll.schedule_type == ScheduleType.ONCE:
                if scheduled_poll.scheduled_time > datetime.now():
                    self.scheduler.add_job(
                        self._execute_scheduled_action,
                        trigger=DateTrigger(run_date=scheduled_poll.scheduled_time),
                        args=[scheduled_poll.id],
                        id=scheduled_poll.id,
                        replace_existing=True
                    )
            # Add other schedule types as needed
            
        except Exception as e:
            logger.error(f"Error rescheduling poll {scheduled_poll.id}: {e}")

# Global scheduler instance
poll_scheduler = PollScheduler()

# Utility functions
def schedule_poll_creation(schedule_id: str, team_id: str, channel_id: str, creator_id: str,
                         poll_data: Dict[str, Any], schedule_type: str, scheduled_time: datetime,
                         cron_expression: str = None) -> bool:
    """Schedule a poll creation."""
    try:
        schedule_enum = ScheduleType(schedule_type)
        return poll_scheduler.schedule_poll_creation(
            schedule_id, team_id, channel_id, creator_id, poll_data,
            schedule_enum, scheduled_time, cron_expression
        )
    except ValueError:
        logger.error(f"Invalid schedule type: {schedule_type}")
        return False

def schedule_poll_ending(schedule_id: str, poll_id: int, team_id: str, channel_id: str, end_time: datetime) -> bool:
    """Schedule a poll ending."""
    return poll_scheduler.schedule_poll_ending(schedule_id, poll_id, team_id, channel_id, end_time)

def schedule_poll_reminder(schedule_id: str, poll_id: int, team_id: str, channel_id: str,
                         remind_time: datetime, reminder_message: str) -> bool:
    """Schedule a poll reminder."""
    return poll_scheduler.schedule_poll_reminder(schedule_id, poll_id, team_id, channel_id, remind_time, reminder_message)

def cancel_scheduled_poll(schedule_id: str) -> bool:
    """Cancel a scheduled poll."""
    return poll_scheduler.cancel_scheduled_poll(schedule_id)

def get_scheduled_polls(team_id: str = None) -> List[Dict[str, Any]]:
    """Get scheduled polls."""
    polls = poll_scheduler.get_scheduled_polls(team_id)
    return [asdict(poll) for poll in polls]

def start_scheduler():
    """Start the poll scheduler."""
    poll_scheduler.load_scheduled_polls_from_db()
    poll_scheduler.start()

def stop_scheduler():
    """Stop the poll scheduler."""
    poll_scheduler.stop()