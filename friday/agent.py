"""
Friday — Core Agent
Built on LiveKit Agents framework with:
  STT  → Deepgram
  LLM  → OpenAI GPT-4o
  TTS  → Deepgram
  VAD  → Silero (local, free)
"""
import asyncio
import json
import logging
from typing import Annotated

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    function_tool,
    room_io,
)
from livekit.plugins import deepgram, openai, silero

from friday.config import get_settings
from friday.knowledge.prompts import build_system_prompt, GREETING, TIME_WARNING, GOODBYE
from friday.tools.email_tool import send_message_to_tanish, send_resume_to_user
from friday.tools.github_tool import (
    get_github_summary,
    get_all_repositories,
    get_repo_details,
    get_recent_activity
)
from friday.tools.calendar_tool import create_meeting

logger   = logging.getLogger("friday.agent")
settings = get_settings()


# ── Agent class ────────────────────────────────────────────────────────────────
class FridayAgent(Agent):
    """Friday — Tanish's AI voice agent."""

    def __init__(self, user_id: str, room: rtc.Room):
        self._user_id  = user_id
        self._room     = room

        super().__init__(
            instructions=build_system_prompt(),
        )

    async def on_enter(self):
        """Called when the agent joins the room — greet the user."""
        await self.session.say(GREETING, allow_interruptions=True)

    # ── Tool methods with Verbal Fillers ───────────────────────────────────────
    @function_tool()
    async def tool_get_current_time(self) -> str:
        """
        Return the current date and time in India (IST).
        Use this when the user asks what time it is or what today's date is.
        """
        from datetime import datetime
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        await self.session.say("Sure, Please give me a moment", allow_interruptions=True)
        return f"It is currently {now.strftime('%A, %d %B %Y')}, at {now.strftime('%I:%M %p')} IST."

    @function_tool()
    async def tool_navigate_ui(
        self,
        section: Annotated[str, "The section of the website to scroll to. Valid values: 'home', 'about', 'experience', 'projects', 'education', 'contact'"],
    ) -> str:
        """
        Remotely control the website's UI to scroll to a specific section.
        Use this whenever you are talking about a specific part of Tanish's life or work.
        """
        await self.session.say(f"Let me show you that on the page.", allow_interruptions=True)
        
        payload = json.dumps({
            "type": "NAVIGATE",
            "section": section.lower()
        }).encode('utf-8')
        
        await self._room.local_participant.publish_data(payload)
        return f"UI navigated to {section} section."

    @function_tool()
    async def tool_send_email(
        self,
        sender_name:  Annotated[str, "The name of the person sending the message"],
        sender_email: Annotated[str, "The email address of the sender (to reply to)"],
        message:      Annotated[str, "The message to forward to Tanish"],
    ) -> str:
        """
        Send a visitor's message directly to Tanish's inbox via email.
        Ask for name, email, and message before calling this.
        """
        await self.session.say("Sure thing, let me get that message sent to Tanish for you.", allow_interruptions=True)
        result = await send_message_to_tanish(sender_name, sender_email, message)
        return result["message"]

    @function_tool()
    async def tool_send_resume(
        self,
        receiver_name:  Annotated[str, "The name of the person requesting the resume"],
        receiver_email: Annotated[str, "The email address to send the resume to"],
    ) -> str:
        """
        Send a PDF of Tanish's resume directly to the user's email address.
        """
        await self.session.say(f"Of course, {receiver_name}. I'm sending Tanish's resume to {receiver_email} right now.", allow_interruptions=True)
        result = await send_resume_to_user(receiver_email, receiver_name)
        return result["message"]

    @function_tool()
    async def tool_github_summary(self) -> str:
        """Fetch and return a voice-friendly summary of Tanish's GitHub."""
        await self.session.say("Let me pull up Tanish's GitHub profile for you.", allow_interruptions=True)
        return await get_github_summary()

    @function_tool()
    async def tool_get_all_repositories(self) -> str:
        """Fetch a list of all public repository names for Tanish."""
        await self.session.say("I'll fetch a list of all Tanish's repositories.", allow_interruptions=True)
        repos = await get_all_repositories()
        return f"Tanish has {len(repos)} repositories. Some are {', '.join(repos[:10])}."

    @function_tool()
    async def tool_get_repo_details(
        self,
        repo_name: Annotated[str, "The name of the repository to get details for"]
    ) -> str:
        """Fetch detailed info about a specific repository."""
        await self.session.say(f"Let me look into the details for {repo_name}.", allow_interruptions=True)
        return await get_repo_details(repo_name)

    @function_tool()
    async def tool_get_recent_github_activity(
        self,
        repo_name: Annotated[str, "The name of the repository to check activity for"]
    ) -> str:
        """Check for recent open issues or pull requests in a specific repository."""
        await self.session.say(f"Checking for recent activity in {repo_name}.", allow_interruptions=True)
        return await get_recent_activity(repo_name)

    @function_tool()
    async def tool_schedule_meeting(
        self,
        requester_name:    Annotated[str, "The name of the person who wants to meet Tanish"],
        requester_email:   Annotated[str, "Their email address for the calendar invite"],
        topic:             Annotated[str, "What they want to discuss"],
        preferred_date:    Annotated[str, "Preferred date"],
        preferred_time:    Annotated[str, "Preferred time in IST"] = "11:00 AM",
        duration_minutes:  Annotated[int, "Meeting duration in minutes"] = 30,
    ) -> str:
        """Schedule a Google Meet / calendar meeting."""
        await self.session.say("One moment while I check availability and book that for you.", allow_interruptions=True)
        result = await create_meeting(
            requester_name=requester_name,
            requester_email=requester_email,
            topic=topic,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            duration_minutes=duration_minutes,
        )
        return result["message"]

    @function_tool()
    async def tool_get_contact_info(self) -> str:
        """Return Tanish's contact details and social links."""
        await self.session.say("I'll get his contact details for you.", allow_interruptions=True)
        return (
            "Tanish's details:\n  Email: tanishrajput9@gmail.com\n"
            "  LinkedIn: linkedin.com/in/tr26\n  GitHub: github.com/tanishra\n"
            "  Portfolio: tanish.website"
        )

    @function_tool()
    async def tool_get_resume_info(self) -> str:
        """Provide a spoken summary of Tanish's resume / CV."""
        await self.session.say("Let me grab a summary of Tanish's background.", allow_interruptions=True)
        return (
            "Tanish Rajput — AI Engineer Current at QualtechEdge. "
            "Built production voice agents and RAG pipelines. "
            "Skills: Python, LLMs, LangChain, LangGraph, AI Agents, LiveKit. "
            "He designs agent systems from first principles."
        )


# ── Call duration enforcer ────────────────────────────────────────────────────
async def _enforce_call_limit(session: AgentSession):
    """
    Enforces settings.max_call_duration_seconds.
    Warns the visitor 30s before the limit, says an uninterruptible goodbye at
    the limit, then closes the session (room deleted via delete_room_on_close).
    Cancelled automatically if the call ends early.
    """
    try:
        limit   = settings.max_call_duration_seconds
        warn_at = max(0, limit - 30)

        await asyncio.sleep(warn_at)
        await session.say(TIME_WARNING, allow_interruptions=True)

        await asyncio.sleep(limit - warn_at)
        await session.say(GOODBYE, allow_interruptions=False)
        await session.aclose()
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.warning(f"call-limit enforcer failed: {e}")


# ── Entry point for LiveKit worker ────────────────────────────────────────────
async def entrypoint(ctx: JobContext):
    """LiveKit calls this function when a new room job is dispatched."""
    logger.info(f"Friday starting in room: {ctx.room.name}")
    await ctx.connect()

    user_id = "anonymous"
    try:
        participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=10)
        user_id = participant.identity or "anonymous"
    except asyncio.TimeoutError:
        logger.warning("no participant joined within 10s — continuing as anonymous")
    except Exception as e:
        logger.warning(f"participant lookup failed: {e}")

    session = AgentSession(
        stt=deepgram.STT(
            api_key=settings.deepgram_api_key,
            model="nova-2",
            language="en-US",
            interim_results=True,
            smart_format=True,
        ),
        llm=openai.LLM(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0.7,
        ),
        tts=deepgram.TTS(
            api_key=settings.deepgram_api_key,
            model="aura-stella-en",  # kind and professional female voice
        ),
        vad=silero.VAD.load(),             # local VAD — free & fast
    )

    # Pass ctx.room to FridayAgent so tools can publish data correctly
    await session.start(
        agent=FridayAgent(user_id=user_id, room=ctx.room),
        room=ctx.room,
        room_options=room_io.RoomOptions(delete_room_on_close=True),
    )
    logger.info(f"Friday active for user: {user_id}")

    # Hard cap on call duration — cancelled if the job ends early
    timer = asyncio.create_task(_enforce_call_limit(session))
    ctx.add_shutdown_callback(timer.cancel)




# ━━━ FRONTEND INTEGRATION GUIDE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Add this listener to your Next.js portfolio:
#
# ```javascript
# import { RoomEvent } from 'livekit-client';
#
# room.on(RoomEvent.DataReceived, (payload, participant) => {
#   const decoder = new TextDecoder();
#   const data = JSON.parse(decoder.decode(payload));
#
#   if (data.type === 'NAVIGATE') {
#     const section = document.getElementById(data.section);
#     if (section) section.scrollIntoView({ behavior: 'smooth' });
#   }
# });
# ```
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
