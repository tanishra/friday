# AGENTS.md — Friday

Real-time voice AI agent for Tanish's portfolio. Cascaded pipeline: Deepgram nova-3 STT → GPT-4o-mini → Deepgram aura-2 TTS over LiveKit Cloud (WebRTC).

## Layout

- `main.py` — entrypoint; starts FastAPI token server (thread) + LiveKit worker
- `friday/agent.py` — `FridayAgent`, AgentSession wiring, tools, call timers
- `friday/config.py` — pydantic-settings env config (fail-fast)
- `friday/observability.py` — per-call JSON flight recorder → `logs/calls/`
- `friday/tools/` — external API tools (email, github, calendar, guards, retries)
- `friday/knowledge/` — system prompt + Tanish facts
- `api/server.py` — `POST /token` (LiveKit JWT, `X-Friday-Key` auth, rate limited)
- `tests/` — pytest suite, all externals mocked

## Commands

```bash
# env — copy .env.example → .env, fill keys (LIVEKIT_*, DEEPGRAM_*, OPENAI_*,
# RESEND_*, GITHUB_TOKEN, FRIDAY_API_KEY). ALERT_WEBHOOK_URL optional.
pip install -r requirements.lock    # pinned + hashed — use this
python main.py                      # API :8080 (/health), worker health :8081
pytest -q                           # 69 tests, no creds needed (dummy env in conftest)
python -m compileall friday/ api/ main.py   # syntax check
```

## Conventions

- **Never block the event loop** — all sync external calls go through `asyncio.to_thread` + `retry_sync` (friday/tools/guards.py)
- **Sanitize every visitor-supplied arg** with `sanitize_text` before use
- **Outbound sends** (email/calendar): normalize + `can_send_to` cap check + `record_send` on success
- **Session lifecycle**: CallRecorder attach → session.start → duration timer → away countdown → goodbye → close
- Tools speak via `session.say(...)`; UI nav via `room.local_participant.publish_data`
- `pythonpath = .` set in pytest.ini — tests import `friday/` directly

## Lockfile

```bash
uv pip compile requirements.txt --generate-hashes -o requirements.lock --python-version 3.11
```

Regenerate after editing `requirements.txt`. CI + Dockerfile install from lock — keep them in sync or CI breaks.

## Gotchas

- `BUGS.md` — full 35-item security/reliability audit trail (untracked by choice)
- LiveKit turn detection = semantic `TurnDetector` (cloud + local fallback), VAD is Silero
- Visitor JWTs: `can_publish_data=False` — visitors are receive-only on data channel
- Call records auto-swept after `LOG_RETENTION_DAYS` (default 30, 0 = keep)
