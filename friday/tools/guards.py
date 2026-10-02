"""
Friday — Outbound send guards
Anti-relay protection: validates recipient emails, caps sends per recipient
per rolling 24h window, and logs every outbound address.

In-memory only — counters reset on restart (single-worker setup; the
10-tokens/hr/IP rate limit on /token bounds exposure regardless).
"""
import logging
import re
import time
from collections import defaultdict

logger = logging.getLogger("friday.tools.guards")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_SENDS_PER_RECIPIENT = 3      # covers resume + auto-reply + invite in one visit
WINDOW_SECONDS = 24 * 3600

_sends: dict[str, list[float]] = defaultdict(list)


def normalize_email(addr: str) -> str | None:
    """Return the lowercased email if it looks valid, else None."""
    if not addr:
        return None
    addr = addr.strip().lower()
    return addr if EMAIL_RE.match(addr) and len(addr) <= 254 else None


def can_send_to(recipient: str) -> bool:
    """True if the recipient is under the rolling-24h send cap."""
    now = time.time()
    times = [t for t in _sends.get(recipient, []) if now - t < WINDOW_SECONDS]
    _sends[recipient] = times
    return len(times) < MAX_SENDS_PER_RECIPIENT


def record_send(recipient: str, kind: str) -> None:
    """Record a successful send and log the outbound recipient."""
    _sends.setdefault(recipient, []).append(time.time())
    logger.info(f"outbound send kind={kind} to={recipient}")


# ── Input sanitization ────────────────────────────────────────────────────────
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(value: str, max_len: int) -> str:
    """Strip control chars and hard-cap length for visitor-supplied strings."""
    if not value:
        return ""
    return CONTROL_CHARS.sub("", str(value)).strip()[:max_len]


# ── Retry helper for blocking external calls (runs inside worker threads) ────
def retry_sync(fn, attempts: int = 2, delay: float = 0.5):
    """Run a blocking fn with one retry + fixed backoff. Raises the last error."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if i < attempts - 1:
                logger.debug(f"retrying after error: {e}")
                time.sleep(delay)
    raise last
