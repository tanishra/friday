"""Prompt building + regression guards for past knowledge-base lies."""
from friday.knowledge.prompts import (
    build_system_prompt, GREETING, TIME_WARNING, GOODBYE, STILL_THERE,
)


def test_prompt_renders_sections():
    p = build_system_prompt()
    for section in ["EDUCATION", "WORK EXPERIENCE", "PROJECTS", "Tanish Rajput"]:
        assert section in p


def test_prompt_has_no_stack_lies():
    p = build_system_prompt()
    assert "ElevenLabs" not in p            # was claimed, actual is Deepgram TTS
    assert "CrewAIRAG" not in p             # comma bug regression
    # Friday's own project line must reflect the real stack
    friday_line = next(l for l in p.splitlines() if "Friday" in l and "Live" in l)
    assert "Redis" not in friday_line and "ElevenLabs" not in friday_line


def test_spoken_strings_exist():
    for s in [GREETING, TIME_WARNING, GOODBYE, STILL_THERE]:
        assert isinstance(s, str) and len(s) > 10


def test_no_markdown_instructions_in_prompt():
    p = build_system_prompt()
    assert "NO MARKDOWN" in p
