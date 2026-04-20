"""
Friday — Email Tool
Sends messages to Tanish's inbox and files to visitors via Resend.
"""
import resend
import base64
from pathlib import Path
from friday.config import get_settings

settings = get_settings()
resend.api_key = settings.resend_api_key

RESUME_PATH = Path(__file__).parent.parent / "knowledge" / "resume.pdf"

async def send_message_to_tanish(
    sender_name: str,
    sender_email: str,
    message: str,
) -> dict:
    """
    Send a visitor's message to Tanish via email.
    Returns {"success": bool, "message": str}
    """
    try:
        subject = f"Portfolio Message from {sender_name} via Friday"
        html_body = f"""
        <div style="font-family: Inter, sans-serif; max-width: 560px; margin: 0 auto; color: #111;">
            <div style="background: #111; padding: 24px; border-radius: 12px 12px 0 0;">
                <h2 style="color: #C4614A; margin: 0; font-size: 1.1rem;">📨 New message via Friday</h2>
            </div>
            <div style="background: #FAFAF8; padding: 28px; border: 1px solid #E8E6E0; border-top: none; border-radius: 0 0 12px 12px;">
                <p style="margin: 0 0 8px;"><strong>From:</strong> {sender_name}</p>
                <p style="margin: 0 0 20px;"><strong>Email:</strong> <a href="mailto:{sender_email}">{sender_email}</a></p>
                <div style="background: white; border: 1px solid #E8E6E0; border-radius: 8px; padding: 16px;">
                    <p style="margin: 0; line-height: 1.6;">{message}</p>
                </div>
                <p style="margin: 20px 0 0; font-size: 0.8rem; color: #999;">
                    Sent via Friday — Tanish's AI voice agent on his portfolio.
                </p>
            </div>
        </div>
        """

        resend.Emails.send({
            "from":    settings.sender_email,
            "to":      [settings.your_email],
            "reply_to": sender_email,
            "subject": subject,
            "html":    html_body,
        })

        # Auto-reply to the sender
        resend.Emails.send({
            "from":    settings.sender_email,
            "to":      [sender_email],
            "subject": f"Got your message, {sender_name}! — Friday (Tanish's AI)",
            "html":    f"""
            <div style="font-family: Inter, sans-serif; max-width: 560px; margin: 0 auto;">
                <p>Hey {sender_name}!</p>
                <p>Your message just landed in Tanish's inbox. He typically replies within 24 hours.</p>
                <p>In the meantime, you can connect with him on 
                   <a href="https://www.linkedin.com/in/tr26/">LinkedIn</a>.</p>
                <p style="color: #999; font-size: 0.8rem; margin-top: 24px;">
                    — Friday, Tanish's AI assistant
                </p>
            </div>
            """,
        })

        return {"success": True, "message": f"Message sent to Tanish! He'll reply to {sender_email} soon."}

    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}

async def send_resume_to_user(receiver_email: str, receiver_name: str) -> dict:
    """
    Sends Tanish's resume PDF as an attachment to the visitor.
    """
    try:
        if not RESUME_PATH.exists():
            return {"success": False, "message": "Resume file not found on the server."}

        with open(RESUME_PATH, "rb") as f:
            resume_content = f.read()
            encoded_content = base64.b64encode(resume_content).decode()

        params = {
            "from": settings.sender_email,
            "to": [receiver_email],
            "subject": f"Resume of Tanish Rajput — Requested via Friday",
            "html": f"""
            <div style="font-family: sans-serif;">
                <p>Hello {receiver_name},</p>
                <p>As requested during our conversation, here is the full resume of <strong>Tanish Rajput</strong>.</p>
                <p>Tanish is an AI Engineer specializing in voice agents, RAG pipelines, and multi-agent architectures.</p>
                <p>Feel free to reply to this email or connect with him on <a href="https://www.linkedin.com/in/tr26/">LinkedIn</a>.</p>
                <br/>
                <p>Best regards,<br/>Friday (Tanish's AI Assistant)</p>
            </div>
            """,
            "attachments": [
                {
                    "content": encoded_content,
                    "filename": "Tanish_Rajput_Resume.pdf",
                }
            ],
        }

        resend.Emails.send(params)
        return {"success": True, "message": f"Resume has been sent to {receiver_email}!"}

    except Exception as e:
        return {"success": False, "message": f"Error sending resume: {str(e)}"}
