"""A transient network error on the Supabase write must not kill the run."""
import urllib.error
import urllib.request

from scraper import store


def test_post_retries_then_succeeds(monkeypatch):
    calls = []

    class FakeResponse:
        status = 201
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def flaky(req, timeout=None):
        calls.append(req)
        if len(calls) < 3:
            raise urllib.error.URLError("transient")
        return FakeResponse()

    monkeypatch.setenv("SUPABASE_URL", "https://example.test")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "k")
    monkeypatch.setattr(urllib.request, "urlopen", flaky)
    monkeypatch.setattr(store.time, "sleep", lambda s: None)

    store._post("listing_snapshot", [{"listing_id": "1"}])
    assert len(calls) == 3


def test_post_raises_after_three_failures(monkeypatch):
    def always_fail(req, timeout=None):
        raise urllib.error.URLError("down")

    monkeypatch.setenv("SUPABASE_URL", "https://example.test")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "k")
    monkeypatch.setattr(urllib.request, "urlopen", always_fail)
    monkeypatch.setattr(store.time, "sleep", lambda s: None)

    try:
        store._post("listing_snapshot", [{"listing_id": "1"}])
    except urllib.error.URLError:
        return
    raise AssertionError("expected URLError")
