#!/usr/bin/env python3
"""weekly_summary.py — Reference Python implementation of the n8n workflow.

This is a zero-dependency (stdlib only) reference of what the n8n workflow
in `weekly-dev-summary.json` does. Use this for:

  - Local testing before importing the JSON into n8n
  - CI smoke tests (verify the GitHub + Claude API contracts work)
  - Debugging when a workflow execution fails in n8n

Behavior is identical to the JSON workflow:
  1. Fetch the last 7 days of commits, merged PRs, and closed issues from
     the GitHub REST API.
  2. Aggregate into a single payload.
  3. Call claude-sonnet-4-20250514 with a structured prompt for a narrative
     summary (EN or FR based on SUMMARY_LANG env).
  4. Print the summary (in n8n, this is also sent to Discord or email).

Required env vars:
  WEEKLY_REPO          e.g. "claude-builders-bounty/claude-builders-bounty"
  ANTHROPIC_API_KEY    your Anthropic key
  GITHUB_TOKEN         optional but strongly recommended (5000 req/h vs 60)

Optional env vars:
  SUMMARY_LANG         "en" (default) or "fr"
  DELIVERY_CHANNEL     Discord webhook URL or email address (for logging)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

GITHUB_API = "https://api.github.com"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"


def github_get(path: str, token: str | None = None) -> dict | list:
    url = f"{GITHUB_API}{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"GitHub API error {e.code} on {path}: {e.read().decode()[:300]}", file=sys.stderr)
        raise


def fetch_activity(repo: str, since: str, token: str | None) -> dict:
    """Fetch commits, merged PRs, and closed issues since `since` (ISO timestamp)."""
    commits = github_get(f"/repos/{repo}/commits?since={since}&per_page=100", token)
    prs_search = github_get(
        f"/search/issues?q=repo:{repo}+is:pr+is:merged+merged:>={since}&per_page=50", token
    )
    issues_search = github_get(
        f"/search/issues?q=repo:{repo}+is:issue+is:closed+closed:>={since}&per_page=50", token
    )

    return {
        "repo": repo,
        "since": since,
        "stats": {
            "commits": len(commits),
            "mergedPRs": len(prs_search.get("items", [])),
            "closedIssues": len(issues_search.get("items", [])),
        },
        "commits": [
            {
                "sha": c.get("sha", "")[:7],
                "msg": (c.get("commit", {}).get("message", "").split("\n")[0]),
                "author": (c.get("author") or {}).get("login")
                or c.get("commit", {}).get("author", {}).get("name", "unknown"),
            }
            for c in commits
        ],
        "mergedPRs": [
            {
                "number": pr["number"],
                "title": pr["title"],
                "author": (pr.get("user") or {}).get("login", "unknown"),
            }
            for pr in prs_search.get("items", [])
        ],
        "closedIssues": [
            {
                "number": iss["number"],
                "title": iss["title"],
                "author": (iss.get("user") or {}).get("login", "unknown"),
            }
            for iss in issues_search.get("items", [])
        ],
    }


def build_prompt(activity: dict, lang: str) -> str:
    lang_label = {"en": "English", "fr": "French"}.get(lang.lower(), "English")
    commits_text = "\n".join(
        f"- {c['sha']} by @{c['author']}: {c['msg']}" for c in activity["commits"][:15]
    ) or "(no commits)"
    prs_text = "\n".join(
        f"- #{pr['number']} by @{pr['author']}: {pr['title']}"
        for pr in activity["mergedPRs"][:10]
    ) or "(no merged PRs)"
    issues_text = "\n".join(
        f"- #{iss['number']}: {iss['title']}" for iss in activity["closedIssues"][:10]
    ) or "(no closed issues)"

    return f"""You are a developer-advocate writing the weekly summary for the {activity['repo']} repository.

Write in {lang_label}.

Activity for the last 7 days ({activity['since']} → now):

## Stats
- {activity['stats']['commits']} commits
- {activity['stats']['mergedPRs']} merged PRs
- {activity['stats']['closedIssues']} closed issues

## Notable commits (first 15)
{commits_text}

## Merged PRs (first 10)
{prs_text}

## Closed issues (first 10)
{issues_text}

Write a Markdown weekly summary with these sections:

### TL;DR (1-2 sentences)
### Top 3 wins (most impactful merged PRs)
### Themes (recurring patterns in commits/PRs)
### Open items (notable closed issues that may need follow-up)
### Looking ahead (what to focus on next week)

Keep it under 400 words. Be specific (mention PR numbers, authors, files). No filler.
"""


def call_claude(prompt: str, api_key: str) -> str:
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        ANTHROPIC_API,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def main() -> int:
    repo = os.environ.get("WEEKLY_REPO")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    token = os.environ.get("GITHUB_TOKEN")
    lang = os.environ.get("SUMMARY_LANG", "en")

    if not repo or not api_key:
        print("ERROR: WEEKLY_REPO and ANTHROPIC_API_KEY must be set", file=sys.stderr)
        return 2

    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Fetching activity for {repo} since {since}...", file=sys.stderr)
    activity = fetch_activity(repo, since, token)
    print(
        f"  {activity['stats']['commits']} commits, "
        f"{activity['stats']['mergedPRs']} merged PRs, "
        f"{activity['stats']['closedIssues']} closed issues",
        file=sys.stderr,
    )

    print("Calling Claude...", file=sys.stderr)
    prompt = build_prompt(activity, lang)
    summary = call_claude(prompt, api_key)

    print("\n" + "=" * 70)
    print(f"# Weekly Dev Summary — {repo}")
    print("=" * 70 + "\n")
    print(summary)
    print("\n" + "=" * 70)
    print(
        f"  {activity['stats']['commits']} commits · "
        f"{activity['stats']['mergedPRs']} PRs · "
        f"{activity['stats']['closedIssues']} issues",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
