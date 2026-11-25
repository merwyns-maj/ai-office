# prod guard (T-040, ask mode T-043)

A Claude Code PreToolUse hook for agent access to production. One stdlib-only Python file plus a JSON config. It covers the `Bash` tool and MCP tools (`mcp__*`). Merwyn's decision of 25 Nov 2026 (R-14): agents may read prod; prod writes run only if Merwyn confirms them; agents never submit to Bytebase. So:

- **Prod writes ask Merwyn.** The hook returns `permissionDecision: "ask"` and Claude Code shows him a prompt with the reason.
- **Bytebase is always blocked** and left to Merwyn: the agent prepares the plan (change, target, rollback) and hands it to him; he submits it himself.
- Anything the guard cannot classify still blocks, and every error path is fail-closed (exit 2, empty stdout).

Merwyn's confirmation in the prompt is his instruction for that one call.

**Installing is not done here.** This folder builds and tests the guard using fixtures only. Putting it in `~/.claude`, nimbus, klik-workspace or any other repo is a write outside this repo and a Merwyn human gate.

## Files

| File | What |
|---|---|
| `prod_guard.py` | The hook. Reads the hook JSON on stdin. Exit 0 with no output allows; exit 0 with one JSON line on stdout asks Merwyn; exit 2 with one stderr line blocks. No other exit codes. |
| `prod_guard.example.json` | Starter config: tool-name patterns, `.invalid` placeholders, empty allowlist. No real host or credential. |

Tests: `tests/test_prod_guard.py` with fixtures in `tests/fixtures/guard/`.

## Run the tests

From the repo root (runs every test in the repo, including `engine/runtime`):

```
python -m unittest -v
```

The output lists each case as `test_ask_...`, `test_block_...`, `test_allow_...`, `test_malformed_...`. No test makes a network call.

## What it does

Decision order (first match wins):

1. Input is not a JSON object, has no `tool_name`, or Bash has no string `command` (or MCP `tool_input` is not an object) -> block `malformed-input`.
2. `kubectl get|describe|edit` of `secret(s)` in Bash (matched across newlines), or any `__kubectl_` MCP tool whose name or any argument value mentions `secret(s)` -> block `k8s-secret-read`, in every context. In code, not config.
3. Bash command containing `bytebase` (any case), or MCP tool whose name contains `bytebase` -> block `bytebase`, whether or not it names prod or looks like a read. In code, not config. The reason tells the agent not to submit, to prepare the plan and hand it to Merwyn.
4. The call does not name prod (no `bash.prod_targets` / `mcp.prod_tools` match) -> allow.
5. Bash: `bash.write` rule match -> **ask** with the rule id (`bash-kubectl-write`, `bash-sql-file`, ...); SQL write keyword -> **ask** `sql-write:<KW>`; `bash.read_only` match -> allow; anything else -> block `default-deny`.
6. MCP: every SQL field is classified first. `sql-multi-statement` or `sql-not-read-only` -> block. Then an `mcp.write_tools` match -> **ask** with the rule id; any SQL field with a write keyword -> **ask** `sql-write:<KW>`; read tool -> allow; generic SQL tool with SQL -> allow (without SQL -> block `malformed-input`); anything else -> block `default-deny`.

Why some things block rather than ask: `default-deny`, `sql-multi-statement` and `sql-not-read-only` mean the guard cannot tell what the call does. A prompt is only meaningful when the guard knows it is a write, so Merwyn is asked about one clear write at a time. A write tool whose SQL has two statements therefore blocks `sql-multi-statement`.

MCP SQL (fields in `mcp.sql_fields`: `sql`, `query`, `statement`) is classified in code: more than one statement, any write or DDL keyword, `SELECT ... INTO`, `FOR UPDATE`, `nextval(`, `EXPLAIN ANALYZE` and similar are not read-only; false positives are never allowed through.

**Allowlist.** The `allowlist` key is required and must be `[]`. Any entry is a config error, so an old T-040 config with entries fails loudly (every call blocks with `rule=config-error`) instead of being silently ignored. No prod write is pre-approved.

**Output.** One of: nothing (allow); one JSON line on stdout, exit 0 (ask):

```
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"prod-guard ASK [rule=bash-kubectl-write] tool=Bash. This is a prod write and runs only if Merwyn confirms it. Merwyn: read the full command, and any file it runs, before you confirm. If it is denied, do not try another way; hand the change to Merwyn."}}
```

or one line on stderr, exit 2 (block). Both are built only from the rule id, the sanitised tool name and fixed text. They never contain the command or SQL (a WHERE clause can hold a NIK). stdout is written once, after the decision is final and after every error path has returned, so a crash cannot end as "ask JSON, then allow": any failure is exit 2, which blocks and ignores stdout.

Config lookup: `--config PATH`, then env `PROD_GUARD_CONFIG`, then `prod_guard.json` next to the script. A missing or invalid config blocks every call (`rule=config-error`). Check a config with `python3 prod_guard.py --check-config --config PATH`.

## Ask semantics

Source: https://code.claude.com/docs/en/hooks (PreToolUse decision control). `permissionDecision: "ask"` prompts the user to confirm and shows `permissionDecisionReason` in the prompt. Precedence is deny > defer > ask > allow. In a `-p` / headless run nobody can answer, so "ask" ends as a denial and Claude reads the reason (this is why the reason says "do not try another way; hand the change to Merwyn"). On exit 2 Claude Code blocks and ignores stdout JSON.

## What could auto-approve an ask (R-15)

Checked 25 Nov 2026 by Janice (PMO) against https://code.claude.com/docs/en/permissions (precedence among rules, hooks and mods) and https://code.claude.com/docs/en/permission-modes. The engineer could not re-fetch the pages from the build sandbox (proxy returned 403), so this list rests on that check; the install step 0 test below is the proof.

1. **Settings rules cannot weaken the guard.** Deny and ask rules are evaluated regardless of what a PreToolUse hook returns, so settings can only make it stricter. No allow rule overriding a hook "ask" is documented.
2. **Auto mode** cannot silently approve a hook-forced prompt.
3. **Mods handling `tool.check`.** Without managed settings or a Team/Enterprise login (Merwyn uses a personal Max login), an installed mod handling `tool.check` can approve a call that a PreToolUse hook blocked or would prompt for. Install no `tool.check` mods on a machine where the guard is installed, unless managed settings are in place.
4. **`bypassPermissions` / `--dangerously-skip-permissions`: behaviour for a hook "ask" is not documented.** Until a `claude --debug` test shows otherwise, treat it as auto-approving an ask. Never run it on a guarded machine. Engine and SDK runs must not set `bypassPermissions`. Candidate to verify at install: managed `permissions.disableBypassPermissionsMode`.

## Read access and what this guard does not do

- **It does not gate reads.** Allowed reads of prod (SELECT, `kubectl get/logs`, `pg_execute_query`) return real personal data (borrower, lender, NIK) into the agent's context and transcript. Merwyn approved agent reads on 25 Nov 2026 (R-14). Legal sign-off for cloud contexts is his to confirm. The read-only DB role (R-8) is still the real control. No prod rows in this repo, brains or logs.
- **It is a safety net against agent mistakes, not a security boundary.** A determined or confused agent can get around it.
- Known limits:
  - Prod access that is not named with `-prod__` or a configured pattern: new MCP server names, aliases, env vars, a script file that calls psql, base64 into sh, a default kube context that is prod.
  - `kubectl` aliases (for example `k`) are not covered.
  - A `SELECT` that calls a mutating function (for example `SELECT my_cleanup_fn()`) cannot be seen by the classifier.
  - Write or Edit by the agent could weaken `~/.claude/hooks/prod_guard.json` or `settings.json`. At install, protect them with file permissions (not writable by the agent's user) or Claude Code managed settings.
  - A hook timeout is non-blocking unless `onFailure: "block"` is set (see below); there is no internal deadline on Windows (no `SIGALRM`).
  - If Claude Code's own runner fails before the shell starts, the wrapper cannot help.
  - MCP SQL field names are assumed (`sql`, `query`, `statement`); an unrecognised field blocks.
  - `bash-sql-file` asks without the file's SQL in the prompt; the reason tells Merwyn to read the file before confirming. Merwyn approving without reading is a residual risk.
  - Prod-targeted Bash commands are also scanned for SQL write words, so words like `cluster`, `set` or `do` in such a command now ask instead of block (false positive).
  - The Bytebase match is a substring, so any command that only mentions it (for example a grep in docs) blocks; that fails closed. `byte''base` quote-splitting is the same gap as `sec''rets`. Bytebase MCP is matched on the tool name only, not on arguments.
- The real control is a read-only DB role (and a scoped kube role) for agent sessions. That is Merwyn's decision and a human gate, not part of this task.

## Settings snippet (for an install task; not applied here)

User-level `~/.claude/settings.json`, because MCP servers are session-wide:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash|mcp__.*",
  "hooks": [{"type": "command", "timeout": 10, "onFailure": "block",
    "command": "python3 ~/.claude/hooks/prod_guard.py --config ~/.claude/hooks/prod_guard.json || exit 2"}]}]}}
```

Why each part (contract per https://code.claude.com/docs/en/hooks, checked 25 Nov 2026 by Janice; see R-15 above): exit 2 blocks and stderr is shown as the reason; any other non-zero exit is non-blocking, so `|| exit 2` turns a missing `python3` (127), a syntax error (1) or a kill by signal into a block. Exit 0, with or without the ask JSON, passes through unchanged. `|| exit 2` and `onFailure: "block"` are mandatory. A timed-out PreToolUse hook does not block unless `"onFailure": "block"` is set (Claude Code v2.1.295+). `timeout` is in seconds; the guard's internal 5 s deadline sits below it.

## Install steps for a company repo (Merwyn gate)

0. **Ask test first.** In a throwaway session run `claude --debug` in each permission mode you use (default, acceptEdits, auto, bypassPermissions) with a placeholder prod write, and record whether the prompt appears. If any mode does not prompt, do not install in that mode. Until the test says otherwise, bypassPermissions counts as auto-approving an ask and is never used on a guarded machine.
1. Get Merwyn's go-ahead for the target (user settings, nimbus, klik-workspace).
2. Copy `prod_guard.py` and `prod_guard.example.json` to `~/.claude/hooks/`; rename the copy to `prod_guard.json` and add the real prod tool-name and command patterns there (keep `"allowlist": []`). The installed config lives outside any repo and is never committed (`prod_guard.json` is in this repo's `.gitignore` as a backstop).
3. Run `python3 ~/.claude/hooks/prod_guard.py --check-config --config ~/.claude/hooks/prod_guard.json`; expect `config OK`.
4. Make the hook files and `settings.json` read-only for the agent's user, or use managed settings. Install no `tool.check` mods unless managed settings are in place.
5. Add the settings snippet above, with `|| exit 2` and `onFailure: "block"` (mandatory).
6. In a throwaway session, try a placeholder write (expect a prompt showing the reason), a Bytebase call (expect a block with the hand-to-Merwyn reason) and a read (passes). Mandatory before real use.

## Timeouts and alerts

Keep the hook fast: no network, no subprocess, stdin capped at 1 MiB. The internal deadline (`--deadline`, default 5 s, 0 disables, for tests only) kills a runaway process and the wrapper turns that into exit 2. Treat any "hook timed out" or hook-error notice as an alert: stop the session and tell Merwyn.

- **Shell quote-splitting.** The shell joins `sec''rets` into `secrets` after the guard has read the raw text, so `kubectl get sec''rets` is not caught. Like aliases, this is a known gap: the guard stops mistakes, not a determined agent.
