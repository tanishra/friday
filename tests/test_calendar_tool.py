"""Calendar tool: date parsing, Google path, email fallback (all mocked)."""
from types import SimpleNamespace

import friday.tools.calendar_tool as ct


async def test_fallback_email_when_no_service(monkeypatch):
    monkeypatch.setattr(ct, "_get_google_service", lambda: None)
    sent = []
    monkeypatch.setattr("friday.tools.email_tool._send_email", lambda p: sent.append(p))
    # _send_email is imported inside create_meeting — patch at module attr of email_tool
    import friday.tools.email_tool as et
    monkeypatch.setattr(et, "_send_email", lambda p: sent.append(p))
    out = await ct.create_meeting("Alice", "alice@x.com", "chat", "tomorrow", "11:00 AM", 30)
    assert out["success"] is True
    assert sent, "fallback email should have been sent"
    assert "alice@x.com" in sent[0]["html"]


async def test_bad_date_returns_failure(monkeypatch):
    monkeypatch.setattr(ct, "_get_google_service", lambda: None)
    out = await ct.create_meeting("A", "a@x.com", "t", "the 47th of blanuary", "noon", 30)
    assert out["success"] is False


async def test_google_path_creates_event(monkeypatch):
    inserted = []

    class FakeEvents:
        def insert(self, **kw):
            inserted.append(kw)
            return SimpleNamespace(execute=lambda: {"hangoutLink": "https://meet.link/x"})

    service = SimpleNamespace(events=lambda: FakeEvents())
    monkeypatch.setattr(ct, "_get_google_service", lambda: service)
    out = await ct.create_meeting("Bob", "bob@x.com", "sync", "tomorrow", "10:00 AM", 30)
    assert out["success"] is True
    assert "meet.link" in out["meet_link"]
    assert inserted[0]["sendUpdates"] == "all"
