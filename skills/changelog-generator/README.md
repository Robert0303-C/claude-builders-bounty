# changelog-generator

Bash script + Claude Code skill that turns a git history into a structured `CHANGELOG.md`, auto-categorized into Added / Changed / Fixed / Removed.

## Install (2 commands)

```bash
# 1. Drop the skill into your project
cp -r skills/changelog-generator .claude/skills/

# 2. (Optional) Make the script executable
chmod +x .claude/skills/changelog-generator/changelog.sh
```

## Use

```bash
# Default: writes ./CHANGELOG.md with everything since the last semver tag
bash .claude/skills/changelog-generator/changelog.sh

# Since a specific tag
bash .claude/skills/changelog-generator/changelog.sh CHANGELOG.md v1.0.0

# Full history (no tag)
bash .claude/skills/changelog-generator/changelog.sh CHANGELOG.md ""
```

## As a Claude Code skill

Once installed at `.claude/skills/changelog-generator/`, you can ask Claude Code:

> "Update the changelog"
> "Generate release notes for v2.0"

Claude Code will run the script, show the diff, and let you review.

## Sample output

```markdown
# Changelog

## Changes since v1.2.0

_Generated on 2026-06-13T15:00:00Z — 47 commits_

### Added
- feat: dark mode toggle

### Changed
- refactor: extract payment client

### Fixed
- fix: race condition in checkout flow
```

## Classification rules

| Section | Match prefix |
|---|---|
| Added | `feat:`, `add:`, `new:`, `introduce:` |
| Changed | `refactor:`, `change:`, `update:`, `improve:`, `perf:`, `chore:`, `build:`, `ci:`, `docs:`, `style:`, `test:` |
| Fixed | `fix:`, `bug:`, `repair:`, `patch:` |
| Removed | `remove:`, `delete:`, `drop:`, `deprecate:` |
| Other | (anything else) |

## Requirements

- `bash` 4+
- `git` in PATH
- Tested on Linux, macOS, WSL

## License

MIT
