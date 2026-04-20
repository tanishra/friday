"""
Friday — Configuration
Loads all settings from .env via Pydantic BaseSettings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # ignore keys not declared here
    )

    # ── LiveKit ───────────────────────────────────────────────────────────────
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    # ── STT / LLM / TTS ──────────────────────────────────────────────────────
    deepgram_api_key: str
    openai_api_key: str
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # ── Email ─────────────────────────────────────────────────────────────────
    resend_api_key: str
    sender_email: str
    your_email: str               
    gmail_user: str = ""
    gmail_app_password: str = ""

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = ""         
    github_username: str = "tanishra"

    # ── Agent config ──────────────────────────────────────────────────────────
    agent_name: str = "Friday"
    owner_name: str = "Tanish"
    max_call_duration_seconds: int = 120   # 2 min limit on portfolio
    session_ttl_seconds: int = 3600

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    api_port: int = 8080           # Token server port


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
