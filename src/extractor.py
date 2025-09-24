import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.I)


def find_emails_in_text(text: str):
    if not text:
        return set()
    return set(m.group(0).lower() for m in EMAIL_RE.finditer(text))
