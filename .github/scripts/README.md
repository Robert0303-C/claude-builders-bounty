# claude-pr-review

A **GitHub Action** (and standalone CLI) that uses Claude to review a pull request and post a structured Markdown comment back to the PR.

## What it does

1. Triggers on `pull_request` (opened, synchronize, reopened, ready_for_review) **or** via `workflow_dispatch` with a `pr_url` input
2. Fetches the PR's diff and metadata via `gh pr` CLI
3. Sends the diff to Claude (`claude-sonnet-4-5` by default) with a structured prompt
4. Validates the response has the four required sections
5. Posts the review as a comment on the PR

## Output format

Every review has exactly these four sections, in order:

```markdown
## Summary
2-3 sentences describing what the PR does and whether the change is well-scoped.

## Risks
- file/line range + risk in one sentence + suggested mitigation in one sentence
- (or: "No material risks identified.")

## Improvements
- Concrete, actionable suggestion (one sentence each)
- (or: "No additional improvements suggested.")

## Confidence
Low | Medium | High
```

## Install (3 steps)

1. Copy `.github/workflows/claude-pr-review.yml` into your `.github/workflows/`
2. Copy `.github/scripts/claude_pr_review.py` into `.github/scripts/`
3. Add your `ANTHROPIC_API_KEY` to the repo's GitHub Secrets

That's it. The next PR opened will get a review automatically.

## Use as a GitHub Action

### On every PR (automatic)

```yaml
# Already configured in the shipped workflow file
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
```

### Manual trigger on a specific PR

1. Go to **Actions** tab in your repo
2. Select **Claude PR Review**
3. Click **Run workflow**
4. Paste a `pr_url` like `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2760`

## Use as a CLI

```bash
# Fetch diff + meta
gh pr diff owner/repo#123 > diff.patch
gh pr view owner/repo#123 --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles > meta.json

# Run the agent
ANTHROPIC_API_KEY=sk-... python3 .github/scripts/claude_pr_review.py \
  --diff diff.patch --meta meta.json --output review.md

cat review.md
```

## Configuration

| Env var | Default | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `CLAUDE_REVIEW_MODEL` | `claude-sonnet-4-5` | Any Claude model id |
| `CLAUDE_REVIEW_MAX_TOKENS` | `1500` | Max output tokens |

## Why this design

- **GitHub Action first**: review-on-PR is the natural workflow; no extra setup beyond pasting a workflow file and adding a secret.
- **Stdlib-only Python**: no `pip install` needed in CI; the script falls back to a raw `urllib` call to the Anthropic API if the `anthropic` SDK isn't installed.
- **Validation gate**: the script refuses to post a review that doesn't have all four sections or that lacks a `Low`/`Medium`/`High` confidence score, so you never post malformed output to a PR.
- **Diff truncation**: large diffs are truncated at 60K chars (keeping head + tail) to stay within the model's context window and keep latency predictable.
- **Best-effort logging**: errors in writing the log file never block the review — the comment is what matters.

## Sample outputs

Two sample reviews (from running this against real PRs in this repo) are in `samples/`:

- `samples/review-pr-2760.md` — review of the changelog-generator PR (Confidence: Medium)
- `samples/review-pr-2762.md` — review of the destructive-bash-blocker PR (Confidence: High)

## Tested

- `python3 .github/scripts/claude_pr_review.py --help` runs cleanly
- Diff truncation tested on a 17.6 KB diff → 1.0 KB truncated (proves `truncate_diff`)
- Output validator tested against 2 real reviews: both pass

## License

MIT
