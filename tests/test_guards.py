"""Outbound send guards — validation, per-recipient cap, logging."""
import time

from friday.tools.guards import (
    normalize_email, can_send_to, record_send,
    MAX_SENDS_PER_RECIPIENT, WINDOW_SECONDS, _sends,
)


def test_normalize_valid():
    assert normalize_email("  User@Example.COM ") == "user@example.com"
    assert normalize_email("a@b.co") == "a@b.co"


def test_normalize_invalid():
    for bad in ["", None, "nope", "a@b", "@x.com", "a b@c.com", "a@b@c.com"]:
        assert normalize_email(bad) is None


def test_cap_allows_then_blocks():
    _sends.clear()
    addr = "victim@x.com"
    for _ in range(MAX_SENDS_PER_RECIPIENT):
        assert can_send_to(addr)
        record_send(addr, "test")
    assert not can_send_to(addr)


def test_cap_is_per_recipient():
    _sends.clear()
    record_send("a@x.com", "t")
    record_send("a@x.com", "t")
    record_send("a@x.com", "t")
    assert not can_send_to("a@x.com")
    assert can_send_to("b@x.com")


def test_cap_window_prunes_old_sends():
    _sends.clear()
    addr = "old@x.com"
    _sends[addr] = [time.time() - WINDOW_SECONDS - 10] * 5  # all expired
    assert can_send_to(addr)


def test_record_send_logs(caplog):
    _sends.clear()
    import logging
    with caplog.at_level(logging.INFO, logger="friday.tools.guards"):
        record_send("z@x.com", "resume")
    assert "to=z@x.com" in caplog.text
    assert "kind=resume" in caplog.text


# ── sanitize_text ─────────────────────────────────────────────────────────────
from friday.tools.guards import sanitize_text, retry_sync


def test_sanitize_strips_control_chars():
    assert sanitize_text("he\x00llo\x1f world", 100) == "hello world"
    assert sanitize_text("  padded  ", 100) == "padded"
    assert sanitize_text("", 10) == ""
    assert sanitize_text(None, 10) == ""


def test_sanitize_truncates():
    assert sanitize_text("x" * 500, 10) == "x" * 10
    assert sanitize_text("a\nb\nc", 100) == "a\nb\nc"   # newlines kept


# ── retry_sync ────────────────────────────────────────────────────────────────
def test_retry_succeeds_second_attempt():
    calls = []
    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionError("blip")
        return "ok"
    assert retry_sync(flaky, delay=0.01) == "ok"
    assert len(calls) == 2


def test_retry_raises_after_exhaustion():
    calls = []
    def always_fail():
        calls.append(1)
        raise RuntimeError("dead")
    import pytest
    with pytest.raises(RuntimeError):
        retry_sync(always_fail, delay=0.01)
    assert len(calls) == 2


def test_retry_no_delay_on_success():
    import time as t
    t0 = t.monotonic()
    retry_sync(lambda: "fast", delay=5.0)
    assert t.monotonic() - t0 < 0.1
