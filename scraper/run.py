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
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

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

# 2026-09-11..13 were lost with the scrape itself working: Supabase was unhealthy
# (Disk IO exhausted), every write 504'd, and the parsed rows died with the process.
# A listing that disappears can never be scraped for a past day, so a dead database
# must cost a delay, not the day. Failed batches land here, keyed by their day, and
# the next run replays them. data/ is gitignored.
SPOOL = Path(__file__).resolve().parent.parent / "data" / "spool"


def spool(rows: list[dict], day: date) -> None:
    SPOOL.mkdir(parents=True, exist_ok=True)
    with open(SPOOL / f"{day.isoformat()}.jsonl", "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def replay_spool() -> int:
    """Write spooled days back to Supabase. Returns rows still stuck on disk.

    Safe to repeat: save_snapshots is idempotent on (listing_id, scraped_at), so a
    file replayed twice, or overlapping a later partial write, cannot duplicate.
    """
    stuck = 0
    for path in sorted(SPOOL.glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        try:
            store.save_snapshots(rows, scraped_at=date.fromisoformat(path.stem))
        except Exception as e:
            print(f"spool {path.name}: still cannot write ({type(e).__name__}), kept", file=sys.stderr)
            stuck += len(rows)
            continue
        path.unlink()
        print(f"spool {path.name}: replayed {len(rows)} rows")
    return stuck


def collect(max_listings: int = MAX_LISTINGS, *, write: bool = True) -> tuple[dict[str, dict], int, int]:
    """Walk the index, flushing snapshots to Supabase as we go.

    Writes happen per batch inside the loop, not once at the end. A full census is
    ~45 minutes (543 pages x the 5s crawl-delay) and a killed run used to lose the
    whole day -- which already happened once (07-24, ^C, zero rows). Because
    `save_snapshots` is idempotent on (listing_id, scraped_at), a partial write plus
    a later re-run compose into a complete day with no reconciliation needed.

    A batch the database refuses is spooled to disk instead of ending the run.
    After the first refusal the rest of the walk spools without trying: each failed
    write already burns ~3 minutes of retries, times ~25 batches.
    """
    seen: dict[str, dict] = {}
    buffer: list[dict] = []
    failed = 0
    barren = 0
    written = 0
    db_down = False
    day = date.today()

    def flush() -> None:
        nonlocal written, buffer, db_down
        if write and buffer:
            if not db_down:
                try:
                    written += store.save_snapshots(buffer, scraped_at=day)
                    print(f"  flushed {len(buffer)} rows, {written} written so far")
                except Exception as e:
                    db_down = True
                    print(f"  DB write failed ({type(e).__name__}: {e}), spooling to disk", file=sys.stderr)
            if db_down:
                spool(buffer, day)
                print(f"  spooled {len(buffer)} rows")
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

    if not args.dry_run:
        replay_spool()  # an earlier day's rows go in before today's walk adds load

    if args.skip_if_collected and not args.dry_run:
        try:
            done = store.already_collected()
        except Exception as e:
            # Can't tell -- the database is the thing that's down. Walk anyway: an
            # unneeded census costs politeness, a skipped one can cost the day.
            print(f"cannot check today's count ({type(e).__name__}), collecting anyway", file=sys.stderr)
            done = False
        if done:
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

    # Last chance for this run: the database may have recovered during the walk.
    stuck = replay_spool()

    # The rows are already in the database -- the walk wrote them as it went -- so
    # this can no longer gate the write. It labels the day instead. A thin day
    # recorded as thin is usable; a thin day thrown away leaves a hole that is
    # indistinguishable from a day nobody looked.
    thin = len(records) < MIN_EXPECTED
    try:
        store.log_run("motortrader", written, failed,
                      "under_threshold" if thin else "ok")
    except Exception as e:
        print(f"log_run failed: {type(e).__name__}", file=sys.stderr)
    print(f"wrote {written} snapshot rows")

    if stuck:
        # Data is safe on disk but not in the database. Stay red until a replay lands.
        print(f"FAIL: {stuck} rows spooled in {SPOOL}, database unreachable", file=sys.stderr)
        return 1

    if thin:
        # Loud failure: a non-zero exit emails, and withholding the ping lets the
        # dead-man's switch go red. Silence is the alert.
        print(f"FAIL: only {len(records)} listings, expected >= {MIN_EXPECTED}", file=sys.stderr)
        return 1

    ping_healthcheck()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
