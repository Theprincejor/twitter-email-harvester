#!/bin/bash
# Setup two instances of the bot on one VPS

set -e

echo "🚀 Setting up dual instance deployment..."

# Instance 1
INSTANCE1="/opt/email-campaign-bot-1"
echo "📦 Setting up Instance 1 at $INSTANCE1"

sudo mkdir -p $INSTANCE1
sudo useradd -m -s /bin/bash campaignbot1 2>/dev/null || true
sudo chown -R campaignbot1:campaignbot1 $INSTANCE1

# Instance 2
INSTANCE2="/opt/email-campaign-bot-2"
echo "📦 Setting up Instance 2 at $INSTANCE2"

sudo mkdir -p $INSTANCE2
sudo useradd -m -s /bin/bash campaignbot2 2>/dev/null || true
sudo chown -R campaignbot2:campaignbot2 $INSTANCE2

# Create service files for both instances
echo "📋 Creating service files..."

# Instance 1 Telegram Bot
cat > /tmp/campaign-bot-1-telegram.service <<EOF
[Unit]
Description=Email Campaign Telegram Bot - Instance 1
After=network.target

[Service]
Type=simple
User=campaignbot1
Group=campaignbot1
WorkingDirectory=$INSTANCE1
Environment="PATH=$INSTANCE1/venv/bin"
ExecStart=$INSTANCE1/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot-1-telegram

[Install]
WantedBy=multi-user.target
EOF

# Instance 1 Scraper
cat > /tmp/campaign-bot-1-scraper.service <<EOF
[Unit]
Description=Email Campaign Scraper - Instance 1
After=network.target

[Service]
Type=simple
User=campaignbot1
Group=campaignbot1
WorkingDirectory=$INSTANCE1
Environment="PATH=$INSTANCE1/venv/bin"
ExecStart=$INSTANCE1/venv/bin/python follower_scraper1.py
Restart=always
RestartSec=30

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot-1-scraper

[Install]
WantedBy=multi-user.target
EOF

# Instance 2 Telegram Bot
cat > /tmp/campaign-bot-2-telegram.service <<EOF
[Unit]
Description=Email Campaign Telegram Bot - Instance 2
After=network.target

[Service]
Type=simple
User=campaignbot2
Group=campaignbot2
WorkingDirectory=$INSTANCE2
Environment="PATH=$INSTANCE2/venv/bin"
ExecStart=$INSTANCE2/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot-2-telegram

[Install]
WantedBy=multi-user.target
EOF

# Instance 2 Scraper
cat > /tmp/campaign-bot-2-scraper.service <<EOF
[Unit]
Description=Email Campaign Scraper - Instance 2
After=network.target

[Service]
Type=simple
User=campaignbot2
Group=campaignbot2
WorkingDirectory=$INSTANCE2
Environment="PATH=$INSTANCE2/venv/bin"
ExecStart=$INSTANCE2/venv/bin/python follower_scraper1.py
Restart=always
RestartSec=30

StandardOutput=journal
StandardError=journal
SyslogIdentifier=campaign-bot-2-scraper

[Install]
WantedBy=multi-user.target
EOF

# Install service files
sudo mv /tmp/campaign-bot-1-telegram.service /etc/systemd/system/
sudo mv /tmp/campaign-bot-1-scraper.service /etc/systemd/system/
sudo mv /tmp/campaign-bot-2-telegram.service /etc/systemd/system/
sudo mv /tmp/campaign-bot-2-scraper.service /etc/systemd/system/

sudo systemctl daemon-reload

echo "✅ Dual instance setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy project files to both directories:"
echo "   scp -r * user@vps:$INSTANCE1/"
echo "   scp -r * user@vps:$INSTANCE2/"
echo ""
echo "2. Configure each instance with different:"
echo "   - Telegram bot tokens in config.yaml"
echo "   - Twitter accounts in cookie files"
echo "   - Campaign templates"
echo ""
echo "3. Setup virtual environments:"
echo "   cd $INSTANCE1 && sudo -u campaignbot1 python3.11 -m venv venv && sudo -u campaignbot1 ./venv/bin/pip install -r requirements.txt"
echo "   cd $INSTANCE2 && sudo -u campaignbot2 python3.11 -m venv venv && sudo -u campaignbot2 ./venv/bin/pip install -r requirements.txt"
echo ""
echo "4. Enable and start services:"
echo "   sudo systemctl enable campaign-bot-1-telegram campaign-bot-1-scraper"
echo "   sudo systemctl enable campaign-bot-2-telegram campaign-bot-2-scraper"
echo "   sudo systemctl start campaign-bot-1-telegram campaign-bot-1-scraper"
echo "   sudo systemctl start campaign-bot-2-telegram campaign-bot-2-scraper"
