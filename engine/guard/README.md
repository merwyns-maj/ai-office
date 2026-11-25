# prod guard (T-040)

A Claude Code PreToolUse hook that blocks agent writes to production. One stdlib-only Python file plus a JSON config. It covers the `Bash` tool and MCP tools (`mcp__*`). It is default-deny for anything that names prod, and fail-closed on every error.

**Installing is not done here.** This folder builds and tests the guard using fixtures only. Putting it in `~/.claude`, nimbus, klik-workspace or any other repo is a write outside this repo and a Merwyn human gate.

## Files

| File | What |
|---|---|
| `prod_guard.py` | The hook. Reads the hook JSON on stdin. Exit 0 allows (no output); exit 2 blocks (one line on stderr). No other exit codes. |
| `prod_guard.example.json` | Starter config: tool-name patterns, `.invalid` placeholders, one placeholder allowlist entry. No real host or credential. |

Tests: `tests/test_prod_guard.py` with fixtures in `tests/fixtures/guard/`.

## Run the tests

From the repo root (runs every test in the repo, including `engine/runtime`):

```
python -m unittest -v
```

The output lists each case as `test_block_...`, `test_allow_...`, `test_malformed_...`. No test makes a network call.

## What it does

Decision order (first match wins):

1. Input is not a JSON object, has no `tool_name`, or Bash has no string `command` → block `malformed-input`.
2. `kubectl get|describe|edit` of `secret(s)` in Bash (matched across newlines), or any `__kubectl_` MCP tool whose name or any argument value mentions `secret(s)` → block `k8s-secret-read`, in every context. This rule is in code, not config.
3. The call does not name prod (no `bash.prod_targets` / `mcp.prod_tools` match) → allow.
4. Bash command matches an allowlist entry (and is eligible, below) → allow.
5. Write rule or SQL write keyword → block with the rule id (`bash-kubectl-write`, `sql-write:DELETE`, `mcp-pg-write`, ...).
6. Read-only command or tool → allow. Anything else → block `default-deny`.

MCP SQL (fields in `mcp.sql_fields`: `sql`, `query`, `statement`) is classified in code: more than one statement, any write or DDL keyword, `SELECT ... INTO`, `FOR UPDATE`, `nextval(`, `EXPLAIN ANALYZE` and similar are blocked; false positives block by design.

Allowlist entries are for submitting a Bytebase change issue only. A command can never match the allowlist if it contains `;` `&` `|` a backtick `$(` `>` `<` a newline, `..`, or the whole word `apply`, `rollout`, `approve`, `deploy`, `execute` or `run-now`. `load_config` rejects any entry whose `action` is not exactly `"submit-change-issue"`. Every entry added to the allowlist needs human review.

stderr is one line built only from the rule id, the sanitised tool name and a fixed reason. It never contains the command or SQL (a WHERE clause can hold a NIK).

Config lookup: `--config PATH`, then env `PROD_GUARD_CONFIG`, then `prod_guard.json` next to the script. A missing or invalid config blocks every call (`rule=config-error`). Check a config with `python3 prod_guard.py --check-config --config PATH`.

## What this guard does not do

- **It does not gate reads.** Allowed reads of prod (SELECT, `kubectl get/logs`, `pg_execute_query`) return real personal data (borrower, lender, NIK) into the agent's context and transcript. Agent read access to prod needs Merwyn's and legal's approval (UU PDP). Installing this guard does not grant it.
- **It is a safety net against agent mistakes, not a security boundary.** A determined or confused agent can get around it.
- Known limits:
  - Prod access that is not named with `-prod__` or a configured pattern: new MCP server names, aliases, env vars, a script file that calls psql, base64 into sh, a default kube context that is prod.
  - `kubectl` aliases (for example `k`) are not covered.
  - A `SELECT` that calls a mutating function (for example `SELECT my_cleanup_fn()`) cannot be seen by the classifier.
  - Write or Edit by the agent could weaken `~/.claude/hooks/prod_guard.json` or `settings.json`. At install, protect them with file permissions (not writable by the agent's user) or Claude Code managed settings.
  - A hook timeout is non-blocking unless `onFailure: "block"` is set (see below); there is no internal deadline on Windows (no `SIGALRM`).
  - If Claude Code's own runner fails before the shell starts, the wrapper cannot help.
  - MCP SQL field names are assumed (`sql`, `query`, `statement`); an unrecognised field blocks.
  - Prod-targeted Bash commands are also scanned for SQL write words, so words like `cluster`, `set` or `do` in such a command block it (false positive, fails closed).
  - Every allowlist entry needs human review.
- The real control is a read-only DB role (and a scoped kube role) for agent sessions. That is Merwyn's decision and a human gate, not part of this task.

## Settings snippet (for an install task; not applied here)

User-level `~/.claude/settings.json`, because MCP servers are session-wide:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash|mcp__.*",
  "hooks": [{"type": "command", "timeout": 10, "onFailure": "block",
    "command": "python3 ~/.claude/hooks/prod_guard.py --config ~/.claude/hooks/prod_guard.json || exit 2"}]}]}}
```

Why each part (contract verified against https://code.claude.com/docs/en/hooks on 25 Nov 2026): exit 2 blocks and stderr is shown as the reason; any other non-zero exit is non-blocking, so `|| exit 2` turns a missing `python3` (127), a syntax error (1) or a kill by signal into a block. A timed-out PreToolUse hook does not block unless `"onFailure": "block"` is set (Claude Code v2.1.295+). `timeout` is in seconds; the guard's internal 5 s deadline sits below it.

## Install steps for a company repo (Merwyn gate)

1. Get Merwyn's go-ahead for the target (user settings, nimbus, klik-workspace).
2. Copy `prod_guard.py` and `prod_guard.example.json` to `~/.claude/hooks/`; rename the copy to `prod_guard.json` and add the real prod tool-name and command patterns there. The installed config lives outside any repo and is never committed (`prod_guard.json` is in this repo's `.gitignore` as a backstop).
3. Run `python3 ~/.claude/hooks/prod_guard.py --check-config --config ~/.claude/hooks/prod_guard.json`; expect `config OK`.
4. Make the hook files and `settings.json` read-only for the agent's user, or use managed settings.
5. Add the settings snippet above.
6. In a throwaway session, try a blocked call (a placeholder write) and an allowed read; confirm exit 2 shows the reason and the read passes.

## Timeouts and alerts

Keep the hook fast: no network, no subprocess, stdin capped at 1 MiB. The internal deadline (`--deadline`, default 5 s, 0 disables, for tests only) kills a runaway process and the wrapper turns that into exit 2. Treat any "hook timed out" or hook-error notice as an alert: stop the session and tell Merwyn.
