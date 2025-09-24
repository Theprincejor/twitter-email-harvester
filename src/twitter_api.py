import tweepy
from . import config


def create_api():
    if not all(
        [
            config.CONSUMER_KEY,
            config.CONSUMER_SECRET,
            config.ACCESS_TOKEN,
            config.ACCESS_TOKEN_SECRET,
        ]
    ):
        raise RuntimeError("Twitter API keys are missing. Check .env")

    auth = tweepy.OAuth1UserHandler(
        config.CONSUMER_KEY,
        config.CONSUMER_SECRET,
        config.ACCESS_TOKEN,
        config.ACCESS_TOKEN_SECRET,
    )
    return tweepy.API(auth, wait_on_rate_limit=True)
