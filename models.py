from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, Index, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Poll(Base):
    __tablename__ = "polls"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    team_id = Column(String(255), nullable=False, index=True)
    channel_id = Column(String(255), nullable=False, index=True)
    creator_id = Column(String(255), nullable=False, index=True)
    vote_type = Column(String(50), nullable=False)  # 'single' or 'multiple'
    status = Column(String(50), default="active", index=True)  # 'active' or 'ended'
    created_at = Column(DateTime, default=datetime.now, index=True)
    ended_at = Column(DateTime, nullable=True)
    message_ts = Column(String(255), nullable=True, index=True)  # Slack message timestamp
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_team_status', 'team_id', 'status'),
        Index('idx_channel_status', 'channel_id', 'status'),
        Index('idx_creator_created', 'creator_id', 'created_at'),
        Index('idx_team_created', 'team_id', 'created_at'),
    )
    
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    voted_users = relationship("VotedUser", back_populates="poll", cascade="all, delete-orphan")
    user_votes = relationship("UserVote", back_populates="poll", cascade="all, delete-orphan")
    analytics = relationship("PollAnalytics", back_populates="poll", cascade="all, delete-orphan")
    shares = relationship("PollShare", back_populates="poll", cascade="all, delete-orphan")

class PollOption(Base):
    __tablename__ = "poll_options"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    vote_count = Column(Integer, default=0, index=True)
    order_index = Column(Integer, nullable=False)
    
    # Composite index for poll ordering
    __table_args__ = (
        Index('idx_poll_order', 'poll_id', 'order_index'),
    )
    
    poll = relationship("Poll", back_populates="options")

class VotedUser(Base):
    __tablename__ = "voted_users"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    voted_at = Column(DateTime, default=datetime.now, index=True)
    
    # Composite indexes for duplicate prevention and analytics
    __table_args__ = (
        Index('idx_poll_user', 'poll_id', 'user_id'),
        Index('idx_user_voted', 'user_id', 'voted_at'),
    )
    
    poll = relationship("Poll", back_populates="voted_users")

class UserVote(Base):
    __tablename__ = "user_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("poll_options.id"), nullable=False, index=True)
    voted_at = Column(DateTime, default=datetime.now, index=True)
    
    # Composite indexes for vote tracking and analytics
    __table_args__ = (
        Index('idx_poll_option', 'poll_id', 'option_id'),
        Index('idx_user_poll', 'user_id', 'poll_id'),
        Index('idx_option_voted', 'option_id', 'voted_at'),
    )
    
    poll = relationship("Poll", back_populates="user_votes")
    option = relationship("PollOption")

class PollAnalytics(Base):
    __tablename__ = "poll_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    total_votes = Column(Integer, default=0)
    unique_voters = Column(Integer, default=0)
    participation_rate = Column(Float, default=0.0)  # percentage
    avg_response_time = Column(Float, default=0.0)  # minutes
    peak_voting_hour = Column(Integer, nullable=True)  # 0-23 hour format
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    poll = relationship("Poll", back_populates="analytics")

class VoteActivity(Base):
    __tablename__ = "vote_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    hour = Column(Integer, nullable=False)  # 0-23
    vote_count = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.now)
    
    poll = relationship("Poll")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    team_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), default="user", index=True)  # 'admin', 'user', 'viewer'
    permissions = Column(Text, nullable=True)  # JSON string of specific permissions
    assigned_by = Column(String(255), nullable=True)  # User ID who assigned this role
    assigned_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True, index=True)
    
    # Composite indexes for role management
    __table_args__ = (
        Index('idx_team_role', 'team_id', 'role'),
        Index('idx_user_team', 'user_id', 'team_id'),
    )

class TeamSettings(Base):
    __tablename__ = "team_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String(255), nullable=False, unique=True)
    allow_public_polls = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=False)
    max_options_per_poll = Column(Integer, default=10)
    max_polls_per_user_per_day = Column(Integer, default=5)
    default_poll_duration_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    team_id = Column(String(255), nullable=False, index=True)
    poll_created = Column(Boolean, default=True)
    poll_ended = Column(Boolean, default=True)
    vote_milestone = Column(Boolean, default=True)  # Every 5 votes
    close_race = Column(Boolean, default=True)
    role_changed = Column(Boolean, default=True)
    daily_summary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Composite index for user settings lookup
    __table_args__ = (
        Index('idx_user_team_settings', 'user_id', 'team_id'),
    )

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    team_id = Column(String(255), nullable=False, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False, index=True)  # 'poll_created', 'vote_milestone', etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.now, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Composite indexes for notification queries
    __table_args__ = (
        Index('idx_user_sent', 'user_id', 'sent_at'),
        Index('idx_user_unread', 'user_id', 'read_at'),
        Index('idx_poll_type', 'poll_id', 'notification_type'),
    )
    
    poll = relationship("Poll")

class PollShare(Base):
    __tablename__ = "poll_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)
    channel_id = Column(String(255), nullable=False, index=True)
    message_ts = Column(String(255), nullable=True, index=True)  # Slack message timestamp
    shared_by = Column(String(255), nullable=False, index=True)  # User who shared it
    shared_at = Column(DateTime, default=datetime.now, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Composite indexes for cross-channel sharing
    __table_args__ = (
        Index('idx_poll_channel', 'poll_id', 'channel_id'),
        Index('idx_channel_active', 'channel_id', 'is_active'),
    )
    
    poll = relationship("Poll", back_populates="shares")

class CrossChannelView(Base):
    __tablename__ = "cross_channel_views"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    team_id = Column(String(255), nullable=False)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.now)
    
    poll = relationship("Poll")

class ScheduledPoll(Base):
    __tablename__ = "scheduled_polls"
    
    id = Column(String(255), primary_key=True)  # UUID or custom ID
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=True)  # Null for create actions
    team_id = Column(String(255), nullable=False, index=True)
    channel_id = Column(String(255), nullable=False)
    creator_id = Column(String(255), nullable=False)
    action = Column(String(50), nullable=False)  # 'create', 'end', 'remind', 'notify'
    schedule_type = Column(String(50), nullable=False)  # 'once', 'daily', 'weekly', 'monthly', 'custom_cron'
    scheduled_time = Column(DateTime, nullable=False, index=True)
    cron_expression = Column(String(255), nullable=True)
    poll_data = Column(JSON, nullable=True)  # Poll creation data for create actions
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0)
    
    # Composite indexes for scheduling queries
    __table_args__ = (
        Index('idx_scheduled_active_time', 'is_active', 'scheduled_time'),
        Index('idx_team_active', 'team_id', 'is_active'),
        Index('idx_action_active', 'action', 'is_active'),
    )
    
    poll = relationship("Poll")

# Database configuration moved to database/config.py for better separation of concerns
# Import database utilities from the dedicated database module
from database import get_db_config, get_db

# Legacy compatibility - get engine and session from database config
def get_engine():
    """Get database engine (legacy compatibility)."""
    return get_db_config().engine

def get_session_local():
    """Get session factory (legacy compatibility).""" 
    return get_db_config().session_factory

# For backward compatibility
engine = property(get_engine)
SessionLocal = property(get_session_local)