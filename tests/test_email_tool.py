"""Email tool: send paths, failure paths, resume attachment (Resend mocked)."""
import friday.tools.email_tool as et


async def test_message_sends_two_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(et, "_send_email", lambda params: sent.append(params))
    out = await et.send_message_to_tanish("Alice", "alice@x.com", "hello")
    assert out["success"] is True
    assert len(sent) == 2                       # owner + auto-reply
    assert sent[0]["to"] == ["tanish@test.com"]
    assert sent[0]["reply_to"] == "alice@x.com"
    assert sent[1]["to"] == ["alice@x.com"]


async def test_message_failure(monkeypatch):
    def boom(params):
        raise RuntimeError("resend down")
    monkeypatch.setattr(et, "_send_email", boom)
    out = await et.send_message_to_tanish("A", "a@x.com", "m")
    assert out["success"] is False
    assert "Failed" in out["message"]


async def test_resume_sends_attachment(monkeypatch, tmp_path):
    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(b"%PDF-fake")
    monkeypatch.setattr(et, "RESUME_PATH", pdf)
    sent = []
    monkeypatch.setattr(et, "_send_email", lambda params: sent.append(params))
    out = await et.send_resume_to_user("bob@x.com", "Bob")
    assert out["success"] is True
    assert sent[0]["attachments"][0]["filename"] == "Tanish_Rajput_Resume.pdf"


async def test_resume_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(et, "RESUME_PATH", tmp_path / "nope.pdf")
    out = await et.send_resume_to_user("bob@x.com", "Bob")
    assert out["success"] is False
    assert "not found" in out["message"]
