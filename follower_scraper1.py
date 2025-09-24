import os
import json
import re
import asyncio
from itertools import cycle
from twikit import Client, TooManyRequests, NotFound

COOKIE_FILES = [
    "account1_twitter_cookies.json",
    "account2_twitter_cookies.json",
    "account3_twitter_cookies.json",
]
OUTPUT_FILE = "followers_emails2.csv"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def extract_username_from_cookie_file(cookie_file: str):
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r'"screen_name"\s*:\s*"([^"]+)"', txt)
        if m:
            return m.group(1)
        m = re.search(r'"username"\s*:\s*"([^"]+)"', txt)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def load_clients():
    clients = []
    for file in COOKIE_FILES:
        if not os.path.exists(file):
            print(f"⚠️ Missing cookie file: {file}, skipping...")
            continue

        client = Client(language="en-US")
        client.load_cookies(file)

        username = extract_username_from_cookie_file(file) or "unknown"
        clients.append({"client": client, "cookie_file": file, "label": username})
        print(f"🔑 Loaded client {username} from {file}")

    if not clients:
        raise RuntimeError("❌ No valid clients found.")
    print(f"✅ Loaded {len(clients)} client(s)")
    return clients


def extract_emails(user):
    """Extract emails from bio or URL fields."""
    sources = [user.description or "", user.url or ""]
    emails = []
    for text in sources:
        emails.extend(EMAIL_RE.findall(text))
    return emails


def save_emails(records):
    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        if not file_exists:
            f.write("id,username,name,email\n")
        for r in records:
            f.write(f"{r['id']},{r['username']},{r['name']},{r['email']}\n")
    print(f"💾 Appended {len(records)} records to {OUTPUT_FILE}")


async def scrape_user_followers(username, clients):
    clients_cycle = cycle(clients)

    first = clients[0]
    try:
        user = await first["client"].get_user_by_screen_name(username)
    except Exception as e:
        print(f"❌ Could not resolve @{username}: {e}")
        return

    print(f"👤 Scraping followers of {username} (id={user.id})")

    cursor = None
    total = 0

    while True:
        entry = next(clients_cycle)
        client = entry["client"]
        label = entry["label"]
        cookie_file = entry["cookie_file"]

        try:
            if cursor:
                result = await client.get_user_followers(
                    user.id, count=200, cursor=cursor
                )
            else:
                result = await user.get_followers(count=200)

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

            if batch_records:
                save_emails(batch_records)
            else:
                print(f"ℹ️ No emails in this batch from {label} ({cookie_file})")

            total += len(result)
            cursor = result.next_cursor
            if not cursor:
                print("✅ Finished all followers.")
                break

            await asyncio.sleep(3)

        except TooManyRequests:
            print(f"⏳ Rate limit hit on {label} ({cookie_file}). Switching...")
            await asyncio.sleep(5)
            continue

        except NotFound:
            print(f"⚠️ Page not found (404) while using {label}. Skipping this page.")
            cursor = None
            continue

        except Exception as e:
            msg = str(e).lower()
            if "locked" in msg:
                print(
                    f"🚨 Account LOCKED: {label} ({cookie_file}). Unlock it at https://x.com/account/access"
                )
            else:
                print(f"⚠️ Unexpected error with {label} ({cookie_file}): {e}")
            break

    print(f"🏁 Finished {username}. Scraped ~{total} followers.")


async def main():
    clients = load_clients()
    await scrape_user_followers("RevokeCash", clients)


if __name__ == "__main__":
    asyncio.run(main())
