import csv
import smtplib
import random
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


SMTP_SERVER = "smtp.hostinger.com"
SMTP_PORT = 587
SMTP_USER = "aave@team-suuport.com"
SMTP_PASS = "]x]VwkG@1vM;"

FROM_EMAIL = "Aave Support <aave@team-suuport.com>"
SUBJECT = "Quick Question"

HTML_TEMPLATE = """
<html>
  <body>
    <p>Hi {name},</p>
    <p>I came across your profile and thought you might be interested in what we’re building at <b>Our Company</b>.</p>
    <p>Would you be open to a short chat?</p>
    <p>Best,<br>Your Name</p>
    <p style="font-size:11px;color:gray;">If this isn’t relevant, reply STOP and I won’t reach out again.</p>
  </body>
</html>
"""

TEXT_TEMPLATE = """
Hi {name},

I came across your profile and thought you might be interested in what we’re building at Our Company.

Would you be open to a short chat?

Best,
Your Name

(Reply STOP to opt-out)
"""


def deduplicate_csv(
    in_file="data/followers_emails.csv", out_file="data/followers_emails_deduped.csv"
):
    """Remove duplicate emails and return cleaned file path"""
    if not os.path.exists(in_file):
        raise FileNotFoundError(f"❌ Input file not found: {in_file}")

    seen = set()
    deduped_rows = []

    with open(in_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip().lower()
            if email and email not in seen:
                seen.add(email)
                deduped_rows.append(row)

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "username", "name", "email"])
        writer.writeheader()
        writer.writerows(deduped_rows)

    print(f"🧹 Deduplicated {len(deduped_rows)} unique emails → {out_file}")
    return out_file


def send_email(to_email, name):
    msg = MIMEMultipart("alternative")
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = SUBJECT

    text_content = TEXT_TEMPLATE.format(name=name or "there")
    html_content = HTML_TEMPLATE.format(name=name or "there")

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())

    print(f"✅ Sent email to {to_email}")


def bulk_send(csv_file="data/followers_emails.csv", limit=20):
    # Deduplicate first
    clean_file = deduplicate_csv(csv_file)

    with open(clean_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break

            email = row["email"]
            name = row.get("name", "")

            try:
                send_email(email, name)
            except Exception as e:
                print(f"⚠️ Failed to {email}: {e}")

            # human-like delay (5–15s)
            sleep_for = random.randint(5, 15)
            print(f"⏳ Sleeping {sleep_for}s before next...")
            time.sleep(sleep_for)


if __name__ == "__main__":
    bulk_send(limit=20)  # sends 20 deduplicated emails per run
