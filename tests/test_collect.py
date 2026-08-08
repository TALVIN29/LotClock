"""A killed run must keep the batches it already finished.

2026-07-24 was lost exactly this way: the run started, logged, was interrupted, and
wrote nothing. That was survivable at 8 minutes; a full census is ~45, so the walk
now flushes per batch. This pins that behaviour -- it is the only reason the census
is safe to leave unattended.
"""
from __future__ import annotations

import pytest

from scraper import run, store


def _records(page: int, n: int) -> list[dict]:
    return [{"listing_id": f"p{page}-{i}", "source": "motortrader",
             "price_myr": 50000, "url": "u", "title": "t"} for i in range(n)]


@pytest.fixture
def harness(monkeypatch):
    """Synthetic pages, no network, no database. Returns the list of written rows."""
    saved: list[dict] = []
    monkeypatch.setattr(run.fetch, "get", lambda url, **kw: "<html></html>")
    monkeypatch.setattr(store, "save_snapshots",
                        lambda rows, **kw: (saved.extend(rows), len(rows))[1])
    return saved


def test_interrupted_walk_keeps_finished_batches(harness, monkeypatch):
    # 200 listings a page; ^C on page 5, after batch one (500 rows) is full.
    def fake_parse(html, url=None):
        page = int(url.rsplit("=", 1)[1])
        if page >= 5:
            raise KeyboardInterrupt
        return _records(page, 200)

    monkeypatch.setattr(run, "parse_index", fake_parse)

    with pytest.raises(KeyboardInterrupt):
        run.collect(max_listings=10_000)

    # Pages 1-3 take the buffer to 600, past the 500 threshold, so it flushes;
    # page 4's 200 are still buffered and lost, which is the accepted cost.
    # Losing 200 beats losing the day. (`save_snapshots` chunks by BATCH itself,
    # so a 600-row flush is two POSTs, not an oversized one.)
    assert len(harness) == 600 > store.BATCH
    assert {r["listing_id"] for r in harness} >= {"p1-0", "p3-0"}


def test_dry_run_writes_nothing(harness, monkeypatch):
    monkeypatch.setattr(run, "parse_index",
                        lambda html, url=None: _records(int(url.rsplit("=", 1)[1]), 200))

    seen, failed, written = run.collect(max_listings=1_000, write=False)

    assert written == 0
    assert harness == []
    assert len(seen) >= 1_000


def test_complete_walk_writes_every_listing(harness, monkeypatch):
    def fake_parse(html, url=None):
        page = int(url.rsplit("=", 1)[1])
        return _records(page, 200) if page <= 6 else []

    monkeypatch.setattr(run, "parse_index", fake_parse)

    seen, failed, written = run.collect(max_listings=10_000)

    # Ends on the barren-page rule, and the tail flush must catch the remainder --
    # 1,200 is not a multiple of the 500 batch size, which is the point.
    assert written == 1_200 == len(seen)
    assert len(harness) == 1_200
