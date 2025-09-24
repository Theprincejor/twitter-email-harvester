import asyncio
from twikit import Client


async def main(cookies_file):
    client = Client(language="en-US")
    client.load_cookies(cookies_file)  # no await here
    print(f"✅ Logged in with cookies from {cookies_file}")


if __name__ == "__main__":
    asyncio.run(main("account3_twitter_cookies.json"))
