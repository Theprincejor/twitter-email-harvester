# VPS Deployment Guide - GitHub Clone Method

Complete guide to deploy your email campaign bot on a VPS by cloning from GitHub.

## 🚀 Quick Deployment (Single Instance)

### Prerequisites
- VPS with Ubuntu 20.04/22.04 (or similar)
- Root or sudo access
- SSH access to your VPS
- GitHub repo: https://github.com/Theprincejor/twitter-email-harvester

### Step 1: Connect to VPS

```bash
ssh root@your-vps-ip
# OR
ssh your-username@your-vps-ip
```

### Step 2: Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 3: Install Dependencies

```bash
# Install Python 3.11
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip git

# Verify installation
python3.11 --version
```

### Step 4: Clone Repository

```bash
# Clone to /opt/email-campaign-bot
cd /opt
sudo git clone https://github.com/Theprincejor/twitter-email-harvester.git email-campaign-bot

# Navigate to directory
cd email-campaign-bot
```

### Step 5: Create Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Configure Bot

**Edit config.yaml:**
```bash
nano config.yaml
```

**Update these sections:**
```yaml
campaigns:
  azuki:
    smtp:
      password: "YOUR_REAL_SMTP_PASSWORD"  # Change this!

telegram:
  bot_token: "YOUR_BOT_TOKEN"  # Already set if you pushed it
  admin_chat_ids:
    - YOUR_TELEGRAM_USER_ID  # Already set if you pushed it
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 7: Add Warmup/Checkpoint Emails

**Option A: Via Telegram (Recommended)**
```bash
# Start bot
python telegram_bot_extended.py

# In Telegram:
/add_emails
→ Select campaign
→ Select Warmup/Checkpoint
→ Paste your emails
```

**Option B: Edit CSV files**
```bash
nano templates/azuki_warmup.csv
nano templates/azuki_checkpoint.csv
```

### Step 8: Test Bot

```bash
# Make sure venv is activated
source venv/bin/activate

# Run bot
python telegram_bot_extended.py
```

You should see: `🤖 Extended Telegram bot started...`

**Test in Telegram:**
```
/start
/status
/add_emails
```

If working, press `Ctrl+C` to stop and continue to setup as service.

### Step 9: Setup as Systemd Service

**Create service file:**
```bash
sudo nano /etc/systemd/system/campaign-bot.service
```

**Paste this:**
```ini
[Unit]
Description=Email Campaign Telegram Bot
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/email-campaign-bot
Environment="PATH=/opt/email-campaign-bot/venv/bin"
ExecStart=/opt/email-campaign-bot/venv/bin/python telegram_bot_extended.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X`, `Y`, `Enter`

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable campaign-bot
sudo systemctl start campaign-bot
```

**Check status:**
```bash
sudo systemctl status campaign-bot
```

Should show: `active (running)`

### Step 10: Monitor Logs

```bash
# Real-time logs
sudo journalctl -u campaign-bot -f

# Last 50 lines
sudo journalctl -u campaign-bot -n 50

# Stop following: Ctrl+C
```

### ✅ Done! Your bot is now running 24/7

Test in Telegram:
```
/status
/start_process
```

---

## 🔄 Dual Instance Deployment (2 Bots on 1 VPS)

For running two independent bots on the same VPS.

### Step 1: Clone for Both Instances

```bash
# Instance 1
cd /opt
sudo git clone https://github.com/Theprincejor/twitter-email-harvester.git email-campaign-bot-1

# Instance 2
sudo git clone https://github.com/Theprincejor/twitter-email-harvester.git email-campaign-bot-2
```

### Step 2: Setup Instance 1

```bash
cd /opt/email-campaign-bot-1

# Create venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Edit config
nano config.yaml
```

**Update config.yaml for Instance 1:**
```yaml
campaigns:
  azuki:
    smtp:
      user: "bot1@yourdomain.com"  # Different email for bot 1
      password: "bot1_password"

telegram:
  bot_token: "BOT_1_TOKEN_HERE"  # Different bot token
  admin_chat_ids:
    - YOUR_USER_ID
```

### Step 3: Setup Instance 2

```bash
cd /opt/email-campaign-bot-2

# Create venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Edit config
nano config.yaml
```

**Update config.yaml for Instance 2:**
```yaml
campaigns:
  azuki:
    smtp:
      user: "bot2@yourdomain.com"  # Different email for bot 2
      password: "bot2_password"

telegram:
  bot_token: "BOT_2_TOKEN_HERE"  # Different bot token
  admin_chat_ids:
    - YOUR_USER_ID
```

### Step 4: Create Service Files

**Instance 1 service:**
```bash
sudo nano /etc/systemd/system/campaign-bot-1.service
```

```ini
[Unit]
Description=Email Campaign Bot - Instance 1
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/email-campaign-bot-1
Environment="PATH=/opt/email-campaign-bot-1/venv/bin"
ExecStart=/opt/email-campaign-bot-1/venv/bin/python telegram_bot_extended.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot-1

[Install]
WantedBy=multi-user.target
```

**Instance 2 service:**
```bash
sudo nano /etc/systemd/system/campaign-bot-2.service
```

```ini
[Unit]
Description=Email Campaign Bot - Instance 2
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/email-campaign-bot-2
Environment="PATH=/opt/email-campaign-bot-2/venv/bin"
ExecStart=/opt/email-campaign-bot-2/venv/bin/python telegram_bot_extended.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot-2

[Install]
WantedBy=multi-user.target
```

### Step 5: Start Both Instances

```bash
sudo systemctl daemon-reload
sudo systemctl enable campaign-bot-1 campaign-bot-2
sudo systemctl start campaign-bot-1 campaign-bot-2
```

**Check status:**
```bash
sudo systemctl status campaign-bot-1
sudo systemctl status campaign-bot-2
```

### Step 6: Monitor Both

```bash
# Instance 1 logs
sudo journalctl -u campaign-bot-1 -f

# Instance 2 logs (new terminal)
sudo journalctl -u campaign-bot-2 -f
```

---

## 🔧 Updating from GitHub

When you push updates to GitHub, update your VPS:

### Single Instance Update

```bash
cd /opt/email-campaign-bot

# Stop service
sudo systemctl stop campaign-bot

# Pull latest changes
git pull origin main

# Update dependencies if requirements.txt changed
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start campaign-bot

# Check status
sudo systemctl status campaign-bot
```

### Dual Instance Update

```bash
# Update Instance 1
cd /opt/email-campaign-bot-1
sudo systemctl stop campaign-bot-1
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start campaign-bot-1

# Update Instance 2
cd /opt/email-campaign-bot-2
sudo systemctl stop campaign-bot-2
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start campaign-bot-2

# Check both
sudo systemctl status campaign-bot-1
sudo systemctl status campaign-bot-2
```

---

## 📊 Useful Commands

### Service Management

```bash
# Start
sudo systemctl start campaign-bot

# Stop
sudo systemctl stop campaign-bot

# Restart
sudo systemctl restart campaign-bot

# Status
sudo systemctl status campaign-bot

# Enable (auto-start on boot)
sudo systemctl enable campaign-bot

# Disable (don't auto-start)
sudo systemctl disable campaign-bot
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u campaign-bot -f

# Last 100 lines
sudo journalctl -u campaign-bot -n 100

# Today's logs
sudo journalctl -u campaign-bot --since today

# Logs from specific time
sudo journalctl -u campaign-bot --since "2025-01-01 10:00:00"

# Clear old logs
sudo journalctl --vacuum-time=7d
```

### Check Resources

```bash
# CPU/Memory usage
top

# Disk usage
df -h

# Check if bot is running
ps aux | grep telegram_bot

# Network connections
netstat -tulpn | grep python
```

---

## 🐛 Troubleshooting

### Bot not starting

**Check logs:**
```bash
sudo journalctl -u campaign-bot -n 50
```

**Common issues:**

1. **Python version wrong:**
```bash
python3.11 --version
```

2. **Dependencies missing:**
```bash
cd /opt/email-campaign-bot
source venv/bin/activate
pip install -r requirements.txt
```

3. **Config file syntax error:**
```bash
# Test YAML syntax
python3.11 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

4. **Permission issues:**
```bash
sudo chown -R root:root /opt/email-campaign-bot
sudo chmod -R 755 /opt/email-campaign-bot
```

### Bot crashes/restarts

**Check logs for errors:**
```bash
sudo journalctl -u campaign-bot -n 100 | grep -i error
```

**Common causes:**
- SMTP authentication failure
- Invalid bot token
- Network issues
- Out of memory

### Can't connect to bot on Telegram

1. **Check bot is running:**
```bash
sudo systemctl status campaign-bot
```

2. **Check bot token in config.yaml**

3. **Test bot token:**
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

### Emails not sending

1. **Check SMTP credentials in config.yaml**

2. **Test SMTP manually:**
```bash
python3.11
>>> import smtplib
>>> server = smtplib.SMTP('smtp.hostinger.com', 587)
>>> server.starttls()
>>> server.login('support@dropsair.com', 'YOUR_PASSWORD')
>>> server.quit()
>>> exit()
```

3. **Check email files exist:**
```bash
ls -la data/
```

### High CPU/Memory usage

**Check process:**
```bash
top -p $(pgrep -f telegram_bot)
```

**Reduce load:**
- Lower mails per day
- Increase delays in config.yaml
- Check for infinite loops in logs

---

## 🔐 Security Best Practices

### 1. Use SSH Keys (not passwords)

```bash
# On your local machine
ssh-keygen -t rsa -b 4096

# Copy to VPS
ssh-copy-id root@your-vps-ip
```

### 2. Setup Firewall

```bash
sudo ufw allow ssh
sudo ufw enable
```

### 3. Keep System Updated

```bash
# Weekly updates
sudo apt-get update && sudo apt-get upgrade -y
```

### 4. Secure Config Files

```bash
# Make config readable only by root
sudo chmod 600 /opt/email-campaign-bot/config.yaml
```

### 5. Monitor Logs

```bash
# Check daily
sudo journalctl -u campaign-bot --since today
```

---

## 📈 Scaling Tips

### For 50-100 emails/day
- Single instance
- 1GB RAM VPS
- Basic monitoring

### For 500 emails/day
- Single instance
- 2GB RAM VPS
- Multiple SMTP accounts
- Daily log monitoring

### For 1000+ emails/day
- Dual instances
- 4GB RAM VPS
- Multiple SMTP accounts per instance
- Aggressive warmup
- Real-time monitoring

---

## 🎯 Quick Reference

### One-Line Deploy (Single Instance)

```bash
cd /opt && sudo git clone https://github.com/Theprincejor/twitter-email-harvester.git email-campaign-bot && cd email-campaign-bot && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && echo "Now edit config.yaml and run: python telegram_bot_extended.py"
```

### One-Line Update

```bash
cd /opt/email-campaign-bot && sudo systemctl stop campaign-bot && git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl start campaign-bot && sudo systemctl status campaign-bot
```

---

## ✅ Deployment Checklist

- [ ] VPS purchased and accessible via SSH
- [ ] Python 3.11 installed
- [ ] Repository cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] config.yaml updated with real credentials
- [ ] Warmup/checkpoint emails added
- [ ] Bot tested manually
- [ ] Systemd service created
- [ ] Service enabled and started
- [ ] Logs checked for errors
- [ ] Tested via Telegram
- [ ] Auto-start on boot verified

---

## 🆘 Getting Help

**Check logs:**
```bash
sudo journalctl -u campaign-bot -n 100
```

**Test bot manually:**
```bash
cd /opt/email-campaign-bot
source venv/bin/activate
python telegram_bot_extended.py
```

**Common commands:**
```bash
# Restart everything
sudo systemctl restart campaign-bot

# Check if running
ps aux | grep telegram

# Kill if stuck
pkill -f telegram_bot

# Start fresh
sudo systemctl stop campaign-bot
cd /opt/email-campaign-bot
source venv/bin/activate
python telegram_bot_extended.py
```

---

## 🎊 Success!

Your bot is now deployed and running 24/7 on VPS!

**Next steps:**
1. Test with small email list
2. Monitor deliverability
3. Gradually scale up
4. Add more campaigns as needed

**Telegram commands:**
```
/status         - Check all campaigns
/start_process  - Start new campaign
/add_emails     - Add warmup/checkpoint emails
/stop_process   - Stop campaign
```

Happy campaigning! 🚀
