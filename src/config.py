import os
from dotenv import load_dotenv

load_dotenv()

# Twitter API keys
CONSUMER_KEY = os.getenv("TW_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TW_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TW_ACCESS_TOKEN_SECRET")

# Target and options
TARGET_SCREEN_NAME = os.getenv("TARGET_SCREEN_NAME", "twitter")
MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", "100"))
CRAWL_LINKED_SITE = os.getenv("CRAWL_LINKED_SITE", "false").lower() == "true"
SLEEP_BETWEEN_CALLS = float(os.getenv("SLEEP_BETWEEN_CALLS", "1.0"))
