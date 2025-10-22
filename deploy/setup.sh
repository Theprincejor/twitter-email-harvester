#!/bin/bash
# Setup script for VPS deployment

set -e

echo "🚀 Starting Email Campaign Bot Setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Create user for the bot
echo "👤 Creating bot user..."
if ! id "campaignbot" &>/dev/null; then
    sudo useradd -m -s /bin/bash campaignbot
fi

# Create directory structure
echo "📁 Creating directory structure..."
INSTALL_DIR="/opt/email-campaign-bot"
sudo mkdir -p $INSTALL_DIR
sudo chown campaignbot:campaignbot $INSTALL_DIR

# Copy files (run from your local machine)
echo "📋 Files should be copied to $INSTALL_DIR"
echo "   Run: scp -r * user@your-vps:$INSTALL_DIR/"

# Create virtual environment
echo "🔧 Setting up virtual environment..."
cd $INSTALL_DIR
sudo -u campaignbot python3.11 -m venv venv
sudo -u campaignbot ./venv/bin/pip install --upgrade pip
sudo -u campaignbot ./venv/bin/pip install -r requirements.txt

# Create data directory
echo "📊 Creating data directory..."
sudo -u campaignbot mkdir -p $INSTALL_DIR/data

# Set permissions
sudo chown -R campaignbot:campaignbot $INSTALL_DIR
sudo chmod -R 755 $INSTALL_DIR

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit config.yaml with your settings"
echo "2. Copy your Twitter cookie files"
echo "3. Copy your email templates to templates/"
echo "4. Run: sudo systemctl enable campaign-bot-telegram"
echo "5. Run: sudo systemctl start campaign-bot-telegram"
