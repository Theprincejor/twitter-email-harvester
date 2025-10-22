import csv
import smtplib
import random
import time
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

# ========================
# Configuration
# ========================
SMTP_SERVER = "smtp.hostinger.com"
SMTP_PORT = 587
SMTP_USER = "support@dropsair.com"
SMTP_PASS = "A~4aQ;a/XVF"

FROM_EMAIL = "Azuki Support <support@dropsair.com>"
REPLY_TO = "Azuki Support <support@dropsair.com>"
SUBJECT = "An Invitation to The Garden"

INPUT_CSV = "data/followers_emails.csv"
DEDUPED_CSV = "data/followers_emails_deduped.csv"
FAILED_CSV = "data/failed_emails.csv"
SENT_CSV = "data/sent_emails.csv"
RESUME_FILE = "data/last_index.txt"
HTML_TEMPLATE_FILE = "template.html"

NOTIFICATION_EMAIL = "theprincejor@atomicmail.io"

MAIL_TESTER_ADDRESS = "test-u5j0j8ppq@srv1.mail-tester.com"
TEST_CSV = "data/test.csv"
WARMUP_DURATION_SECONDS = 10 * 60
WARMUP_INTERVAL_SECONDS = 2 * 60
WARMUP_COUNT = max(1, WARMUP_DURATION_SECONDS // WARMUP_INTERVAL_SECONDS)

DELAY_PER_EMAIL = 5
DELAY_AFTER_BATCH = 20 * 60
MAX_NON_RATE_RETRIES = 3
RATE_LIMIT_SLEEP = 30 * 60


# ========================
# Utilities
# ========================
def get_smtp_connection():
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    return server


def load_html_template():
    try:
        with open(HTML_TEMPLATE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"FATAL: HTML template not found at '{HTML_TEMPLATE_FILE}'")
        return None


def send_notification_email(subject, body):
    msg = MIMEText(body)
    msg["From"] = FROM_EMAIL
    msg["To"] = NOTIFICATION_EMAIL
    msg["Subject"] = subject
    try:
        with get_smtp_connection() as server:
            server.sendmail(FROM_EMAIL, NOTIFICATION_EMAIL, msg.as_string())
        print("📬 Notification sent.")
    except Exception as e:
        print(f"🚨 Notification failed: {e}")


def deduplicate_csv(in_file=INPUT_CSV, out_file=DEDUPED_CSV):
    if not os.path.exists(in_file):
        raise FileNotFoundError(f"Input file not found: {in_file}")
    seen = set()
    deduped_rows = []
    fieldnames = ["id", "username", "name", "email"]
    with open(in_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip().lower()
            if email and email not in seen:
                seen.add(email)
                deduped_rows.append(row)
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)
    print(f"🧹 Deduplicated {len(deduped_rows)} emails → {out_file}")
    return out_file


def log_failed_email(row, error):
    fieldnames = ["id", "username", "name", "email", "error"]
    file_exists = os.path.isfile(FAILED_CSV)
    with open(FAILED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row_copy = row.copy()
        row_copy["error"] = str(error)
        writer.writerow(row_copy)


def log_sent_email(row):
    fieldnames = ["id", "username", "name", "email", "timestamp"]
    file_exists = os.path.isfile(SENT_CSV)
    with open(SENT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row_copy = {
            k: v for k, v in row.items() if k in ["id", "username", "name", "email"]
        }
        row_copy["timestamp"] = datetime.now().isoformat()
        writer.writerow(row_copy)


def is_rate_limit_exception(e):
    txt = str(e).lower()
    if hasattr(e, "smtp_code"):
        try:
            code = int(e.smtp_code)
            if code in (421, 450, 451, 452):
                return True
        except Exception:
            pass
    return any(
        k in txt for k in ("rate", "too many", "limit", "throttle", "temporarily")
    )


# ========================
# Send email (with headers)
# ========================
def send_email_raw(to_email, name, html_template):
    if not to_email:
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = SUBJECT
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["Reply-To"] = REPLY_TO

    # ✅ Deliverability headers
    msg["List-Unsubscribe"] = "<mailto:support@dropsair.com?subject=unsubscribe>"
    msg["Precedence"] = "bulk"
    msg["X-Mailer"] = "Azuki Mailer v1.0"
    msg["Feedback-ID"] = "campaign123:dropsair.com:mailer"
    msg["X-Priority"] = "3"
    msg["X-Company"] = "DropsAir"
    msg["X-Source"] = "Azuki-Mailer"

    text_content = (
        f"Hi {name or 'there'},\nPlease view this email in an HTML-compatible client."
    )
    html_content = html_template.format(name=name or "there")

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html", _charset="utf-8"))

    non_rate_retries = 0
    while True:
        try:
            with get_smtp_connection() as server:
                server.sendmail(FROM_EMAIL, to_email, msg.as_string())
            return True
        except Exception as e:
            if is_rate_limit_exception(e):
                print(
                    f"🚦 Rate limit detected for {to_email}. Sleeping {RATE_LIMIT_SLEEP // 60} min..."
                )
                time.sleep(RATE_LIMIT_SLEEP)
                continue
            else:
                non_rate_retries += 1
                print(
                    f"⚠️ Error sending to {to_email} (attempt {non_rate_retries}): {e}"
                )
                if non_rate_retries >= MAX_NON_RATE_RETRIES:
                    return False
                print("⏱️ Waiting 15s before retrying non-rate error...")
                time.sleep(15)
                continue


# ========================
# Mail-Tester + Warm-up
# ========================
def send_mailtester_and_warmup(html_template):
    try:
        print(f"📨 Sending Mail-Tester test to {MAIL_TESTER_ADDRESS}")
        send_email_raw(MAIL_TESTER_ADDRESS, "Mail Tester", html_template)
    except Exception as e:
        print(f"⚠️ Mail-Tester send exception: {e}")

    if not os.path.exists(TEST_CSV):
        print(f"⚠️ Warm-up file not found: {TEST_CSV}. Skipping warm-up.")
        return

    with open(TEST_CSV, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    if not reader:
        print("⚠️ test.csv is empty. Skipping warm-up.")
        return

    print(
        f"🔥 Warm-up: sending {WARMUP_COUNT} messages from {TEST_CSV} every {WARMUP_INTERVAL_SECONDS // 60} min."
    )
    picks = random.sample(range(len(reader)), min(WARMUP_COUNT, len(reader)))

    for idx_num, idx in enumerate(picks, start=1):
        row = reader[idx]
        email = row.get("email", "").strip()
        name = row.get("name", "")
        if email:
            print(f"🔁 Warm-up send {idx_num}/{len(picks)} → {email}")
            success = send_email_raw(email, name, html_template)
            if success:
                log_sent_email(row)
            else:
                log_failed_email(row, "Warm-up failed")

        if idx_num < len(picks):
            time.sleep(WARMUP_INTERVAL_SECONDS)


# ========================
# Resume helpers
# ========================
def get_last_index():
    if os.path.exists(RESUME_FILE):
        try:
            with open(RESUME_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0


def save_last_index(index):
    with open(RESUME_FILE, "w", encoding="utf-8") as f:
        f.write(str(index))


# ========================
# Bulk send with resume
# ========================
def bulk_send(csv_file=INPUT_CSV, limit=100000):
    html_template = load_html_template()
    if not html_template:
        return

    send_mailtester_and_warmup(html_template)

    try:
        clean_file = deduplicate_csv(csv_file)
        with open(clean_file, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        total_to_send = min(len(rows), limit)
        print(f"📧 Starting bulk send for {total_to_send} emails.")

        start_index = get_last_index()
        if start_index >= total_to_send:
            print("✅ All emails already sent.")
            save_last_index(0)
            return

        print(f"▶️ Resuming from index {start_index}")

        for i, row in enumerate(rows[start_index:limit], start=start_index):
            email = row.get("email", "").strip()
            name = row.get("name", "")
            if not email:
                save_last_index(i + 1)
                continue

            print(f"📨 Sending {i + 1}/{total_to_send} → {email}")
            success = send_email_raw(email, name, html_template)
            if success:
                log_sent_email(row)
            else:
                log_failed_email(row, "Failed after retries")

            save_last_index(i + 1)

            if (i + 1) % 50 == 0 and (i + 1) < total_to_send:
                print("😴 Sent 50 emails. Sleeping 20 minutes...")
                time.sleep(DELAY_AFTER_BATCH)
            elif (i + 1) < total_to_send:
                time.sleep(DELAY_PER_EMAIL)

        print("✅ Bulk send complete.")
        send_notification_email(
            "Mailer Completed", f"✅ Finished sending {total_to_send} emails."
        )
        save_last_index(0)
    except Exception as e:
        print(f"🚨 Critical error: {e}")
        send_notification_email("Mailer FAILED", f"🚨 Critical error: {e}")


# ========================
# Resend failed emails
# ========================
def resend_failed_emails(csv_file=FAILED_CSV):
    html_template = load_html_template()
    if not html_template:
        return

    if not os.path.exists(csv_file):
        print("❌ No failed_emails.csv found.")
        return

    with open(csv_file, newline="", encoding="utf-8") as f:
        failed_rows = list(csv.DictReader(f))

    if not failed_rows:
        print("✅ No failed emails to retry.")
        return

    print(f"🔁 Retrying {len(failed_rows)} failed emails...")

    remaining = []
    for i, row in enumerate(failed_rows, start=1):
        email = row.get("email", "").strip()
        name = row.get("name", "")
        if not email:
            continue

        success = send_email_raw(email, name, html_template)
        if success:
            log_sent_email(row)
        else:
            row["error"] = "Still failing after retry"
            remaining.append(row)

        if i % 50 == 0 and i < len(failed_rows):
            time.sleep(DELAY_AFTER_BATCH)
        elif i < len(failed_rows):
            time.sleep(DELAY_PER_EMAIL)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "username", "name", "email", "error"]
        )
        writer.writeheader()
        writer.writerows(remaining)

    send_notification_email(
        "Retry Completed",
        f"✅ {len(failed_rows) - len(remaining)} resent.\n❌ {len(remaining)} still failing.",
    )


# ========================
# Entrypoint
# ========================
if __name__ == "__main__":
    choice = (
        input("Type 'main' to send new emails or 'retry' to resend failed: ")
        .strip()
        .lower()
    )
    if choice == "retry":
        resend_failed_emails() 
    else:
        bulk_send()
