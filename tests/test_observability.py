"""CallRecorder: JSON record written, idempotent, crash-safe."""
import json
import os
import time
from types import SimpleNamespace

import friday.observability as obs


def _rec(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, "LOG_DIR", tmp_path)
    return obs.CallRecorder(room_name="test-room", user_id="v1")


def test_record_written(tmp_path, monkeypatch):
    r = _rec(tmp_path, monkeypatch)
    r._on_item(SimpleNamespace(item=SimpleNamespace(role="user", text_content="hi")))
    r._on_item(SimpleNamespace(item=SimpleNamespace(role="assistant", text_content="hello")))
    r._on_item(SimpleNamespace(item=SimpleNamespace(role="system", text_content="skip")))
    r._on_tools(SimpleNamespace(zipped=lambda: [
        (SimpleNamespace(name="navigate_ui", arguments={"section": "about"}),
         SimpleNamespace(output="ok", is_error=False)),
    ]))
    r._on_error(SimpleNamespace(error=Exception("boom")))
    r.finish()

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    d = json.loads(files[0].read_text())
    assert d["room"] == "test-room"
    assert [t["text"] for t in d["transcript"]] == ["hi", "hello"]   # system skipped
    assert d["tools"][0]["name"] == "navigate_ui"
    assert d["errors"][0]["error"].endswith("boom")
    assert d["duration_s"] >= 0
    assert "ended_at" in d
    assert isinstance(d["usage"], list)


def test_finish_idempotent(tmp_path, monkeypatch):
    r = _rec(tmp_path, monkeypatch)
    r.finish()
    r.finish()
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_garbage_events_never_raise(tmp_path, monkeypatch):
    r = _rec(tmp_path, monkeypatch)
    r._on_item(object())
    r._on_tools(object())
    r._on_metrics(object())
    r._on_error(object())
    r.finish()
    assert len(list(tmp_path.glob("*.json"))) == 1


# ── Error alerting ────────────────────────────────────────────────────────────
def test_alert_fired_on_errors(tmp_path, monkeypatch):
    fired = []
    monkeypatch.setattr(obs, "_fire_alert", lambda url, msg: fired.append((url, msg)))
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://hooks.slack.com/x")
    from friday.config import get_settings
    get_settings.cache_clear()

    r = _rec(tmp_path, monkeypatch)
    r._on_error(SimpleNamespace(error=Exception("boom")))
    r.finish()

    assert len(fired) == 1
    assert "test-room" in fired[0][1] and "errors=1" in fired[0][1]
    get_settings.cache_clear()


def test_alert_not_fired_on_clean_call(tmp_path, monkeypatch):
    fired = []
    monkeypatch.setattr(obs, "_fire_alert", lambda url, msg: fired.append((url, msg)))
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://hooks.slack.com/x")
    from friday.config import get_settings
    get_settings.cache_clear()

    r = _rec(tmp_path, monkeypatch)
    r.finish()

    assert fired == []
    get_settings.cache_clear()


def test_alert_disabled_without_url(tmp_path, monkeypatch):
    fired = []
    monkeypatch.setattr(obs, "_fire_alert", lambda url, msg: fired.append(msg))
    monkeypatch.delenv("ALERT_WEBHOOK_URL", raising=False)
    from friday.config import get_settings
    get_settings.cache_clear()

    r = _rec(tmp_path, monkeypatch)
    r._on_error(SimpleNamespace(error=Exception("boom")))
    r.finish()

    assert fired == []


def test_alert_failure_never_breaks_finish(tmp_path, monkeypatch):
    def boom(url, msg):
        raise RuntimeError("webhook down")
    monkeypatch.setattr(obs, "_fire_alert", boom)
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://hooks.slack.com/x")
    from friday.config import get_settings
    get_settings.cache_clear()

    r = _rec(tmp_path, monkeypatch)
    r._on_error(SimpleNamespace(error=Exception("x")))
    r.finish()                                   # must not raise

    assert len(list(tmp_path.glob("*.json"))) == 1
    get_settings.cache_clear()


# ── Log retention sweep ───────────────────────────────────────────────────────
def _make_record(path, age_days):
    f = path / f"call-{age_days}d.json"
    f.write_text("{}")
    old = time.time() - age_days * 86400
    os.utime(f, (old, old))
    return f


def test_sweep_deletes_old_keeps_fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, "LOG_DIR", tmp_path)
    old_f = _make_record(tmp_path, 40)
    new_f = _make_record(tmp_path, 2)

    obs._sweep_old_records(30)

    assert not old_f.exists()
    assert new_f.exists()


def test_sweep_disabled_at_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, "LOG_DIR", tmp_path)
    old_f = _make_record(tmp_path, 400)

    obs._sweep_old_records(0)

    assert old_f.exists()


def test_sweep_missing_dir_no_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, "LOG_DIR", tmp_path / "nonexistent")
    obs._sweep_old_records(30)          # must not raise
