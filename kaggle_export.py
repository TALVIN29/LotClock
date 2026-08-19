"""Build the Kaggle release: derived tables, never the raw scrape dump.

Two CSVs:

  lotclock_daily_coverage.csv  one row per collection day -- rows harvested,
                               era, and whether the day is complete enough to
                               count as an observation. Publishing this is the
                               point: absence only means something on a day we
                               actually looked properly.
  lotclock_listings.csv        one row per listing in the full-census era, with
                               duration + event columns ready for survival
                               analysis, honestly right-censored.

Coverage eras are NOT pooled. Everything before 2026-08-09 harvested ~15% of the
site (the crawl hit its page cap), so a listing "missing" then is a sampling
artefact, not a delisting. The survival table therefore uses census days only,
and a day is only an observation if it cleared COMPLETE_MIN rows -- several
census runs were killed mid-walk and would otherwise fake a mass disappearance.

    python kaggle_export.py          # write kaggle/ from Supabase
    python kaggle_export.py --test   # self-check on synthetic data, no network
"""
from __future__ import annotations

import csv
import json
import os
import sys
import urllib.request
from collections import defaultdict

from exit_rule import load_env
from price_moves import CENSUS_FROM, EXIT_N

OUT = "kaggle"
# A census day below this is a killed run, not a light day: full runs land
# ~12,400 rows. 8,153 (08-11) and 4,097 (08-15) are partial walks.
COMPLETE_MIN = 10_000


def fetch_rows() -> list[dict]:
    """Every snapshot row, read-only, paged."""
    from scraper.store import _cfg

    url, key = _cfg()
    out: list[dict] = []
    offset, PAGE = 0, 1000
    while True:
        req = urllib.request.Request(
            f"{url}/rest/v1/listing_snapshot?select=listing_id,scraped_at,price_myr,title,raw"
            f"&order=id.asc&limit={PAGE}&offset={offset}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"})
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read())
        out.extend(batch)
        if len(batch) < PAGE:
            return out
        offset += PAGE


def coverage(rows: list[dict]) -> list[dict]:
    per_day: dict[str, int] = defaultdict(int)
    for r in rows:
        per_day[r["scraped_at"]] += 1
    out = []
    for d in sorted(per_day):
        census = d >= CENSUS_FROM
        out.append({
            "date": d,
            "listings_seen": per_day[d],
            "coverage_era": "full_census" if census else "partial_15pct",
            "is_observation_day": int(census and per_day[d] >= COMPLETE_MIN),
        })
    return out


def make_model(title: str | None) -> tuple[str | None, str | None]:
    """Titles are 'YEAR MAKE MODEL ...'. Two tokens is all this earns.

    ponytail: naive split, so two-word makes ("LAND ROVER") land as make=LAND,
    model=ROVER. Documented in the data card rather than hard-coded into a
    marque list that goes stale.
    """
    parts = (title or "").split()
    if len(parts) < 2:
        return None, None
    return parts[1], parts[2] if len(parts) > 2 else None


def listings(rows: list[dict], days: list[str], n: int = EXIT_N) -> list[dict]:
    """One row per listing observed in the census era, survival-ready."""
    index = {d: i for i, d in enumerate(days)}
    last_i = len(days) - 1

    seen: dict[str, dict[int, float | None]] = defaultdict(dict)
    attrs: dict[str, dict] = {}
    pre_census: set[str] = set()
    for r in rows:
        lid = r["listing_id"]
        d = r["scraped_at"]
        if d < CENSUS_FROM:
            pre_census.add(lid)
            continue
        if d not in index:
            continue           # partial walk: not an observation
        p = r["price_myr"]
        seen[lid][index[d]] = float(p) if p is not None else None
        attrs[lid] = r         # last write wins; attributes are static per listing

    out = []
    for lid, by_i in seen.items():
        pos = sorted(by_i)
        prices = [by_i[i] for i in pos if by_i[i] is not None]
        raw = attrs[lid].get("raw") or {}
        make, model = make_model(attrs[lid].get("title"))
        exited = (last_i - pos[-1]) >= n
        out.append({
            "listing_id": lid,
            "make": make,
            "model": model,
            "year": raw.get("year"),
            "condition": raw.get("condition"),
            "transmission": raw.get("transmission"),
            "mileage_band": raw.get("mileage_band"),
            "location_state": raw.get("location_state"),
            "first_price_myr": prices[0] if prices else None,
            "last_price_myr": prices[-1] if prices else None,
            "price_cut_myr": round(prices[0] - prices[-1]) if len(prices) > 1 and prices[0] > prices[-1] else 0,
            "observed_days_seen": len(pos),
            # duration for survival analysis: observed days from first sighting
            # to last, inclusive. Observed, not calendar -- see the coverage CSV.
            "duration_obs_days": pos[-1] - pos[0] + 1,
            "event_exited": int(exited),
            "listed_before_census": int(lid in pre_census),
        })
    return out


def write(name: str, rows: list[dict]) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}: {len(rows):,} rows")


def main() -> int:
    load_env()
    rows = fetch_rows()
    cov = coverage(rows)
    days = [c["date"] for c in cov if c["is_observation_day"]]
    print(f"observation days ({len(days)}): {', '.join(days)}")
    dropped = [c["date"] for c in cov
               if c["coverage_era"] == "full_census" and not c["is_observation_day"]]
    print(f"census days dropped as partial walks: {', '.join(dropped) or 'none'}")
    write("lotclock_daily_coverage.csv", cov)
    ls = listings(rows, days)
    write("lotclock_listings.csv", ls)
    ev = sum(r["event_exited"] for r in ls)
    print(f"events (exited, N={EXIT_N} observed days absent): {ev:,} "
          f"({ev / len(ls) * 100:.1f}%); censored {100 - ev / len(ls) * 100:.1f}%")
    return 0


def _test() -> int:
    rows = [
        # partial era: ignored for survival, but marks the listing as pre-existing
        {"listing_id": "a", "scraped_at": "2026-08-01", "price_myr": 50000,
         "title": "2015 PERODUA MYVI 1.3", "raw": {"year": 2015}},
        {"listing_id": "a", "scraped_at": "2026-08-09", "price_myr": 50000,
         "title": "2015 PERODUA MYVI 1.3", "raw": {"year": 2015}},
        {"listing_id": "a", "scraped_at": "2026-08-10", "price_myr": 48000,
         "title": "2015 PERODUA MYVI 1.3", "raw": {"year": 2015}},
        # killed walk -- must not count as an observation day
        {"listing_id": "b", "scraped_at": "2026-08-11", "price_myr": 1000,
         "title": "2020 HONDA CITY", "raw": {}},
        {"listing_id": "b", "scraped_at": "2026-08-12", "price_myr": 1000,
         "title": "2020 HONDA CITY", "raw": {}},
    ]
    rows += [dict(rows[1], listing_id=f"pad{i}") for i in range(10_000)]   # 08-09 complete
    rows += [dict(rows[2], listing_id=f"pad{i}") for i in range(10_000)]   # 08-10 complete
    rows += [dict(rows[4], listing_id=f"pad{i}") for i in range(10_000)]   # 08-12 complete

    cov = {c["date"]: c for c in coverage(rows)}
    assert cov["2026-08-01"]["coverage_era"] == "partial_15pct", cov
    assert cov["2026-08-01"]["is_observation_day"] == 0, cov
    assert cov["2026-08-09"]["is_observation_day"] == 1, cov
    assert cov["2026-08-11"]["is_observation_day"] == 0, cov   # 1 row, killed walk

    days = [d for d, c in sorted(cov.items()) if c["is_observation_day"]]
    assert days == ["2026-08-09", "2026-08-10", "2026-08-12"], days

    by_id = {r["listing_id"]: r for r in listings(rows, days, n=1)}
    a = by_id["a"]
    assert a["listed_before_census"] == 1, a
    assert a["observed_days_seen"] == 2 and a["duration_obs_days"] == 2, a
    assert a["price_cut_myr"] == 2000, a
    assert a["event_exited"] == 1, a            # absent on the last observation day
    assert (a["make"], a["model"], a["year"]) == ("PERODUA", "MYVI", 2015), a
    b = by_id["b"]
    assert b["observed_days_seen"] == 1, b      # 08-11 dropped, only 08-12 counts
    assert b["event_exited"] == 0, b            # seen on the final day: censored
    assert b["listed_before_census"] == 0, b
    print("kaggle_export self-check ok")
    return 0


if __name__ == "__main__":
    sys.exit(_test() if "--test" in sys.argv else main())
