#!/usr/bin/env python3
"""claude_pr_review.py — Claude Code sub-agent that reviews a PR diff.

Usage:
    python3 claude_pr_review.py --diff <diff.patch> --meta <meta.json> --output <review.md>

Reads the diff and PR metadata, calls the Anthropic API (claude-sonnet-4-5)
with a structured prompt, and writes a Markdown review with:
  - Summary (2-3 sentences)
  - Risks (list)
  - Improvements (list)
  - Confidence score (Low / Medium / High)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Hard caps to keep token usage predictable on big diffs.
MAX_DIFF_CHARS = 60_000
MAX_FILE_SAMPLES = 25
MAX_RISKS = 8
MAX_IMPROVEMENTS = 8

PROMPT_TEMPLATE = """You are a senior software engineer doing a pull-request review.

# Pull request

Title: {title}
Author: {author}
Base: {base}  ←  Head: {head}
Stats: +{additions} / -{deletions} across {changed_files} file(s)

## PR description

{body}

## Diff (truncated to {diff_chars} chars)

```
{diff}
```

# Your task

Produce a Markdown code review with EXACTLY these four sections, in this order:

## Summary
2-3 sentences describing what the PR does and whether the change is well-scoped.

## Risks
Bullet list (max {max_risks}) of concrete risks. Each bullet must call out:
  - the file/line range
  - the risk in one sentence
  - the suggested mitigation in one sentence

If there are no real risks, write a single bullet: "No material risks identified."

## Improvements
Bullet list (max {max_improvements}) of concrete, actionable improvements. Each bullet must be one sentence.

If there are no improvements, write a single bullet: "No additional improvements suggested."

## Confidence
Exactly one of: `Low`, `Medium`, `High`.

# Rules

- Be specific. Reference filenames, function names, or line ranges from the diff.
- Do NOT invent issues that aren't visible in the diff.
- Do NOT comment on style/formatting (let the linter handle that).
- Do NOT recommend test coverage if the PR is config/docs-only.
- Output ONLY the four `## ` sections, no preamble, no explanation.

# Begin
"""


def truncate_diff(diff: str, max_chars: int) -> str:
    if len(diff) <= max_chars:
        return diff
    # Keep the start (file headers + first context) and end (last hunks)
    head = diff[: max_chars * 2 // 3]
    tail = diff[-(max_chars // 3):]
    return f"{head}\n\n... [truncated {len(diff) - max_chars} chars] ...\n\n{tail}"


def call_claude(prompt: str) -> str:
    """Call the Anthropic Messages API. Returns the model output text.

    Uses the `anthropic` SDK if installed, else raw urllib to avoid the dep.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var is required", file=sys.stderr)
        sys.exit(2)

    model = os.environ.get("CLAUDE_REVIEW_MODEL", "claude-sonnet-4-5")
    max_tokens = int(os.environ.get("CLAUDE_REVIEW_MAX_TOKENS", "1500"))

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        from anthropic import Anthropic  # type: ignore

        client = Anthropic(api_key=api_key)
        msg = client.messages.create(**payload)
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    except ImportError:
        # Fallback: raw urllib call.
        import urllib.request

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
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
        return "".join(b.get("text", "") for b in data.get("content", []))


def validate_review(text: str) -> str:
    """Make sure the review has all four required sections, in order."""
    required = ["## Summary", "## Risks", "## Improvements", "## Confidence"]
    cursor = 0
    for section in required:
        idx = text.find(section, cursor)
        if idx < 0:
            raise ValueError(f"Review missing section: {section}")
        cursor = idx + len(section)

    # Confidence must be Low / Medium / High on its own line.
    conf_match = re.search(
        r"## Confidence\s*\n+\s*(Low|Medium|High)\b",
        text[cursor:],
        re.IGNORECASE,
    )
    if not conf_match:
        raise ValueError("Review missing valid Confidence (Low/Medium/High)")
    return text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--diff", required=True, help="Path to the diff file (unified)")
    p.add_argument("--meta", required=True, help="Path to PR metadata JSON (gh pr view --json ...)")
    p.add_argument("--output", required=True, help="Path to write the Markdown review")
    args = p.parse_args()

    diff = Path(args.diff).read_text(encoding="utf-8", errors="replace")
    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))

    diff_chars = min(len(diff), MAX_DIFF_CHARS)
    prompt = PROMPT_TEMPLATE.format(
        title=meta.get("title", "(no title)"),
        author=(meta.get("author") or {}).get("login", "(unknown)"),
        base=meta.get("baseRefName", "?"),
        head=meta.get("headRefName", "?"),
        additions=meta.get("additions", "?"),
        deletions=meta.get("deletions", "?"),
        changed_files=meta.get("changedFiles", "?"),
        body=(meta.get("body") or "(no description)")[:2000],
        diff=truncate_diff(diff, MAX_DIFF_CHARS),
        diff_chars=diff_chars,
        max_risks=MAX_RISKS,
        max_improvements=MAX_IMPROVEMENTS,
    )

    review = call_claude(prompt)

    try:
        review = validate_review(review)
    except ValueError as e:
        print(f"WARNING: model output failed validation ({e}); writing as-is", file=sys.stderr)
        # Still write so the user can see what came back, but mark it invalid
        review = f"<!-- REVIEW VALIDATION FAILED: {e} -->\n\n" + review

    Path(args.output).write_text(review, encoding="utf-8")
    print(f"Wrote {args.output} ({len(review)} chars)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
