import asyncio
from twikit import Client


async def main(cookies_file):
    client = Client(language="en-US")
    await client.load_cookies(cookies_file)
    print(f"✅ Logged in with cookies from {cookies_file}")
    return client


if __name__ == "__main__":
    asyncio.run(main("account2_twitter_cookies.json"))
