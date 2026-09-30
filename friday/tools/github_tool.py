"""
Friday — GitHub Tool
Fetches Tanish's public GitHub profile and repository data using PyGithub.

PyGithub is synchronous — all blocking calls run via asyncio.to_thread
so the agent event loop never stalls audio/VAD/TTS.
"""
import asyncio
import base64

from github import Github
from friday.config import get_settings

settings = get_settings()

def _get_client():
    """Return an authenticated GitHub client."""
    if settings.github_token:
        return Github(settings.github_token)
    return Github()


# ── Sync implementations (run inside worker threads) ─────────────────────────
def _get_all_repositories_sync() -> list[str]:
    g = _get_client()
    user = g.get_user(settings.github_username)
    return [repo.name for repo in user.get_repos()]


def _get_repo_details_sync(repo_name: str) -> str:
    g = _get_client()
    try:
        repo = g.get_repo(f"{settings.github_username}/{repo_name}")

        details = [
            f"Repository: {repo.name}",
            f"Description: {repo.description or 'No description'}",
            f"Primary Language: {repo.language or 'Unknown'}",
            f"Stars: {repo.stargazers_count}",
            f"Forks: {repo.forks_count}",
            f"Open Issues: {repo.open_issues_count}",
            f"Created at: {repo.created_at.strftime('%Y-%m-%d')}",
            f"Last Updated: {repo.updated_at.strftime('%Y-%m-%d')}"
        ]

        # Try to get a snippet of the README
        try:
            readme = repo.get_readme()
            content = base64.b64decode(readme.content).decode('utf-8')
            # Take the first 300 characters for a voice-friendly summary
            summary = content[:300].replace('\n', ' ').strip()
            details.append(f"README Summary: {summary}...")
        except Exception:
            details.append("README: Not available or empty.")

        return "\n".join(details)
    except Exception as e:
        return f"Error fetching details for {repo_name}: {str(e)}"


def _get_recent_activity_sync(repo_name: str) -> str:
    g = _get_client()
    try:
        repo = g.get_repo(f"{settings.github_username}/{repo_name}")
        issues = repo.get_issues(state='open')

        if issues.totalCount == 0:
            return f"There are no open issues or pull requests in {repo_name}."

        activity = [f"Recent open items in {repo_name}:"]
        for i in issues[:5]:
            type_label = "PR" if i.pull_request else "Issue"
            activity.append(f"- {type_label} #{i.number}: {i.title}")

        return "\n".join(activity)
    except Exception as e:
        return f"Error fetching activity for {repo_name}: {str(e)}"


def _get_github_summary_sync() -> str:
    g = _get_client()
    try:
        user = g.get_user(settings.github_username)
        repos = user.get_repos(sort='updated', direction='desc')

        repo_names = [r.name for r in repos[:5]]
        return (
            f"Tanish's GitHub profile has {user.public_repos} public repositories "
            f"and {user.followers} followers. "
            f"His most recently updated projects are: {', '.join(repo_names)}. "
            f"I can provide more details on any of these if you'd like."
        )
    except Exception:
        return f"I'm having trouble connecting to GitHub right now, but you can check out his work at github.com/{settings.github_username}."


# ── Async public API (non-blocking) ──────────────────────────────────────────
async def get_all_repositories() -> list[str]:
    """Fetch a list of all public repository names for Tanish."""
    return await asyncio.to_thread(_get_all_repositories_sync)


async def get_repo_details(repo_name: str) -> str:
    """Fetch detailed info about a specific repository, including its README."""
    return await asyncio.to_thread(_get_repo_details_sync, repo_name)


async def get_recent_activity(repo_name: str) -> str:
    """Fetch recent issues and pull requests for a specific repo."""
    return await asyncio.to_thread(_get_recent_activity_sync, repo_name)


async def get_github_summary() -> str:
    """Returns a high-level voice-friendly summary of Tanish's GitHub."""
    return await asyncio.to_thread(_get_github_summary_sync)
