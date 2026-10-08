"""Token endpoint: auth matrix, rate limit, open routes."""
import importlib

from fastapi.testclient import TestClient

KEY = "test-secret-key"


def _client():
    import api.server as server
    return TestClient(server.app)


def test_health_open():
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_token_no_key_403():
    r = _client().post("/token", json={})
    assert r.status_code == 403


def test_token_wrong_key_403():
    r = _client().post("/token", json={}, headers={"X-Friday-Key": "wrong"})
    assert r.status_code == 403


def test_token_valid_key_200():
    r = _client().post("/token", json={}, headers={"X-Friday-Key": KEY})
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["room_name"].startswith("friday-")
    assert body["livekit_url"].startswith("wss://")
    assert body["expires_at"]


def test_token_ignores_client_room_name():
    r = _client().post(
        "/token",
        json={"room_name": "shared-room", "identity": "bob"},
        headers={"X-Friday-Key": KEY},
    )
    assert r.status_code == 200
    name = r.json()["room_name"]
    assert name != "shared-room"
    assert name.startswith("friday-")


def test_token_rooms_unique_per_call():
    client = _client()
    names = {
        client.post("/token", json={}, headers={"X-Friday-Key": KEY}).json()["room_name"]
        for _ in range(3)
    }
    assert len(names) == 3


def test_token_rate_limit(monkeypatch):
    """Reload the app with a tiny limit, expect 429 past it."""
    from friday.config import get_settings
    import os
    monkeypatch.setenv("TOKEN_RATE_LIMIT", "2/minute")
    get_settings.cache_clear()
    import api.server as server
    importlib.reload(server)
    try:
        client = TestClient(server.app)
        codes = [
            client.post("/token", json={}, headers={"X-Friday-Key": KEY}).status_code
            for _ in range(3)
        ]
        assert codes[:2] == [200, 200]
        assert codes[2] == 429
    finally:
        monkeypatch.setenv("TOKEN_RATE_LIMIT", "100/hour")
        get_settings.cache_clear()
        importlib.reload(server)
