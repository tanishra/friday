"""
Friday — Tanish's Knowledge Base
Everything Friday knows about Tanish Rajput.
Single source of truth — update here, reflects everywhere.
"""

# ── Personal ──────────────────────────────────────────────────────────────────
PERSONAL = {
    "name":          "Tanish Rajput",
    "nickname":      "Tanish",
    "age":           "23",
    "location":      "Noida, Uttar Pradesh, India",
    "email":         "tanishrajput9@gmail.com",
    "phone":         "+91 (available on request)",
    "timezone":      "IST (UTC+5:30)",
    "languages":     ["Hindi (native)", "English (fluent)"],
    "communication": "Prefers async communication; replies within 24h on LinkedIn, faster on email.",
}

# ── Social & Links ────────────────────────────────────────────────────────────
SOCIAL = {
    "github":   "https://github.com/tanishra",
    "linkedin": "https://www.linkedin.com/in/tr26/",
    "email":    "mailto:tanishrajput9@gmail.com",
    "portfolio": "https://tanish.website",   
}

# ── Education ─────────────────────────────────────────────────────────────────
EDUCATION = [
    {
        "degree":      "B.Tech — Information Technology",
        "institution": "NIET Greater Noida",
        "period":      "2021 – 2025",
        "cgpa":        "9.01",
        "highlights": [
            "Specialised in Artificial Intelligence",
            "Multiple end-to-end ML and AI projects",
        ],
    }
]

# ── Work Experience ───────────────────────────────────────────────────────────
EXPERIENCE = [
    {
        "role":        "AI Engineer",
        "company":     "QualtechEdge",
        "period":      "November 2025 – Present",
        "type":        "Full-time",
        "location":    "Noida, India",
        "description": (
            "Building production-grade LangGraph-based voice agents and RAG pipelines. "
            "Designing multi-agent architectures with custom AgentLoop orchestrators, "
            "multi-tier memory systems, and real-time tool execution pipelines — "
            "entirely from scratch without relying on high-level frameworks."
        ),
        "tech": ["Python", "LangGraph", "FastAPI", "Redis", "PostgreSQL", "LiveKit"],
        "current": True,
    },
    {
        "role":        "Software Engineer",
        "company":     "Microsoft",
        "period":      "June 2024 – August 2024",
        "type":        "Internship",
        "description": (
            "Worked on integrating an audio panel in to Microsoft Designer application using React.js, Next.js, and Fluent UI v9. "
            "Contributed to internal Microsoft products during a 3-month internship."
        ),
        "tech": ["React.js", "Next.js", "Fluent UI v9", "Node.js"],
        "current": False,
    },
]

# ── Skills ────────────────────────────────────────────────────────────────────
SKILLS = {
    "languages":       ["Python", "Java"],
    "ai_ml": [
        "LLMs (OpenAI, Claude, Gemini, Groq, Mistral, DeepSeek, Sarvam, Moonshot, LLaMA)",
        "LangChain / LangGraph",
        "CrewAI"
        "RAG Pipelines",
        "Prompt Engineering",
        "Context Engineering",
        "Vector Databases",
        "Embeddings",
        "Fine-tuning LLMs",
        "Agentic AI",
        "MCP (Model Context Protocol)",
        "Voice Agents (LiveKit, Deepgram, ElevenLabs)",
        "AI Agents Architectures or Design Patterns",
        "Multi Agent Systems"
    ],
    "frameworks":      ["FastAPI", "Flask", "Asyncio"],
    "infrastructure":  ["Docker", "Redis", "PostgreSQL", "Supabase", "MongoDB", "AWS", "Vercel", "Neon"],
    "tools":           ["Git", "GitHub", "VS Code", "Postman", "LangSmith", "Cursor", "Windsurf"],
}

# ── Projects ──────────────────────────────────────────────────────────────────
PROJECTS = [
    {
        "name":        "Taxyn",
        "tagline":     "GST Compliance Automation for Indian CA Firms",
        "status":      "Active",
        "description": (
            "Production-grade GST document automation platform for Indian Chartered Accountant firms. "
            "Features a custom stateless AgentLoop with explicit Context passing, "
            "Docling-based PDF extraction, Instructor for structured LLM output, "
            "and a 21-file codebase with Streamlit UI. Automates repetitive GST filing tasks."
        ),
        "tech":        ["Python", "GPT-4o", "Docling", "Instructor", "Streamlit", "FastAPI"],
        "github":      "https://github.com/tanishra/taxyn",
        "category":    "AI Product",
    },
    {
        "name":        "Arogyam AI",
        "tagline":     "Clinical Intelligence Platform for Indian Tier 2/3 Hospitals",
        "status":      "Architecture Phase",
        "description": (
            "Multi-agent clinical decision support system targeting resource-constrained hospitals. "
            "Architecture features: Redis Streams event bus, PostgreSQL with hospital-level row isolation, "
            "closed-loop RLHF system for doctor feedback, and a custom multi-agent pipeline — no frameworks."
        ),
        "tech":        ["Python", "Redis Streams", "PostgreSQL", "Multi-Agent", "RLHF"],
        "github":      None,
        "category":    "AI System",
    },
    {
        "name":        "Friday",
        "tagline":     "Real-time AI Voice Agent",
        "status":      "In Progress",
        "description": (
            "The very agent you're talking to right now. An AI voice assistant built entirely from scratch "
            "on LiveKit, using Deepgram for speech-to-text, OpenAI GPT-4o for reasoning, "
            "and ElevenLabs for natural speech synthesis. "
            "Friday can answer questions about Tanish, send emails, check GitHub, schedule meetings, and more."
        ),
        "tech":        ["LiveKit", "Python", "Deepgram", "OpenAI", "ElevenLabs", "FastAPI", "Redis"],
        "github":      "https://github.com/tanishra/friday",
        "category":    "Voice Agent",
    },
]

# ── Personality & Goals ───────────────────────────────────────────────────────
PERSONALITY = {
    "style":       "Direct, intellectually intense, casually confident, kind",
    "interests":   ["AI systems architecture", "voice agents", "LLMs", "Startups", "Sci-Fi movies","Building AI Startups"],
    "hobbies":     ["Building AI products", "reading about AI research", "reading AI books"],
    "philosophy":  (
        "AI is just one component of a well-engineered system. "
        "Build from first principles, no frameworks, full control."
    ),
    "long_term_goal": (
        "Founding AI-powered companies that create massive real-world value. "
        "The current AI era is the defining window — building with urgency and conviction."
    ),
    "fun_facts": [
        "Prefers building from scratch over using abstractions",
        "Codes using Claude Code, Gemini CLI, and Codex CLI",
        "Communicates in Hinglish (Hindi-English mix) casually",
    ],
}

# ── Availability ──────────────────────────────────────────────────────────────
AVAILABILITY = {
    "open_to":       ["Full-time roles", "AI Projects", "interesting collaborations", "Freelancing"],
    "not_open_to":   ["MLM", "sales roles", "non-technical positions","not related to AI things"],
    "response_time": "Usually within 24 hours on email/LinkedIn",
    "preferred_contact": "Email: tanishrajput9@gmail.com or LinkedIn: linkedin.com/in/tr26/",
}

# ── What Friday can do on behalf of Tanish ────────────────────────────────────
FRIDAY_CAPABILITIES = [
    "Answer any question about Tanish — his skills, experience, projects, education and more",
    "Send a message/email directly to Tanish on the user's behalf",
    "Show Tanish's GitHub profile and recent repositories",
    "Schedule a Google Meet or calendar meeting with Tanish",
    "Explain any of Tanish's projects in detail",
    "Tell you about Tanish's tech stack and what he's currently building",
    "Share Tanish's social links and contact details",
]
