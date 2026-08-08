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

# Full census. The 2026-08-08 audit found the old 2,000 cap bound on every single
# run -- 16 of 16 -- so we were sampling 15% of a 13,029-listing site and calling
# the missing 85% "sold". These are set clear of the real end of results (~page
# 543 at 24 listings a page) so that the crawl stops because it ran out of cars,
# not because it ran out of budget. If a log line ever says "reached
# max_listings" again, the site grew and these need raising.
MAX_LISTINGS = int(os.getenv("SCRAPE_MAX_LISTINGS", "20000"))
# A run that harvests a fraction of the site is worse than no run: it manufactures
# absences that look like sales. Fail loudly below ~60% of known inventory.
MIN_EXPECTED = int(os.getenv("SCRAPE_MIN_EXPECTED", "8000"))
MAX_PAGES = 700
# Featured cards repeat on every page, so a page of pure repeats means we have
# walked off the end of the real results.
EMPTY_PAGE_LIMIT = 3


def collect(max_listings: int = MAX_LISTINGS, *, write: bool = True) -> tuple[dict[str, dict], int, int]:
    """Walk the index, flushing snapshots to Supabase as we go.

    Writes happen per batch inside the loop, not once at the end. A full census is
    ~45 minutes (543 pages x the 5s crawl-delay) and a killed run used to lose the
    whole day -- which already happened once (07-24, ^C, zero rows). Because
    `save_snapshots` is idempotent on (listing_id, scraped_at), a partial write plus
    a later re-run compose into a complete day with no reconciliation needed.
    """
    seen: dict[str, dict] = {}
    buffer: list[dict] = []
    failed = 0
    barren = 0
    written = 0

    def flush() -> None:
        nonlocal written, buffer
        if write and buffer:
            written += store.save_snapshots(buffer)
            print(f"  flushed {len(buffer)} rows, {written} written so far")
        buffer = []

    for page in range(1, MAX_PAGES + 1):
        url = fetch.index_url(page)
        try:
            html = fetch.get(url)
        except Exception as e:  # one bad page must not end the run
            print(f"page {page}: FAILED {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
            if failed >= 5:
                print("too many page failures, stopping", file=sys.stderr)
                break
            continue

        records = parse_index(html, url=url)
        fresh = [r for r in records if r["listing_id"] not in seen]
        for r in fresh:
            seen[r["listing_id"]] = r
        buffer.extend(fresh)

        print(f"page {page}: {len(records)} parsed, {len(fresh)} new, {len(seen)} total")

        if len(buffer) >= store.BATCH:
            flush()

        barren = barren + 1 if not fresh else 0
        if barren >= EMPTY_PAGE_LIMIT:
            print("no new listings for 3 pages, assuming end of results")
            break
        if len(seen) >= max_listings:
            print(f"reached max_listings={max_listings}")
            break

    flush()
    return seen, failed, written


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
    ap.add_argument("--skip-if-collected", action="store_true",
                    help="exit early when another host already took today's snapshot")
    args = ap.parse_args()

    if args.skip_if_collected and not args.dry_run and store.already_collected():
        # Second collector on a day the first one already covered. Exit 0 and
        # ping, because "nothing to do" is a healthy outcome, not a miss.
        print("today already collected by another host, skipping")
        ping_healthcheck()
        return 0

    seen, failed, written = collect(args.max, write=not args.dry_run)
    records = list(seen.values())
    priced = [r for r in records if r.get("price_myr")]
    print(f"\ncollected {len(records)} listings, {len(priced)} with a price, {failed} page failures")

    if args.dry_run:
        for r in records[:3]:
            print(" ", r)
        return 0

    # The rows are already in the database -- the walk wrote them as it went -- so
    # this can no longer gate the write. It labels the day instead. A thin day
    # recorded as thin is usable; a thin day thrown away leaves a hole that is
    # indistinguishable from a day nobody looked.
    thin = len(records) < MIN_EXPECTED
    store.log_run("motortrader", written, failed,
                  "under_threshold" if thin else "ok")
    print(f"wrote {written} snapshot rows")

    if thin:
        # Loud failure: a non-zero exit emails, and withholding the ping lets the
        # dead-man's switch go red. Silence is the alert.
        print(f"FAIL: only {len(records)} listings, expected >= {MIN_EXPECTED}", file=sys.stderr)
        return 1

    ping_healthcheck()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
