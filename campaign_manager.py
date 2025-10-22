"""
Campaign Manager - Handles email campaign state, warmup, checkpoints, and sending
"""
import csv
import smtplib
import random
import time
import os
import json
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Dict, List, Optional
import yaml
import threading


class CampaignState:
    """Manages the state of a campaign"""

    def __init__(self, campaign_id: str, data_dir: str = "data"):
        self.campaign_id = campaign_id
        self.data_dir = data_dir
        self.state_file = os.path.join(data_dir, f"campaign_{campaign_id}_state.json")
        self.state = self._load_state()
        self._lock = threading.Lock()

    def _load_state(self) -> Dict:
        """Load campaign state from file"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "status": "stopped",  # stopped, running, paused
            "twitter_username": None,
            "last_email_index": 0,
            "emails_sent_today": 0,
            "last_reset_date": datetime.now().date().isoformat(),
            "total_sent": 0,
            "total_failed": 0,
            "warmup_completed": False,
            "settings": {
                "use_warmup_checkpoint": False,
                "mails_per_day": 100,
                "warmup_count": 10,
                "warmup_interval_minutes": 10,
                "checkpoint_interval": 10  # Send checkpoint email every N emails
            }
        }

    def _save_state(self):
        """Save campaign state to file"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)

    def update(self, **kwargs):
        """Update state with new values"""
        with self._lock:
            self.state.update(kwargs)
            self._save_state()

    def update_settings(self, **kwargs):
        """Update campaign settings"""
        with self._lock:
            self.state["settings"].update(kwargs)
            self._save_state()

    def increment_sent(self):
        """Increment emails sent counter"""
        with self._lock:
            self.state["emails_sent_today"] += 1
            self.state["total_sent"] += 1
            self.state["last_email_index"] += 1
            self._save_state()

    def increment_failed(self):
        """Increment failed emails counter"""
        with self._lock:
            self.state["total_failed"] += 1
            self._save_state()

    def check_daily_limit(self) -> bool:
        """Check if daily limit is reached, reset if new day"""
        with self._lock:
            today = datetime.now().date().isoformat()
            if self.state["last_reset_date"] != today:
                self.state["emails_sent_today"] = 0
                self.state["last_reset_date"] = today
                self._save_state()

            mails_per_day = self.state["settings"]["mails_per_day"]
            return self.state["emails_sent_today"] < mails_per_day

    def get_status(self) -> Dict:
        """Get current campaign status"""
        with self._lock:
            return self.state.copy()


class CampaignManager:
    """Manages email campaigns with warmup, checkpoints, and rate limiting"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.data_dir = self.config['settings']['data_dir']
        os.makedirs(self.data_dir, exist_ok=True)

        self.active_campaigns: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}

    def get_campaigns(self) -> List[str]:
        """Get list of available campaigns"""
        return list(self.config['campaigns'].keys())

    def get_campaign_config(self, campaign_id: str) -> Dict:
        """Get configuration for a specific campaign"""
        if campaign_id not in self.config['campaigns']:
            raise ValueError(f"Campaign '{campaign_id}' not found")
        return self.config['campaigns'][campaign_id]

    def _get_smtp_connection(self, smtp_config: Dict):
        """Create SMTP connection"""
        server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
        server.starttls()
        server.login(smtp_config['user'], smtp_config['password'])
        return server

    def _load_html_template(self, template_path: str) -> Optional[str]:
        """Load HTML template"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Template not found: {template_path}")
            return None

    def _send_email(self, to_email: str, name: str, html_template: str,
                   subject: str, smtp_config: Dict) -> bool:
        """Send a single email with retry logic"""
        if not to_email:
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = smtp_config['from_email']
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        msg["Reply-To"] = smtp_config['reply_to']

        # Deliverability headers
        msg["List-Unsubscribe"] = f"<mailto:{smtp_config['user']}?subject=unsubscribe>"
        msg["Precedence"] = "bulk"
        msg["X-Priority"] = "3"

        text_content = f"Hi {name or 'there'},\nPlease view this email in an HTML-compatible client."
        html_content = html_template.format(name=name or "there")

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html", _charset="utf-8"))

        max_retries = self.config['settings']['max_retries']
        for attempt in range(max_retries):
            try:
                with self._get_smtp_connection(smtp_config) as server:
                    server.sendmail(smtp_config['from_email'], to_email, msg.as_string())
                return True
            except Exception as e:
                print(f"Error sending to {to_email} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(15)

        return False

    def _log_email(self, campaign_id: str, row: Dict, status: str, error: str = ""):
        """Log sent or failed email"""
        log_file = os.path.join(
            self.data_dir,
            f"campaign_{campaign_id}_{status}.csv"
        )

        fieldnames = ["id", "username", "name", "email", "timestamp"]
        if status == "failed":
            fieldnames.append("error")

        file_exists = os.path.isfile(log_file)
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            log_row = {k: v for k, v in row.items() if k in fieldnames}
            log_row["timestamp"] = datetime.now().isoformat()
            if status == "failed":
                log_row["error"] = error

            writer.writerow(log_row)

    def _load_test_emails(self, campaign_id: str) -> List[Dict]:
        """Load test emails (used for both warmup and checkpoint)"""
        test_file = os.path.join(self.config['settings']['data_dir'], f"campaign_{campaign_id}_test_emails.csv")

        # Fallback to old warmup file for backwards compatibility
        if not os.path.exists(test_file):
            template_dir = "templates"
            old_warmup = os.path.join(template_dir, f"{campaign_id}_warmup.csv")
            if os.path.exists(old_warmup):
                test_file = old_warmup

        if not os.path.exists(test_file):
            return []

        with open(test_file, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _send_warmup_emails(self, campaign_id: str, campaign_config: Dict,
                           state: CampaignState, stop_flag: threading.Event) -> bool:
        """Send warmup emails - first 10 from test email list"""
        test_emails = self._load_test_emails(campaign_id)

        if not test_emails:
            print(f"⚠️ No test emails found for campaign {campaign_id}")
            return True

        settings = state.state["settings"]
        warmup_count = min(settings.get("warmup_count", 10), len(test_emails))
        warmup_interval = settings.get("warmup_interval_minutes", 10) * 60

        print(f"🔥 Starting warmup: {warmup_count} emails, {warmup_interval // 60} min intervals")

        html_template = self._load_html_template(campaign_config['template'])
        if not html_template:
            return False

        # Send first N emails from test list
        for idx in range(warmup_count):
            if stop_flag.is_set():
                print("⏸️ Warmup stopped by user")
                return False

            row = test_emails[idx]
            email = row.get('email', '').strip()
            name = row.get('name', '')

            if email:
                print(f"🔁 Warmup {idx + 1}/{warmup_count} → {email}")
                success = self._send_email(
                    email, name, html_template,
                    campaign_config['subject'],
                    campaign_config['smtp']
                )

                if success:
                    self._log_email(campaign_id, row, "sent")
                else:
                    self._log_email(campaign_id, row, "failed", "Warmup failed")

                if idx < warmup_count - 1:
                    time.sleep(warmup_interval)

        state.update(warmup_completed=True, checkpoint_index=0)
        print("✅ Warmup completed")
        return True

    def _send_checkpoint_email(self, campaign_id: str, campaign_config: Dict, state: CampaignState):
        """Send checkpoint email - rotates through all test emails"""
        test_emails = self._load_test_emails(campaign_id)

        if not test_emails:
            return

        html_template = self._load_html_template(campaign_config['template'])
        if not html_template:
            return

        # Get current checkpoint index (rotates through all test emails)
        checkpoint_index = state.state.get("checkpoint_index", 0)

        # Pick email from rotation
        row = test_emails[checkpoint_index % len(test_emails)]
        email = row.get('email', '').strip()
        name = row.get('name', '')

        if email:
            print(f"✓ Checkpoint {checkpoint_index + 1} → {email} (rotation)")
            self._send_email(
                email, name, html_template,
                campaign_config['subject'],
                campaign_config['smtp']
            )

        # Increment checkpoint index for next rotation
        state.update(checkpoint_index=checkpoint_index + 1)

    def _run_campaign(self, campaign_id: str, twitter_username: str,
                     state: CampaignState, stop_flag: threading.Event):
        """Run the email campaign"""
        try:
            campaign_config = self.get_campaign_config(campaign_id)

            # Handle warmup
            if state.state["settings"]["use_warmup_checkpoint"] and not state.state["warmup_completed"]:
                if not self._send_warmup_emails(campaign_id, campaign_config, state, stop_flag):
                    state.update(status="stopped")
                    return

            # Load email list
            email_file = os.path.join(self.data_dir, f"{twitter_username}_emails.csv")
            if not os.path.exists(email_file):
                # Try the followers_emails.csv as fallback
                email_file = os.path.join(self.data_dir, "followers_emails.csv")
                if not os.path.exists(email_file):
                    print(f"❌ Email file not found for {twitter_username}")
                    state.update(status="stopped")
                    return

            with open(email_file, newline='', encoding='utf-8') as f:
                email_list = list(csv.DictReader(f))

            html_template = self._load_html_template(campaign_config['template'])
            if not html_template:
                state.update(status="stopped")
                return

            start_index = state.state["last_email_index"]
            total_emails = len(email_list)

            print(f"📧 Starting campaign: {total_emails} emails, resuming from index {start_index}")

            settings = state.state["settings"]
            checkpoint_interval = settings.get("checkpoint_interval", 10)

            for i in range(start_index, total_emails):
                if stop_flag.is_set():
                    print("⏸️ Campaign paused by user")
                    state.update(status="paused")
                    return

                # Check daily limit
                if not state.check_daily_limit():
                    print(f"📊 Daily limit reached ({settings['mails_per_day']} emails)")
                    state.update(status="paused")
                    return

                row = email_list[i]
                email = row.get('email', '').strip()
                name = row.get('name', '')

                if not email:
                    state.increment_sent()
                    continue

                print(f"📨 Sending {i + 1}/{total_emails} → {email}")

                success = self._send_email(
                    email, name, html_template,
                    campaign_config['subject'],
                    campaign_config['smtp']
                )

                if success:
                    self._log_email(campaign_id, row, "sent")
                    state.increment_sent()
                else:
                    self._log_email(campaign_id, row, "failed", "Failed after retries")
                    state.increment_failed()

                # Send checkpoint email if enabled
                if settings["use_warmup_checkpoint"] and (i + 1) % checkpoint_interval == 0:
                    self._send_checkpoint_email(campaign_id, campaign_config, state)

                # Delay between emails
                delay = self.config['settings']['delay_per_email']
                if (i + 1) % 50 == 0 and (i + 1) < total_emails:
                    delay = self.config['settings']['delay_after_batch']
                    print(f"😴 Batch complete, sleeping {delay // 60} minutes...")

                time.sleep(delay)

            print(f"✅ Campaign completed! Sent: {state.state['total_sent']}, Failed: {state.state['total_failed']}")
            state.update(status="completed")

        except Exception as e:
            print(f"🚨 Campaign error: {e}")
            state.update(status="error")

    def start_campaign(self, campaign_id: str, twitter_username: str,
                      use_warmup_checkpoint: bool = False,
                      mails_per_day: int = 100) -> Dict:
        """Start a new campaign"""
        if campaign_id in self.active_campaigns:
            return {"success": False, "message": "Campaign already running"}

        state = CampaignState(campaign_id, self.data_dir)
        state.update(
            status="running",
            twitter_username=twitter_username,
            last_email_index=0,
            warmup_completed=False
        )
        state.update_settings(
            use_warmup_checkpoint=use_warmup_checkpoint,
            mails_per_day=mails_per_day
        )

        stop_flag = threading.Event()
        self.stop_flags[campaign_id] = stop_flag

        thread = threading.Thread(
            target=self._run_campaign,
            args=(campaign_id, twitter_username, state, stop_flag),
            daemon=True
        )
        thread.start()
        self.active_campaigns[campaign_id] = thread

        return {"success": True, "message": f"Campaign '{campaign_id}' started"}

    def stop_campaign(self, campaign_id: str) -> Dict:
        """Stop a running campaign"""
        if campaign_id not in self.active_campaigns:
            return {"success": False, "message": "Campaign not running"}

        self.stop_flags[campaign_id].set()
        self.active_campaigns[campaign_id].join(timeout=5)

        del self.active_campaigns[campaign_id]
        del self.stop_flags[campaign_id]

        state = CampaignState(campaign_id, self.data_dir)
        state.update(status="stopped")

        return {"success": True, "message": f"Campaign '{campaign_id}' stopped"}

    def continue_campaign(self, campaign_id: str) -> Dict:
        """Continue a paused campaign"""
        if campaign_id in self.active_campaigns:
            return {"success": False, "message": "Campaign already running"}

        state = CampaignState(campaign_id, self.data_dir)
        if state.state["status"] not in ["paused", "stopped"]:
            return {"success": False, "message": "Campaign cannot be continued"}

        twitter_username = state.state.get("twitter_username")
        if not twitter_username:
            return {"success": False, "message": "No twitter username found in state"}

        state.update(status="running")

        stop_flag = threading.Event()
        self.stop_flags[campaign_id] = stop_flag

        thread = threading.Thread(
            target=self._run_campaign,
            args=(campaign_id, twitter_username, state, stop_flag),
            daemon=True
        )
        thread.start()
        self.active_campaigns[campaign_id] = thread

        return {"success": True, "message": f"Campaign '{campaign_id}' continued"}

    def get_campaign_status(self, campaign_id: str) -> Dict:
        """Get status of a campaign"""
        state = CampaignState(campaign_id, self.data_dir)
        status = state.get_status()
        status["is_running"] = campaign_id in self.active_campaigns
        return status
