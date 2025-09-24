import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .extractor import find_emails_in_text

HEADERS = {"User-Agent": "EmailHarvester/0.1 (+https://example.com)"}


def fetch_site_emails(url, timeout=8):
    emails = set()
    if not url:
        return emails
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "http://" + url

        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return emails

        emails.update(find_emails_in_text(resp.text))

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].startswith("mailto:"):
                addr = a["href"].split("mailto:")[1].split("?")[0]
                if addr:
                    emails.add(addr.lower())
    except Exception:
        pass
    return emails
