"""
Test fixtures. Env vars MUST be set before any friday/* module imports —
pydantic Settings reads env at construction and get_settings() is lru_cached.
"""
import os

# ── Dummy env (must run before friday imports) ────────────────────────────────
for _k, _v in {
    "LIVEKIT_URL":          "wss://test.livekit.cloud",
    "LIVEKIT_API_KEY":      "testkey",
    "LIVEKIT_API_SECRET":   "testsecret0123456789abcdef0123456789abcdef",
    "DEEPGRAM_API_KEY":     "test-dg",
    "OPENAI_API_KEY":       "test-oai",
    "RESEND_API_KEY":       "test-resend",
    "SENDER_EMAIL":         "friday@test.com",
    "YOUR_EMAIL":           "tanish@test.com",
    "FRIDAY_API_KEY":       "test-secret-key",
    "TOKEN_RATE_LIMIT":     "100/hour",
    "GITHUB_USERNAME":      "tanishra",
}.items():
    os.environ.setdefault(_k, _v)

from friday.config import get_settings  # noqa: E402
get_settings.cache_clear()

import pytest  # noqa: E402


class FakeSession:
    """Minimal AgentSession stand-in — records speech + close calls."""

    def __init__(self):
        self.said = []          # list[(text, allow_interruptions)]
        self.closed = False
        self._handlers = {}

    async def say(self, text, allow_interruptions=True):
        self.said.append((text, allow_interruptions))

    async def aclose(self):
        self.closed = True

    def on(self, event, handler=None):
        if handler is None:
            def deco(fn):
                self._handlers[event] = fn
                return fn
            return deco
        self._handlers[event] = handler

    def emit(self, event, ev):
        if event in self._handlers:
            self._handlers[event](ev)


@pytest.fixture
def fake_session():
    return FakeSession()


@pytest.fixture
def friday_agent(fake_session, monkeypatch):
    """FridayAgent with the session property patched to the FakeSession."""
    from unittest.mock import MagicMock
    from friday.agent import FridayAgent

    # Agent.session is a read-only property fed by LiveKit's activity context —
    # patch it on the class so tools can call session.say() in tests.
    monkeypatch.setattr(FridayAgent, "session", property(lambda self: fake_session))
    return FridayAgent(user_id="test-visitor", room=MagicMock())


async def call_tool(tool, *args, **kwargs):
    """Invoke a @function_tool's underlying coroutine (bound via _instance)."""
    return await tool._func(tool._instance, *args, **kwargs)
