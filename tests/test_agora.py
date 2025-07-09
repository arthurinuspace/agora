import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Poll, PollOption, VotedUser, UserVote
from slack_handlers import create_poll, process_vote, end_poll
from config import Config
import os

TEST_DATABASE_URL = "sqlite:///./test_agora.db"

@pytest.fixture
def test_db():
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    with patch("models.get_db", override_get_db):
        with patch("slack_handlers.get_db", override_get_db):
            yield TestingSessionLocal()
    
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DATABASE_URL.replace("sqlite:///./", "")):
        os.remove(TEST_DATABASE_URL.replace("sqlite:///./", ""))

class TestPollCreation:
    def test_create_poll_success(self, test_db):
        question = "What should we have for lunch?"
        options = ["Pizza", "Sushi", "Burgers"]
        team_id = "T123456"
        channel_id = "C123456"
        user_id = "U123456"
        vote_type = "single"
        
        poll_id = create_poll(question, options, team_id, channel_id, user_id, vote_type)
        
        assert poll_id is not None
        
        poll = test_db.query(Poll).filter(Poll.id == poll_id).first()
        assert poll.question == question
        assert poll.team_id == team_id
        assert poll.channel_id == channel_id
        assert poll.creator_id == user_id
        assert poll.vote_type == vote_type
        assert poll.status == "active"
        
        poll_options = test_db.query(PollOption).filter(PollOption.poll_id == poll_id).all()
        assert len(poll_options) == 3
        assert poll_options[0].text == "Pizza"
        assert poll_options[1].text == "Sushi"
        assert poll_options[2].text == "Burgers"

class TestVotingSystem:
    def test_process_vote_success(self, test_db):
        poll_id = create_poll("Test question", ["Option 1", "Option 2"], "T123", "C123", "U123", "single")
        poll = test_db.query(Poll).filter(Poll.id == poll_id).first()
        option_id = poll.options[0].id
        user_id = "U456"
        
        success = process_vote(poll_id, option_id, user_id)
        
        assert success is True
        
        test_db.expire_all()
        
        voted_user = test_db.query(VotedUser).filter(
            VotedUser.poll_id == poll_id,
            VotedUser.user_id == user_id
        ).first()
        assert voted_user is not None
        
        user_vote = test_db.query(UserVote).filter(
            UserVote.poll_id == poll_id,
            UserVote.user_id == user_id
        ).first()
        assert user_vote is not None
        
        updated_option = test_db.query(PollOption).filter(PollOption.id == option_id).first()
        assert updated_option.vote_count == 1
    
    def test_process_vote_duplicate_single_choice(self, test_db):
        poll_id = create_poll("Test question", ["Option 1", "Option 2"], "T123", "C123", "U123", "single")
        poll = test_db.query(Poll).filter(Poll.id == poll_id).first()
        option_id = poll.options[0].id
        user_id = "U456"
        
        process_vote(poll_id, option_id, user_id)
        success = process_vote(poll_id, option_id, user_id)
        
        assert success is False
        
        test_db.expire_all()
        updated_option = test_db.query(PollOption).filter(PollOption.id == option_id).first()
        assert updated_option.vote_count == 1
    
    def test_process_vote_multiple_choice(self, test_db):
        poll_id = create_poll("Test question", ["Option 1", "Option 2"], "T123", "C123", "U123", "multiple")
        poll = test_db.query(Poll).filter(Poll.id == poll_id).first()
        option1_id = poll.options[0].id
        option2_id = poll.options[1].id
        user_id = "U456"
        
        success1 = process_vote(poll_id, option1_id, user_id)
        success2 = process_vote(poll_id, option2_id, user_id)
        
        assert success1 is True
        assert success2 is True
        
        user_votes = test_db.query(UserVote).filter(UserVote.poll_id == poll_id).all()
        assert len(user_votes) == 2

class TestPollManagement:
    def test_end_poll_success(self, test_db):
        poll_id = create_poll("Test question", ["Option 1", "Option 2"], "T123", "C123", "U123", "single")
        creator_id = "U123"
        
        success = end_poll(poll_id, creator_id)
        
        assert success is True
        
        poll = test_db.query(Poll).filter(Poll.id == poll_id).first()
        assert poll.status == "ended"
        assert poll.ended_at is not None
    
    def test_end_poll_unauthorized(self, test_db):
        poll_id = create_poll("Test question", ["Option 1", "Option 2"], "T123", "C123", "U123", "single")
        non_creator_id = "U456"
        
        success = end_poll(poll_id, non_creator_id)
        
        assert success is False
        
        poll = test_db.query(Poll).filter(Poll.id == poll_id).first()
        assert poll.status == "active"
        assert poll.ended_at is None

class TestConfigValidation:
    def test_config_validation_success(self):
        with patch.dict(os.environ, {
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_SIGNING_SECRET": "test-secret"
        }):
            Config.SLACK_BOT_TOKEN = "xoxb-test-token"
            Config.SLACK_SIGNING_SECRET = "test-secret"
            
            assert Config.validate() is True
    
    def test_config_validation_missing_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            Config.SLACK_BOT_TOKEN = None
            Config.SLACK_SIGNING_SECRET = None
            
            with pytest.raises(ValueError, match="Missing required environment variables"):
                Config.validate()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])