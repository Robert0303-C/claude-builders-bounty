---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history, auto-categorized by Conventional Commits style prefixes.
allowed-tools: Bash
---

# Changelog Generator

Generates a structured `CHANGELOG.md` from your repo's git history, auto-categorizing commits into Added / Changed / Fixed / Removed.

## When to use

- After a release, when preparing release notes
- When `CHANGELOG.md` is missing or out of date
- When the user says "generate changelog", "update changelog", "release notes"

## How to use

Run the script from the project root:

```bash
bash .claude/skills/changelog-generator/changelog.sh [output_file] [since_tag]
```

- `output_file` — defaults to `CHANGELOG.md` in the current directory
- `since_tag` — defaults to the most recent semver tag (e.g. `v1.2.3`); pass any tag or omit to dump the full history

The script reads commits with `git log` (excludes merges), classifies by leading keyword, and writes a Markdown file with a header, generation timestamp, and the four standard sections.

## Classification rules

- **Added** — `feat:`, `add:`, `new:`, `introduce:`
- **Changed** — `refactor:`, `change:`, `update:`, `improve:`, `perf:`, `chore:`, `build:`, `ci:`, `docs:`, `style:`, `test:`
- **Fixed** — `fix:`, `bug:`, `repair:`, `patch:`
- **Removed** — `remove:`, `delete:`, `drop:`, `deprecate:`
- **Other** — anything that doesn't match; surfaced at the bottom so you can edit by hand

## Requirements

- `bash` 4+ (uses `mapfile` and arrays)
- `git` in `$PATH`
- A git repository (script exits with a clear error if not in one)

## Notes

- Pure bash, no external dependencies
- Excludes merge commits to keep the log clean
- Works in any repo, regardless of language
