"""Parse Motortrader car-index HTML into listing records.

The markup differs between featured and regular cards, so we slice the page at
each listing's data-urn and extract inside that window rather than depending on
a stable container class. Every field is optional: a missing one becomes None
rather than raising, because a site tweak must degrade the row, not kill the run.

Price trap worth knowing: each card carries BOTH an asking price ("RM 170,888")
and a loan installment ("RM 2,304 / month"). Confusing them is the classic
bait-price bug, so they are matched by separate, distinct patterns.
"""
from __future__ import annotations

import re

URN = re.compile(r'data-urn="(\d{9,})"')
PRICE = re.compile(r'featured-ads-section__price">\s*RM\s*([\d,]+)')
MONTHLY = re.compile(r'loancalc-css">\s*RM\s*([\d,]+)\s*/\s*month')
TITLE = re.compile(r'top-title[^>]*>\s*<a[^>]*>\s*([^<]+?)\s*</a>', re.S)
URL = re.compile(r'href="(https://www\.motortrader\.com\.my/usedcar/[^"]+?/\d{9,})')
DESC = re.compile(r'featured-ads-section__desc">\s*([^<]+?)\s*<')

CONDITIONS = {"USED", "NEW", "RECOND", "RECONDITIONED"}
TRANSMISSIONS = {"AUTO", "MANUAL", "AUTOMATIC"}


def _int(s: str | None) -> int | None:
    return int(s.replace(",", "")) if s else None


def _classify(descs: list[str]) -> dict:
    """Sort the loose <span> labels by shape, not by position.

    Position varies between card types; shape doesn't. A year is always 4
    digits, a mileage band always mentions k/km, and so on.
    """
    out: dict[str, str | int | None] = {
        "location_state": None, "condition": None,
        "year": None, "transmission": None, "mileage_band": None,
    }
    for d in descs:
        u = d.upper().strip()
        if not u:
            continue
        if u in CONDITIONS:
            out["condition"] = u
        elif u in TRANSMISSIONS:
            out["transmission"] = u
        elif re.fullmatch(r"(19|20)\d{2}", u):
            out["year"] = int(u)
        elif re.search(r"\d\s*K\s*[-–]|KM\b|\dK\b", u):
            out["mileage_band"] = d.strip()
        elif re.fullmatch(r"[A-Z .'/-]{3,}", u) and out["location_state"] is None:
            out["location_state"] = d.strip()
    return out


def parse_index(html: str) -> list[dict]:
    """Return one record per unique listing found on a car-index page.

    Featured cards repeat across pages, so the same listing_id can appear more
    than once here; the caller (and the DB unique constraint) dedupes.
    """
    marks = [m.start() for m in URN.finditer(html)]
    if not marks:
        return []
    marks.append(len(html))

    records: dict[str, dict] = {}
    for i, start in enumerate(marks[:-1]):
        chunk = html[start:marks[i + 1]]
        urn = URN.search(chunk)
        if not urn:
            continue
        listing_id = urn.group(1)

        price = _int(PRICE.search(chunk).group(1) if PRICE.search(chunk) else None)
        monthly = _int(MONTHLY.search(chunk).group(1) if MONTHLY.search(chunk) else None)
        title = TITLE.search(chunk)
        url = URL.search(chunk)

        rec = {
            "listing_id": listing_id,
            "source": "motortrader",
            "price_myr": price,
            "monthly_installment_myr": monthly,
            "title": title.group(1).strip() if title else None,
            "url": url.group(1) if url else None,
            **_classify(DESC.findall(chunk)),
        }

        # Cards are split across two data-urn hits (compare + bookmark widgets),
        # so merge rather than overwrite: keep whichever slice found more.
        prev = records.get(listing_id)
        if prev is None or _filled(rec) > _filled(prev):
            records[listing_id] = rec

    return list(records.values())


def _filled(rec: dict) -> int:
    return sum(1 for v in rec.values() if v is not None)
