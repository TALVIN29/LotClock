"""How much of what sits on the lot is what the country actually buys?

LotClock measures supply standing still: listings, and how long they stand.
It cannot see demand, so "500 Toyotas listed" has no denominator -- busy or
stuck reads the same. JPJ publishes the other half: every car registered in
Malaysia, monthly, CC BY 4.0.

    https://data.gov.my/data-catalogue/registration_transactions_car

Joining them gives a listings-per-registration ratio per make, which is the
first number here that says anything about a market rather than about a
website.

The first thing it says is uncomfortable and worth keeping: motortrader is not
the Malaysian car market. Perodua is the country's best-selling make by a wide
margin and barely appears on the lot; Mercedes-Benz is all over the lot and
registers a fraction as often. This is a Klang Valley premium/recond channel,
and the ratio is the evidence for saying so out loud.

TWO THINGS THIS DELIBERATELY DOES NOT DO
  - It does not join on state. 87.5% of JPJ rows carry state "Rakan Niaga", the
    trade-partner registration point, not where the car went. A state join would
    look fine and mean nothing.
  - It does not fuzzy-match models. Make-level matching covers most listings on
    exact strings; model strings do not line up ("ALPHARD" vs "Alphard 2.5") and
    a similarity threshold invented here would be a knob nobody can defend. The
    model-level match rate is measured and reported, not patched.

WINDOWS DO NOT ALIGN, AND ARE NOT MADE TO
JPJ publishes monthly and lags; LotClock's census era starts 2026-08-09. The
ratio is listings-on-the-lot-now against registrations-over-the-JPJ-window, so
it is a shape comparison across makes, not a rate per unit time. Both windows
are printed with the output so the mismatch cannot be forgotten.

    python jpj_join.py            # download (cached), join, print the table
    python jpj_join.py --csv      # also write jpj_vs_listings.csv
    python jpj_join.py --test     # self-check on synthetic data, no network
"""
from __future__ import annotations

import csv
import os
import sys
import urllib.request
from collections import Counter, defaultdict

YEAR = 2026
JPJ_URL = f"https://storage.data.gov.my/transportation/cars_{YEAR}.csv"
CACHE = f"data/jpj_cars_{YEAR}.csv"
LISTINGS = "kaggle/lotclock_listings.csv"
OUT_CSV = "jpj_vs_listings.csv"

# JPJ's own state field, for the 87.5% of rows that are dealer paperwork rather
# than a destination. Named here so the reason it is excluded stays visible.
TRADE_STATE = "Rakan Niaga"

# LotClock's make comes from the first token after the year in a listing title,
# so two-word makes arrive truncated. These are the truncations seen in the
# 2026-09-10 census, mapped to JPJ's spelling. Hyphen/space differences are
# handled by _norm and need no entry here.
ALIASES = {
    "LAND": "LAND ROVER",
    "ROVER": "LAND ROVER",
    "ASTON": "ASTON MARTIN",
    "ALFA": "ALFA ROMEO",
    "GREAT": "GREAT WALL",
}


def _norm(maker: str) -> str:
    """Upper-case, and treat hyphens as spaces.

    JPJ writes "MERCEDES BENZ" and "ROLLS ROYCE"; listing titles hyphenate both.
    That is a spelling difference, not a different manufacturer.
    """
    return maker.upper().replace("-", " ").strip()


def fetch_jpj(url: str = JPJ_URL, cache: str = CACHE) -> str:
    """Download the JPJ car registrations CSV once, then reuse it.

    ~32 MB and refreshed monthly, so re-downloading it per run would be rude to
    a public endpoint for data that cannot have changed.
    """
    if os.path.exists(cache):
        return cache
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    tmp = cache + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, cache)          # never leave a half file looking complete
    return cache


def jpj_counts(path: str) -> tuple[Counter, Counter, str, str]:
    """Registrations per make, per make+model, and the date range covered."""
    per_make: Counter = Counter()
    per_model: Counter = Counter()
    lo = hi = ""
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            mk = _norm(r["maker"])
            per_make[mk] += 1
            per_model[(mk, _norm(r["model"]))] += 1
            d = r["date_reg"]
            lo = d if not lo or d < lo else lo
            hi = d if not hi or d > hi else hi
    return per_make, per_model, lo, hi


def listing_counts(path: str = LISTINGS) -> tuple[Counter, Counter]:
    """Listings per make and per make+model, from the Kaggle export."""
    per_make: Counter = Counter()
    per_model: Counter = Counter()
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["make"]:
                continue
            mk = ALIASES.get(_norm(r["make"]), _norm(r["make"]))
            per_make[mk] += 1
            per_model[(mk, _norm(r["model"] or ""))] += 1
    return per_make, per_model


def join(lot: Counter, jpj: Counter) -> list[dict]:
    """One row per make, ordered by how over-represented the lot is.

    `listings_per_1k_reg` is listings on the lot per 1,000 registrations. High
    means the make sits on this website far out of proportion to how often the
    country actually buys it. Makes with no registrations at all are kept with a
    null ratio rather than dropped -- a make that sells zero and lists often is
    the finding, not an error.
    """
    rows = []
    for mk, n_lot in lot.items():
        n_reg = jpj.get(mk, 0)
        rows.append({
            "make": mk,
            "listings": n_lot,
            "registrations": n_reg,
            "listings_per_1k_reg": round(1000 * n_lot / n_reg, 1) if n_reg else None,
            "matched": int(mk in jpj),
        })
    rows.sort(key=lambda r: (r["listings_per_1k_reg"] is not None,
                             r["listings_per_1k_reg"] or 0, r["listings"]),
              reverse=True)
    return rows


def report(rows: list[dict], lot: Counter, jpj: Counter,
           lot_model: Counter, jpj_model: Counter, lo: str, hi: str) -> None:
    total = sum(lot.values())
    matched = sum(r["listings"] for r in rows if r["matched"])
    print(f"JPJ registrations {lo} .. {hi}   ({sum(jpj.values()):,} cars)")
    print(f"LotClock listings from {LISTINGS}   ({total:,} listings)")
    print("Windows differ -- this compares shape across makes, not a rate per day.\n")

    print(f"{'make':16} {'listings':>9} {'regs':>9} {'per 1k reg':>11}")
    for r in rows:
        if r["listings"] < 20:
            continue
        ratio = "-" if r["listings_per_1k_reg"] is None else f"{r['listings_per_1k_reg']:.1f}"
        print(f"{r['make']:16} {r['listings']:>9,} {r['registrations']:>9,} {ratio:>11}")

    print(f"\nmakes matched to JPJ: {sum(r['matched'] for r in rows)}/{len(rows)}"
          f" = {100*matched/total:.1f}% of listings")

    unmatched = [(r["make"], r["listings"]) for r in rows if not r["matched"]]
    if unmatched:
        print("unmatched makes (title-parse noise or genuinely never registered):")
        for mk, n in sorted(unmatched, key=lambda x: -x[1])[:10]:
            print(f"   {mk:18} {n:>5}")

    # Measured, not fixed: says how far a model-level join would actually get.
    m_hit = sum(n for k, n in lot_model.items() if k in jpj_model)
    print(f"\nmodel-level exact match would cover {100*m_hit/total:.1f}% of listings"
          f" -- reported, not patched (see module docstring)")


def _test() -> int:
    lot = Counter({"MERCEDES BENZ": 100, "PERODUA": 5, "GHOSTMAKE": 3})
    jpj = Counter({"MERCEDES BENZ": 1000, "PERODUA": 50000})
    rows = {r["make"]: r for r in join(lot, jpj)}

    assert rows["MERCEDES BENZ"]["listings_per_1k_reg"] == 100.0, rows["MERCEDES BENZ"]
    assert rows["PERODUA"]["listings_per_1k_reg"] == 0.1, rows["PERODUA"]
    # A make that never registers must survive with a null ratio, not vanish.
    assert rows["GHOSTMAKE"]["listings_per_1k_reg"] is None
    assert rows["GHOSTMAKE"]["matched"] == 0
    # Over-representation must sort above the mass-market make.
    order = [r["make"] for r in join(lot, jpj)]
    assert order.index("MERCEDES BENZ") < order.index("PERODUA"), order

    assert _norm("Mercedes-Benz") == "MERCEDES BENZ"
    assert ALIASES[_norm("Land")] == "LAND ROVER"
    print("jpj_join self-check ok")
    return 0


def main() -> int:
    path = fetch_jpj()
    jpj, jpj_model, lo, hi = jpj_counts(path)
    lot, lot_model = listing_counts()
    rows = join(lot, jpj)
    report(rows, lot, jpj, lot_model, jpj_model, lo, hi)

    if "--csv" in sys.argv:
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {OUT_CSV}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(_test() if "--test" in sys.argv else main())
