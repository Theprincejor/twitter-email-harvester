"""
Test script to verify campaign bot setup
"""
import os
import sys
import yaml


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False


def check_config():
    """Check config.yaml"""
    print("\n📋 Checking configuration...")

    if not check_file_exists("config.yaml", "Config file"):
        return False

    try:
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        # Check telegram config
        if 'telegram' not in config:
            print("❌ Telegram config missing")
            return False

        if config['telegram']['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
            print("⚠️  Bot token not configured in config.yaml")
        else:
            print("✅ Telegram bot token configured")

        if not config['telegram']['admin_chat_ids']:
            print("⚠️  No admin chat IDs configured")
        else:
            print(f"✅ Admin chat IDs: {config['telegram']['admin_chat_ids']}")

        # Check campaigns
        if 'campaigns' not in config:
            print("❌ No campaigns configured")
            return False

        print(f"✅ {len(config['campaigns'])} campaign(s) configured:")
        for campaign_id, campaign in config['campaigns'].items():
            print(f"   - {campaign_id}: {campaign['name']}")

            # Check template
            if check_file_exists(campaign['template'], f"     Template"):
                pass

            # Check warmup
            if 'warmup_emails' in campaign:
                check_file_exists(campaign['warmup_emails'], f"     Warmup CSV")

            # Check checkpoint
            if 'checkpoint_emails' in campaign:
                check_file_exists(campaign['checkpoint_emails'], f"     Checkpoint CSV")

        return True

    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")

    required = [
        'yaml',
        'telegram',
        'csv',
        'smtplib'
    ]

    missing = []
    for module in required:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} not installed")
            missing.append(module)

    if missing:
        print(f"\n⚠️  Install missing packages:")
        print(f"   pip install -r requirements.txt")
        return False

    return True


def check_structure():
    """Check directory structure"""
    print("\n📁 Checking directory structure...")

    required_dirs = ['data', 'templates', 'deploy']
    required_files = [
        'campaign_manager.py',
        'telegram_bot.py',
        'requirements.txt',
        'README.md'
    ]

    all_good = True

    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"❌ {dir_name}/ directory missing")
            all_good = False

    for file_name in required_files:
        if check_file_exists(file_name, file_name):
            pass
        else:
            all_good = False

    return all_good


def check_data_files():
    """Check for email data files"""
    print("\n📊 Checking data files...")

    data_dir = "data"
    if not os.path.exists(data_dir):
        print("⚠️  data/ directory not found")
        return False

    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    if not csv_files:
        print("⚠️  No CSV files found in data/")
        print("   You'll need email lists to run campaigns")
    else:
        print(f"✅ Found {len(csv_files)} CSV file(s):")
        for csv_file in csv_files:
            size = os.path.getsize(os.path.join(data_dir, csv_file))
            print(f"   - {csv_file} ({size} bytes)")

    return True


def test_smtp_config():
    """Test SMTP configuration"""
    print("\n📧 Testing SMTP configuration...")

    try:
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        for campaign_id, campaign in config['campaigns'].items():
            smtp = campaign.get('smtp', {})

            print(f"\n   Campaign: {campaign_id}")
            print(f"   Server: {smtp.get('server', 'NOT SET')}")
            print(f"   Port: {smtp.get('port', 'NOT SET')}")
            print(f"   User: {smtp.get('user', 'NOT SET')}")

            if smtp.get('password') == 'YOUR_PASSWORD':
                print(f"   Password: ⚠️  NOT CONFIGURED")
            else:
                print(f"   Password: ✅ SET")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all checks"""
    print("🔍 Campaign Bot Setup Verification")
    print("=" * 50)

    checks = [
        ("Directory structure", check_structure),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Data files", check_data_files),
        ("SMTP config", test_smtp_config)
    ]

    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n✅ All checks passed! You're ready to start the bot.")
        print("\nNext steps:")
        print("1. Configure your bot token and SMTP passwords in config.yaml")
        print("2. Add email lists to data/")
        print("3. Run: python telegram_bot.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("See README.md for setup instructions.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
