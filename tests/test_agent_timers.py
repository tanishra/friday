"""Call-limit timer + away countdown sequencing."""
import asyncio

import friday.agent as agent_mod
from friday.knowledge.prompts import TIME_WARNING, GOODBYE, STILL_THERE


async def test_call_limit_sequence(monkeypatch, fake_session):
    """warn → goodbye → close, in order."""
    monkeypatch.setattr(agent_mod.settings, "max_call_duration_seconds", 0)
    # limit=0 → warn_at=0 → warn immediately, goodbye right after
    await agent_mod._enforce_call_limit(fake_session)

    texts = [t for t, _ in fake_session.said]
    assert texts == [TIME_WARNING, GOODBYE]
    assert fake_session.said[0][1] is True     # warning interruptible
    assert fake_session.said[1][1] is False    # goodbye not
    assert fake_session.closed is True


async def test_call_limit_cancel_early(monkeypatch, fake_session):
    """Visitor hangs up before limit → no goodbye, no close."""
    monkeypatch.setattr(agent_mod.settings, "max_call_duration_seconds", 60)
    task = asyncio.create_task(agent_mod._enforce_call_limit(fake_session))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert fake_session.said == []
    assert fake_session.closed is False


async def test_away_countdown_sequence(fake_session):
    await agent_mod._away_countdown(fake_session, delay=0.01)
    texts = [t for t, _ in fake_session.said]
    assert texts == [STILL_THERE, GOODBYE]
    assert fake_session.closed is True


async def test_away_countdown_cancel(fake_session):
    task = asyncio.create_task(agent_mod._away_countdown(fake_session, delay=60))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert fake_session.said == [(STILL_THERE, True)]   # nudge sent, no goodbye
    assert fake_session.closed is False
