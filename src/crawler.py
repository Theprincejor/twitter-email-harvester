import time
import tweepy
from . import config, twitter_api, extractor, site_fetcher
from .logger import logger


def harvest_emails(screen_name, max_followers=100):
    api = twitter_api.create_api()
    results = []
    count = 0

    logger.info(f"Scanning up to {max_followers} followers of @{screen_name}")

    for user in tweepy.Cursor(
        api.get_followers, screen_name=screen_name, count=200
    ).items():
        if count >= max_followers:
            break
        count += 1

        username = getattr(user, "screen_name", "")
        description = getattr(user, "description", "")
        profile_url = getattr(user, "url", None)

        profile_emails = extractor.find_emails_in_text(description)
        site_emails = (
            site_fetcher.fetch_site_emails(profile_url)
            if config.CRAWL_LINKED_SITE
            else set()
        )

        results.append(
            {
                "screen_name": username,
                "profile_emails": sorted(profile_emails),
                "site_emails": sorted(site_emails),
                "profile_url": profile_url,
            }
        )

        if profile_emails or site_emails:
            logger.info(f"@{username}: {profile_emails | site_emails}")

        time.sleep(config.SLEEP_BETWEEN_CALLS)

    logger.info(f"Done. Scanned {count} followers.")
    return results
