"""How many observed days of absence before a listing is really gone?

A listing vanishing from one day's harvest does NOT mean it sold: the 2026-08-08
coverage audit found 94% of single-day disappearances came back. The crawl walks
~92 pages over ~8 minutes and the site reorders underneath it, so listings fall
between page boundaries and return the next day.

This fits the threshold from the data instead of guessing it: measure how long
absences actually last, and pick the smallest N where "absent N observed days in
a row" almost never reverses.

Gaps are counted in OBSERVED days, not calendar days -- collection has holes
(07-24, 08-01..03, 08-06), and a listing cannot be seen on a day nobody looked.

    python exit_rule.py          # fit against Supabase
    python exit_rule.py --test   # self-check on synthetic data, no network
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import defaultdict


def load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def fetch_presence() -> dict[str, set[str]]:
    """{listing_id: {date, ...}} for every snapshot row. Read-only."""
    from scraper.store import _cfg

    url, key = _cfg()
    seen: dict[str, set[str]] = defaultdict(set)
    offset, PAGE = 0, 1000
    while True:
        req = urllib.request.Request(
            f"{url}/rest/v1/listing_snapshot?select=listing_id,scraped_at"
            f"&order=id.asc&limit={PAGE}&offset={offset}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read())
        for r in batch:
            seen[r["listing_id"]].add(r["scraped_at"])
        if len(batch) < PAGE:
            return seen
        offset += PAGE


def gap_lengths(presence: dict[str, set[str]], days: list[str]) -> dict[int, int]:
    """Histogram of interior absence runs, in observed days.

    Only absences that END (the listing came back) are counted. A trailing
    absence is right-censoring, not a gap, and folding it in here would be the
    same mistake as calling a one-day absence a sale.
    """
    index = {d: i for i, d in enumerate(days)}
    hist: dict[int, int] = defaultdict(int)
    for dates in presence.values():
        idx = sorted(index[d] for d in dates if d in index)
        for a, b in zip(idx, idx[1:]):
            if b - a > 1:
                hist[b - a - 1] += 1
    return dict(hist)


def survival_of_absence(hist: dict[int, int], trailing: dict[int, int]) -> list[tuple[int, int, int, float]]:
    """For each N: how many absences reached N days, and how many still returned.

    `trailing` counts listings whose absence ran to the end of the data -- they
    reached N but had no chance to return, so they belong in the denominator's
    exposure but never in the returned count.
    """
    if not hist and not trailing:
        return []
    top = max(list(hist) + list(trailing))
    rows = []
    for n in range(1, top + 1):
        returned = sum(c for g, c in hist.items() if g >= n)
        censored = sum(c for g, c in trailing.items() if g >= n)
        reached = returned + censored
        if reached == 0:
            continue
        rows.append((n, reached, returned, returned / reached))
    return rows


def trailing_absences(presence: dict[str, set[str]], days: list[str]) -> dict[int, int]:
    index = {d: i for i, d in enumerate(days)}
    last = len(days) - 1
    hist: dict[int, int] = defaultdict(int)
    for dates in presence.values():
        idx = sorted(index[d] for d in dates if d in index)
        if idx and idx[-1] < last:
            hist[last - idx[-1]] += 1
    return dict(hist)


def choose_n(rows, threshold: float = 0.05) -> int | None:
    """Smallest N where fewer than `threshold` of absences that long ever reverse."""
    for n, _reached, _returned, rate in rows:
        if rate < threshold:
            return n
    return None


def main() -> int:
    load_env()
    presence = fetch_presence()
    days = sorted({d for ds in presence.values() for d in ds})
    print(f"{len(presence)} listings across {len(days)} observed days\n")

    hist = gap_lengths(presence, days)
    trailing = trailing_absences(presence, days)
    print("closed absence gaps (listing came back), by length in observed days:")
    for g in sorted(hist):
        print(f"  {g:2d} day(s): {hist[g]:5d}")

    rows = survival_of_absence(hist, trailing)
    print("\nN = consecutive observed days absent")
    print(" N   reached   came back   return rate")
    for n, reached, returned, rate in rows:
        print(f"{n:2d}   {reached:7d}   {returned:9d}   {rate:9.1%}")

    n = choose_n(rows)
    if n is None:
        print("\nNo N yet clears the 5% bar -- the series is too short. Collect more days.")
    else:
        exits = sum(c for g, c in trailing.items() if g >= n)
        print(f"\nN = {n}: absent {n} observed days in a row reverses <5% of the time.")
        print(f"Under that rule, {exits} listings count as exited (vs 295 by naive last-seen).")
    return 0


def _test() -> int:
    days = ["d1", "d2", "d3", "d4", "d5"]
    presence = {
        "flicker": {"d1", "d2", "d4", "d5"},          # 1-day gap, returned
        "long":    {"d1", "d5"},                       # 3-day gap, returned
        "gone":    {"d1", "d2"},                       # trailing absence of 3
        "always":  set(days),
    }
    assert gap_lengths(presence, days) == {1: 1, 3: 1}, gap_lengths(presence, days)
    assert trailing_absences(presence, days) == {3: 1}
    rows = survival_of_absence({1: 1, 3: 1}, {3: 1})
    # N=1: all three absences reach it, two came back -> 2/3
    assert rows[0] == (1, 3, 2, 2 / 3), rows[0]
    # N=3: two reach it (the long gap and the trailing one), one came back
    assert rows[2] == (3, 2, 1, 0.5), rows[2]
    assert choose_n([(1, 10, 9, 0.9), (2, 10, 4, 0.4), (3, 10, 0, 0.0)]) == 3
    assert choose_n([(1, 10, 9, 0.9)]) is None
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(_test() if "--test" in sys.argv else main())
