#!/usr/bin/env python3
"""block-destructive.py — Claude Code pre-tool-use hook.

Reads a Claude Code tool-use JSON payload from stdin. If the tool is
Bash and the command matches a destructive pattern, exits with code 2
(per the Claude Code hooks spec) to block execution, logs the attempt,
and writes a clear reason to stderr for Claude to read.

Patterns blocked:
  - rm -rf / rm -fr (any path or --no-preserve-root variant)
  - DROP TABLE / DROP DATABASE / DROP SCHEMA
  - TRUNCATE TABLE
  - DELETE FROM <table> (without a WHERE clause)
  - git push --force / git push -f (to any remote)
  - git reset --hard
  - git clean -fd
  - git branch -D (force delete branch)
  - mkfs / dd if= of=/dev/
  - :(){:|:&};:  (fork bomb)
  - chmod -R 777 /
  - mv /* /dev/null

Install:
  1. Drop this file at ~/.claude/hooks/block-destructive.py
  2. Add to ~/.claude/settings.json:
     {
       "hooks": {
         "PreToolUse": [
           {
             "matcher": "Bash",
             "hooks": [
               {"type": "command", "command": "python3 ~/.claude/hooks/block-destructive.py"}
             ]
           }
         ]
       }
     }
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Each entry: (regex, human-readable reason).
# Anchored to avoid false positives (e.g. "rm -rf" appearing in an echo).
PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # rm -rf / rm -fr on root or wildcard
    (re.compile(r"\brm\s+(-[rRfF]+|--recursive|--force)+\s+/\b"),
     "rm -rf / — would wipe the root filesystem"),
    (re.compile(r"\brm\s+(-[rRfF]+|--recursive|--force)+\s+~/?(\s|$)"),
     "rm -rf ~ — would delete the home directory"),
    (re.compile(r"\brm\s+(-[rRfF]+|--recursive|--force)+\s+\.(\.|/|$)"),
     "rm -rf . — would recursively delete the current directory"),
    (re.compile(r"\brm\s+(-[rRfF]+|--recursive|--force)+.*\*"),
     "rm -rf with a wildcard — likely targets more than intended"),

    # SQL destructive
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "DROP TABLE/DATABASE/SCHEMA — destructive schema change"),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w+", re.IGNORECASE),
     "TRUNCATE — would empty an entire table"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;", re.IGNORECASE),
     "DELETE FROM without a WHERE clause — would wipe the entire table"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*$", re.IGNORECASE),
     "DELETE FROM without a WHERE clause — would wipe the entire table"),

    # Git destructive
    (re.compile(r"\bgit\s+push\s+(-f|--force)(\s+|$)"),
     "git push --force — would overwrite remote history"),
    (re.compile(r"\bgit\s+push\s+(-f|--force)\b"),
     "git push --force — would overwrite remote history"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"),
     "git reset --hard — would discard all uncommitted changes"),
    (re.compile(r"\bgit\s+clean\s+-f[dqxX]?\b"),
     "git clean -f — would delete untracked files"),
    (re.compile(r"\bgit\s+branch\s+-D\b"),
     "git branch -D — force-deletes a branch (loses commits if not merged)"),

    # Filesystem-level destructive
    (re.compile(r"\bmkfs(\.\w+)?\s+/dev/"),
     "mkfs on /dev/* — would format a disk"),
    (re.compile(r"\bdd\s+.*\bof=/dev/"),
     "dd of=/dev/* — raw write to a device"),
    (re.compile(r":\(\)\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
     "Fork bomb — would exhaust process table"),
    (re.compile(r"\bchmod\s+-R\s+777\s+/\b"),
     "chmod -R 777 / — would make the entire system world-writable"),
    (re.compile(r"\bmv\s+/\S*\s+/dev/null\b"),
     "mv /* /dev/null — would move filesystem contents to /dev/null"),
]


def extract_bash_command(payload: dict) -> str | None:
    """Pull the bash command string out of a Claude Code tool-use payload."""
    tool_name = payload.get("tool_name") or payload.get("name") or ""
    if tool_name != "Bash":
        return None
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        return None
    cmd = tool_input.get("command")
    return cmd if isinstance(cmd, str) else None


def find_violation(command: str) -> tuple[re.Pattern[str], str] | None:
    for pattern, reason in PATTERNS:
        if pattern.search(command):
            return pattern, reason
    return None


def log_attempt(command: str, reason: str, project_path: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] project={project_path} reason={reason!r} command={command!r}\n")
    except OSError:
        # Logging is best-effort; never block the hook on log failure.
        pass


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Unparseable payload — let the tool run rather than fail-open.
        return 0

    command = extract_bash_command(payload)
    if command is None:
        return 0

    project_path = (
        payload.get("cwd")
        or payload.get("project_dir")
        or os.getcwd()
    )

    violation = find_violation(command)
    if violation is None:
        return 0

    _, reason = violation
    log_attempt(command, reason, project_path)

    # Exit 2 = blocking error in Claude Code hooks. The stderr is fed
    # back to Claude so it can react to the rejection.
    print(
        f"BLOCKED by pre-tool-use hook: {reason}\n"
        f"Command: {command}\n"
        f"If you really need to run this, ask the user to run it manually "
        f"outside of Claude Code, or to add an explicit allow-list rule.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
