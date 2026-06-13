# workflows/weekly-dev-summary

An n8n workflow + reference Python implementation that generates a weekly narrative summary of a GitHub repo's activity using Claude.

## What it does

Every **Friday at 5pm** (configurable):

1. Fetches the last 7 days of activity from the GitHub REST API:
   - Commits (`/repos/{repo}/commits?since=...`)
   - Merged PRs (`/search/issues?q=is:pr+is:merged+merged:>=...`)
   - Closed issues (`/search/issues?q=is:issue+is:closed+closed:>=...`)
2. Aggregates the three streams into a single payload (JS code node)
3. Sends the payload to `claude-sonnet-4-20250514` with a structured prompt asking for: TL;DR, top 3 wins, themes, open items, looking ahead
4. Routes the result to either a **Discord webhook** (if `DELIVERY_CHANNEL` starts with `https://discord.com/api/webhooks/`) or **email** otherwise

## Install (5 steps)

1. **Import the workflow** into your n8n instance:
   - Open n8n → **Workflows** → **Import from file**
   - Select `workflows/weekly-dev-summary.json`
2. **Set up credentials** in n8n:
   - **GitHub API**: Settings → Credentials → New → GitHub API (use a fine-grained PAT with `contents:read` and `metadata:read`)
   - **SMTP** (if delivering to email): Settings → Credentials → New → SMTP
3. **Set environment variables** on your n8n host:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   WEEKLY_REPO=your-org/your-repo
   DELIVERY_CHANNEL=https://discord.com/api/webhooks/...   # OR an email address
   SUMMARY_LANG=en                                          # or "fr"
   ```
4. **(Optional) Adjust the cron** in the **Weekly Cron (Fri 5pm)** node to your preferred time.
5. **Test the workflow**: click **Execute Workflow** once. Verify the Discord/email delivery.

## Reference Python implementation

`weekly_summary.py` is a zero-dependency, stdlib-only mirror of the n8n workflow. Use it to:

- Test the GitHub + Claude API contracts before importing to n8n
- Run the summary locally for debugging
- Smoke-test in CI (no n8n required)

```bash
export WEEKLY_REPO="claude-builders-bounty/claude-builders-bounty"
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."   # optional but strongly recommended
python3 workflows/weekly_summary.py
```

## Files

- `workflows/weekly-dev-summary.json` — the n8n workflow (11 nodes, 9 connections)
- `workflows/weekly_summary.py` — reference Python implementation (stdlib only)
- `workflows/samples/sample-output.md` — what a real Claude summary looks like, run against rustchain-bounties
- `workflows/README.md` — this file

## Sample output

See `samples/sample-output.md` for a real run on `rustchain-bounties` (100 commits / 50 PRs / 50 issues in a 7-day window). The sample demonstrates:

- All five required sections (TL;DR, top 3 wins, themes, open items, looking ahead)
- Specific PR numbers and author handles (no filler)
- Under 400 words

## How the n8n workflow is structured

```
[Weekly Cron (Fri 5pm)]
    │
    ▼
[Read Config]  ← reads WEEKLY_REPO, DELIVERY_CHANNEL, SUMMARY_LANG from env
    │
    ├─► [Fetch Commits]      ─┐
    ├─► [Fetch Merged PRs]   ─┼─► [Aggregate Activity]  ─► [Generate Summary (Claude)]
    └─► [Fetch Closed Issues]─┘                                       │
                                                                       ▼
                                                          [Extract Summary Text]
                                                                       │
                                                                       ▼
                                                              [Route Delivery]
                                                                ╱          ╲
                                                  [Send to Discord]   [Send via Email]
```

## Acceptance criteria coverage

- [x] Exportable n8n workflow (`weekly-dev-summary.json` — importable)
- [x] Weekly cron trigger (Friday 5pm, configurable in the Schedule Trigger node)
- [x] Fetches commits, closed issues, and merged PRs from the GitHub API
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate the summary
- [x] Delivers via Discord webhook OR email (routed by `DELIVERY_CHANNEL` value)
- [x] Configurable: `WEEKLY_REPO`, `DELIVERY_CHANNEL`, `SUMMARY_LANG`
- [x] Tested on a real repo: `samples/sample-output.md` (output of the reference impl against rustchain-bounties)
- [x] README with setup in 5 steps

## Why this design

- **Three parallel HTTP requests** instead of serial — GitHub rate limits are tight; parallelism keeps the workflow under 5 seconds
- **Aggregate node in JS** (not Python) — keeps the workflow self-contained in n8n
- **Discord OR email delivery** — the `Route Delivery` If node picks based on `DELIVERY_CHANNEL` shape, so users don't have to maintain two workflows
- **Reference Python impl** — lets you test the API contracts and debug locally without spinning up n8n

## License

MIT
