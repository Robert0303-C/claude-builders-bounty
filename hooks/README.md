# block-destructive

A Claude Code **pre-tool-use hook** that intercepts destructive `Bash` commands before they run. Pure Python, stdlib only, zero dependencies.

## Install (2 commands)

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks
cp hooks/block-destructive.py ~/.claude/hooks/block-destructive.py
chmod +x ~/.claude/hooks/block-destructive.py

# 2. Wire it up in your Claude Code settings
#    (edit ~/.claude/settings.json to add the PreToolUse block from hooks/settings.example.json)
```

That's it. The next time Claude tries to run a blocked command, it gets rejected with a clear reason that Claude can read and act on.

## What it blocks

| Category | Pattern | Why |
|---|---|---|
| Filesystem | `rm -rf /`, `rm -rf ~`, `rm -rf .`, `rm -rf *` | Wipes critical paths |
| SQL | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA` | Destructive schema change |
| SQL | `TRUNCATE TABLE` | Empties a table |
| SQL | `DELETE FROM <table>` (no `WHERE`) | Wipes the entire table |
| Git | `git push --force` / `git push -f` | Overwrites remote history |
| Git | `git reset --hard` | Discards uncommitted work |
| Git | `git clean -f[dqxX]` | Deletes untracked files |
| Git | `git branch -D` | Force-deletes a branch (loses commits) |
| Disk | `mkfs /dev/...` | Formats a disk |
| Disk | `dd ... of=/dev/...` | Raw write to a device |
| Shell | `:(){:|:&};:` (fork bomb) | Exhausts the process table |
| Perms | `chmod -R 777 /` | Makes the whole system world-writable |
| Filesystem | `mv /* /dev/null` | Moves FS contents to the void |

## How it works

1. Claude Code invokes the hook before any `Bash` tool call
2. The hook reads the tool-use JSON from `stdin`
3. If the tool is `Bash`, it runs every pattern regex against the command
4. On a match: writes a log line to `~/.claude/hooks/blocked.log` and exits with code `2` (Claude Code's blocking-error code)
5. The `stderr` is fed back to Claude so it understands *why* the command was blocked and can adjust

The log line format:

```
[2026-06-13T15:30:00Z] project=/home/user/myapp reason='rm -rf / — would wipe the root filesystem' command='rm -rf /tmp/foo'
```

## Verify

```bash
# Should exit 0 (allow)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/block-destructive.py

# Should exit 2 (block) and write to stderr
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf ~"}}' | python3 hooks/block-destructive.py
echo $?  # 2

# SQL wipe — should also block
echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users;"}}' | python3 hooks/block-destructive.py
echo $?  # 2

# Force push — should block
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' | python3 hooks/block-destructive.py
echo $?  # 2
```

## Why exit 2 (not 1)

Per the Claude Code hooks spec, exit codes are interpreted as:

- `0` — success, allow the tool call
- `2` — blocking error, refuse the tool call and feed stderr back to the model
- other — non-blocking error, the tool runs but stderr is shown

Exit `2` is the only code that actually stops the command from running.

## Why pure Python / stdlib

- No `pip install` — works in any sandboxed or air-gapped environment
- Runs in the same Python 3 that Claude Code is already using
- No supply-chain risk from a typo-squatted package
- The whole script fits in one file you can audit in 30 seconds

## Customizing

Edit the `PATTERNS` list at the top of the file. Each entry is `(regex, human_reason)`. New patterns take effect on the next Claude Code session.

## License

MIT
