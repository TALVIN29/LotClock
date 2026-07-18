"""Daily collection run.

Walks car-index pages, parses each, and appends one snapshot row per listing per
day. Exits non-zero when the harvest is suspiciously small, so GitHub Actions
emails on a silent breakage rather than logging a green run over an empty result.

Usage:
    python -m scraper.run              # full run, writes to Supabase
    python -m scraper.run --dry-run    # parse only, print a summary, no writes
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request

from scraper import fetch, store
from scraper.parse import parse_index

MAX_LISTINGS = int(os.getenv("SCRAPE_MAX_LISTINGS", "2000"))
MIN_EXPECTED = int(os.getenv("SCRAPE_MIN_EXPECTED", "200"))
MAX_PAGES = 400
# Featured cards repeat on every page, so a page of pure repeats means we have
# walked off the end of the real results.
EMPTY_PAGE_LIMIT = 3


def collect(max_listings: int = MAX_LISTINGS) -> tuple[dict[str, dict], int]:
    seen: dict[str, dict] = {}
    failed = 0
    barren = 0

    for page in range(1, MAX_PAGES + 1):
        try:
            html = fetch.get(fetch.index_url(page))
        except Exception as e:  # one bad page must not end the run
            print(f"page {page}: FAILED {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
            if failed >= 5:
                print("too many page failures, stopping", file=sys.stderr)
                break
            continue

        records = parse_index(html)
        fresh = [r for r in records if r["listing_id"] not in seen]
        for r in fresh:
            seen[r["listing_id"]] = r

        print(f"page {page}: {len(records)} parsed, {len(fresh)} new, {len(seen)} total")

        barren = barren + 1 if not fresh else 0
        if barren >= EMPTY_PAGE_LIMIT:
            print("no new listings for 3 pages, assuming end of results")
            break
        if len(seen) >= max_listings:
            print(f"reached max_listings={max_listings}")
            break

    return seen, failed


def ping_healthcheck() -> None:
    """Dead-man's switch: silence is the alert, so this must be the last thing."""
    url = os.getenv("HEALTHCHECK_URL")
    if not url:
        return
    try:
        urllib.request.urlopen(url, timeout=15).read()
    except Exception as e:
        print(f"healthcheck ping failed: {e}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="parse only, no writes")
    ap.add_argument("--max", type=int, default=MAX_LISTINGS)
    args = ap.parse_args()

    seen, failed = collect(args.max)
    records = list(seen.values())
    priced = [r for r in records if r.get("price_myr")]
    print(f"\ncollected {len(records)} listings, {len(priced)} with a price, {failed} page failures")

    if args.dry_run:
        for r in records[:3]:
            print(" ", r)
        return 0

    if len(records) < MIN_EXPECTED:
        # Loud failure: GitHub emails on a non-zero exit. A quiet run that
        # collected nothing is worse than a crash, because nobody notices.
        store.log_run("motortrader", len(records), failed, "under_threshold")
        print(f"FAIL: only {len(records)} listings, expected >= {MIN_EXPECTED}", file=sys.stderr)
        return 1

    written = store.save_snapshots(records)
    store.log_run("motortrader", written, failed, "ok")
    print(f"wrote {written} snapshot rows")

    ping_healthcheck()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
