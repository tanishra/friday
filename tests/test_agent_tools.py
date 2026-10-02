"""Agent tools: email guards, publish_data fallback, misc tools."""
from unittest.mock import MagicMock

import friday.agent as agent_mod
from tests.conftest import call_tool


async def test_send_email_invalid_address(friday_agent, fake_session):
    out = await call_tool(friday_agent.send_email, "A", "not-an-email", "hi")
    assert "valid email" in out
    assert fake_session.said == []          # no filler on rejection


async def test_send_email_capped(friday_agent, monkeypatch):
    monkeypatch.setattr(agent_mod, "can_send_to", lambda e: False)
    out = await call_tool(friday_agent.send_email, "A", "a@x.com", "hi")
    assert "directly" in out


async def test_send_email_happy_records(friday_agent, monkeypatch):
    recorded = []
    monkeypatch.setattr(agent_mod, "can_send_to", lambda e: True)
    monkeypatch.setattr(agent_mod, "record_send", lambda e, k: recorded.append((e, k)))
    monkeypatch.setattr(
        agent_mod, "send_message_to_tanish",
        lambda n, e, m: _ok({"success": True, "message": "sent"}),
    )
    out = await call_tool(friday_agent.send_email, "A", "a@x.com", "hi")
    assert out == "sent"
    assert recorded == [("a@x.com", "message")]


async def test_send_email_failure_not_counted(friday_agent, monkeypatch):
    recorded = []
    monkeypatch.setattr(agent_mod, "can_send_to", lambda e: True)
    monkeypatch.setattr(agent_mod, "record_send", lambda e, k: recorded.append(e))
    monkeypatch.setattr(
        agent_mod, "send_message_to_tanish",
        lambda n, e, m: _ok({"success": False, "message": "boom"}),
    )
    out = await call_tool(friday_agent.send_email, "A", "a@x.com", "hi")
    assert out == "boom"
    assert recorded == []                   # no quota burn on failed send


async def test_send_resume_invalid(friday_agent):
    out = await call_tool(friday_agent.send_resume, "B", "bad-email")
    assert "valid email" in out


async def test_schedule_meeting_capped(friday_agent, monkeypatch):
    monkeypatch.setattr(agent_mod, "can_send_to", lambda e: False)
    out = await call_tool(
        friday_agent.schedule_meeting, "A", "a@x.com", "chat", "tomorrow"
    )
    assert "invites" in out


async def test_navigate_ui_publish_fails_gracefully(friday_agent, fake_session):
    friday_agent._room.local_participant.publish_data = MagicMock(
        side_effect=Exception("channel closed")
    )
    # make the awaited call raise — need async raise
    async def raise_it(*a, **kw):
        raise Exception("channel closed")
    friday_agent._room.local_participant.publish_data = raise_it
    out = await call_tool(friday_agent.navigate_ui, "projects")
    assert "couldn't navigate" in out.lower()


async def test_navigate_ui_happy(friday_agent):
    published = []

    async def pub(payload):
        published.append(payload)

    friday_agent._room.local_participant.publish_data = pub
    out = await call_tool(friday_agent.navigate_ui, "Projects")
    assert "projects" in out.lower()
    assert b'"section": "projects"' in published[0]


async def test_get_current_time_ist(friday_agent):
    out = await call_tool(friday_agent.get_current_time)
    assert "IST" in out


async def _ok(d):
    return d


async def test_navigate_ui_rejects_bad_section(friday_agent):
    called = []
    async def pub(payload):
        called.append(payload)
    friday_agent._room.local_participant.publish_data = pub
    out = await call_tool(friday_agent.navigate_ui, "evil-section")
    assert "can only show" in out.lower()
    assert called == []


async def test_send_email_empty_message_after_sanitize(friday_agent):
    out = await call_tool(friday_agent.send_email, "A", "a@x.com", "\x00\x1f")
    assert "what the message should say" in out


async def test_send_email_sanitizes_name(friday_agent, monkeypatch):
    captured = []
    monkeypatch.setattr(agent_mod, "can_send_to", lambda e: True)
    monkeypatch.setattr(agent_mod, "record_send", lambda e, k: None)
    async def capture(n, e, m):
        captured.append((n, m))
        return {"success": True, "message": "ok"}
    monkeypatch.setattr(agent_mod, "send_message_to_tanish", capture)
    await call_tool(friday_agent.send_email, "Al\x00ice" + "x" * 200, "a@x.com", "hello")
    name, msg = captured[0]
    assert len(name) == 100 and "\x00" not in name
