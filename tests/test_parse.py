"""Checks behind the parser's three load-bearing claims.

  1. it finds listings at all, on a real saved page
  2. it never confuses the asking price with the monthly loan installment
  3. a missing/changed field degrades the row instead of raising

Run: python -m pytest tests -q
"""
from pathlib import Path

from scraper.parse import parse_index

FIXTURE = Path(__file__).parent / "fixtures" / "car_index.html"
HTML = FIXTURE.read_text(encoding="utf-8", errors="replace")
URL = "https://www.motortrader.com.my/car/index?page=1"


def test_finds_listings():
    recs = parse_index(HTML)
    assert len(recs) >= 30, f"only {len(recs)} listings parsed"
    assert all(r["listing_id"].isdigit() for r in recs)
    assert len({r["listing_id"] for r in recs}) == len(recs), "duplicate ids returned"


def test_price_is_not_the_monthly_installment():
    # every card shows both "RM 170,888" and "RM 2,304 / month"; mixing them up
    # is the classic bait-price bug this project exists to avoid
    recs = [r for r in parse_index(HTML) if r["price_myr"] and r["monthly_installment_myr"]]
    assert recs, "fixture should contain cards with both figures"
    for r in recs:
        assert r["price_myr"] > r["monthly_installment_myr"] * 5, r
        assert r["price_myr"] >= 2000, r


def test_fields_extracted():
    recs = parse_index(HTML)
    got = lambda k: sum(1 for r in recs if r[k] is not None)
    assert got("title") >= len(recs) * 0.8
    assert got("price_myr") >= len(recs) * 0.8
    assert got("year") >= len(recs) * 0.8


def test_missing_fields_degrade_not_raise():
    # simulate a site redesign that drops the price markup entirely
    broken = HTML.replace("featured-ads-section__price", "some-new-class")
    recs = parse_index(broken)
    assert len(recs) >= 30, "listings must still be found"
    assert all(r["price_myr"] is None for r in recs)


def test_renamed_container_still_yields_a_sample():
    # a site redesign that renames the card container defeats the CSS selector;
    # adaptive relocation should still hand back *some* cards to re-derive the
    # new markup from. Partial by design -- see _cards() -- so this asserts a
    # floor, not full recovery.
    parse_index(HTML, url=URL)  # save the selector first
    renamed = HTML.replace(
        "superdeals-featured-cnabadv__featured-ads-section-listing", "listing-card-v2"
    )
    recs = parse_index(renamed, url=URL)
    assert 0 < len(recs) < 34, f"expected a partial harvest, got {len(recs)}"
    assert any(r["price_myr"] for r in recs), "recovered cards must still parse fields"


def test_empty_html_returns_nothing():
    assert parse_index("") == []
    assert parse_index("<html><body>nothing here</body></html>") == []
