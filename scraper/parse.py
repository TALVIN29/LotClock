"""Parse Motortrader car-index HTML into listing records.

Selector-based (Scrapling/lxml) rather than regex. One CSS query finds the card
containers; every field is then read *inside* its own card, so a listing can no
longer borrow a neighbour's price the way a flat regex slice could.

Every field is optional: a missing one becomes None rather than raising, because
a site tweak must degrade the row, not kill the run.

Price trap worth knowing: each card carries BOTH an asking price ("RM 170,888")
and a loan installment ("RM 2,304 / month"). Confusing them is the classic
bait-price bug, so they are read from separate, distinct elements.

The card selector -- the one that decides whether we get any data at all -- is
saved by Scrapling on every successful run and relearned by similarity if the
class name ever changes. Field selectors are deliberately NOT adaptive: a card
we can still find with a missing price is a degraded row we want to see, not a
gap to paper over with a guessed element.
"""
from __future__ import annotations

import re
from pathlib import Path

from scrapling import Selector

# ponytail: adaptive memory is a local SQLite file, so it only survives on the
# scheduled-task host. An ephemeral CI runner relearns nothing; commit the file
# or move it to Supabase if collection ever moves fully into Actions.
_STORAGE = {"storage_file": str(Path(__file__).resolve().parent.parent / ".scrapling_adaptive.db")}

CARD = "div.superdeals-featured-cnabadv__featured-ads-section-listing"

URN = "span[data-urn]::attr(data-urn)"
PRICE = ".featured-ads-section__price::text"
MONTHLY = ".loancalc-css::text"
TITLE = ".featured-ads-section__top-title a::text"
LINK = ".featured-ads-section__top-title a::attr(href)"
DESC = ".featured-ads-section__desc::text"

MONEY = re.compile(r"RM\s*([\d,]+)")
LISTING_URL = re.compile(r"^(https://www\.motortrader\.com\.my/usedcar/.+?/\d{9,})")

CONDITIONS = {"USED", "NEW", "RECOND", "RECONDITIONED"}
TRANSMISSIONS = {"AUTO", "MANUAL", "AUTOMATIC"}


def _first(card, selector: str) -> str | None:
    got = card.css(selector).getall()
    return got[0].strip() if got and got[0].strip() else None


def _money(card, selector: str) -> int | None:
    """Read the first RM figure out of an element, or None if it isn't there."""
    raw = _first(card, selector)
    if not raw:
        return None
    m = MONEY.search(raw)
    return int(m.group(1).replace(",", "")) if m else None


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


def _cards(page: Selector):
    """Find the listing cards, relearning the selector if the markup moved.

    The normal path saves the match, so there is something to compare against
    later. Only when the saved selector returns nothing do we ask Scrapling to
    find the element that most resembles what we stored last time.

    Measured on the saved fixture with the container class renamed: relocation
    recovers 12 of 34 listings, not all of them, because the page ships two card
    variants and only one shape is remembered. So this is a partial harvest that
    still trips SCRAPE_MIN_EXPECTED -- it buys a sample of the new markup to fix
    the selector from, not an uninterrupted run. Do not treat it as self-healing.
    """
    found = page.css(CARD, identifier="card", auto_save=True)
    if found:
        return found
    return page.css(CARD, identifier="card", adaptive=True)


def parse_index(html: str, url: str = "") -> list[dict]:
    """Return one record per unique listing found on a car-index page.

    Featured cards repeat across pages, so the same listing_id can appear more
    than once here; the caller (and the DB unique constraint) dedupes.
    """
    if not html or not html.strip():
        return []

    page = Selector(html, url=url, adaptive=True, storage_args=_STORAGE)

    records: dict[str, dict] = {}
    for card in _cards(page):
        listing_id = _first(card, URN)
        if not listing_id or not listing_id.isdigit():
            continue

        link = _first(card, LINK)
        if link:
            m = LISTING_URL.match(link)
            link = m.group(1) if m else None

        rec = {
            "listing_id": listing_id,
            "source": "motortrader",
            "price_myr": _money(card, PRICE),
            "monthly_installment_myr": _money(card, MONTHLY),
            "title": _first(card, TITLE),
            "url": link,
            **_classify(card.css(DESC).getall()),
        }

        # The same listing can appear twice on a page (featured + regular slot).
        # Keep whichever copy carries more fields.
        prev = records.get(listing_id)
        if prev is None or _filled(rec) > _filled(prev):
            records[listing_id] = rec

    return list(records.values())


def _filled(rec: dict) -> int:
    return sum(1 for v in rec.values() if v is not None)
