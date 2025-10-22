#!/bin/bash
# Install systemd services

set -e

echo "📦 Installing systemd services..."

# Copy service files
sudo cp campaign-bot-telegram.service /etc/systemd/system/
sudo cp campaign-bot-scraper.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable campaign-bot-telegram
sudo systemctl enable campaign-bot-scraper

echo "✅ Services installed!"
echo ""
echo "To start services:"
echo "  sudo systemctl start campaign-bot-telegram"
echo "  sudo systemctl start campaign-bot-scraper"
echo ""
echo "To check status:"
echo "  sudo systemctl status campaign-bot-telegram"
echo "  sudo systemctl status campaign-bot-scraper"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u campaign-bot-telegram -f"
echo "  sudo journalctl -u campaign-bot-scraper -f"
