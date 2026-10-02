"""Config: env loading + fail-fast validation."""
import pytest


def test_settings_loads_from_env():
    from friday.config import get_settings
    s = get_settings()
    assert s.friday_api_key == "test-secret-key"
    assert s.livekit_url.startswith("wss://")
    assert s.max_call_duration_seconds == 120
    assert s.token_rate_limit == "100/hour"


def test_missing_required_field_fails(monkeypatch):
    from friday.config import Settings
    monkeypatch.delenv("LIVEKIT_API_SECRET", raising=False)
    with pytest.raises(Exception):
        Settings(_env_file=None)


def test_extra_env_keys_ignored(monkeypatch):
    from friday.config import Settings
    monkeypatch.setenv("SOME_UNRELATED_KEY", "x")
    Settings()  # should not raise (extra="ignore")
