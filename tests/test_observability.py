"""CallRecorder: JSON record written, idempotent, crash-safe."""
import json
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
