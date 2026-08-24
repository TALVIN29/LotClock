"""What do Malaysian used-car listings do to their price before they disappear?

Three numbers nobody publishes for this market:

  1. how many listings ever move their price, and by how much
  2. how long a listing sits before its first cut
  3. days-on-market for listings that actually exited, censored honestly

Coverage regimes are NOT pooled. Every day up to 2026-08-08 is a ~15% partial
harvest (~2,010 rows); 2026-08-09 is the first full census (12,392 rows). A
listing "appearing" on the census day is a coverage change, not new inventory,
and an absence measured across that boundary is meaningless. The default window
therefore stops before the census -- see CENSUS_FROM.

Exit rule N comes from exit_rule.py, fitted on the same partial-harvest era.
N = 5 is the defensible threshold (11.7% of 5-day absences still reversed);
N = 6 reads 0% but is window-limited.

    python price_moves.py           # partial-harvest era (default window)
    python price_moves.py --census  # census era only, killed walks dropped
    python price_moves.py --test    # self-check on synthetic data, no network
"""
from __future__ import annotations

import json
import statistics
import sys
import urllib.request
from collections import defaultdict

from exit_rule import load_env

CENSUS_FROM = "2026-08-09"   # first full-census day; window is everything before it
EXIT_N = 5                   # observed days absent before a listing counts as gone
COMPLETE_MIN = 10_000        # rows a census day must clear to count as observed


def fetch_prices() -> dict[str, dict[str, float | None]]:
    """{listing_id: {date: price_myr}} for every snapshot row. Read-only."""
    from scraper.store import _cfg

    url, key = _cfg()
    seen: dict[str, dict[str, float | None]] = defaultdict(dict)
    offset, PAGE = 0, 1000
    while True:
        req = urllib.request.Request(
            f"{url}/rest/v1/listing_snapshot?select=listing_id,scraped_at,price_myr"
            f"&order=id.asc&limit={PAGE}&offset={offset}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read())
        for r in batch:
            p = r["price_myr"]
            seen[r["listing_id"]][r["scraped_at"]] = float(p) if p is not None else None
        if len(batch) < PAGE:
            return dict(seen)
        offset += PAGE


def moves(prices: dict[str, dict[str, float | None]], days: list[str]) -> dict:
    """Price-change statistics over the observed days given, in order."""
    idx = {d: i for i, d in enumerate(days)}
    multi = cuts = rises = 0
    first_cut_pct: list[float] = []
    first_cut_myr: list[float] = []
    days_to_first_cut: list[int] = []
    depth_pct: list[float] = []

    for lid, by_day in prices.items():
        seq = [(idx[d], by_day[d]) for d in sorted(by_day) if d in idx and by_day[d]]
        if len(seq) < 2:
            continue
        multi += 1
        first_i, first_p = seq[0]
        cut_seen = False
        moved_down = False
        for (pi, pp), (ci, cp) in zip(seq, seq[1:]):
            if cp == pp:
                continue
            if cp < pp:
                moved_down = True
                if not cut_seen:
                    cut_seen = True
                    first_cut_myr.append(pp - cp)
                    first_cut_pct.append((pp - cp) / pp * 100)
                    days_to_first_cut.append(ci - first_i)
            else:
                rises += 1
        if moved_down:
            cuts += 1
            depth_pct.append((first_p - seq[-1][1]) / first_p * 100)

    return {
        "listings_multi_day": multi,
        "listings_cut": cuts,
        "cut_rate_pct": round(cuts / multi * 100, 2) if multi else 0.0,
        "raises": rises,
        "median_first_cut_pct": round(statistics.median(first_cut_pct), 2) if first_cut_pct else None,
        "median_first_cut_myr": round(statistics.median(first_cut_myr)) if first_cut_myr else None,
        "median_obs_days_to_first_cut": statistics.median(days_to_first_cut) if days_to_first_cut else None,
        "median_total_discount_pct": round(statistics.median(depth_pct), 2) if depth_pct else None,
    }


def dom(prices: dict[str, dict[str, float | None]], days: list[str], n: int = EXIT_N) -> dict:
    """Days-on-market, in OBSERVED days, split into exited and still-censored.

    A listing counts as exited only if its trailing absence reaches n observed
    days. Anything shorter is right-censored: it may yet come back, and the
    window ends before we can know.
    """
    idx = {d: i for i, d in enumerate(days)}
    last = len(days) - 1
    exited: list[int] = []
    censored: list[int] = []
    for by_day in prices.values():
        pos = sorted(idx[d] for d in by_day if d in idx)
        if not pos:
            continue
        span = pos[-1] - pos[0] + 1
        (exited if last - pos[-1] >= n else censored).append(span)
    return {
        "exited": len(exited),
        "censored": len(censored),
        "censored_pct": round(len(censored) / (len(exited) + len(censored)) * 100, 1)
        if exited or censored else 0.0,
        "median_dom_obs_days_exited": statistics.median(exited) if exited else None,
    }


def observed_days(prices: dict[str, dict[str, float | None]], census: bool) -> list[str]:
    """Days to model on. Census era drops killed walks: a partial day's absences
    are a coverage artefact and would read as exits."""
    per_day: dict[str, int] = defaultdict(int)
    for by_day in prices.values():
        for d in by_day:
            per_day[d] += 1
    if not census:
        return sorted(d for d in per_day if d < CENSUS_FROM)
    return sorted(d for d, n in per_day.items() if d >= CENSUS_FROM and n >= COMPLETE_MIN)


def main() -> int:
    load_env()
    census = "--census" in sys.argv
    prices = fetch_prices()
    days = observed_days(prices, census)
    regime = (f"census era only, days under {COMPLETE_MIN:,} rows dropped as killed walks"
              if census else
              f"partial-harvest regime only; {CENSUS_FROM} census excluded")
    print(f"window: {days[0]} .. {days[-1]}  ({len(days)} observed days, {regime})")
    print(f"listings seen in window: {sum(1 for b in prices.values() if any(d in days for d in b)):,}")
    for k, v in moves(prices, days).items():
        print(f"  {k}: {v}")
    print(f"exit rule N = {EXIT_N} observed days")
    for k, v in dom(prices, days, EXIT_N).items():
        print(f"  {k}: {v}")
    return 0


def _test() -> int:
    days = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8"]
    prices = {
        "steady":  {d: 50000.0 for d in days},
        "cut":     {"d1": 100000.0, "d2": 100000.0, "d3": 90000.0, "d4": 80000.0},
        "raise":   {"d1": 10000.0, "d2": 11000.0},
        "oneday":  {"d1": 70000.0},
        "noprice": {"d1": None, "d2": None},
    }
    m = moves(prices, days)
    assert m["listings_multi_day"] == 3, m          # steady, cut, raise
    assert m["listings_cut"] == 1, m
    assert m["raises"] == 1, m
    assert m["median_first_cut_pct"] == 10.0, m     # 100k -> 90k
    assert m["median_first_cut_myr"] == 10000, m
    assert m["median_obs_days_to_first_cut"] == 2, m
    assert m["median_total_discount_pct"] == 20.0, m  # 100k -> 80k

    d = dom(prices, days, n=3)
    # last observed day index is 7; cut/raise/oneday/noprice all trail >= 3 days
    assert d["exited"] == 4, d
    assert d["censored"] == 1, d                    # steady runs to the end
    assert d["median_dom_obs_days_exited"] == 2, d  # spans 4,2,1,2 -> median 2
    global COMPLETE_MIN
    era = {
        "a": {"2026-07-20": 1.0},   # partial era
        "b": {"2026-08-09": 1.0},   # census day, 2 rows below
        "c": {"2026-08-09": 1.0, "2026-08-11": 1.0},   # 08-11 has 1 row: killed walk
    }
    COMPLETE_MIN = 1
    assert observed_days(era, census=False) == ["2026-07-20"]
    assert observed_days(era, census=True) == ["2026-08-09", "2026-08-11"]
    COMPLETE_MIN = 2
    assert observed_days(era, census=True) == ["2026-08-09"], "thin day must drop"
    COMPLETE_MIN = 10_000

    print("price_moves self-check ok")
    return 0


if __name__ == "__main__":
    sys.exit(_test() if "--test" in sys.argv else main())
