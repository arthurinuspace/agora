# Usage Guide

## 📝 Basic Usage

### Creating Your First Poll

```
/agora What should we have for lunch?
```

This opens a modal where you can:
- Edit the poll question
- Add multiple options (one per line)
- Configure voting settings
- Set scheduling options

### Quick Poll Examples

```
# Simple yes/no poll
/agora Should we implement this feature?

# Multiple choice poll
/agora Which meeting time works best?

# Decision making poll
/agora What's our next sprint priority?
```

## 📊 Poll Types

### Single Choice Polls
- Users can select only one option
- Great for decisions and preferences
- Default poll type

### Multiple Choice Polls
- Users can select multiple options
- Useful for gathering multiple preferences
- Enable in poll creation modal

### Ranked Choice Polls
- Users rank options in order of preference
- Advanced voting method
- Best for complex decision-making

## 🔧 Advanced Features

### Scheduled Polls

1. Use `/agora` to create a poll
2. In the modal, set:
   - **Start Time**: When voting begins
   - **End Time**: When voting automatically ends
   - **Timezone**: Your local timezone

### Anonymous vs. Non-Anonymous

- **Anonymous** (default): Voter identities are hidden
- **Non-Anonymous**: Voter names are visible to poll creator
- Configure in poll creation modal

### Poll Management

#### For Poll Creators
- **Edit Poll**: Modify question and options (if no votes yet)
- **End Poll**: Stop voting and show final results
- **Delete Poll**: Remove poll completely
- **Export Results**: Download data in CSV/JSON/Excel

#### For Voters
- **Vote**: Select your choice(s)
- **Change Vote**: Update your selection (if allowed)
- **View Results**: See current vote counts

## 📊 Analytics & Insights

### Real-time Results
- Live vote counts
- Participation percentages
- Visual progress bars
- Trend indicators

### Detailed Analytics
- **Participation Rate**: Who voted vs. who didn't
- **Voting Patterns**: When votes were cast
- **Option Performance**: Which options are trending
- **Demographic Insights**: Channel-based analysis

### Export Options

```bash
# Available formats
CSV     # Spreadsheet-compatible
JSON    # API-friendly format
Excel   # Advanced spreadsheet features
PDF     # Print-friendly reports
```

## 🔍 Using the Web Dashboard

### Access Dashboard
1. Go to `https://your-domain.com/admin`
2. Sign in with Slack authentication
3. View your workspace polls

### Dashboard Features
- **Active Polls**: Currently running polls
- **Poll History**: All past polls
- **Analytics**: Workspace-wide statistics
- **User Management**: Admin controls
- **Export Tools**: Bulk data export

## 📱 Mobile Usage

### Slack Mobile App
- Full feature compatibility
- Native poll interaction
- Push notifications for poll updates
- Offline vote queuing

### Mobile Web Dashboard
- Responsive design
- Touch-friendly interface
- Mobile-optimized charts
- Swipe gestures

## 💬 Slack Integration Features

### Slash Commands

```
/agora help                    # Show help message
/agora status                  # Check app status
/agora settings               # Configure preferences
/agora analytics              # View workspace stats
```

### Interactive Components

- **Poll Cards**: Rich poll display in channels
- **Vote Buttons**: One-click voting
- **Results View**: Expandable results section
- **Action Buttons**: Poll management controls

### Notifications

- **Poll Created**: Notify channel members
- **Poll Ending**: Remind users to vote
- **Results Ready**: Share final results
- **Mentions**: Tag users in poll discussions

## 🔔 Best Practices

### Creating Effective Polls

1. **Clear Questions**: Be specific and unambiguous
2. **Balanced Options**: Provide comprehensive choices
3. **Appropriate Timing**: Consider team schedules
4. **Right Audience**: Target relevant team members
5. **Follow Up**: Share results and next steps

### Managing Participation

- **Encourage Voting**: Explain importance of participation
- **Set Deadlines**: Create urgency with end times
- **Remind Users**: Send gentle reminders
- **Make it Fun**: Use engaging questions and emojis

### Data Privacy

- **Respect Anonymity**: Don't try to identify anonymous voters
- **Secure Storage**: Data is encrypted and secured
- **Limited Access**: Only authorized users can view results
- **Data Retention**: Automatic cleanup of old poll data

## 🚫 Troubleshooting

### Common Issues

#### Poll Not Appearing
```
# Check app permissions
/agora status

# Verify bot is in channel
@agora ping

# Reinstall app if needed
# Contact admin for workspace permissions
```

#### Can't Vote
```
# Refresh Slack app
# Check if poll is still active
# Verify you haven't already voted (if single vote)
```

#### Results Not Loading
```
# Check internet connection
# Try refreshing the poll
# Contact admin if problem persists
```

### Error Messages

| Error | Cause | Solution |
|-------|--------|----------|
| "Poll not found" | Poll was deleted | Contact poll creator |
| "Voting ended" | Poll expired | Results are final |
| "Permission denied" | Not in workspace | Join workspace first |
| "Rate limited" | Too many requests | Wait and try again |

## See Also

- [Quick Start Guide](quick-start.md)
- [Configuration Guide](configuration.md)
- [API Documentation](api.md)
- [Admin Guide](admin.md)
