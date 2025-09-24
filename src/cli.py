import argparse
from . import config, crawler
from .storage import csv_exporter
from .logger import logger


def main():
    parser = argparse.ArgumentParser(description="Twitter Email Harvester")
    parser.add_argument(
        "--target", default=config.TARGET_SCREEN_NAME, help="Target screen name"
    )
    parser.add_argument(
        "--limit", type=int, default=config.MAX_FOLLOWERS, help="Max followers to scan"
    )
    args = parser.parse_args()

    results = crawler.harvest_emails(args.target, args.limit)
    filename = csv_exporter.export_to_csv(results, args.target)
    logger.info(f"Results saved to {filename}")


if __name__ == "__main__":
    main()
