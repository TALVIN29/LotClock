"""A dead database must delay a day, not lose it.

2026-09-11..13 were lost this way: pages scraped fine, every Supabase write 504'd,
and the parsed rows died with the process.
"""
from __future__ import annotations

from datetime import date

from scraper import run, store


def _records(page: int, n: int) -> list[dict]:
    return [{"listing_id": f"p{page}-{i}", "source": "motortrader",
             "price_myr": 50000, "url": "u", "title": "t"} for i in range(n)]


def test_db_outage_spools_then_replays(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "SPOOL", tmp_path)
    monkeypatch.setattr(run.fetch, "get", lambda url, **kw: "<html></html>")
    monkeypatch.setattr(run, "parse_index",
                        lambda html, url=None: _records(int(url.rsplit("=", 1)[1]), 200)
                        if int(url.rsplit("=", 1)[1]) <= 6 else [])

    calls = []

    def down(rows, **kw):
        calls.append(len(rows))
        raise TimeoutError("504")

    monkeypatch.setattr(store, "save_snapshots", down)
    seen, failed, written = run.collect(max_listings=10_000)

    # Nothing written, nothing lost, and only one write attempted (circuit opens).
    assert written == 0 and len(calls) == 1
    files = list(tmp_path.glob("*.jsonl"))
    assert [f.stem for f in files] == [date.today().isoformat()]
    assert sum(1 for _ in files[0].open()) == 1_200 == len(seen)

    # Still down: replay keeps the file and reports it stuck.
    assert run.replay_spool() == 1_200 and files[0].exists()

    # Database back: replay writes under the spooled day and clears the file.
    saved = {}
    monkeypatch.setattr(store, "save_snapshots",
                        lambda rows, scraped_at=None: saved.update(day=scraped_at, n=len(rows)) or len(rows))
    assert run.replay_spool() == 0
    assert saved == {"day": date.today(), "n": 1_200}
    assert not files[0].exists()
