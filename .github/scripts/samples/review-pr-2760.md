## Summary
Adds a pure-bash changelog generator under `skills/changelog-generator/`, with a SKILL.md manifest, a 2-command install README, and a 200-commit sample output. The change is well-scoped and self-contained.

## Risks
- `changelog.sh` uses `mapfile` (bash 4+); macOS users on the default bash 3.2 will hit a syntax error — recommend adding a `#!/usr/bin/env bash` shebang check or falling back to `read -a` for portability.
- `changelog.sh:73` — the in-script `echo "Wrote..."` line uses `${#COMMITS[@]}` which is fine, but the `printf '%d'` wrapper is redundant and may confuse a linter.
- The "Other" bucket is unfiltered — if maintainers use a non-conventional commit style, every commit lands there, defeating the auto-categorization. Consider adding a `Bump`/`Bumped` prefix as a Changed match.

## Improvements
- Add a `--help` flag that prints usage and exits, since the script is positioned as a standalone tool.
- Consider a `--dry-run` flag that prints the would-be CHANGELOG to stdout without writing the file, useful in pre-commit hooks.
- The sample output in `sample-output.md` is 214 lines from 200 commits — it would be more useful to keep only the most recent ~30 commits and add a "Full history" link.

## Confidence
Medium
