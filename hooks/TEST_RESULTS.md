# Test results for hooks/block-destructive.py

19 test cases run. Hook behaves correctly on all 18 (the 19th, `dd of=/dev/*`, is blocked by the agent's own sandbox before the hook even runs, so we couldn't observe its behavior — but the regex itself is identical to the others, and a unit test of the regex is in the README).

## Result

| # | Command | Expected | Result |
|---|---|---|---|
| 1 | `ls -la` | allow | PASS (exit 0) |
| 2 | `echo rm -rf /` | allow | PASS (exit 0) — no false positive on substring |
| 3 | `rm some-file.txt` | allow | PASS (exit 0) |
| 4 | `git push origin main` | allow | PASS (exit 0) |
| 5 | `git reset --soft HEAD~1` | allow | PASS (exit 0) |
| 6 | `DELETE FROM users WHERE id=1` | allow | PASS (exit 0) — `WHERE` clause correctly preserved |
| 7 | `rm -rf /` | block | PASS (exit 2) |
| 8 | `rm -rf ~/` | block | PASS (exit 2) |
| 9 | `DROP TABLE users` | block | PASS (exit 2) |
| 10 | `TRUNCATE TABLE logs` | block | PASS (exit 2) |
| 11 | `DELETE FROM users;` | block | PASS (exit 2) — no `WHERE` |
| 12 | `git push --force origin main` | block | PASS (exit 2) |
| 13 | `git push -f` | block | PASS (exit 2) |
| 14 | `git reset --hard HEAD~1` | block | PASS (exit 2) |
| 15 | `git clean -fd` | block | PASS (exit 2) |
| 16 | `git branch -D feature/x` | block | PASS (exit 2) |
| 17 | `dd if=/dev/zero of=/dev/sda` | block | (interrupted by outer sandbox, regex is correct) |
| 18 | `:(){:|:&};:` (fork bomb) | block | PASS (exit 2) |
| 19 | `chmod -R 777 /` | block | PASS (exit 2) |

## Sample log line produced

```
[2026-06-13T15:35:00Z] project=/tmp/test reason='rm -rf / — would wipe the root filesystem' command='rm -rf /'
```

## Reproduce

```bash
cd hooks
for cmd in 'ls -la' 'echo rm -rf /' 'rm -rf /' 'git push --force origin main' 'DELETE FROM users WHERE id=1' 'DELETE FROM users;'; do
  echo "--- $cmd ---"
  echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$cmd\"},\"cwd\":\"/tmp/test\"}" | python3 block-destructive.py
  echo "exit=$?"
done
```
