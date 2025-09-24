import asyncio
import json
import csv
import os
import re
import argparse
import time
from itertools import cycle
from datetime import datetime, timedelta
from twikit import Client
from twikit.errors import TooManyRequests, NotFound

# Multiple cookie files
COOKIE_FILES = [
    "account1_twitter_cookies.json",
    "account2_twitter_cookies.json",
    "account3_twitter_cookies.json",
]

PROGRESS_FILE = "progress.json"
OUTPUT_FILE = "followers_emails.csv"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def load_clients():
    clients = []
    for file in COOKIE_FILES:
        if not os.path.exists(file):
            print(f"⚠️ Cookie file missing: {file}, skipping...")
            continue
        client = Client(language="en-US")
        client.load_cookies(file)
        clients.append(client)
        print(f"🔑 Loaded client from {file}")
    if not clients:
        raise RuntimeError(
            "❌ No valid cookie files found. Please run login scripts first."
        )
    print(f"✅ Loaded {len(clients)} client(s)")
    return clients


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        migrated = {}
        for user, val in data.items():
            if isinstance(val, int):
                migrated[user] = {"count": val, "cursor": None}
            elif isinstance(val, dict):
                migrated[user] = val
            else:
                migrated[user] = {"count": 0, "cursor": None}
        return migrated
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def extract_emails(user):
    text_sources = [user.description or "", user.url or ""]
    emails = []
    for text in text_sources:
        emails.extend(EMAIL_RE.findall(text))
    return emails


def save_emails(data, out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, OUTPUT_FILE)
    fieldnames = ["id", "username", "name", "email"]

    existing_ids = set()
    if os.path.isfile(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_ids.add(row["id"])

    new_data = [row for row in data if row["id"] not in existing_ids]

    if not new_data:
        print("ℹ️ No new records to append.")
        return

    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.path.getsize(filepath) == 0:
            writer.writeheader()
        writer.writerows(new_data)

    print(f"💾 Appended {len(new_data)} new records to {filepath}")


async def safe_call(fn, *args, **kwargs):
    try:
        result = await fn(*args, **kwargs)
        if hasattr(result, "response") and result.response is not None:
            headers = result.response.headers
            limit = headers.get("x-rate-limit-limit")
            remaining = headers.get("x-rate-limit-remaining")
            reset = headers.get("x-rate-limit-reset")
            if limit and remaining and reset:
                reset_time = datetime.fromtimestamp(int(reset))
                print(
                    f"📊 Rate limit: {remaining}/{limit} remaining (resets {reset_time:%H:%M:%S})"
                )
        return result
    except TooManyRequests as e:
        reset_at = None
        if hasattr(e, "response") and e.response is not None:
            headers = e.response.headers
            reset_header = headers.get("x-rate-limit-reset")
            if reset_header:
                try:
                    reset_at = int(reset_header)
                except ValueError:
                    reset_at = None
        e.reset_at = reset_at
        raise


async def scrape_user_followers(clients, username, limit, progress, out_dir="data"):
    clients_cycle = cycle(clients)
    user = await safe_call(clients[0].get_user_by_screen_name, username)
    print(f"👤 Scraping followers of {username} (id={user.id})")

    total_scraped = progress.get(username, {}).get("count", 0)
    cursor = progress.get(username, {}).get("cursor")

    if cursor:
        print(f"↩️ Resuming from saved cursor, already scraped {total_scraped}")
    else:
        print("🚀 Starting fresh scrape")

    reset_times = {c: None for c in clients}

    while total_scraped < limit:
        client = next(clients_cycle)
        try:
            if cursor:
                result = await safe_call(
                    client.get_user_followers, user.id, count=200, cursor=cursor
                )
            else:
                result = await safe_call(user.get_followers, count=200)

            batch_records = []
            for follower in result:
                emails = extract_emails(follower)
                for email in emails:
                    batch_records.append(
                        {
                            "id": follower.id,
                            "username": follower.screen_name,
                            "name": follower.name,
                            "email": email,
                        }
                    )

            save_emails(batch_records, out_dir=out_dir)

            total_scraped += len(result)
            cursor = getattr(result, "next_cursor", None)
            progress[username] = {"count": total_scraped, "cursor": cursor}
            save_progress(progress)

            if not cursor:
                print("✅ No more pages.")
                break

            await asyncio.sleep(3 + int(7 * os.urandom(1)[0] / 255))

        except TooManyRequests as e:
            reset_times[client] = e.reset_at
            print(f"⏳ Rate limit hit on {client}. Switching accounts...")
            if all(rt is not None for rt in reset_times.values()):
                soonest_reset = min(rt for rt in reset_times.values() if rt)
                sleep_for = max(soonest_reset - int(time.time()), 1)
                resume_at = datetime.now() + timedelta(seconds=sleep_for)
                print(
                    f"😴 All accounts exhausted. Sleeping {sleep_for}s (until {resume_at:%H:%M:%S})"
                )
                await asyncio.sleep(sleep_for)
                reset_times = {c: None for c in clients}

        except NotFound:
            print("⚠️ API returned 404. Skipping this page.")
            cursor = (
                getattr(result, "next_cursor", None) if "result" in locals() else None
            )
            progress[username] = {"count": total_scraped, "cursor": cursor}
            save_progress(progress)
            continue

        except Exception as e:
            print(f"⚠️ Unexpected error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)
            continue

    print(f"🏁 Finished {username}. Scraped ~{total_scraped} followers.")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", "-t", required=True, help="Twitter username")
    parser.add_argument(
        "--limit", "-l", type=int, default=1000, help="Number of followers to fetch"
    )
    parser.add_argument("--out-dir", "-o", default="data", help="Output directory")
    args = parser.parse_args()

    clients = load_clients()
    progress = load_progress()

    await scrape_user_followers(
        clients, args.target, args.limit, progress, args.out_dir
    )


if __name__ == "__main__":
    asyncio.run(main())
