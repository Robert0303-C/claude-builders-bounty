#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file] [since_tag]
#   output_file  default: CHANGELOG.md
#   since_tag    default: last semver tag, or all commits if none

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
SINCE_TAG="${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}"

if [ -n "$SINCE_TAG" ]; then
  RANGE="${SINCE_TAG}..HEAD"
  RANGE_LABEL="Changes since ${SINCE_TAG}"
else
  RANGE=""
  RANGE_LABEL="Full history"
fi

# Collect commits
if [ -n "$RANGE" ]; then
  mapfile -t COMMITS < <(git log "${RANGE}" --pretty=format:"%s" --no-merges 2>/dev/null || true)
else
  mapfile -t COMMITS < <(git log --pretty=format:"%s" --no-merges 2>/dev/null || true)
fi

if [ ${#COMMITS[@]} -eq 0 ]; then
  echo "No commits found${SINCE_TAG:+ since $SINCE_TAG}. Nothing to write." >&2
  exit 1
fi

# Categorize
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

for msg in "${COMMITS[@]}"; do
  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat*|add*|new*|introduce*)                  ADDED+=("$msg") ;;
    fix*|bug*|repair*|patch*)                    FIXED+=("$msg") ;;
    remove*|delete*|drop*|deprecate*)            REMOVED+=("$msg") ;;
    refactor*|change*|update*|improve*|perf*|chore*|build*|ci*|docs*|style*|test*) CHANGED+=("$msg") ;;
    *)                                           OTHER+=("$msg") ;;
  esac
done

# Build markdown
{
  echo "# Changelog"
  echo ""
  echo "## ${RANGE_LABEL}"
  echo ""
  echo "_Generated on $(date -u +%Y-%m-%dT%H:%M:%SZ) — $(printf '%d' "${#COMMITS[@]}") commits_"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for m in "${ADDED[@]}"; do echo "- ${m}"; done
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for m in "${CHANGED[@]}"; do echo "- ${m}"; done
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for m in "${FIXED[@]}"; do echo "- ${m}"; done
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for m in "${REMOVED[@]}"; do
      echo "- ${m}"
    done
    echo ""
  fi

  if [ ${#OTHER[@]} -gt 0 ]; then
    echo "### Other"
    for m in "${OTHER[@]}"; do echo "- ${m}"; done
    echo ""
  fi
} > "$OUTPUT"

echo "Wrote ${OUTPUT} with $(printf '%d' "${#COMMITS[@]}") commits from ${RANGE:-full history}." >&2
