from slack_bolt import App
from slack_bolt.context.say import Say
from slack_bolt.context.ack import Ack
from sqlalchemy.orm import Session
from models import Poll, PollOption, VotedUser, UserVote, PollAnalytics, VoteActivity, UserRole, TeamSettings, NotificationSettings, Notification, PollShare, CrossChannelView, get_db
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

def register_handlers(app: App):
    @app.command("/agora")
    def handle_agora_command(ack: Ack, body: dict, say: Say):
        ack()
        
        try:
            text = body.get("text", "").strip()
            team_id = body["team_id"]
            channel_id = body["channel_id"]
            user_id = body["user_id"]
            
            # Handle special admin commands
            if text.startswith("admin "):
                handle_admin_command(app, text, team_id, user_id, say)
                return
            
            # Check if user can create polls
            can_create, reason = can_create_poll(user_id, team_id)
            if not can_create:
                safe_say(app, say, f"❌ {reason}", user_id)
                return
            
            if not text:
                safe_say(app, say, "Please provide a question for the poll. Usage: `/agora What should we have for lunch?`", user_id)
                return
            
            show_poll_creation_modal(app, body["trigger_id"], text, team_id, channel_id, user_id)
            
        except Exception as e:
            logger.error(f"Error in /agora command: {e}")
            try:
                say("Sorry, there was an error processing your request. Please try again.")
            except Exception as say_error:
                logger.error(f"Failed to send error message: {say_error}")
                # If we can't send a message via say(), use respond() instead
                try:
                    app.client.chat_postMessage(
                        channel=user_id,  # Send as DM to user
                        text="Sorry, there was an error processing your request. Please try again."
                    )
                except Exception as dm_error:
                    logger.error(f"Failed to send DM: {dm_error}")
                    # As last resort, just log the error
    
    @app.view("poll_creation_modal")
    def handle_poll_creation_submission(ack: Ack, body: dict, view: dict, say: Say):
        ack()
        
        try:
            values = view["state"]["values"]
            question = values["question_block"]["question_input"]["value"]
            options_text = values["options_block"]["options_input"]["value"]
            vote_type = values["vote_type_block"]["vote_type_select"]["selected_option"]["value"]
            
            team_id = body["team"]["id"]
            channel_id = view["private_metadata"]
            user_id = body["user"]["id"]
            
            options = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
            
            if len(options) < 2:
                return {"response_action": "errors", "errors": {"options_block": "Please provide at least 2 options"}}
            
            # Check team settings for max options
            settings = get_team_settings(team_id)
            if len(options) > settings.max_options_per_poll:
                return {"response_action": "errors", "errors": {"options_block": f"Maximum {settings.max_options_per_poll} options allowed"}}
            
            poll_id = create_poll(question, options, team_id, channel_id, user_id, vote_type)
            send_poll_to_channel(app, poll_id, channel_id)
            
            # Send notifications about new poll
            notify_poll_created(app, poll_id, user_id, team_id)
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}")
            return {"response_action": "errors", "errors": {"question_block": "Error creating poll. Please try again."}}
    
    @app.view("channel_selection_modal")
    def handle_channel_selection_submission_wrapper(ack, body, view):
        handle_channel_selection_submission(app, ack, body, view)
    
    @app.action(re.compile(r"^vote_option_\d+$"))
    def handle_vote(ack: Ack, body: dict, say: Say):
        ack()
        
        try:
            action = body["actions"][0]
            poll_id = int(action["action_id"].split("_")[2])
            option_id = int(action["value"])
            user_id = body["user"]["id"]
            
            success = process_vote(poll_id, option_id, user_id)
            
            if success:
                update_shared_poll_messages(app, poll_id)
                
                # Send notifications
                db = next(get_db())
                try:
                    total_votes = sum(option.vote_count for option in db.query(Poll).filter(Poll.id == poll_id).first().options)
                    notify_vote_milestone(app, poll_id, total_votes)
                    notify_close_race(app, poll_id)
                finally:
                    db.close()
            else:
                try:
                    say("You have already voted in this poll!", ephemeral=True)
                except Exception as say_error:
                    logger.error(f"Failed to send already voted message: {say_error}")
                    safe_say(app, say, "You have already voted in this poll!", user_id)
                
        except Exception as e:
            logger.error(f"Error processing vote: {e}")
            try:
                say("Sorry, there was an error processing your vote. Please try again.", ephemeral=True)
            except Exception as say_error:
                logger.error(f"Failed to send error message: {say_error}")
                safe_say(app, say, "Sorry, there was an error processing your vote. Please try again.", user_id)
    
    @app.action(re.compile(r"^end_poll_\d+$"))
    def handle_end_poll(ack: Ack, body: dict, say: Say):
        ack()
        
        try:
            action = body["actions"][0]
            poll_id = int(action["action_id"].split("_")[2])
            user_id = body["user"]["id"]
            team_id = body["team"]["id"]
            
            # Check permissions
            can_end, reason = can_end_poll(user_id, team_id, poll_id)
            if not can_end:
                try:
                    say(f"❌ {reason}", ephemeral=True)
                except Exception as say_error:
                    logger.error(f"Failed to send permission error message: {say_error}")
                    safe_say(app, say, f"❌ {reason}", user_id)
                return
            
            success = end_poll(poll_id, user_id)
            
            if success:
                update_shared_poll_messages(app, poll_id)
                # Send poll ended notifications
                notify_poll_ended(app, poll_id)
            else:
                try:
                    say("❌ Error ending poll. Please try again.", ephemeral=True)
                except Exception as say_error:
                    logger.error(f"Failed to send poll end error message: {say_error}")
                    safe_say(app, say, "❌ Error ending poll. Please try again.", user_id)
                
        except Exception as e:
            logger.error(f"Error ending poll: {e}")
            try:
                say("Sorry, there was an error ending the poll. Please try again.", ephemeral=True)
            except Exception as say_error:
                logger.error(f"Failed to send error message: {say_error}")
                safe_say(app, say, "Sorry, there was an error ending the poll. Please try again.", user_id)
    
    @app.action(re.compile(r"^view_results_\d+$"))
    def handle_view_results(ack: Ack, body: dict, say: Say):
        ack()
        
        try:
            action = body["actions"][0]
            poll_id = int(action["action_id"].split("_")[2])
            
            results_text = generate_detailed_results(poll_id)
            try:
                say(results_text, ephemeral=True)
            except Exception as say_error:
                logger.error(f"Failed to send results message: {say_error}")
                safe_say(app, say, results_text, user_id)
                
        except Exception as e:
            logger.error(f"Error viewing results: {e}")
            try:
                say("Sorry, there was an error viewing the results. Please try again.", ephemeral=True)
            except Exception as say_error:
                logger.error(f"Failed to send error message: {say_error}")
                safe_say(app, say, "Sorry, there was an error viewing the results. Please try again.", user_id)
    
    @app.action(re.compile(r"^share_poll_\d+$"))
    def handle_share_poll(ack: Ack, body: dict, say: Say):
        ack()
        
        try:
            action = body["actions"][0]
            poll_id = int(action["action_id"].split("_")[2])
            user_id = body["user"]["id"]
            team_id = body["team"]["id"]
            
            # Check permissions
            if not check_permission(user_id, team_id, "create_poll"):
                try:
                    say("❌ You don't have permission to share polls.", ephemeral=True)
                except Exception as say_error:
                    logger.error(f"Failed to send permission error message: {say_error}")
                    safe_say(app, say, "❌ You don't have permission to share polls.", user_id)
                return
            
            show_channel_selection_modal(app, body["trigger_id"], poll_id, user_id)
                
        except Exception as e:
            logger.error(f"Error sharing poll: {e}")
            try:
                say("Sorry, there was an error sharing the poll. Please try again.", ephemeral=True)
            except Exception as say_error:
                logger.error(f"Failed to send error message: {say_error}")
                safe_say(app, say, "Sorry, there was an error sharing the poll. Please try again.", user_id)

def show_poll_creation_modal(app: App, trigger_id: str, initial_question: str, team_id: str, channel_id: str, user_id: str):
    modal_view = {
        "type": "modal",
        "callback_id": "poll_creation_modal",
        "title": {"type": "plain_text", "text": "🗳️ Create Poll", "emoji": True},
        "submit": {"type": "plain_text", "text": "🚀 Create Poll", "emoji": True},
        "close": {"type": "plain_text", "text": "❌ Cancel", "emoji": True},
        "private_metadata": channel_id,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "📊 *Create an anonymous poll for your team*\nYour poll will be posted to this channel for everyone to vote on."}
            },
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "question_block",
                "label": {"type": "plain_text", "text": "❓ Poll Question", "emoji": True},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "question_input",
                    "initial_value": initial_question,
                    "multiline": False,
                    "placeholder": {"type": "plain_text", "text": "What should we have for lunch?"}
                }
            },
            {
                "type": "input",
                "block_id": "options_block",
                "label": {"type": "plain_text", "text": "📝 Options (one per line)", "emoji": True},
                "hint": {"type": "plain_text", "text": "💡 Add 2-10 options for people to choose from"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "options_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "🍕 Pizza\n🍣 Sushi\n🍔 Burgers\n🥗 Salads"}
                }
            },
            {
                "type": "input",
                "block_id": "vote_type_block",
                "label": {"type": "plain_text", "text": "🗳️ Vote Type", "emoji": True},
                "hint": {"type": "plain_text", "text": "Choose how many options voters can select"},
                "element": {
                    "type": "static_select",
                    "action_id": "vote_type_select",
                    "options": [
                        {"text": {"type": "plain_text", "text": "🗳️ Single Choice - One option per person", "emoji": True}, "value": "single"},
                        {"text": {"type": "plain_text", "text": "☑️ Multiple Choice - Multiple options per person", "emoji": True}, "value": "multiple"}
                    ],
                    "initial_option": {"text": {"type": "plain_text", "text": "🗳️ Single Choice - One option per person", "emoji": True}, "value": "single"}
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "🔒 *Privacy:* All votes are anonymous. Only vote counts are shown, not who voted for what."}
            }
        ]
    }
    
    app.client.views_open(trigger_id=trigger_id, view=modal_view)

def create_poll(question: str, options: list, team_id: str, channel_id: str, user_id: str, vote_type: str) -> int:
    db = next(get_db())
    try:
        poll = Poll(
            question=question,
            team_id=team_id,
            channel_id=channel_id,
            creator_id=user_id,
            vote_type=vote_type
        )
        db.add(poll)
        db.commit()
        db.refresh(poll)
        
        for i, option_text in enumerate(options):
            option = PollOption(
                poll_id=poll.id,
                text=option_text,
                order_index=i
            )
            db.add(option)
        
        db.commit()
        return poll.id
    finally:
        db.close()

def send_poll_to_channel(app: App, poll_id: int, channel_id: str):
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        blocks = build_poll_blocks(poll)
        
        response = app.client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=f"Poll: {poll.question}"
        )
        
        poll.message_ts = response["ts"]
        db.commit()
    finally:
        db.close()

def build_poll_blocks(poll: Poll) -> list:
    # Calculate total votes for percentage calculation
    total_votes = sum(option.vote_count for option in poll.options)
    
    # Header with emoji and enhanced formatting
    vote_type_emoji = "🗳️" if poll.vote_type == "single" else "☑️"
    status_emoji = "🔴" if poll.status == "active" else "🔒"
    
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"📊 *{poll.question}*"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{vote_type_emoji} *{poll.vote_type.title()} Choice* • {status_emoji} *{poll.status.title()}* • 👥 *{total_votes} total votes*"}
        },
        {"type": "divider"}
    ]
    
    if poll.status == "active":
        for i, option in enumerate(poll.options):
            # Create visual progress bar
            percentage = (option.vote_count / total_votes * 100) if total_votes > 0 else 0
            progress_bar = create_progress_bar(percentage)
            
            # Add option number emoji
            option_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i] if i < 10 else "📌"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{option_emoji} *{option.text}*\n{progress_bar} `{option.vote_count} votes ({percentage:.1f}%)`"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🗳️ Vote", "emoji": True},
                    "action_id": f"vote_option_{poll.id}",
                    "value": str(option.id),
                    "style": "primary"
                }
            })
        
        blocks.extend([
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🛑 End Poll", "emoji": True},
                        "action_id": f"end_poll_{poll.id}",
                        "style": "danger"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📈 View Results", "emoji": True},
                        "action_id": f"view_results_{poll.id}"
                    }
                ]
            }
        ])
    else:
        # Enhanced results display for ended polls
        winner_votes = max(option.vote_count for option in poll.options) if poll.options else 0
        
        for i, option in enumerate(poll.options):
            percentage = (option.vote_count / total_votes * 100) if total_votes > 0 else 0
            progress_bar = create_progress_bar(percentage)
            
            # Add winner emoji
            is_winner = option.vote_count == winner_votes and winner_votes > 0
            option_emoji = "🏆" if is_winner else ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i] if i < 10 else "📌"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{option_emoji} *{option.text}*\n{progress_bar} `{option.vote_count} votes ({percentage:.1f}%)`"}
            })
        
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"🔒 Poll ended at {poll.ended_at.strftime('%Y-%m-%d %H:%M')} • 👥 {total_votes} total votes"}]
            }
        ])
    
    return blocks

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create a visual progress bar using Unicode characters"""
    filled_length = int(length * percentage / 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"`{bar}`"

def process_vote(poll_id: int, option_id: int, user_id: str) -> bool:
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll or poll.status != "active":
            return False
        
        existing_vote = db.query(VotedUser).filter(
            VotedUser.poll_id == poll_id,
            VotedUser.user_id == user_id
        ).first()
        
        if existing_vote and poll.vote_type == "single":
            return False
        
        if not existing_vote:
            voted_user = VotedUser(poll_id=poll_id, user_id=user_id)
            db.add(voted_user)
        
        user_vote = UserVote(poll_id=poll_id, user_id=user_id, option_id=option_id)
        db.add(user_vote)
        
        option = db.query(PollOption).filter(PollOption.id == option_id).first()
        if option:
            option.vote_count += 1
        
        db.commit()
        
        # Update analytics after successful vote
        update_poll_analytics(poll_id)
        
        return True
    finally:
        db.close()

def end_poll(poll_id: int, user_id: str) -> bool:
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll or poll.creator_id != user_id:
            return False
        
        poll.status = "ended"
        poll.ended_at = datetime.now()
        db.commit()
        return True
    finally:
        db.close()

def update_poll_message(app: App, poll_id: int, channel_id: str, message_ts: str):
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        blocks = build_poll_blocks(poll)
        
        app.client.chat_update(
            channel=channel_id,
            ts=message_ts,
            blocks=blocks,
            text=f"Poll: {poll.question}"
        )
    finally:
        db.close()

def generate_detailed_results(poll_id: int) -> str:
    """Generate detailed analytics text for poll results"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return "❌ Poll not found"
        
        # Update analytics before generating results
        update_poll_analytics(poll_id)
        
        total_votes = sum(option.vote_count for option in poll.options)
        unique_voters = len(poll.voted_users)
        
        # Get analytics data
        analytics = db.query(PollAnalytics).filter(PollAnalytics.poll_id == poll_id).first()
        
        # Calculate time metrics
        poll_duration = None
        if poll.ended_at:
            poll_duration = poll.ended_at - poll.created_at
        
        # Build detailed results
        results = []
        results.append(f"📊 *Poll Analytics: {poll.question}*")
        results.append("")
        
        # Basic metrics
        results.append(f"🗳️ *Vote Type:* {poll.vote_type.title()} Choice")
        results.append(f"📈 *Total Votes:* {total_votes}")
        results.append(f"👥 *Unique Voters:* {unique_voters}")
        results.append(f"🕒 *Created:* {poll.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        if poll.ended_at:
            results.append(f"🔒 *Ended:* {poll.ended_at.strftime('%Y-%m-%d %H:%M')}")
            if poll_duration:
                hours = poll_duration.total_seconds() / 3600
                results.append(f"⏱️ *Duration:* {hours:.1f} hours")
        
        # Advanced analytics
        if analytics:
            results.append(f"📊 *Participation Rate:* {analytics.participation_rate:.1f}%")
            if analytics.avg_response_time > 0:
                results.append(f"⏱️ *Avg Response Time:* {analytics.avg_response_time:.1f} minutes")
            if analytics.peak_voting_hour is not None:
                results.append(f"🕒 *Peak Voting Hour:* {analytics.peak_voting_hour:02d}:00")
        
        results.append("")
        results.append("*📊 Option Breakdown:*")
        
        # Sort options by vote count (descending)
        sorted_options = sorted(poll.options, key=lambda x: x.vote_count, reverse=True)
        
        for i, option in enumerate(sorted_options):
            percentage = (option.vote_count / total_votes * 100) if total_votes > 0 else 0
            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}️⃣"
            
            # Create mini progress bar
            progress_bar = create_progress_bar(percentage, 15)
            
            results.append(f"{rank_emoji} *{option.text}*")
            results.append(f"   {progress_bar} {option.vote_count} votes ({percentage:.1f}%)")
        
        # Additional insights
        if total_votes > 0:
            results.append("")
            results.append("*🔍 Insights:*")
            
            # Winner analysis
            winner = max(poll.options, key=lambda x: x.vote_count)
            if winner.vote_count > 0:
                winner_percentage = (winner.vote_count / total_votes * 100)
                results.append(f"• 🏆 *Leading option:* {winner.text} ({winner_percentage:.1f}%)")
            
            # Participation rate (if multiple choice)
            if poll.vote_type == "multiple":
                avg_votes_per_person = total_votes / unique_voters if unique_voters > 0 else 0
                results.append(f"• 📊 *Avg votes per person:* {avg_votes_per_person:.1f}")
            
            # Close race detection
            if len(poll.options) >= 2:
                top_two = sorted(poll.options, key=lambda x: x.vote_count, reverse=True)[:2]
                vote_diff = top_two[0].vote_count - top_two[1].vote_count
                if vote_diff <= 1 and total_votes > 2:
                    results.append("• 🏁 *Close race:* Top two options are very close!")
        
        # Voting timeline
        vote_timeline = get_voting_timeline(poll_id)
        if vote_timeline:
            results.append("")
            results.append("*📈 Voting Timeline:*")
            results.append(vote_timeline)
        
        return "\n".join(results)
    
    finally:
        db.close()

def update_poll_analytics(poll_id: int):
    """Update or create analytics data for a poll"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        # Calculate metrics
        total_votes = sum(option.vote_count for option in poll.options)
        unique_voters = len(poll.voted_users)
        
        # Calculate participation rate (simplified - could be enhanced with channel member count)
        participation_rate = min(100.0, (unique_voters / max(1, total_votes)) * 100)
        
        # Calculate average response time
        avg_response_time = 0.0
        if poll.user_votes:
            response_times = []
            for vote in poll.user_votes:
                response_time = (vote.voted_at - poll.created_at).total_seconds() / 60  # minutes
                response_times.append(response_time)
            avg_response_time = sum(response_times) / len(response_times)
        
        # Find peak voting hour
        peak_voting_hour = None
        if poll.user_votes:
            hour_counts = {}
            for vote in poll.user_votes:
                hour = vote.voted_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            if hour_counts:
                peak_voting_hour = max(hour_counts, key=hour_counts.get)
        
        # Update or create analytics
        analytics = db.query(PollAnalytics).filter(PollAnalytics.poll_id == poll_id).first()
        if analytics:
            analytics.total_votes = total_votes
            analytics.unique_voters = unique_voters
            analytics.participation_rate = participation_rate
            analytics.avg_response_time = avg_response_time
            analytics.peak_voting_hour = peak_voting_hour
            analytics.updated_at = datetime.now()
        else:
            analytics = PollAnalytics(
                poll_id=poll_id,
                total_votes=total_votes,
                unique_voters=unique_voters,
                participation_rate=participation_rate,
                avg_response_time=avg_response_time,
                peak_voting_hour=peak_voting_hour
            )
            db.add(analytics)
        
        # Update vote activity tracking
        update_vote_activity(poll_id)
        
        db.commit()
    
    finally:
        db.close()

def update_vote_activity(poll_id: int):
    """Update hourly vote activity tracking"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        # Clear existing activity data
        db.query(VoteActivity).filter(VoteActivity.poll_id == poll_id).delete()
        
        # Calculate hourly activity
        hour_counts = {}
        for vote in poll.user_votes:
            hour = vote.voted_at.hour
            date = vote.voted_at.date()
            key = (hour, date)
            hour_counts[key] = hour_counts.get(key, 0) + 1
        
        # Store activity data
        for (hour, date), count in hour_counts.items():
            activity = VoteActivity(
                poll_id=poll_id,
                hour=hour,
                vote_count=count,
                date=datetime.combine(date, datetime.min.time())
            )
            db.add(activity)
        
        db.commit()
    
    finally:
        db.close()

def get_voting_timeline(poll_id: int) -> str:
    """Generate a visual timeline of voting activity"""
    db = next(get_db())
    try:
        activities = db.query(VoteActivity).filter(
            VoteActivity.poll_id == poll_id
        ).order_by(VoteActivity.hour).all()
        
        if not activities:
            return ""
        
        # Create hourly chart
        timeline = []
        timeline.append("```")
        timeline.append("Hour | Votes | Activity")
        timeline.append("-" * 25)
        
        for activity in activities:
            hour_str = f"{activity.hour:02d}:00"
            votes = activity.vote_count
            bar = "█" * min(votes, 10)  # Max 10 characters for bar
            timeline.append(f"{hour_str} | {votes:5d} | {bar}")
        
        timeline.append("```")
        return "\n".join(timeline)
    
    finally:
        db.close()

# Permission Management Functions

def get_user_role(user_id: str, team_id: str) -> str:
    """Get the role of a user in a team"""
    db = next(get_db())
    try:
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.team_id == team_id,
            UserRole.is_active == True
        ).first()
        
        return user_role.role if user_role else "user"  # Default to 'user' role
    finally:
        db.close()

def set_user_role(user_id: str, team_id: str, role: str, assigned_by: str) -> bool:
    """Set or update a user's role"""
    if role not in ["admin", "user", "viewer"]:
        return False
    
    db = next(get_db())
    try:
        # Check if assigner has admin permission
        assigner_role = get_user_role(assigned_by, team_id)
        if assigner_role != "admin":
            return False
        
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.team_id == team_id
        ).first()
        
        if user_role:
            user_role.role = role
            user_role.assigned_by = assigned_by
            user_role.assigned_at = datetime.now()
        else:
            user_role = UserRole(
                user_id=user_id,
                team_id=team_id,
                role=role,
                assigned_by=assigned_by
            )
            db.add(user_role)
        
        db.commit()
        return True
    finally:
        db.close()

def check_permission(user_id: str, team_id: str, action: str) -> bool:
    """Check if user has permission to perform an action"""
    role = get_user_role(user_id, team_id)
    
    permissions = {
        "admin": ["create_poll", "end_any_poll", "view_results", "vote", "manage_users", "manage_settings"],
        "user": ["create_poll", "end_own_poll", "view_results", "vote"],
        "viewer": ["view_results", "vote"]
    }
    
    return action in permissions.get(role, [])

def get_team_settings(team_id: str) -> TeamSettings:
    """Get team settings, creating default if not exists"""
    db = next(get_db())
    try:
        settings = db.query(TeamSettings).filter(TeamSettings.team_id == team_id).first()
        if not settings:
            settings = TeamSettings(team_id=team_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
    finally:
        db.close()

def can_create_poll(user_id: str, team_id: str) -> tuple[bool, str]:
    """Check if user can create a poll with detailed reason"""
    if not check_permission(user_id, team_id, "create_poll"):
        return False, "You don't have permission to create polls. Contact an admin for access."
    
    settings = get_team_settings(team_id)
    
    # Check daily poll limit
    db = next(get_db())
    try:
        today = datetime.now().date()
        today_polls = db.query(Poll).filter(
            Poll.creator_id == user_id,
            Poll.team_id == team_id,
            Poll.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        if today_polls >= settings.max_polls_per_user_per_day:
            return False, f"Daily poll limit reached ({settings.max_polls_per_user_per_day} polls per day)."
        
        return True, ""
    finally:
        db.close()

def can_end_poll(user_id: str, team_id: str, poll_id: int) -> tuple[bool, str]:
    """Check if user can end a specific poll"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return False, "Poll not found."
        
        # Admin can end any poll
        if check_permission(user_id, team_id, "end_any_poll"):
            return True, ""
        
        # User can end their own poll
        if check_permission(user_id, team_id, "end_own_poll") and poll.creator_id == user_id:
            return True, ""
        
        return False, "You can only end polls you created."
    finally:
        db.close()

def safe_say(app: App, say, message: str, user_id: str):
    """Safely send a message with fallback to DM if channel posting fails"""
    try:
        say(message)
    except Exception as say_error:
        logger.error(f"Failed to send message via say(): {say_error}")
        # Try to send DM to user as fallback
        try:
            app.client.chat_postMessage(
                channel=user_id,  # Send as DM to user
                text=message
            )
        except Exception as dm_error:
            logger.error(f"Failed to send DM fallback: {dm_error}")
            # As last resort, just log the error
            logger.error(f"Unable to deliver message to user {user_id}: {message}")

def handle_admin_command(app: App, text: str, team_id: str, user_id: str, say):
    """Handle admin commands"""
    if not check_permission(user_id, team_id, "manage_users"):
        safe_say(app, say, "❌ You don't have admin permissions.", user_id)
        return
    
    parts = text.split()
    if len(parts) < 2:
        safe_say(app, say, "Usage: `/agora admin <command> [args]`\nCommands: role, list [all], end, remove", user_id)
        return
    
    command = parts[1]
    
    # For list command, we don't need user_id
    if command == "list":
        pass
    elif command == "end":
        if len(parts) < 3:
            safe_say(app, say, "Usage: `/agora admin end <poll_id>`", user_id)
            return
    elif command == "remove":
        if len(parts) < 3:
            safe_say(app, say, "Usage: `/agora admin remove <poll_id>`", user_id)
            return
    elif len(parts) < 3:
        safe_say(app, say, "Usage: `/agora admin role <user_id> [role]`", user_id)
        return
    else:
        target_user = parts[2]
    
    if command == "role":
        if len(parts) < 4:
            current_role = get_user_role(target_user, team_id)
            safe_say(app, say, f"👤 User <@{target_user}> has role: *{current_role}*", user_id)
            return
        
        new_role = parts[3]
        if new_role not in ["admin", "user", "viewer"]:
            safe_say(app, say, "❌ Invalid role. Use: admin, user, or viewer", user_id)
            return
        
        success = set_user_role(target_user, team_id, new_role, user_id)
        if success:
            safe_say(app, say, f"✅ Set <@{target_user}> role to *{new_role}*", user_id)
            # Send role change notification to the user
            notify_role_changed(app, target_user, team_id, new_role, user_id)
        else:
            safe_say(app, say, "❌ Failed to set role. Make sure you have admin permissions.", user_id)
    
    elif command == "list":
        db = next(get_db())
        try:
            # Check if "all" parameter is provided
            show_all = len(parts) > 2 and parts[2] == "all"
            
            # List polls for the team
            query = db.query(Poll).filter(Poll.team_id == team_id)
            
            if not show_all:
                # Default: only show active polls
                query = query.filter(Poll.status == "active")
                
            polls = query.order_by(Poll.created_at.desc()).limit(10).all()
            
            if not polls:
                status_text = "active" if not show_all else ""
                safe_say(app, say, f"No {status_text} polls found in this team.", user_id)
                return
            
            poll_list = []
            title = f"*Active Polls:*" if not show_all else f"*All Polls:*"
            poll_list.append(title)
            
            for poll in polls:
                total_votes = sum(option.vote_count for option in poll.options)
                status_emoji = "🟢" if poll.status == "active" else "🔴"
                
                poll_list.append(f"{status_emoji} *ID {poll.id}*: {poll.question}")
                poll_list.append(f"   {total_votes} votes • {poll.created_at.strftime('%m/%d %H:%M')}")
                
                # Show top option
                if poll.options:
                    top_option = max(poll.options, key=lambda x: x.vote_count)
                    poll_list.append(f"   Leading: *{top_option.text}* ({top_option.vote_count} votes)")
                
                poll_list.append("")
            
            safe_say(app, say, "\n".join(poll_list), user_id)
        finally:
            db.close()
    
    elif command == "end":
        poll_id = int(parts[2])
        
        # Check if poll exists and belongs to this team
        db = next(get_db())
        try:
            poll = db.query(Poll).filter(Poll.id == poll_id, Poll.team_id == team_id).first()
            if not poll:
                safe_say(app, say, f"❌ Poll ID {poll_id} not found in this team.", user_id)
                return
            
            if poll.status == "ended":
                safe_say(app, say, f"❌ Poll ID {poll_id} is already ended.", user_id)
                return
            
            # Only poll creator or admin can end the poll
            if poll.creator_id != user_id and not check_permission(user_id, team_id, "manage_users"):
                safe_say(app, say, "❌ Only the poll creator or admins can end this poll.", user_id)
                return
            
            # End the poll
            success = end_poll(poll_id, user_id)
            if success:
                safe_say(app, say, f"✅ Poll ID {poll_id} has been ended.", user_id)
                
                # Update the poll message to show final results
                if poll.message_ts:
                    update_poll_message(app, poll_id, poll.channel_id, poll.message_ts)
                
                # Send notification about poll ending
                notify_poll_ended(app, poll_id)
            else:
                safe_say(app, say, f"❌ Failed to end poll ID {poll_id}.", user_id)
        finally:
            db.close()
    
    elif command == "remove":
        poll_id = int(parts[2])
        
        # Check if poll exists and belongs to this team
        db = next(get_db())
        try:
            poll = db.query(Poll).filter(Poll.id == poll_id, Poll.team_id == team_id).first()
            if not poll:
                safe_say(app, say, f"❌ Poll ID {poll_id} not found in this team.", user_id)
                return
            
            # Only admins can remove polls (more restrictive than ending)
            if not check_permission(user_id, team_id, "manage_users"):
                safe_say(app, say, "❌ Only admins can remove polls.", user_id)
                return
            
            # Get poll info before deletion
            poll_question = poll.question
            
            # Delete related records first (due to foreign key constraints)
            db.query(UserVote).filter(UserVote.poll_id == poll_id).delete()
            db.query(VotedUser).filter(VotedUser.poll_id == poll_id).delete()
            db.query(PollOption).filter(PollOption.poll_id == poll_id).delete()
            db.query(PollAnalytics).filter(PollAnalytics.poll_id == poll_id).delete()
            db.query(VoteActivity).filter(VoteActivity.poll_id == poll_id).delete()
            db.query(Notification).filter(Notification.poll_id == poll_id).delete()
            db.query(PollShare).filter(PollShare.poll_id == poll_id).delete()
            
            # Delete the poll itself
            db.delete(poll)
            db.commit()
            
            safe_say(app, say, f"✅ Poll ID {poll_id} '*{poll_question}*' has been permanently removed.", user_id)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing poll {poll_id}: {e}")
            safe_say(app, say, f"❌ Failed to remove poll ID {poll_id}.", user_id)
        finally:
            db.close()
    
    else:
        safe_say(app, say, "❌ Unknown command. Use: role, list [all], end, remove", user_id)

# Notification System Functions

def get_notification_settings(user_id: str, team_id: str) -> NotificationSettings:
    """Get notification settings for a user, creating defaults if not exists"""
    db = next(get_db())
    try:
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.user_id == user_id,
            NotificationSettings.team_id == team_id
        ).first()
        
        if not settings:
            settings = NotificationSettings(user_id=user_id, team_id=team_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings
    finally:
        db.close()

def send_notification(app: App, user_id: str, team_id: str, notification_type: str, title: str, message: str, poll_id: int = None):
    """Send a notification to a user if they have it enabled"""
    try:
        # Check if user has this notification type enabled
        settings = get_notification_settings(user_id, team_id)
        
        notification_enabled = getattr(settings, notification_type, False)
        if not notification_enabled:
            return
        
        # Store notification in database
        db = next(get_db())
        try:
            notification = Notification(
                user_id=user_id,
                team_id=team_id,
                poll_id=poll_id,
                notification_type=notification_type,
                title=title,
                message=message
            )
            db.add(notification)
            db.commit()
        finally:
            db.close()
        
        # Send DM to user
        try:
            response = app.client.conversations_open(users=[user_id])
            channel_id = response["channel"]["id"]
            
            app.client.chat_postMessage(
                channel=channel_id,
                text=f"🔔 *{title}*\n{message}",
                parse="full"
            )
        except Exception as e:
            logger.error(f"Failed to send DM notification: {e}")
    
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

def notify_poll_created(app: App, poll_id: int, creator_id: str, team_id: str):
    """Notify team members about a new poll"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        # Get all team members who want poll creation notifications
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.team_id == team_id,
            NotificationSettings.poll_created == True,
            NotificationSettings.user_id != creator_id  # Don't notify creator
        ).all()
        
        for setting in settings:
            send_notification(
                app=app,
                user_id=setting.user_id,
                team_id=team_id,
                notification_type="poll_created",
                title="New Poll Created",
                message=f"📊 <@{creator_id}> created a new poll: *{poll.question}*\nGo vote in <#{poll.channel_id}>!",
                poll_id=poll_id
            )
    
    finally:
        db.close()

def notify_vote_milestone(app: App, poll_id: int, vote_count: int):
    """Notify poll creator about vote milestones"""
    if vote_count % 5 != 0:  # Only notify every 5 votes
        return
    
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        send_notification(
            app=app,
            user_id=poll.creator_id,
            team_id=poll.team_id,
            notification_type="vote_milestone",
            title="Vote Milestone Reached",
            message=f"🎉 Your poll *{poll.question}* has reached {vote_count} votes!",
            poll_id=poll_id
        )
    
    finally:
        db.close()

def notify_close_race(app: App, poll_id: int):
    """Notify when there's a close race between top options"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll or len(poll.options) < 2:
            return
        
        # Check if it's a close race
        sorted_options = sorted(poll.options, key=lambda x: x.vote_count, reverse=True)
        top_two = sorted_options[:2]
        
        if top_two[0].vote_count - top_two[1].vote_count <= 1 and top_two[0].vote_count > 0:
            send_notification(
                app=app,
                user_id=poll.creator_id,
                team_id=poll.team_id,
                notification_type="close_race",
                title="Close Race Alert",
                message=f"🏁 Your poll *{poll.question}* has a close race!\n*{top_two[0].text}* ({top_two[0].vote_count}) vs *{top_two[1].text}* ({top_two[1].vote_count})",
                poll_id=poll_id
            )
    
    finally:
        db.close()

def notify_poll_ended(app: App, poll_id: int):
    """Notify about poll ending and results"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        # Find winner
        winner = max(poll.options, key=lambda x: x.vote_count) if poll.options else None
        total_votes = sum(option.vote_count for option in poll.options)
        
        # Get all voters for this poll
        voters = db.query(VotedUser).filter(VotedUser.poll_id == poll_id).all()
        
        for voter in voters:
            if voter.user_id == poll.creator_id:
                continue  # Creator gets a different message
            
            message = f"🔒 Poll ended: *{poll.question}*\n"
            if winner and winner.vote_count > 0:
                percentage = (winner.vote_count / total_votes * 100) if total_votes > 0 else 0
                message += f"🏆 Winner: *{winner.text}* ({winner.vote_count} votes, {percentage:.1f}%)"
            else:
                message += "No votes were cast."
            
            send_notification(
                app=app,
                user_id=voter.user_id,
                team_id=poll.team_id,
                notification_type="poll_ended",
                title="Poll Results",
                message=message,
                poll_id=poll_id
            )
        
        # Special message for creator
        creator_message = f"🔒 Your poll ended: *{poll.question}*\n"
        if winner and winner.vote_count > 0:
            percentage = (winner.vote_count / total_votes * 100) if total_votes > 0 else 0
            creator_message += f"🏆 Winner: *{winner.text}* ({winner.vote_count} votes, {percentage:.1f}%)\n"
            creator_message += f"📊 Total votes: {total_votes} from {len(voters)} voters"
        else:
            creator_message += "No votes were cast."
        
        send_notification(
            app=app,
            user_id=poll.creator_id,
            team_id=poll.team_id,
            notification_type="poll_ended",
            title="Your Poll Results",
            message=creator_message,
            poll_id=poll_id
        )
    
    finally:
        db.close()

def notify_role_changed(app: App, user_id: str, team_id: str, new_role: str, assigned_by: str):
    """Notify user about role change"""
    role_descriptions = {
        "admin": "👑 Admin - Full access to create, manage polls and users",
        "user": "👤 User - Can create and manage your own polls",
        "viewer": "👁️ Viewer - Can vote on polls but not create them"
    }
    
    send_notification(
        app=app,
        user_id=user_id,
        team_id=team_id,
        notification_type="role_changed",
        title="Role Changed",
        message=f"🔄 Your role has been changed to *{new_role}* by <@{assigned_by}>\n{role_descriptions.get(new_role, '')}"
    )

# Cross-Channel Poll Sharing Functions

def show_channel_selection_modal(app: App, trigger_id: str, poll_id: int, user_id: str):
    """Show modal for selecting channels to share poll"""
    try:
        # Get list of channels the bot has access to
        channels_response = app.client.conversations_list(
            types="public_channel,private_channel",
            limit=100
        )
        
        channel_options = []
        for channel in channels_response["channels"]:
            # Skip channels where the poll is already shared
            if not is_poll_shared_in_channel(poll_id, channel["id"]):
                channel_options.append({
                    "text": {"type": "plain_text", "text": f"#{channel['name']}", "emoji": True},
                    "value": channel["id"]
                })
        
        if not channel_options:
            # Use ephemeral message instead of modal if no channels available
            return False
        
        modal_view = {
            "type": "modal",
            "callback_id": "channel_selection_modal",
            "title": {"type": "plain_text", "text": "📤 Share Poll", "emoji": True},
            "submit": {"type": "plain_text", "text": "🚀 Share", "emoji": True},
            "close": {"type": "plain_text", "text": "❌ Cancel", "emoji": True},
            "private_metadata": f"{poll_id}:{user_id}",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "📤 *Share this poll to other channels*\nSelect channels where you want to share this poll."}
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "channels_block",
                    "label": {"type": "plain_text", "text": "📋 Select Channels", "emoji": True},
                    "element": {
                        "type": "multi_static_select",
                        "action_id": "channels_select",
                        "placeholder": {"type": "plain_text", "text": "Choose channels..."},
                        "options": channel_options[:50]  # Slack limit
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "ℹ️ *Note:* The poll will remain synchronized across all channels. Votes from any channel will be counted together."}
                }
            ]
        }
        
        app.client.views_open(trigger_id=trigger_id, view=modal_view)
        return True
        
    except Exception as e:
        logger.error(f"Error showing channel selection modal: {e}")
        return False

def handle_channel_selection_submission(app: App, ack, body, view):
    """Handle channel selection modal submission"""
    ack()
    
    try:
        values = view["state"]["values"]
        selected_channels = values["channels_block"]["channels_select"]["selected_options"]
        
        metadata = view["private_metadata"].split(":")
        poll_id = int(metadata[0])
        user_id = metadata[1]
        
        if not selected_channels:
            return {"response_action": "errors", "errors": {"channels_block": "Please select at least one channel"}}
        
        # Share poll to selected channels
        success_count = 0
        for channel_option in selected_channels:
            channel_id = channel_option["value"]
            if share_poll_to_channel(app, poll_id, channel_id, user_id):
                success_count += 1
        
        if success_count > 0:
            # Success message will be shown by the share_poll_to_channel function
            pass
        else:
            return {"response_action": "errors", "errors": {"channels_block": "Failed to share poll to any channels"}}
        
    except Exception as e:
        logger.error(f"Error handling channel selection: {e}")
        return {"response_action": "errors", "errors": {"channels_block": "Error sharing poll. Please try again."}}

def is_poll_shared_in_channel(poll_id: int, channel_id: str) -> bool:
    """Check if poll is already shared in a channel"""
    db = next(get_db())
    try:
        # Check original poll channel
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if poll and poll.channel_id == channel_id:
            return True
        
        # Check shared channels
        share = db.query(PollShare).filter(
            PollShare.poll_id == poll_id,
            PollShare.channel_id == channel_id,
            PollShare.is_active == True
        ).first()
        
        return share is not None
    finally:
        db.close()

def share_poll_to_channel(app: App, poll_id: int, channel_id: str, shared_by: str) -> bool:
    """Share a poll to a specific channel"""
    try:
        db = next(get_db())
        try:
            poll = db.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                return False
            
            # Check if already shared
            if is_poll_shared_in_channel(poll_id, channel_id):
                return False
            
            # Build poll blocks with cross-channel indicator
            blocks = build_poll_blocks(poll)
            
            # Add cross-channel indicator
            cross_channel_info = {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"📤 Shared from <#{poll.channel_id}> by <@{shared_by}>"}]
            }
            blocks.insert(-1, cross_channel_info)  # Insert before actions
            
            # Post to channel
            response = app.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=f"Poll: {poll.question}"
            )
            
            # Record the share
            share = PollShare(
                poll_id=poll_id,
                channel_id=channel_id,
                message_ts=response["ts"],
                shared_by=shared_by
            )
            db.add(share)
            db.commit()
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error sharing poll to channel: {e}")
        return False

def get_cross_channel_polls(team_id: str, user_id: str) -> list:
    """Get polls visible across all channels for a user"""
    db = next(get_db())
    try:
        # Get polls from user's accessible channels
        polls = db.query(Poll).filter(
            Poll.team_id == team_id,
            Poll.status == "active"
        ).all()
        
        # Track cross-channel view
        for poll in polls:
            view = CrossChannelView(
                user_id=user_id,
                team_id=team_id,
                poll_id=poll.id
            )
            db.merge(view)  # Update if exists
        
        db.commit()
        return polls
        
    finally:
        db.close()

def update_shared_poll_messages(app: App, poll_id: int):
    """Update poll message in all shared channels"""
    db = next(get_db())
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return
        
        # Update original message
        if poll.message_ts:
            update_poll_message(app, poll_id, poll.channel_id, poll.message_ts)
        
        # Update shared messages
        shares = db.query(PollShare).filter(
            PollShare.poll_id == poll_id,
            PollShare.is_active == True
        ).all()
        
        for share in shares:
            if share.message_ts:
                try:
                    blocks = build_poll_blocks(poll)
                    # Add cross-channel indicator
                    cross_channel_info = {
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": f"📤 Shared from <#{poll.channel_id}> by <@{share.shared_by}>"}]
                    }
                    if poll.status == "active":
                        blocks.insert(-1, cross_channel_info)  # Insert before actions
                    else:
                        blocks.append(cross_channel_info)  # Append for ended polls
                    
                    app.client.chat_update(
                        channel=share.channel_id,
                        ts=share.message_ts,
                        blocks=blocks,
                        text=f"Poll: {poll.question}"
                    )
                except Exception as e:
                    logger.error(f"Failed to update shared message in {share.channel_id}: {e}")
        
    finally:
        db.close()