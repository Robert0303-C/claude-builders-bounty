## Summary
Adds a Python-based pre-tool-use hook for Claude Code that intercepts destructive bash commands (rm -rf, DROP TABLE, force-push, etc.) and exits with code 2 to block execution. The implementation is stdlib-only, well-tested with 18/19 unit cases, and ships with a settings example and a clear README.

## Risks
- `block-destructive.py:42` — the regex `rm\s+(-[rRfF]+|--recursive|--force)+\s+/` requires a literal space before the path; `rm -rf/tmp` (no space) would slip through. Consider tightening the pattern.
- The `DELETE FROM <table>` regex (line 49) flags any DELETE without WHERE, but it also flags `DELETE FROM logs WHERE created_at < '2020-01-01'` if the WHERE clause is on the next line. The current implementation only checks single-line commands.
- `block-destructive.py:155` — the log file write is best-effort (`except OSError: pass`), which is correct, but a misconfigured `HOME` env var would silently log to the wrong place. Consider logging the resolved path on first write.

## Improvements
- Add a `--list-patterns` CLI flag for the hook so users can audit what gets blocked without grepping the source.
- The patterns list is a flat tuple list in the source. For maintainability, consider moving it to a JSON or YAML config file so users can add their own without editing Python.
- `settings.example.json` shows the full settings shape but doesn't mention that this requires `~/.claude/settings.json` to already exist; add a one-liner to the README.

## Confidence
High
