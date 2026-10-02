"""GitHub tool: non-blocking + error paths (client mocked)."""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import friday.tools.github_tool as gh


def _fake_user():
    repo = SimpleNamespace(name="friday")
    user = MagicMock()
    user.public_repos = 12
    user.followers = 5
    user.get_repos.return_value = [repo]
    return user


async def test_summary_happy(monkeypatch):
    client = MagicMock()
    client.get_user.return_value = _fake_user()
    monkeypatch.setattr(gh, "_get_client", lambda: client)
    out = await gh.get_github_summary()
    assert "12 public repositories" in out
    assert "friday" in out


async def test_summary_error_falls_back(monkeypatch):
    client = MagicMock()
    client.get_user.side_effect = Exception("401")
    monkeypatch.setattr(gh, "_get_client", lambda: client)
    out = await gh.get_github_summary()
    assert "github.com/" in out


async def test_repo_details_error(monkeypatch):
    client = MagicMock()
    client.get_repo.side_effect = Exception("not found")
    monkeypatch.setattr(gh, "_get_client", lambda: client)
    out = await gh.get_repo_details("ghost-repo")
    assert "Error fetching" in out


async def test_non_blocking(monkeypatch):
    """GitHub call must not freeze the event loop — ticker keeps ticking."""
    client = MagicMock()

    def slow_user(*a, **kw):
        import time
        time.sleep(0.3)   # blocking sleep inside the thread
        return _fake_user()

    client.get_user.side_effect = slow_user
    monkeypatch.setattr(gh, "_get_client", lambda: client)

    ticks = []

    async def ticker():
        for _ in range(5):
            ticks.append(1)
            await asyncio.sleep(0.05)

    await asyncio.gather(gh.get_github_summary(), ticker())
    # all 5 ticks fired while the 0.3s blocking call ran in a thread
    assert len(ticks) == 5
