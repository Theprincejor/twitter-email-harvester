# Email Campaign Bot with Telegram Control

A comprehensive email campaign management system controlled via Telegram bot, with Twitter follower scraping, warmup sequences, checkpoint monitoring, and multi-instance VPS deployment support.

## Features

- **Telegram Bot Control**: Manage campaigns entirely through Telegram commands
- **Multiple Campaigns**: Support for multiple campaigns with different templates and SMTP settings
- **Twitter Integration**: Automatically scrape follower emails from Twitter accounts
- **Warmup System**: Send warmup emails before main campaign to improve deliverability
- **Checkpoint Monitoring**: Periodic test emails to monitor inbox placement
- **Rate Limiting**: Configurable daily limits (50/100/500/1000 emails per day)
- **State Management**: Pause and resume campaigns from where they stopped
- **Multi-Instance Support**: Run multiple independent instances on one VPS
- **Automatic Failover**: Built-in retry logic and error handling

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Telegram Bot                        │
│           (User Control Interface)                   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Campaign Manager                        │
│  - State Management                                  │
│  - Email Queue                                       │
│  - Warmup/Checkpoint Logic                          │
│  - Rate Limiting                                     │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐    ┌──────────────────┐
│  Twitter Scraper  │    │   SMTP Sender    │
│  (Parallel Bots) │    │  (Multi-SMTP)    │
└──────────────────┘    └──────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from @BotFather)
- SMTP credentials
- Twitter account cookies (for scraping)

### Local Setup

1. **Clone the repository**
```bash
git clone <your-repo>
cd email-campaign-bot
```

2. **Create virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure settings**

Edit `config.yaml`:
```yaml
campaigns:
  azuki:
    name: "Azuki Campaign"
    template: "templates/azuki.html"
    subject: "Your Subject"
    smtp:
      server: "smtp.example.com"
      port: 587
      user: "your@email.com"
      password: "your_password"
      from_email: "Campaign <your@email.com>"
      reply_to: "Campaign <your@email.com>"
    warmup_emails: "templates/azuki_warmup.csv"
    checkpoint_emails: "templates/azuki_checkpoint.csv"

telegram:
  bot_token: "YOUR_BOT_TOKEN"
  admin_chat_ids:
    - YOUR_TELEGRAM_USER_ID
```

5. **Setup templates**

- Add HTML templates to `templates/` folder
- Create warmup email lists: `templates/[campaign]_warmup.csv`
- Create checkpoint email lists: `templates/[campaign]_checkpoint.csv`

Format for CSV files:
```csv
id,username,name,email
1,user1,User Name,user@example.com
```

6. **Run the bot**
```bash
python telegram_bot.py
```

## VPS Deployment

### Single Instance Deployment

1. **Copy files to VPS**
```bash
scp -r * user@your-vps:/opt/email-campaign-bot/
```

2. **Run setup script**
```bash
ssh user@your-vps
cd /opt/email-campaign-bot/deploy
chmod +x setup.sh
sudo ./setup.sh
```

3. **Install services**
```bash
chmod +x install-services.sh
sudo ./install-services.sh
```

4. **Start services**
```bash
sudo systemctl start campaign-bot-telegram
sudo systemctl start campaign-bot-scraper
```

### Dual Instance Deployment

For running two independent bots on one VPS:

1. **Run dual setup**
```bash
cd /opt/email-campaign-bot/deploy
chmod +x dual-instance-setup.sh
sudo ./dual-instance-setup.sh
```

2. **Copy files to both instances**
```bash
# Instance 1
scp -r * user@vps:/opt/email-campaign-bot-1/

# Instance 2
scp -r * user@vps:/opt/email-campaign-bot-2/
```

3. **Configure each instance**
- Use different Telegram bot tokens
- Use different Twitter accounts
- Use different SMTP accounts (recommended)

4. **Setup virtual environments**
```bash
# Instance 1
cd /opt/email-campaign-bot-1
sudo -u campaignbot1 python3.11 -m venv venv
sudo -u campaignbot1 ./venv/bin/pip install -r requirements.txt

# Instance 2
cd /opt/email-campaign-bot-2
sudo -u campaignbot2 python3.11 -m venv venv
sudo -u campaignbot2 ./venv/bin/pip install -r requirements.txt
```

5. **Start all services**
```bash
sudo systemctl start campaign-bot-1-telegram campaign-bot-1-scraper
sudo systemctl start campaign-bot-2-telegram campaign-bot-2-scraper
```

## Telegram Bot Commands

### `/start` or `/help`
Show available commands

### `/start_process`
Start a new campaign:
1. Enter Twitter username
2. Select campaign template
3. Choose warmup/checkpoint settings
4. Set daily email limit (50/100/500/1000)
5. Confirm and start

### `/stop_process`
Stop a running campaign. The campaign state is saved and can be resumed later.

### `/continue_process`
Continue a paused or stopped campaign from where it left off.

### `/status`
View status of all campaigns:
- Current state (running/paused/stopped)
- Emails sent today
- Total sent/failed
- Daily limit

### `/settings`
View and modify campaign settings

## Campaign Workflow

### 1. Start Process
```
User: /start_process
Bot: Enter Twitter username
User: azuki
Bot: Select Campaign → [Azuki Campaign]
User: [Select Azuki]
Bot: Use Warmup/Checkpoint? [Yes/No]
User: [Yes]
Bot: Emails per day? [50/100/500/1000]
User: [100]
Bot: Confirm and start?
User: [Confirm]
Bot: ✅ Campaign started
```

### 2. Warmup Phase (if enabled)
- Sends 10 warmup emails to known good addresses
- 10-minute interval between warmup emails
- Improves sender reputation before bulk sending

### 3. Main Campaign
- Sends emails from the scraped list
- Respects daily limit
- Every 10 emails, sends checkpoint email
- Automatically pauses when daily limit reached

### 4. Stop/Continue
- Stop: Saves current position, can resume later
- Continue: Resumes from last sent email

## Monitoring

### Check Service Status
```bash
sudo systemctl status campaign-bot-telegram
sudo systemctl status campaign-bot-scraper
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u campaign-bot-telegram -f

# Last 100 lines
sudo journalctl -u campaign-bot-telegram -n 100
```

### View Campaign Data
All campaign data stored in `data/` folder:
- `campaign_[id]_state.json` - Current state
- `campaign_[id]_sent.csv` - Successfully sent emails
- `campaign_[id]_failed.csv` - Failed emails

## File Structure

```
email-campaign-bot/
├── config.yaml                 # Main configuration
├── campaign_manager.py         # Campaign logic
├── telegram_bot.py             # Telegram bot interface
├── follower_scraper1.py        # Twitter scraper
├── mailer.py                   # Original mailer (deprecated)
├── requirements.txt            # Python dependencies
├── templates/
│   ├── azuki.html             # Email template
│   ├── azuki_warmup.csv       # Warmup emails
│   └── azuki_checkpoint.csv   # Checkpoint emails
├── data/
│   ├── campaign_*_state.json  # Campaign states
│   ├── campaign_*_sent.csv    # Sent logs
│   └── campaign_*_failed.csv  # Failed logs
└── deploy/
    ├── setup.sh               # VPS setup script
    ├── dual-instance-setup.sh # Dual instance setup
    ├── install-services.sh    # Service installer
    ├── campaign-bot-telegram.service
    └── campaign-bot-scraper.service
```

## Twitter Scraper Setup

The scraper runs continuously in the background, extracting emails from Twitter followers.

1. **Get Twitter Cookies**
   - Login to Twitter in browser
   - Use browser extension to export cookies
   - Save as `account1_twitter_cookies.json`, etc.

2. **Configure Scraper**
   - Edit `follower_scraper1.py`
   - Set target username in `scrape_user_followers("username", clients)`

3. **Auto-start with systemd**
   - The scraper service runs automatically
   - Restarts on failure
   - Rotates through multiple accounts to avoid rate limits

## Troubleshooting

### Bot not responding
```bash
# Check if service is running
sudo systemctl status campaign-bot-telegram

# Restart service
sudo systemctl restart campaign-bot-telegram

# Check logs for errors
sudo journalctl -u campaign-bot-telegram -n 50
```

### Emails not sending
1. Check SMTP credentials in `config.yaml`
2. Verify email file exists: `data/[username]_emails.csv`
3. Check campaign state: `/status` in Telegram
4. Review logs for error messages

### Daily limit reached
Campaign automatically pauses when daily limit is reached. It will reset at midnight and can be continued with `/continue_process`.

### Warmup emails not sending
1. Check warmup CSV file exists: `templates/[campaign]_warmup.csv`
2. Ensure CSV has correct format (id,username,name,email)
3. Verify SMTP settings work

## Security Notes

1. **Keep config.yaml private** - Contains sensitive credentials
2. **Use strong passwords** - For SMTP and bot tokens
3. **Limit admin_chat_ids** - Only trusted users
4. **Regular backups** - Of data/ folder
5. **Monitor logs** - For suspicious activity

## Rate Limiting & Deliverability

### Recommended Settings
- **New domain**: 50 emails/day for first week
- **Established domain**: 100-500 emails/day
- **Warmed up domain**: 1000+ emails/day

### Best Practices
1. Always use warmup for new campaigns
2. Enable checkpoint monitoring
3. Start with low daily limits
4. Gradually increase over time
5. Monitor bounce rates
6. Keep unsubscribe link in emails

## Support & Contributing

For issues or questions:
1. Check logs: `journalctl -u campaign-bot-telegram`
2. Review configuration
3. Test with small email list first
4. Open GitHub issue with details

## License

MIT License - See LICENSE file

## Disclaimer

This tool is for legitimate email marketing only. Users are responsible for:
- Compliance with anti-spam laws (CAN-SPAM, GDPR, etc.)
- Obtaining proper consent from recipients
- Including unsubscribe mechanisms
- Respecting opt-out requests

Always ensure your email campaigns comply with local laws and regulations.
