"""Polite HTTP fetching.

motortrader.com.my/robots.txt sets `Crawl-delay: 5` for `User-agent: *` with an
empty Disallow, so crawling is permitted at that rate. We honour the 5s and
identify honestly with a contact URL, so they can see who we are and block us
deliberately if they ever want to.
"""
from __future__ import annotations

import os
import time
import urllib.error
import urllib.request

BASE = "https://www.motortrader.com.my"
USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "LotClock/0.1 (+https://github.com/TALVIN29/LotClock)",
)
DELAY = float(os.getenv("SCRAPE_DELAY_SECONDS", "5"))

_last_request = 0.0


def get(url: str, retries: int = 3) -> str:
    """Fetch a URL, never faster than DELAY since the previous request."""
    global _last_request

    for attempt in range(retries):
        wait = DELAY - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)

        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                _last_request = time.time()
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            _last_request = time.time()
            # 4xx that isn't rate-limiting means the page is genuinely gone --
            # retrying just adds load for no reason.
            if e.code in (404, 410):
                raise
            if e.code == 429 or e.code >= 500:
                time.sleep(DELAY * (attempt + 2))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            _last_request = time.time()
            if attempt == retries - 1:
                raise
            time.sleep(DELAY * (attempt + 2))

    raise RuntimeError(f"exhausted retries for {url}")


def index_url(page: int) -> str:
    return f"{BASE}/car/index?page={page}"
