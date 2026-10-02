"""
Friday — Call Observability
Per-call flight recorder: subscribes to AgentSession events and writes one
JSON record per call to logs/calls/ — transcript, tool executions, pipeline
latency metrics, token usage, and errors. Passive listeners only; never
mutates session behavior.
"""
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from livekit.agents.metrics import UsageCollector

logger = logging.getLogger("friday.observability")

LOG_DIR = Path("logs/calls")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class CallRecorder:
    """Records one call's transcript, tools, metrics, usage, and errors."""

    def __init__(self, room_name: str, user_id: str):
        self._t0 = time.monotonic()
        self._finished = False
        self._usage = UsageCollector()
        self._metric_vals: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        self._rec = {
            "room":        room_name,
            "user_id":     user_id,
            "started_at":  _utcnow(),
            "transcript":  [],
            "tools":       [],
            "errors":      [],
        }

    # ── Event handlers (sync, cheap — append only) ────────────────────────────
    def _on_item(self, ev) -> None:
        try:
            item = ev.item
            role = getattr(item, "role", None)
            text = getattr(item, "text_content", None)
            if role in ("user", "assistant") and text:
                self._rec["transcript"].append({"ts": _utcnow(), "role": role, "text": text})
        except Exception as e:
            logger.debug(f"transcript capture skipped: {e}")

    def _on_tools(self, ev) -> None:
        try:
            for call, out in ev.zipped():
                self._rec["tools"].append({
                    "ts":     _utcnow(),
                    "name":   getattr(call, "name", "?"),
                    "args":   getattr(call, "arguments", None),
                    "output": str(getattr(out, "output", ""))[:2000],
                    "error":  bool(getattr(out, "is_error", False)),
                })
        except Exception as e:
            logger.debug(f"tool capture skipped: {e}")

    def _on_metrics(self, ev) -> None:
        try:
            m = ev.metrics
            self._usage.collect(m)
            mtype = getattr(m, "type", type(m).__name__)
            bucket = self._metric_vals[mtype]
            bucket["count"].append(1.0)
            for field in ("ttft", "ttfb", "duration", "audio_duration"):
                val = getattr(m, field, None)
                if isinstance(val, (int, float)):
                    bucket[field].append(val)
        except Exception as e:
            logger.debug(f"metric capture skipped: {e}")

    def _on_error(self, ev) -> None:
        try:
            self._rec["errors"].append({"ts": _utcnow(), "error": str(getattr(ev, "error", ev))})
        except Exception:
            pass

    # ── Wiring ────────────────────────────────────────────────────────────────
    def attach(self, session) -> None:
        session.on("conversation_item_added", self._on_item)
        session.on("function_tools_executed", self._on_tools)
        session.on("metrics_collected", self._on_metrics)
        session.on("error", self._on_error)

    # ── Finalize ─────────────────────────────────────────────────────────────
    def finish(self) -> None:
        """Write the call record. Idempotent — safe to call on close AND shutdown."""
        if self._finished:
            return
        self._finished = True

        duration = time.monotonic() - self._t0
        self._rec["ended_at"] = _utcnow()
        self._rec["duration_s"] = round(duration, 1)

        # aggregate metrics → summary per pipeline stage
        summary = {}
        for mtype, fields in self._metric_vals.items():
            agg = {"count": int(len(fields.get("count", [])))}
            for field, vals in fields.items():
                if field == "count" or not vals:
                    continue
                agg[f"{field}_avg"] = round(sum(vals) / len(vals), 3)
                agg[f"{field}_max"] = round(max(vals), 3)
            summary[mtype] = agg
        self._rec["metrics_summary"] = summary

        # token/usage totals
        try:
            u = self._usage.get_summary()
            self._rec["usage"] = {
                "llm_prompt_tokens":     u.llm_prompt_tokens,
                "llm_completion_tokens": u.llm_completion_tokens,
                "tts_characters":        u.tts_characters_count,
                "stt_audio_s":           round(u.stt_audio_duration, 1),
                "tts_audio_s":           round(u.tts_audio_duration, 1),
            }
        except Exception as e:
            logger.debug(f"usage summary failed: {e}")
            self._rec["usage"] = {}

        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            fname = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}_{self._rec['room']}.json"
            (LOG_DIR / fname).write_text(json.dumps(self._rec, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"call record write failed: {e}")

        llm = summary.get("llm_metrics", {})
        logger.info(
            f"call ended room={self._rec['room']} duration={duration:.0f}s "
            f"turns={len(self._rec['transcript'])} tools={len(self._rec['tools'])} "
            f"errors={len(self._rec['errors'])} llm_ttft_avg={llm.get('ttft_avg', '-')}s"
        )
