# Quick Start Guide

Get your email campaign bot running in 10 minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Telegram bot token (from [@BotFather](https://t.me/BotFather))
- [ ] Your Telegram user ID
- [ ] SMTP email credentials
- [ ] Twitter account cookies (optional, for scraping)

## Step 1: Install Dependencies (2 minutes)

```bash
# Clone or download the project
cd email-campaign-bot

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure Bot (3 minutes)

Edit `config.yaml`:

```yaml
campaigns:
  azuki:
    name: "Azuki Campaign"
    template: "templates/azuki.html"
    subject: "An Invitation to The Garden"
    smtp:
      server: "smtp.hostinger.com"        # Your SMTP server
      port: 587
      user: "support@dropsair.com"        # Your email
      password: "YOUR_PASSWORD"            # Your SMTP password
      from_email: "Azuki Support <support@dropsair.com>"
      reply_to: "Azuki Support <support@dropsair.com>"
    warmup_emails: "templates/azuki_warmup.csv"
    checkpoint_emails: "templates/azuki_checkpoint.csv"

telegram:
  bot_token: "8262377717:AAEbRPqVo_INpRPUjzWAZRUxNNxzoNyXQdA"
  admin_chat_ids:
    - 1724099455  # Your Telegram user ID
```

## Step 3: Setup Templates (2 minutes)

Your templates are already in `templates/`:
- `templates/azuki.html` - Email template
- `templates/azuki_warmup.csv` - Warmup emails list
- `templates/azuki_checkpoint.csv` - Checkpoint emails list

**Edit warmup and checkpoint CSV files** with your real email addresses:

`templates/azuki_warmup.csv`:
```csv
id,username,name,email
1,warmup1,Warmup User 1,your-warmup-email-1@gmail.com
2,warmup2,Warmup User 2,your-warmup-email-2@gmail.com
```

`templates/azuki_checkpoint.csv`:
```csv
id,username,name,email
1,checkpoint1,Monitor 1,your-monitor-email@gmail.com
```

## Step 4: Prepare Email List (1 minute)

Put your scraped emails in `data/followers_emails.csv`:

```csv
id,username,name,email
1,user1,John Doe,john@example.com
2,user2,Jane Smith,jane@example.com
```

## Step 5: Start Bot (1 minute)

```bash
python telegram_bot.py
```

You should see: `🤖 Telegram bot started...`

## Step 6: Use Telegram Bot (1 minute)

1. **Open Telegram** and find your bot
2. **Send** `/start` to see commands
3. **Send** `/start_process` to begin:
   - Enter Twitter username: `azuki`
   - Select campaign: **Azuki Campaign**
   - Use warmup? **Yes** (recommended)
   - Emails per day? **50** (start small)
   - **Confirm & Start**

## Your First Campaign

The bot will now:
1. ✅ Send 10 warmup emails (10 min intervals)
2. ✅ Start main campaign
3. ✅ Send checkpoint emails every 10 sends
4. ✅ Respect daily limit (50 emails)
5. ✅ Auto-pause at midnight

## Monitor Progress

```bash
# Check status in Telegram
/status

# Or view logs
tail -f campaign.log  # if logging enabled
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `/start_process` | Start new campaign |
| `/stop_process` | Pause campaign |
| `/continue_process` | Resume campaign |
| `/status` | View progress |
| `/settings` | Change settings |

## VPS Deployment (Optional)

For 24/7 operation:

```bash
# 1. Copy to VPS
scp -r * user@vps:/opt/email-campaign-bot/

# 2. SSH to VPS
ssh user@vps

# 3. Run setup
cd /opt/email-campaign-bot/deploy
chmod +x setup.sh
sudo ./setup.sh

# 4. Install services
chmod +x install-services.sh
sudo ./install-services.sh

# 5. Start services
sudo systemctl start campaign-bot-telegram
```

## Two Instances on One VPS

Run two bots simultaneously:

```bash
cd /opt/email-campaign-bot/deploy
chmod +x dual-instance-setup.sh
sudo ./dual-instance-setup.sh
```

Then configure each instance with different:
- Telegram bot token
- SMTP credentials
- Twitter accounts

## Troubleshooting

### Bot not starting?
```bash
# Check if port is already in use
ps aux | grep telegram_bot.py

# Kill if needed
pkill -f telegram_bot.py

# Start again
python telegram_bot.py
```

### Emails not sending?
1. Verify SMTP credentials in `config.yaml`
2. Test SMTP manually:
   ```python
   python
   >>> import smtplib
   >>> server = smtplib.SMTP('smtp.hostinger.com', 587)
   >>> server.starttls()
   >>> server.login('your@email.com', 'password')
   >>> server.quit()
   ```

### Telegram bot not responding?
1. Check bot token is correct
2. Verify your user ID in `admin_chat_ids`
3. Make sure bot is running (`python telegram_bot.py`)

## Next Steps

1. **Test with small list** - Start with 10-20 emails
2. **Monitor deliverability** - Check spam folders
3. **Gradually increase** - Move from 50 to 100 to 500 per day
4. **Add more campaigns** - Copy campaign config in `config.yaml`
5. **Setup scrapers** - For automatic email collection

## Support

Need help? Check:
1. **README.md** - Full documentation
2. **Logs** - `journalctl -u campaign-bot-telegram`
3. **GitHub Issues** - Report problems

Happy campaigning! 🚀
