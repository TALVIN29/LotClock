"""Write snapshots to Supabase via its REST endpoint.

Deliberately no supabase-py dependency: this is two POSTs against PostgREST, and
a dependency that wraps `urllib` is not worth maintaining.

Append-only by design. We never UPDATE a price -- a price change is a new dated
row. That is the entire reason the project can measure anything over time.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import date

BATCH = 500
# A day is only "collected" above this many rows. Same env var the run uses for its
# thin-day threshold, deliberately: one knob, and the two must never disagree about
# what a complete day is.
MIN_COMPLETE = int(os.getenv("SCRAPE_MIN_EXPECTED", "8000"))


def _cfg() -> tuple[str, str]:
    url = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return url, key


def _post(table: str, rows: list[dict], *, on_conflict: str | None = None) -> None:
    """POST rows to PostgREST.

    `on_conflict` must name the unique constraint's columns. PostgREST resolves
    conflicts against the PRIMARY KEY unless told otherwise, and ours is the
    surrogate `id`, so without this a re-run collides with the composite
    (listing_id, scraped_at) constraint and 409s instead of being ignored.
    """
    url, key = _cfg()
    endpoint = f"{url}/rest/v1/{table}"
    prefer = "return=minimal"
    if on_conflict:
        endpoint += f"?on_conflict={on_conflict}"
        prefer += ",resolution=ignore-duplicates"

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(rows).encode(),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": prefer,
        },
        method="POST",
    )
    # Retry: a single transient blip used to kill a 45-minute census mid-walk
    # (2026-08-11 and 08-12 both died here, WinError 10060). The write is
    # idempotent on (listing_id, scraped_at), so re-POSTing a batch is safe.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status >= 300:
                    raise RuntimeError(f"supabase {table} returned {r.status}")
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def day_row_count(scraped_at: date | None = None) -> int:
    """How many snapshot rows exist for a given day.

    Asks PostgREST for an exact count rather than fetching rows: `Prefer:
    count=exact` puts `start-end/total` in the Content-Range response header. This
    is the same technique the 2026-08-08 continuity audit used, and for the same
    reason -- the database is the only record of what was collected, the log is not.
    """
    url, key = _cfg()
    day = (scraped_at or date.today()).isoformat()
    req = urllib.request.Request(
        f"{url}/rest/v1/listing_snapshot"
        f"?scraped_at=eq.{day}&select=listing_id",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "count=exact",
            "Range-Unit": "items",
            "Range": "0-0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        total = r.headers.get("Content-Range", "").split("/")[-1]
    return int(total) if total.isdigit() else 0


def already_collected(scraped_at: date | None = None) -> bool:
    """Has today been collected *completely*?

    Two machines collect so that neither one being off creates a gap. This is what
    makes the second host exit early instead of walking the whole index again,
    doubling the request load on a source that grants access on the strength of
    behaving well. The writes are idempotent; the politeness is not.

    Testing that *any* row exists was correct only while a run wrote once, at the
    end -- all or nothing. Now that a run flushes per batch, a run killed halfway
    leaves thousands of rows behind, and an existence test would read that as done
    and skip the host that could have finished the day. So the test is a count
    against the same threshold the run itself uses to call a day thin.
    """
    return day_row_count(scraped_at) >= MIN_COMPLETE


def save_snapshots(records: list[dict], scraped_at: date | None = None) -> int:
    """Insert one row per listing per day. Re-runs on the same day are no-ops.

    The (listing_id, scraped_at) unique constraint plus ignore-duplicates makes
    this idempotent, so a retried or double-triggered job cannot corrupt the
    series.
    """
    if not records:
        return 0
    day = (scraped_at or date.today()).isoformat()

    rows = [{
        "listing_id": r["listing_id"],
        "scraped_at": day,
        "source": r["source"],
        "price_myr": r.get("price_myr"),
        "url": r.get("url"),
        "title": r.get("title"),
        "raw": r,
    } for r in records]

    for i in range(0, len(rows), BATCH):
        _post("listing_snapshot", rows[i:i + BATCH],
              on_conflict="listing_id,scraped_at")
    return len(rows)


def log_run(source: str, rows_ok: int, rows_failed: int, status: str) -> None:
    _post("scrape_run", [{
        "source": source,
        "rows_ok": rows_ok,
        "rows_failed": rows_failed,
        "status": status,
    }])
