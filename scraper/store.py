"""Write snapshots to Supabase via its REST endpoint.

Deliberately no supabase-py dependency: this is two POSTs against PostgREST, and
a dependency that wraps `urllib` is not worth maintaining.

Append-only by design. We never UPDATE a price -- a price change is a new dated
row. That is the entire reason the project can measure anything over time.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date

BATCH = 500


def _cfg() -> tuple[str, str]:
    url = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return url, key


def _post(table: str, rows: list[dict], *, ignore_dupes: bool) -> None:
    url, key = _cfg()
    prefer = "return=minimal"
    if ignore_dupes:
        prefer += ",resolution=ignore-duplicates"

    req = urllib.request.Request(
        f"{url}/rest/v1/{table}",
        data=json.dumps(rows).encode(),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": prefer,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status >= 300:
            raise RuntimeError(f"supabase {table} returned {r.status}")


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
        _post("listing_snapshot", rows[i:i + BATCH], ignore_dupes=True)
    return len(rows)


def log_run(source: str, rows_ok: int, rows_failed: int, status: str) -> None:
    _post("scrape_run", [{
        "source": source,
        "rows_ok": rows_ok,
        "rows_failed": rows_failed,
        "status": status,
    }], ignore_dupes=False)
