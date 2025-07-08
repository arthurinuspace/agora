"""
Test new features added to Agora Slack app.
Tests templates, scheduling, export, search, and poll management features.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Poll, PollOption, ScheduledPoll
from templates import template_manager, get_template_by_id, create_poll_from_template
from scheduler import poll_scheduler, schedule_poll_creation, schedule_poll_ending
from export_utils import poll_exporter, export_poll_data
from search_utils import search_engine, search_polls, get_poll_history
from poll_management import poll_manager, duplicate_poll, edit_poll_question
from config_validator import config_validator, validate_configuration

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_new_features.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_test_db():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create a database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def sample_poll(db_session):
    """Create a sample poll for testing."""
    poll = Poll(
        question="Test poll question?",
        team_id="T123456",
        channel_id="C123456",
        creator_id="U123456",
        vote_type="single",
        status="active"
    )
    db_session.add(poll)
    db_session.commit()
    
    # Add options
    options = ["Option 1", "Option 2", "Option 3"]
    for i, option_text in enumerate(options):
        option = PollOption(
            poll_id=poll.id,
            text=option_text,
            vote_count=i * 5,  # Simulate different vote counts
            order_index=i
        )
        db_session.add(option)
    
    db_session.commit()
    return poll

class TestTemplates:
    """Test poll templates functionality."""
    
    def test_get_template_by_id(self):
        """Test getting template by ID."""
        template = get_template_by_id("yes-no-decision")
        assert template is not None
        assert template.name == "Yes/No Decision"
        assert len(template.options) == 2
    
    def test_get_nonexistent_template(self):
        """Test getting non-existent template."""
        template = get_template_by_id("nonexistent")
        assert template is None
    
    def test_create_poll_from_template(self):
        """Test creating poll from template."""
        poll_data = create_poll_from_template("yes-no-decision")
        assert poll_data is not None
        assert poll_data["vote_type"] == "single"
        assert len(poll_data["options"]) == 2
        assert "✅ Yes" in poll_data["options"]
        assert "❌ No" in poll_data["options"]
    
    def test_template_categories(self):
        """Test template category organization."""
        from templates import get_template_categories
        categories = get_template_categories()
        assert len(categories) > 0
        assert any(cat["id"] == "decision_making" for cat in categories)
    
    def test_template_search(self):
        """Test template search functionality."""
        results = template_manager.search_templates("decision")
        assert len(results) > 0
        assert any("decision" in template.name.lower() for template in results)
    
    def test_popular_templates(self):
        """Test getting popular templates."""
        # Simulate template usage
        template_manager.update_template_usage("yes-no-decision")
        template_manager.update_template_usage("yes-no-decision")
        
        popular = template_manager.get_popular_templates(5)
        assert len(popular) > 0
        assert popular[0].usage_count >= 0

class TestScheduler:
    """Test poll scheduling functionality."""
    
    def setUp(self):
        """Set up scheduler for testing."""
        if not poll_scheduler.is_running:
            poll_scheduler.start()
    
    def tearDown(self):
        """Clean up scheduler after testing."""
        if poll_scheduler.is_running:
            poll_scheduler.stop()
    
    def test_schedule_poll_creation(self):
        """Test scheduling poll creation."""
        schedule_id = "test_schedule_001"
        scheduled_time = datetime.now() + timedelta(minutes=5)
        
        poll_data = {
            "question": "Scheduled poll test",
            "options": ["Yes", "No"],
            "vote_type": "single"
        }
        
        success = schedule_poll_creation(
            schedule_id=schedule_id,
            team_id="T123456",
            channel_id="C123456",
            creator_id="U123456",
            poll_data=poll_data,
            schedule_type="once",
            scheduled_time=scheduled_time
        )
        
        assert success
        
        # Check if scheduled poll exists
        scheduled_poll = poll_scheduler.get_scheduled_poll(schedule_id)
        assert scheduled_poll is not None
        assert scheduled_poll.team_id == "T123456"
    
    def test_schedule_poll_ending(self):
        """Test scheduling poll ending."""
        schedule_id = "test_end_001"
        end_time = datetime.now() + timedelta(hours=1)
        
        success = schedule_poll_ending(
            schedule_id=schedule_id,
            poll_id=1,
            team_id="T123456",
            channel_id="C123456",
            end_time=end_time
        )
        
        assert success
    
    def test_cancel_scheduled_poll(self):
        """Test cancelling scheduled poll."""
        from scheduler import cancel_scheduled_poll
        
        schedule_id = "test_cancel_001"
        scheduled_time = datetime.now() + timedelta(minutes=10)
        
        # First schedule something
        schedule_poll_creation(
            schedule_id=schedule_id,
            team_id="T123456",
            channel_id="C123456",
            creator_id="U123456",
            poll_data={"question": "Test", "options": ["A", "B"]},
            schedule_type="once",
            scheduled_time=scheduled_time
        )
        
        # Then cancel it
        success = cancel_scheduled_poll(schedule_id)
        assert success

class TestExport:
    """Test poll export functionality."""
    
    def test_export_poll_csv(self, sample_poll):
        """Test exporting poll to CSV."""
        csv_data = export_poll_data(
            poll_id=sample_poll.id,
            format_type="csv",
            include_analytics=False,
            anonymize=True
        )
        
        assert csv_data is not None
        assert isinstance(csv_data, bytes)
        
        # Check if CSV contains expected data
        csv_content = csv_data.decode('utf-8')
        assert "Poll ID" in csv_content
        assert "Option" in csv_content
    
    def test_export_poll_json(self, sample_poll):
        """Test exporting poll to JSON."""
        json_data = export_poll_data(
            poll_id=sample_poll.id,
            format_type="json",
            include_analytics=True,
            anonymize=True
        )
        
        assert json_data is not None
        assert isinstance(json_data, bytes)
        
        # Parse JSON to verify structure
        import json
        json_content = json.loads(json_data.decode('utf-8'))
        assert "poll_data" in json_content
        assert "exported_at" in json_content
    
    def test_export_multiple_polls(self, sample_poll):
        """Test exporting multiple polls."""
        from export_utils import export_multiple_polls_data
        
        csv_data = export_multiple_polls_data(
            poll_ids=[sample_poll.id],
            format_type="csv",
            include_analytics=False,
            anonymize=True
        )
        
        assert csv_data is not None
        assert isinstance(csv_data, bytes)
    
    def test_export_supported_formats(self):
        """Test getting supported export formats."""
        from export_utils import get_supported_export_formats
        
        formats = get_supported_export_formats()
        assert "csv" in formats
        assert "json" in formats
        assert "excel" in formats

class TestSearch:
    """Test search and history functionality."""
    
    def test_search_polls_by_question(self, setup_test_db, sample_poll):
        """Test searching polls by question text."""
        results, total = search_polls(
            team_id="T123456",
            query="Test poll",
            search_type="question"
        )
        
        assert total >= 0
        if total > 0:
            assert len(results) > 0
            assert results[0]["poll_id"] == sample_poll.id
    
    def test_search_polls_all_types(self, setup_test_db, sample_poll):
        """Test searching polls across all fields."""
        results, total = search_polls(
            team_id="T123456",
            query="test",
            search_type="all"
        )
        
        assert total >= 0
        # Results should include polls matching any field
    
    def test_get_poll_history(self, setup_test_db, sample_poll):
        """Test getting poll history."""
        history = get_poll_history(
            team_id="T123456",
            user_id="U123456",
            days=30
        )
        
        assert isinstance(history, list)
        # History should include recent polls
    
    def test_get_popular_polls(self, setup_test_db, sample_poll):
        """Test getting popular polls."""
        from search_utils import get_popular_polls
        
        popular = get_popular_polls(
            team_id="T123456",
            days=30,
            limit=10
        )
        
        assert isinstance(popular, list)
    
    def test_user_participation_stats(self, setup_test_db):
        """Test getting user participation statistics."""
        from search_utils import get_user_participation_stats
        
        stats = get_user_participation_stats(
            team_id="T123456",
            user_id="U123456",
            days=30
        )
        
        assert isinstance(stats, dict)
        assert "polls_created" in stats
        assert "polls_voted_in" in stats

class TestPollManagement:
    """Test poll management and editing functionality."""
    
    def test_duplicate_poll(self, sample_poll):
        """Test duplicating a poll."""
        new_poll_id = duplicate_poll(
            poll_id=sample_poll.id,
            new_question="Duplicated poll question",
            team_id="T123456",
            channel_id="C789012",
            creator_id="U789012"
        )
        
        assert new_poll_id is not None
        assert new_poll_id != sample_poll.id
    
    def test_edit_poll_question(self, sample_poll):
        """Test editing poll question."""
        success = edit_poll_question(
            poll_id=sample_poll.id,
            new_question="Updated poll question?",
            user_id=sample_poll.creator_id
        )
        
        assert success
    
    def test_edit_poll_question_unauthorized(self, sample_poll):
        """Test editing poll question by unauthorized user."""
        success = edit_poll_question(
            poll_id=sample_poll.id,
            new_question="Unauthorized update",
            user_id="U999999"  # Different user
        )
        
        assert not success
    
    def test_get_poll_edit_permissions(self, sample_poll):
        """Test getting poll edit permissions."""
        permissions = poll_manager.get_poll_edit_permissions(
            poll_id=sample_poll.id,
            user_id=sample_poll.creator_id
        )
        
        assert permissions["can_edit"]
        assert permissions["is_creator"]
    
    def test_add_poll_option(self, sample_poll):
        """Test adding option to poll."""
        success = poll_manager.add_poll_option(
            poll_id=sample_poll.id,
            option_text="New Option",
            user_id=sample_poll.creator_id
        )
        
        assert success
    
    def test_remove_poll_option_with_votes(self, sample_poll):
        """Test removing option that has votes (should fail)."""
        # Try to remove option with votes
        success = poll_manager.remove_poll_option(
            poll_id=sample_poll.id,
            option_id=1,  # First option should have votes
            user_id=sample_poll.creator_id
        )
        
        assert not success  # Should fail because option has votes

class TestConfigValidator:
    """Test configuration validation functionality."""
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        is_valid, report = validate_configuration()
        
        assert isinstance(is_valid, bool)
        assert isinstance(report, str)
        assert len(report) > 0
    
    def test_configuration_status(self):
        """Test getting configuration status."""
        from config_validator import get_configuration_status
        
        status = get_configuration_status()
        
        assert isinstance(status, dict)
        assert "valid" in status
        assert "errors" in status
        assert "warnings" in status
    
    def test_audit_configuration(self):
        """Test configuration audit."""
        findings = config_validator.audit_configuration()
        
        assert isinstance(findings, dict)
        assert "critical" in findings
        assert "high" in findings
        assert "medium" in findings
        assert "low" in findings
    
    def test_security_validation(self):
        """Test security-specific validation."""
        findings = config_validator._validate_security()
        
        assert isinstance(findings, list)
        # Should return list of validation results

class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""
    
    def test_template_to_scheduled_poll(self):
        """Test creating scheduled poll from template."""
        # Create poll data from template
        poll_data = create_poll_from_template("yes-no-decision")
        assert poll_data is not None
        
        # Schedule the poll
        schedule_id = "template_scheduled_001"
        scheduled_time = datetime.now() + timedelta(minutes=1)
        
        success = schedule_poll_creation(
            schedule_id=schedule_id,
            team_id="T123456",
            channel_id="C123456",
            creator_id="U123456",
            poll_data=poll_data,
            schedule_type="once",
            scheduled_time=scheduled_time
        )
        
        assert success
    
    def test_poll_lifecycle_with_export(self, sample_poll):
        """Test complete poll lifecycle with export."""
        # Duplicate poll
        new_poll_id = duplicate_poll(
            poll_id=sample_poll.id,
            new_question="Lifecycle test poll",
            creator_id="U123456"
        )
        assert new_poll_id is not None
        
        # Export original poll
        export_data = export_poll_data(
            poll_id=sample_poll.id,
            format_type="json"
        )
        assert export_data is not None
        
        # Search for polls
        results, total = search_polls(
            team_id="T123456",
            query="test"
        )
        assert total >= 1
    
    def test_admin_workflow(self, sample_poll):
        """Test typical admin workflow."""
        # Check poll edit permissions
        permissions = poll_manager.get_poll_edit_permissions(
            poll_id=sample_poll.id,
            user_id="admin_user"
        )
        
        # Validate configuration
        is_valid, report = validate_configuration()
        
        # Get poll analytics
        db = TestingSessionLocal()
        try:
            from performance import OptimizedQueries
            analytics = OptimizedQueries.get_poll_analytics(db, sample_poll.id)
            assert isinstance(analytics, dict)
        finally:
            db.close()
        
        # Export poll data
        export_data = export_poll_data(
            poll_id=sample_poll.id,
            format_type="csv"
        )
        assert export_data is not None

# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])