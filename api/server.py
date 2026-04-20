"""
Friday — Token API Server
FastAPI app that issues LiveKit tokens for the portfolio frontend.

The portfolio's Next.js app calls:
  POST /token   →  gets a LiveKit JWT  →  connects to Friday's room

This is what makes Friday "pluggable" into any frontend.
Run: uvicorn api.server:app --port 8080 --reload
"""
import logging
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants
import time

from friday.config import get_settings

logger   = logging.getLogger("friday.api")
settings = get_settings()

app = FastAPI(
    title="Friday Token Server",
    description="Issues LiveKit room tokens for Friday — Tanish's AI voice agent.",
    version="1.0.0",
)

# ── CORS — allow portfolio origin ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",          # Next.js dev
        "https://tanish.website",         # Live Portfolio
        "https://www.tanish.website",     # Live Portfolio (www)
        "https://tanishrajput.dev",       # Legacy domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────────
class TokenRequest(BaseModel):
    identity: str | None = None     # optional visitor identity
    room_name: str | None = None    # optional custom room name


class TokenResponse(BaseModel):
    token:      str
    room_name:  str
    livekit_url: str
    expires_at:  str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "agent": "friday", "version": "1.0.0"}


@app.post("/token", response_model=TokenResponse)
async def get_token(req: TokenRequest):
    try:
        # Generate unique identifiers
        room_name = req.room_name or f"friday-{secrets.token_hex(6)}"
        identity  = req.identity or f"visitor-{secrets.token_hex(4)}"

        # 1. Force TTL to be a clean integer
        # This prevents any weird types from your settings file causing math errors
        try:
            raw_duration = settings.max_call_duration_seconds
            ttl_seconds = int(raw_duration) + 30
        except Exception:
            ttl_seconds = 150 # Safe fallback (2.5 minutes)

        # 2. Create the token
        # Note: AccessToken internally handles the expiration using the TTL integer
        token = AccessToken(
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )

        token.with_identity(identity)
        token.with_name("Portfolio Visitor")

        token.with_grants(VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))

        # Explicitly set TTL as an integer
        token.with_ttl(timedelta(seconds=ttl_seconds))

        jwt = token.to_jwt()

        # 3. Calculate Expiration 
        exp_timestamp = time.time() + ttl_seconds
        expires_str = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc).isoformat()

        logger.info(f"Token issued: room={room_name} identity={identity}")

        return TokenResponse(
            token=jwt,
            room_name=room_name,
            livekit_url=settings.livekit_url,
            expires_at=expires_str,
        )

    except Exception as e:
        # This will print the full technical error to your terminal
        # so we can see the exact line of failure.
        import traceback
        logger.error(f"Critical Token Error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Check server console for traceback")


@app.get("/")
async def root():
    return {
        "agent": "Friday",
        "owner": "Tanish Rajput",
        "status": "running",
        "docs": "/docs",
    }
