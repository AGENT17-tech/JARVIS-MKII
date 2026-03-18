"""
github_sensor.py — JARVIS MKIII GitHub Sensor
Monitors AGENT17-tech commit activity, PRs, and streak.
No auth required for public repos.
"""

import asyncio
import httpx
from datetime import datetime, timezone, timedelta

GITHUB_USER = "AGENT17-tech"
HEADERS     = {
    "Accept":     "application/vnd.github+json",
    "User-Agent": "JARVIS-MKIII",
}


class GitHubSensor:
    def __init__(self):
        print("[GITHUB SENSOR] Initialized.")

    async def read(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get repos sorted by push date
                r = await client.get(
                    f"https://api.github.com/users/{GITHUB_USER}/repos"
                    f"?per_page=10&sort=pushed",
                    headers=HEADERS
                )
                repos = r.json()

                if not isinstance(repos, list) or not repos:
                    return {}

                # Most recently pushed repo
                latest_repo   = repos[0]["name"]
                pushed_at_str = repos[0].get("pushed_at", "")

                # Calculate days since last commit
                days_since = 99
                last_commit = "unknown"
                if pushed_at_str:
                    pushed_dt  = datetime.fromisoformat(
                        pushed_at_str.replace("Z", "+00:00"))
                    now        = datetime.now(timezone.utc)
                    days_since = (now - pushed_dt).days
                    last_commit = pushed_dt.strftime("%Y-%m-%d %H:%M")

                # Count open PRs across all repos
                open_prs = sum(r.get("open_issues_count", 0) for r in repos[:5])

                return {
                    "github": {
                        "last_commit":  last_commit,
                        "days_since":   days_since,
                        "latest_repo":  latest_repo,
                        "open_prs":     open_prs,
                        "total_repos":  len(repos),
                    }
                }
        except Exception as e:
            print(f"[GITHUB SENSOR] Error: {e}")
            return {}


github_sensor = GitHubSensor()

if __name__ == "__main__":
    async def test():
        print("[TEST] GitHub sensor...")
        result = await github_sensor.read()
        if result:
            gh = result.get("github", {})
            print(f"Last commit:  {gh.get('last_commit', 'unknown')}")
            print(f"Days since:   {gh.get('days_since', 99)}")
            print(f"Latest repo:  {gh.get('latest_repo', '')}")
            print(f"Open PRs:     {gh.get('open_prs', 0)}")
            print("[TEST] GitHub PASS")
        else:
            print("[TEST] GitHub FAIL")
    asyncio.run(test())
