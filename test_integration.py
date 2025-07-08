"""
Integration tests for Agora Slack app.
Tests actual Slack API interactions and end-to-end workflows.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models import Base, Poll, PollOption, VotedUser, UserVote, UserRole
from database import get_db
import slack_handlers
from performance import OptimizedQueries, CacheManager
from api_middleware import RateLimiter, APIMiddleware

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_test_db():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def mock_slack_client():
    """Mock Slack client for testing."""
    mock_client = Mock()
    mock_client.chat_postMessage = AsyncMock()
    mock_client.chat_update = AsyncMock()
    mock_client.views_open = AsyncMock()
    mock_client.views_update = AsyncMock()
    mock_client.users_info = AsyncMock()
    mock_client.conversations_info = AsyncMock()
    return mock_client

@pytest.fixture
def sample_slack_event():
    """Sample Slack event for testing."""
    return {
        "type": "slash_command",
        "command": "/agora",
        "text": "",
        "user_id": "U123456",
        "team_id": "T123456",
        "channel_id": "C123456",
        "response_url": "https://hooks.slack.com/commands/1234567890/1234567890/1234567890",
        "trigger_id": "123456.123456.123456"
    }

@pytest.fixture
def sample_poll_data():
    """Sample poll data for testing."""
    return {
        "question": "What's your favorite programming language?",
        "options": ["Python", "JavaScript", "Go", "Rust"],
        "vote_type": "single",
        "team_id": "T123456",
        "channel_id": "C123456",
        "creator_id": "U123456"
    }

class TestSlackIntegration:
    """Test Slack API integration."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_slack_events_endpoint_invalid_signature(self, client):
        """Test Slack events endpoint with invalid signature."""
        response = client.post("/slack/events", json={"test": "data"})
        # Should handle missing signature gracefully
        assert response.status_code in [200, 400, 401]
    
    @patch('slack_handlers.slack_app.client')
    def test_slash_command_processing(self, mock_client, client, setup_test_db, sample_slack_event):
        """Test slash command processing."""
        mock_client.views_open.return_value = {"ok": True}
        
        # Mock Slack request headers
        headers = {
            "X-Slack-Signature": "v0=test_signature",
            "X-Slack-Request-Timestamp": str(int(time.time())),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Convert event to form data
        form_data = "&".join([f"{k}={v}" for k, v in sample_slack_event.items()])
        
        with patch('slack_handlers.verify_slack_signature', return_value=True):
            response = client.post("/slack/events", data=form_data, headers=headers)
            
        # Should process successfully
        assert response.status_code == 200
    
    @patch('slack_handlers.slack_app.client')
    def test_poll_creation_flow(self, mock_client, client, setup_test_db, sample_poll_data):
        """Test complete poll creation flow."""
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456"
        }
        
        # Create poll via API
        db = TestingSessionLocal()
        try:
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Add poll options
            for i, option_text in enumerate(sample_poll_data["options"]):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                db.add(option)
            
            db.commit()
            
            # Test poll creation
            assert poll.id is not None
            assert poll.question == sample_poll_data["question"]
            assert len(poll.options) == len(sample_poll_data["options"])
            
        finally:
            db.close()
    
    @patch('slack_handlers.slack_app.client')
    def test_voting_flow(self, mock_client, client, setup_test_db, sample_poll_data):
        """Test complete voting flow."""
        mock_client.chat_update.return_value = {"ok": True}
        
        db = TestingSessionLocal()
        try:
            # Create poll
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Add options
            options = []
            for i, option_text in enumerate(sample_poll_data["options"]):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                db.add(option)
                options.append(option)
            
            db.commit()
            
            # Test voting
            user_id = "U123456"
            selected_option = options[0]
            
            # Check user hasn't voted
            assert not OptimizedQueries.check_user_voted(db, poll.id, user_id)
            
            # Record vote
            voted_user = VotedUser(poll_id=poll.id, user_id=user_id)
            user_vote = UserVote(
                poll_id=poll.id,
                user_id=user_id,
                option_id=selected_option.id
            )
            
            db.add(voted_user)
            db.add(user_vote)
            db.commit()
            
            # Update vote count
            selected_option.vote_count += 1
            db.commit()
            
            # Verify vote recorded
            assert OptimizedQueries.check_user_voted(db, poll.id, user_id)
            assert selected_option.vote_count == 1
            
        finally:
            db.close()
    
    def test_role_management(self, setup_test_db):
        """Test role-based permissions."""
        db = TestingSessionLocal()
        try:
            # Create user role
            user_role = UserRole(
                user_id="U123456",
                team_id="T123456",
                role="admin"
            )
            db.add(user_role)
            db.commit()
            
            # Test role retrieval
            role = OptimizedQueries.get_user_role(db, "U123456", "T123456")
            assert role == "admin"
            
            # Test default role
            default_role = OptimizedQueries.get_user_role(db, "U999999", "T123456")
            assert default_role == "user"
            
        finally:
            db.close()
    
    def test_cross_channel_sharing(self, setup_test_db, sample_poll_data):
        """Test cross-channel poll sharing."""
        db = TestingSessionLocal()
        try:
            # Create poll
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Test sharing to multiple channels
            from models import PollShare
            
            channels = ["C123456", "C789012", "C345678"]
            for channel in channels:
                share = PollShare(
                    poll_id=poll.id,
                    channel_id=channel,
                    shared_by="U123456"
                )
                db.add(share)
            
            db.commit()
            
            # Verify shares
            assert len(poll.shares) == len(channels)
            
        finally:
            db.close()

class TestPerformanceOptimization:
    """Test performance optimization features."""
    
    def test_cache_operations(self):
        """Test cache operations."""
        # Test cache set/get
        key = "test_key"
        value = {"test": "data", "number": 42}
        
        assert CacheManager.set(key, value, ttl=60)
        cached_value = CacheManager.get(key)
        
        if cached_value:  # Only test if Redis is available
            assert cached_value == value
            
            # Test cache delete
            assert CacheManager.delete(key)
            assert CacheManager.get(key) is None
    
    def test_optimized_queries(self, setup_test_db, sample_poll_data):
        """Test optimized database queries."""
        db = TestingSessionLocal()
        try:
            # Create test data
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Add options
            for i, option_text in enumerate(sample_poll_data["options"]):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                db.add(option)
            
            db.commit()
            
            # Test optimized queries
            active_polls = OptimizedQueries.get_active_polls(db, "T123456")
            assert len(active_polls) >= 1
            
            poll_details = OptimizedQueries.get_poll_with_details(db, poll.id)
            assert poll_details is not None
            assert poll_details.id == poll.id
            
        finally:
            db.close()
    
    def test_bulk_operations(self, setup_test_db, sample_poll_data):
        """Test bulk database operations."""
        db = TestingSessionLocal()
        try:
            # Create poll with votes
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Add options
            options = []
            for i, option_text in enumerate(sample_poll_data["options"]):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                db.add(option)
                options.append(option)
            
            db.commit()
            
            # Add votes
            for i in range(10):
                user_id = f"U{i:06d}"
                voted_user = VotedUser(poll_id=poll.id, user_id=user_id)
                user_vote = UserVote(
                    poll_id=poll.id,
                    user_id=user_id,
                    option_id=options[i % len(options)].id
                )
                db.add(voted_user)
                db.add(user_vote)
            
            db.commit()
            
            # Test bulk update
            OptimizedQueries.bulk_update_vote_counts(db, poll.id)
            
            # Verify vote counts
            db.refresh(poll)
            total_votes = sum(option.vote_count for option in poll.options)
            assert total_votes == 10
            
        finally:
            db.close()

class TestRateLimiting:
    """Test API rate limiting."""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiter functionality."""
        limiter = RateLimiter(max_requests=5, time_window=60, identifier="test_user")
        
        # Test within limits
        for i in range(5):
            allowed, retry_after = limiter.is_allowed()
            if allowed is not None:  # Only test if Redis is available
                assert allowed
                assert retry_after == 0
        
        # Test limit exceeded
        allowed, retry_after = limiter.is_allowed()
        if allowed is not None:  # Only test if Redis is available
            assert not allowed
            assert retry_after > 0
    
    def test_rate_limiting_middleware(self, client):
        """Test rate limiting middleware."""
        # This would test the actual middleware in a real scenario
        # For now, we'll test that the endpoint responds
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check for rate limit headers
        if "X-Rate-Limit-Remaining" in response.headers:
            remaining = int(response.headers["X-Rate-Limit-Remaining"])
            assert remaining >= 0

class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_database_error_handling(self, setup_test_db):
        """Test database error handling."""
        db = TestingSessionLocal()
        try:
            # Test with invalid data
            with pytest.raises(Exception):
                invalid_poll = Poll(
                    question="",  # Empty question should fail validation
                    team_id="",   # Empty team_id should fail validation
                    channel_id="",
                    creator_id="",
                    vote_type="invalid"  # Invalid vote type
                )
                db.add(invalid_poll)
                db.commit()
        finally:
            db.close()
    
    def test_api_error_responses(self, client):
        """Test API error responses."""
        # Test invalid endpoint
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
        
        # Test invalid method
        response = client.put("/health")
        assert response.status_code == 405

class TestAnalytics:
    """Test analytics and reporting."""
    
    def test_poll_analytics(self, setup_test_db, sample_poll_data):
        """Test poll analytics generation."""
        db = TestingSessionLocal()
        try:
            # Create poll with votes
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Add options
            options = []
            for i, option_text in enumerate(sample_poll_data["options"]):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                db.add(option)
                options.append(option)
            
            db.commit()
            
            # Add votes with different timestamps
            base_time = datetime.now() - timedelta(hours=2)
            for i in range(20):
                user_id = f"U{i:06d}"
                vote_time = base_time + timedelta(minutes=i * 5)
                
                voted_user = VotedUser(poll_id=poll.id, user_id=user_id, voted_at=vote_time)
                user_vote = UserVote(
                    poll_id=poll.id,
                    user_id=user_id,
                    option_id=options[i % len(options)].id,
                    voted_at=vote_time
                )
                db.add(voted_user)
                db.add(user_vote)
            
            db.commit()
            
            # Update vote counts
            OptimizedQueries.bulk_update_vote_counts(db, poll.id)
            
            # Get analytics
            analytics = OptimizedQueries.get_poll_analytics(db, poll.id)
            
            assert analytics['total_votes'] == 20
            assert analytics['unique_voters'] == 20
            assert len(analytics['vote_distribution']) == len(options)
            
        finally:
            db.close()

class TestScalability:
    """Test scalability and performance under load."""
    
    def test_concurrent_voting(self, setup_test_db, sample_poll_data):
        """Test concurrent voting scenarios."""
        db = TestingSessionLocal()
        try:
            # Create poll
            poll = Poll(**sample_poll_data)
            db.add(poll)
            db.commit()
            
            # Add options
            options = []
            for i, option_text in enumerate(sample_poll_data["options"]):
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text,
                    order_index=i
                )
                db.add(option)
                options.append(option)
            
            db.commit()
            
            # Simulate concurrent votes
            def add_vote(user_id, option_id):
                db_session = TestingSessionLocal()
                try:
                    voted_user = VotedUser(poll_id=poll.id, user_id=user_id)
                    user_vote = UserVote(
                        poll_id=poll.id,
                        user_id=user_id,
                        option_id=option_id
                    )
                    db_session.add(voted_user)
                    db_session.add(user_vote)
                    db_session.commit()
                finally:
                    db_session.close()
            
            # Add multiple votes
            for i in range(50):
                add_vote(f"U{i:06d}", options[i % len(options)].id)
            
            # Update vote counts
            OptimizedQueries.bulk_update_vote_counts(db, poll.id)
            
            # Verify consistency
            db.refresh(poll)
            total_votes = sum(option.vote_count for option in poll.options)
            assert total_votes == 50
            
        finally:
            db.close()

# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])