---
id: T-040
title: "Prod-guard hook script and tests (repo-only slice of T-019)"
phase: 4-code-tooling
status: done
priority: P0
owner: curator
where: code
project: ai-office
depends_on: []
pr: 11
---

> Slice of T-019 ("biggest risk reducer"). Builds and tests the guard here, using fixture commands only. Installing it in nimbus or klik-workspace is a write to a company repo and stays a Merwyn gate.

## Done when
- [x] Given a fixture hook payload (JSON on stdin) whose Bash command writes to the prod target (e.g. INSERT/UPDATE/DELETE/DDL via a SQL client, or a deploy/migrate command), when the hook script runs, then it exits 2 and prints a reason naming the matched rule on stderr
- [x] Given a fixture payload for a read-only command (e.g. SELECT, `git status`, `ls`), the script exits 0 with no stderr
- [x] Given a fixture payload for a Bytebase script run that matches an entry in the allowlist file, the script exits 0; given one that matches no entry, it exits 2 (default deny)
- [x] Given malformed or empty stdin, or a payload with no command, the script exits 2 (fail closed) and says why
- [x] One test command (stated in the README) runs all fixture cases, exits 0, and the output lists at least 3 blocked, 3 allowed and 1 malformed case
- [x] A scan of the repo files added by this task finds no real hostname, credential, connection string or data row (fixtures use obvious placeholders such as `prod.example.invalid`); the tests make no network call
- [x] README (in the guard's folder) gives the settings snippet and steps a company repo would follow to install it, and states that installing is not done here

## Spec
**Problem.** Agents running in company repos could write to nimbus-prod (production lending data) by mistake, and nothing stops them today. This is the repo-only slice of T-019: build and test the guard here so it is proven before any company repo adopts it.

**In scope**
- A Claude Code PreToolUse hook script, in this repo, for the Bash tool.
- Default-deny policy: a command aimed at the prod target is blocked unless it is read-only or matches an explicit allowlist (the allowlist is a file in this repo).
- Fixture-based tests and a README with install steps.

**Out of scope**
- Installing the hook in nimbus, klik-workspace or any other repo (human gate: writes to a company repo).
- Any real connection, hostname, credential or row; any test that reaches a network.
- Guarding non-Bash tools, non-prod environments, or Bytebase itself; approval workflows; logging or alerting.
- Deciding the final Bytebase allowlist contents (see Open questions); the starter allowlist ships with placeholders only.

**Open questions**
- Merwyn: confirm default-deny with an allowlist, and which Bytebase script invocations belong on it. Non-blocking: build proceeds with default-deny and a placeholder allowlist; entries are added when Merwyn answers.
- Fang (architect): how the prod target is identified without real hostnames in this repo (e.g. a pattern file kept outside the repo, supplied at install). Non-blocking for spec; must be settled in Design.
- Fang (architect): confirm the hook's blocking exit code (2) and stdin payload shape against current Claude Code hook docs before design; the checks above assume them.
- Janice: T-019 and T-024 parent files could not be read in this pass (filenames not found); parent-level constraints are unchecked.

— Emmy (pm)

## Spec approval
- Approved for design. Pick rule (priority, then lowest id, dependencies done) confirmed. Parent tasks are T-019 / T-024 in backlog/. — Janice (pmo)
- Scope amended: the biggest real risk in Merwyn's setup is MCP database and cluster tools, not only Bash. Sessions expose tools named like `mcp__remote-devices__nimbus-prod__pg_execute_mutation`, `..._pg_execute_sql`, `..._pg_manage_schema`, `..._pg_import_table_data`, `mcp__remote-devices__klik-mariadb-prod__mysql_query`, `mcp__remote-devices__kubernetes__kubectl_apply`, `..._kubectl_delete`, and read tools like `..._pg_execute_query`. The guard must cover both Bash commands and MCP tool names. Prod is identified by tool-name and command patterns in a config file (no hostnames or credentials). This replaces "Guarding non-Bash tools" in Out of scope for MCP tools only; Write/Edit and other local tools stay out of scope. — Janice (pmo)

## Design

**Revision 2 (after compliance BLOCK).** This replaces Revision 1 (commit 86568c1). The interfaces stay the same except for the additions listed below.

**What changed from Revision 1 (each item from Wulan's BLOCK, which Merwyn accepted on 25 Nov)**

| # | Compliance item | Change in this revision |
|---|---|---|
| 1 | Fail-open paths (exit 127/1, decode error, timeout) | Settings command ends with `\|\| exit 2`. The script's imports and the whole run, including the stdin read and decode, sit under one top-level handler that exits 2. A self-deadline (`signal.alarm`, default action) stops a slow run, and the wrapper turns that into exit 2. stdin is capped at 1 MiB. New tests cover these cases. The README explains timeouts. |
| 2 | `kubectl get secret(s)` leaks credentials | New rule in code, `k8s-secret-read`, checked before the prod check. It applies to Bash and to every MCP `__kubectl_` tool, whatever the context or cluster. Tests added. |
| 3 | stderr may echo a NIK from SQL | stderr carries the rule id, the tool name (sanitised) and a fixed reason from a table in code. Payload text is never interpolated into it. A sentinel test asserts this. |
| 4 | README must state what the guard is not | New README section: "What this guard does not do", with the limits listed below |
| 5 | Allowlist too permissive | A command containing `..` (or chaining characters, or an apply verb) can never match the allowlist. Every entry must declare `"action": "submit-change-issue"`, or `load_config` fails. |
| 6 | Hygiene scan / installed config | The scan covers `tests/test_prod_guard.py` too. `.gitignore` gets `prod_guard.json`. The README says the installed config lives outside the repo and is never committed. |

**Answers to the Spec's architect questions** (unchanged)
- *How prod is identified without hostnames.* Regex patterns over the MCP tool name (e.g. `-prod__`, `__kubernetes__`) and over the Bash command text (pg service names, kube contexts, client aliases), kept in a JSON config. The repo ships `prod_guard.example.json`, which has tool-name patterns and `.invalid` placeholders only. The installed copy lives outside this repo, in `~/.claude/hooks/`, and any local pattern is added there.
- *Hook contract.* This is RAID R-6 (Assumption). Before opening the PR, the Engineer verifies these against the current Claude Code hook docs and cites the URL in Build notes: the stdin shape, exit 2 blocks, a timeout or any other non-zero exit is non-blocking, the per-hook `timeout` key, and the command runs through a POSIX shell so `|| exit 2` works.

**Approach**
- One self-contained, stdlib-only hook script that can be copied into any repo as a single file plus its config:
  - `engine/__init__.py`, `engine/guard/__init__.py` (both empty, so tests can import)
  - `engine/guard/prod_guard.py`: the hook
  - `engine/guard/prod_guard.example.json`: starter config (tool-name patterns, placeholder command patterns, placeholder allowlist)
  - `engine/guard/README.md`: what it blocks, what it does not do, the test command, the settings snippet, install steps, timeout handling, and "installing is not done here"
  - `tests/__init__.py` (empty), `tests/test_prod_guard.py`, `tests/fixtures/guard/config.json`, `tests/fixtures/guard/slow_config.json` (deadline test only), `tests/fixtures/guard/cases.json`
  - `.gitignore`: add the line `prod_guard.json`
- Policy: default-deny for anything identified as prod, and fail closed on any error, at every layer: the shell wrapper, the import, stdin, config and decide. A non-prod call exits 0 silently.
- No change to `scripts/`, `.claude/settings.json` or any other repo. `engine/README.md` gets one row for `guard/` (whichever of T-039/T-040 merges second rebases; it is a one-line change).

**Fail-closed layers (item 1)**

| Failure | What happens | Exit seen by Claude Code |
|---|---|---|
| `python3` missing (127), script syntax error (1), killed by a signal | Shell wrapper `\|\| exit 2` | 2 |
| Stdlib import fails (e.g. a shadowing module next to the script) | Module-level `try: import ... except BaseException: write fixed line; sys.exit(2)`. Only `import sys` sits outside it. | 2 |
| stdin not UTF-8, over 1 MiB, empty, not JSON | Inside `main`, under `_entry`'s handler; rule `malformed-input` / `input-too-large` | 2 |
| Config missing or invalid | `ConfigError`; rule `config-error` | 2 |
| Any other exception, including `KeyboardInterrupt` or a stray `SystemExit` | `_entry` catches `BaseException`; rule `internal-error`, printing the exception class name only | 2 |
| Runaway regex or a hang | `signal.alarm(deadline)` with the default SIGALRM action (no Python handler, so it also works mid-regex in C). The kernel kills the process and the wrapper turns that into 2. Skipped where SIGALRM does not exist (Windows); the README says so. | 2 |
| Claude Code hook timeout (settings `timeout`) | **Non-blocking: the call proceeds.** The internal deadline (5 s) is below the settings timeout (10 s), so this should not happen. The README tells the operator to treat any "hook timed out" notice as an alert: stop the session and tell Merwyn. | n/a |

Entry point shape (load-bearing):
```python
import sys
try:
    import argparse, json, os, pathlib, re, signal
    from typing import NamedTuple
except BaseException:
    sys.stderr.write("prod-guard BLOCKED [rule=internal-error] tool=<unknown>. Guard failed to start; ask Merwyn.\n")
    sys.exit(2)
...
def _entry() -> None:
    try:
        code = main()
    except BaseException as e:          # incl. SystemExit from argparse, KeyboardInterrupt
        _block_line("internal-error", None, extra=type(e).__name__)
        code = 2
    sys.exit(code if code in (0, 2) else 2)

if __name__ == "__main__":
    _entry()
```
`main` reads `stdin.buffer.read(MAX_INPUT + 1)` and decodes UTF-8 strictly. It never uses text-mode stdin.

**Decision order (function `decide`)**

Input is the parsed payload. Rule ids below appear in the stderr message.

| Step | Bash (`tool_name == "Bash"`) | MCP (`tool_name` starts with `mcp__`) |
|---|---|---|
| 0 | Payload not a JSON object, no `tool_name`, or Bash without a string `tool_input.command` → **block** `malformed-input` | same; `tool_input` must be an object if present |
| 0b (new) | Command matches `K8S_SECRET_BASH` (in code: `\bkubectl\b.*\b(get\|describe\|edit)\b.*\bsecrets?\b`, case-insensitive) → **block** `k8s-secret-read`, **whatever the context** | Tool name matches `__kubectl_` and (the tool name contains `secret`, or any string value anywhere in `tool_input`, walked recursively, matches `\bsecrets?\b`) → **block** `k8s-secret-read` |
| 1 | No `bash.prod_targets` pattern matches the command → **allow** | No `mcp.prod_tools` pattern matches `tool_name` → **allow** |
| 2 | Allowlist check (below) passes → **allow** `allowlist:<id>` | Tool name and SQL `re.fullmatch` an entry with that `tool` pattern (the same entry rules apply) → **allow**. The starter has no MCP entries. |
| 3 | Any `bash.write` pattern matches, or `sql_write_keyword(command)` finds one → **block** `<rule id>` / `sql-write:<KEYWORD>` | `mcp.write_tools` matches → **block** `<rule id>` |
| 4 | Any `bash.read_only` pattern matches → **allow** | SQL found in `tool_input[f]` for `f` in `mcp.sql_fields` and `classify_sql` says write → **block** `sql-write:<KEYWORD>` / `sql-multi-statement` |
| 5 | → **block** `default-deny` | `mcp.read_tools` matches → **allow** |
| 6 | | `mcp.sql_tools` matches, SQL found and read-only → **allow**; matches but no SQL field → **block** `malformed-input` |
| 7 | | → **block** `default-deny` |
| — | Any other `tool_name` (not Bash, not `mcp__`) → **allow** (the matcher should not send them; out of scope) | |

The secret rule is in code, not config, so a config cannot weaken it. It is checked before step 1 because a Bash `kubectl` with no `--context` uses the current context, which may be prod.

**Allowlist check (item 5), in code.** A Bash command is eligible only if:
(a) it contains none of `;` `&` `|` backtick `$(` `>` `<` or a newline;
(b) it does not contain `..`;
(c) it has no whole word `apply`, `rollout`, `approve`, `deploy`, `execute` or `run-now`;
(d) it `re.fullmatch`es the entry's `command`.

If (a), (b) or (c) fails, the command skips the allowlist and goes on to steps 3 to 5, so it ends up blocked by a write rule or by `default-deny`. `load_config` rejects any allowlist entry whose `action` is not exactly `"submit-change-issue"` (config error). Entries exist to submit a Bytebase change issue for human review in Bytebase, never to apply one.

**SQL classifier** (in code; unchanged from Revision 1): strip `--` and `/* */` comments. `sql-multi-statement` if a `;` is followed by more non-space text. It is a write if any whole word (case-insensitive) is in `INSERT UPDATE DELETE MERGE UPSERT REPLACE CREATE ALTER DROP TRUNCATE RENAME GRANT REVOKE COPY CALL DO EXEC EXECUTE SET RESET LOCK VACUUM REINDEX CLUSTER COMMENT REFRESH IMPORT LOAD INTO`, or the text contains `FOR UPDATE`/`FOR SHARE`, `nextval(`, `setval(`, `pg_terminate_backend`, `pg_cancel_backend`, `lo_import`, `lo_export` or `dblink`. Otherwise it is read-only only if the first keyword is `SELECT`, `WITH`, `SHOW`, `EXPLAIN` (not followed by `ANALYZE`), `DESCRIBE`, `DESC`, `TABLE` or `VALUES`; anything else is `sql-not-read-only`. False positives block, by design. Bash uses `sql_write_keyword` only.

**Interfaces**

CLI (`engine/guard/prod_guard.py`):
```
python3 prod_guard.py [--config PATH] [--deadline SECONDS]   # hook mode; payload JSON on stdin; deadline default 5, 0 disables (tests only)
python3 prod_guard.py --check-config [--config PATH]         # prints "prod-guard: config OK (<n> rules)"
```
Config lookup is unchanged: `--config`, then env `PROD_GUARD_CONFIG`, then `prod_guard.json` in the script's folder.

Exit codes: `0` allow (no stdout, no stderr). `2` for everything else. No other codes, whether from the script or from the wrapper.

stderr on block (item 3), always one line, built only from the rule id, the sanitised tool name and a fixed string:
```
prod-guard BLOCKED [rule=<rule-id>] tool=<tool_name>. <REASONS[rule-family]> Prod writes go through an allowlisted Bytebase change issue; ask Merwyn.
```
- `REASONS` is a dict in code, keyed by rule family (`malformed-input`, `input-too-large`, `config-error`, `internal-error`, `k8s-secret-read`, `sql-write`, `sql-multi-statement`, `sql-not-read-only`, `default-deny`, `config-rule`), for example `"Command matches a prod write rule."`.
- `<tool_name>` is printed only if it fullmatches `[A-Za-z0-9_.:-]{1,128}`; otherwise it shows `<invalid>`.
- The `sql-write:<KEYWORD>` suffix comes from the fixed keyword list.
- `config-error` adds the config path and the failure kind (e.g. `bad regex in rule bash-helm-write`), never payload text.
- `internal-error` adds the exception class name only.
- `Decision.reason` holds the fixed `REASONS` string.

Config (`prod_guard.example.json`): the same as Revision 1 except for:
- the allowlist entry:
  ```json
  {"id": "bytebase-placeholder", "tool": "^Bash$", "action": "submit-change-issue",
   "command": "bytebase-submit-issue --project PLACEHOLDER --file migrations/[\\w/-]+\\.sql",
   "note": "Placeholder until Merwyn names the real Bytebase invocations (Spec open question). Submits a change issue only; never applies."}
  ```
  The path class has no `.`, so `..` cannot match it either.
- `bash.read_only` → `bash-kubectl-read` keeps `get|describe|logs|top`. Secrets are already blocked at step 0b.

The full Revision 1 config listing (version 1; bash `prod_targets`, `write`, `read_only`; mcp `prod_tools`, `write_tools`, `read_tools`, `sql_tools`, `sql_fields`) still applies unchanged; see commit 86568c1. `load_config` adds one validation: each allowlist entry needs `id`, `tool`, `command` and `action == "submit-change-issue"`.

Python (`engine/guard/prod_guard.py`):
```python
MAX_INPUT = 1_048_576
class ConfigError(Exception): ...
Decision = NamedTuple("Decision", [("allow", bool), ("rule", str), ("reason", str)])
def load_config(path: pathlib.Path) -> dict
def find_config(cli_path: str | None) -> pathlib.Path
def classify_sql(sql: str) -> tuple[bool, str]
def sql_write_keyword(text: str) -> str | None
def allowlist_eligible(command: str) -> bool          # new: checks (a)-(c)
def mentions_k8s_secret(tool_name: str, tool_input: object, command: str | None) -> bool   # new
def decide(payload: object, config: dict) -> Decision
def format_block(rule: str, tool_name: object, extra: str = "") -> str   # new: the only stderr writer
def main(argv: list[str] | None = None, stdin=sys.stdin, stderr=sys.stderr) -> int
def _entry() -> None                                   # new: top-level BaseException handler
```
Imports allowed: `argparse, json, os, pathlib, re, signal, sys, typing` only (`signal` is new).

Settings snippet for the README (user-level `~/.claude/settings.json`, because MCP servers are session-wide):
```json
{"hooks": {"PreToolUse": [{"matcher": "Bash|mcp__.*",
  "hooks": [{"type": "command", "timeout": 10,
    "command": "python3 ~/.claude/hooks/prod_guard.py --config ~/.claude/hooks/prod_guard.json || exit 2"}]}]}}
```

**README: "What this guard does not do" (item 4).** This section is required and must state:
- **It does not gate reads.** Allowed reads of prod (SELECT, `kubectl get/logs`, `pg_execute_query`) return real personal data (borrower, lender, NIK) into the agent's context and transcript. Agent read access to prod needs Merwyn's and legal's approval (UU PDP); it is not granted by installing this guard.
- **It is a safety net against agent mistakes, not a security boundary.** A determined or confused agent can get around it.
- Known limits:
  - prod access that is not named with `-prod__` / a configured pattern (new MCP server names, aliases, env vars, a script file that calls psql, base64 into sh, a default kube context that is prod)
  - a `SELECT` that calls a mutating function (e.g. `SELECT my_cleanup_fn()`), which the classifier cannot see
  - a hook timeout is non-blocking
  - no internal deadline on Windows
  - MCP SQL field names are assumed
- The real control is a read-only DB role (and a scoped kube role) for agent sessions. That is Merwyn's decision and a human gate, and is not part of this task.
- Timeout handling: keep the hook fast (no network, no subprocess, stdin capped). `timeout: 10` sits above the 5 s internal deadline. Any "hook timed out" or hook-error notice is an alert: stop and tell Merwyn.
- Config handling: the installed `prod_guard.json` lives in `~/.claude/hooks/` (or another path outside any repo) and is never committed. `.gitignore` carries `prod_guard.json` as a backstop.

**Tests** (`python -m unittest -v` from the repo root; stated in the README)
- `cases.json` runner as in Revision 1: one test method per case, run by `subprocess.run([sys.executable, script, "--config", fixture_config], input=...)`. It asserts the exit code, empty stdout always, empty stderr on allow, and `rule=<rule>` in stderr on block.
- **New in this revision:**
  - Leak check (item 3): for every block and malformed case, assert that stderr contains neither the `command` nor any SQL field value from the payload. Plus a dedicated case: MCP `pg_execute_query` with `SELECT * FROM t WHERE nik = 'PII_SENTINEL_X'; DROP TABLE t` (block), where stderr must not contain `PII_SENTINEL_X`, `nik` or `DROP TABLE`. The sentinel is letters, not digits, so the hygiene scan never sees a NIK-shaped number.
  - Fail-closed (item 1), each through the exact settings wrapper, `subprocess.run(["sh", "-c", f"{py} {script} --config {cfg} || exit 2"], ...)`:
    - `test_block_broken_import`: copy the script to a temp dir next to a `re.py` that raises ImportError → exit 2 with `rule=internal-error`
    - `test_block_syntax_error`: copy with garbage appended → exit 2
    - `test_block_missing_interpreter`: `/nonexistent/python3` → exit 2
    - `test_malformed_undecodable_stdin`: bytes `b"\xff\xfe\x00"` → exit 2, `rule=malformed-input`
    - `test_block_oversize_stdin`: 1 MiB + 1 bytes → `rule=input-too-large`
    - `test_block_deadline`: `slow_config.json` with prod target `(a+)+$`, command `"a"*40 + "!"`, `--deadline 1` → exit 2 within 5 s (skipped if no SIGALRM)
    - `test_block_internal_error`: in-process, `main` with a monkeypatched `decide` raising → `_entry` exits 2
  - Secrets (item 2):
    - block `kubectl get secret db-creds`, `kubectl get secrets -A`, `kubectl describe secret/x` (Bash, **no** prod context)
    - block `kubectl --context prod-cluster get secrets -o yaml`
    - block MCP `..._kubernetes__kubectl_get` with `{"resourceType": "secrets"}`
    - block MCP `..._kubernetes__kubectl_get` with nested `{"args": ["secret", "x"]}`
    - block MCP `..._kubernetes__kubectl_get_secret` (name)
    - allow MCP `kubectl_get` pods
    - allow Bash `kubectl get pods` (non-prod)
  - Allowlist (item 5): each of these is blocked (not allowlisted):
    - placeholder Bytebase command with `migrations/../x.sql`
    - with `--file migrations/a.sql apply`
    - with `> out`
    - with `; psql ...` (kept from Revision 1)

    Config test: an entry with `action: "apply"` or with no `action` → `config error`, exit 2.
  - Hygiene (item 6): the scan covers `engine/guard/`, `tests/fixtures/guard/` **and `tests/test_prod_guard.py`**. The scanner's own detection patterns are built by string concatenation so they do not match themselves. Plus a test that `.gitignore` contains `prod_guard.json` and that `engine/guard/prod_guard.json` does not exist in the working tree.
- Kept from Revision 1: all the block, allow and malformed minimum cases, the `classify_sql` unit tests, config tests, `test_example_config_valid`, and the no-network `ast` import check (now with `signal` on the allowed list).

**Risks**

| Risk | Handling |
|---|---|
| Regex guard is bypassable | Default-deny on anything that names prod; unknown prod MCP tools are blocked. The README says plainly that it is a safety net, not a boundary, and lists the limits. The real control is a read-only DB role (Merwyn gate). |
| Reads of prod bring personal data into agent context | Out of the guard's power by design. The README requires Merwyn's and legal's approval before agents get prod read access. |
| Hook timeout or hook error lets a call through (Claude Code treats it as non-blocking) | `\|\| exit 2` covers non-zero exits. The internal deadline (5 s) is below the settings timeout (10 s). stdin is capped at 1 MiB. The README says to treat timeouts as an alert. A residual risk remains if Claude Code's own runner fails before the shell starts; that is noted in the README limits. |
| Default SIGALRM kills the process with no message | The wrapper's exit 2 still blocks. The reason line is missing in that one case; accepted, and documented. |
| stderr leaks payload | One writer (`format_block`), fixed reasons, sanitised tool name, and a leak test over every block case |
| Secret rule false positives (e.g. a pod named `secret-rotator`) | Accepted: it fails closed, and the user rephrases with a resource type |
| MCP `tool_input` field names not confirmed | `sql_fields` is in config; no recognised field → block. The secret scan walks every string value, so it does not depend on field names. |
| Hook contract differs from the assumption | RAID R-6, extended to cover the timeout semantics and shell execution; the Engineer verifies |
| Broken config blocks every Bash and MCP call | A clear `config error` naming the path; `--check-config` is in the install steps. Accepted. |

**Flags.** This touches access control for production data (nimbus-prod, MariaDB prod, Kubernetes). **Wulan (compliance) re-checks this revision before build.** Installing the hook anywhere, and any decision on agent read access to prod or a read-only DB role, are Merwyn human gates and are not part of this task.

**Decision record (draft for April, revised)**
```
Decision: Guard prod with one stdlib PreToolUse hook (Bash + MCP), default-deny and fail-closed at every layer (shell wrapper, import, stdin, config, deadline), prod identified by regexes in a JSON config kept outside the repo; it never echoes payload text and does not gate reads.
Context: T-019/T-040. Agents reach nimbus-prod, MariaDB prod and Kubernetes via MCP and Bash; nothing blocks writes. Compliance BLOCKed Rev 1 for fail-open paths, secret reads, stderr leaks and allowlist looseness; Merwyn accepted all fixes (25 Nov 2026).
Options: A — hook + JSON pattern config (pro: no dependency, testable offline; con: bypassable, timeouts non-blocking).
         B — native per-tool permission deny rules (pro: built in; con: cannot tell SELECT from DELETE in a generic SQL tool; nothing for Bash).
         C — read-only DB role + scoped kube role for agent sessions (pro: real boundary, also limits reads; con: prod credentials and DBA work, human gate).
Chosen: A now as a safety net, because it is buildable and testable here; C is the recommended real control (Merwyn's decision); B may complement A at install.
Consequences: Easier: one tested guard reused across repos; leaks via the guard's own output ruled out. Harder: the config must track new MCP tool names (drift fails safe); false positives block. Reads of prod stay ungated and need Merwyn + legal approval.
Supersedes: the Revision 1 draft (same task, not yet accepted).
Links: T-040, T-019, RAID R-6, compliance BLOCK in T-040 Review log.
```

**Open questions (design)**
- Merwyn: is the `kubernetes` MCP server prod-only, or does it also reach staging? The design treats it as prod (fail-safe). Non-blocking.
- Merwyn: which `tool_input` key carries the SQL for `pg_execute_sql`, `pg_execute_query` and `mysql_query`? Key names only, no query text or data. The design assumes one of `sql`, `query`, `statement`. Non-blocking: unknown keys fail closed.
- Merwyn: the Bytebase allowlist entries (from the Spec) are still open, and each must be a "submit change issue" command. The build ships the placeholder.
- Merwyn (+ legal): whether agent sessions may read prod at all, and whether to commission the read-only DB role (option C). Not needed for this build. It must be answered before any install task.

— Fang (architect)

## Design approval
- Approved for build with Wulan's three notes and onFailure: block. — Janice (pmo)

## Build notes

**What changed** (Revision 2, built as designed; deviations below)
- `engine/guard/prod_guard.py` (hook), `engine/guard/prod_guard.example.json` (starter config), `engine/guard/README.md`, `engine/guard/__init__.py`
- `tests/test_prod_guard.py`, `tests/fixtures/guard/{config.json,slow_config.json,cases.json}`
- `.gitignore` gets `prod_guard.json`; `engine/README.md` gets one row for `guard/`
- Not touched: `scripts/`, `.claude/`, `~/.claude`, any settings.json. The hook is not installed anywhere.
- Build notes from Wulan applied: `K8S_SECRET_BASH` matches across newlines (test `test_block_k8s_secrets_newline`); README limits (Write/Edit could weaken the installed config, `k` aliases uncovered, every allowlist entry needs human review); settings snippet has `|| exit 2` plus `"onFailure": "block"` plus `timeout`, citing https://code.claude.com/docs/en/hooks; `.gitignore` line added.

**Hook contract (RAID R-6)**: relied on Janice's verification in the Review log (25 Nov 2026, https://code.claude.com/docs/en/hooks); I did not re-fetch the docs. Facts used: stdin has `tool_name`/`tool_input`; exit 2 blocks with stderr as the reason; other non-zero exits and (without `onFailure: "block"`) timeouts do not block.

**How to verify**
```
python -m unittest -v        # from repo root; runs ALL tests incl. engine/runtime
python3 engine/guard/prod_guard.py --check-config --config engine/guard/prod_guard.example.json
```

**Test output** (Python 3.13.18 here; stdlib only, no 3.11-only syntax used)
```
Ran 133 tests in 5.0s
OK
```
46 existing (engine/runtime) + 87 new. `cases.json` has 53 cases (31 block, 12 allow, 10 malformed), each its own `test_<expect>_<name>` in the `-v` listing. Mutation checks: reverting the multiline secret regex fails 2 tests; removing the `..` check fails 2 tests.

**Example runs** (fixture config, from repo root; stdout empty in all)
```
MCP nimbus-prod pg_execute_mutation        -> exit=2  prod-guard BLOCKED [rule=mcp-pg-write] tool=mcp__remote-devices__nimbus-prod__pg_execute_mutation. The call matches a prod write rule. Prod writes go through an allowlisted Bytebase change issue; ask Merwyn.
Bash "kubectl get\n secrets"                -> exit=2  prod-guard BLOCKED [rule=k8s-secret-read] tool=Bash. Reading Kubernetes secrets is blocked in every context. ...
MCP pg_execute_query, nik=PII_SENTINEL_X; DROP TABLE t -> exit=2  prod-guard BLOCKED [rule=sql-multi-statement] tool=mcp__...pg_execute_query. The SQL contains more than one statement. ...   (no SQL text echoed)
Bash psql service=nimbus-prod -c "SELECT count(*) FROM t" -> exit=0, no output
Bash git status                            -> exit=0, no output
stdin "not json"                           -> exit=2  prod-guard BLOCKED [rule=malformed-input] tool=<unknown>. The hook input could not be understood. ...
sh -c "/nonexistent/python3 x || exit 2"   -> exit=2
```

**Done-when to test**
| Done when | Test(s) |
|---|---|
| 1 Write to prod exits 2, rule named on stderr | `TestCases.test_block_*` (bash_psql_delete_prod, bash_kubectl_apply_prod, bash_psql_file_prod, bash_helm_upgrade_prod, bash_migrate_prod, mcp_pg_execute_mutation, mcp_pg_manage_schema, mcp_pg_import_table_data, mcp_kubectl_delete, mcp_mysql_query_update, ...); each asserts exit 2, `rule=<id>`, one line |
| 2 Read-only exits 0, no stderr | `TestCases.test_allow_*` (bash_git_status, bash_ls, bash_psql_select_prod, mcp_pg_execute_query_select, mcp_mysql_query_select, mcp_kubectl_get_pods, ...) |
| 3 Bytebase allowlisted 0, unlisted 2 | `test_allow_bash_bytebase_allowlisted`, `test_block_bash_bytebase_not_on_allowlist` (default-deny), `..._dotdot`, `..._apply`, `..._redirect`, `..._allowlist_lookalike_chained`; `TestConfig.test_allowlist_eligibility_enforced_in_decide`; `TestUnits.test_allowlist_eligible` |
| 4 Malformed/empty/no command exits 2 and says why | `TestCases.test_malformed_*` (10), `TestFailClosed.test_malformed_undecodable_stdin`, `test_block_oversize_stdin` |
| 5 One test command; output lists >=3 blocked, 3 allowed, 1 malformed | `python -m unittest -v` (stated in README); `TestCaseCoverage.test_minimum_case_counts` |
| 6 No real host/credential/row; no network | `TestHygiene.*` (scans engine/guard, fixtures, and the test file; checks `.gitignore` and no installed config), `TestNoNetwork.*` (ast import checks) |
| 7 README has snippet and install steps, says install not done here | `engine/guard/README.md` (first paragraph, "Settings snippet", "Install steps"); reviewer reads |
| Rev 2 items | fail-closed: `TestFailClosed.*` through the exact `sh -c "... || exit 2"` wrapper; leak: `TestSentinelLeak.*` and the per-case leak assertion; secrets: `test_block_k8s_*`, `test_block_mcp_kubectl_get_*`, `test_allow_mcp_kubectl_get_pods`, `test_allow_bash_kubectl_get_pods_nonprod`; config action: `TestConfig.test_allowlist_*` |

**Deviations from the design** (all small; none changes an interface)
1. Config patterns compile with `re.IGNORECASE | re.DOTALL` (design: IGNORECASE only). Without DOTALL, `kubectl --context prod\n apply` slipped past `.*` in `bash-kubectl-write`. Same reason as the secret-rule note.
2. Added prod target `bash-bytebase` (`\bbytebase\S*`) to the config. Without it the allowlisted Bytebase command never names prod, so "unlisted Bytebase run -> exit 2" was unreachable.
3. Allowlist `..`/chaining/apply checks are redundant in the starter config (its `--file x.sql` already trips `bash-sql-file`), so a separate test uses a temp config without write rules to prove the eligibility check alone denies.
4. `classify_sql` scans write keywords on the raw text (comments and string literals included), not only the comment-stripped text, and rejects `/*!` MySQL executable comments. Reason: stripping comments naively let `SELECT '--'; DROP TABLE t` hide the DROP. Cost: a write word inside a comment or string blocks (false positive, fails closed). Multi-statement runs first, so `SELECT 1; DROP ...` reports `sql-multi-statement`.
5. `main(argv, stdin=None, stderr=None)` resolves `sys.stdin`/`sys.stderr` at call time (design showed them as default args) so tests can patch them. Argparse errors are routed to the `internal-error` block (parser `error` raises).
6. Broken-import test shadows `json.py`, not `re.py` (argparse imports `re` first on some setups; json is not preloaded). Same mechanism.
7. A blank (whitespace-only) Bash `command` is `malformed-input` (design only said missing/non-string).

**Known limits / things for the reviewer**
- Prod-targeted Bash commands are scanned with the SQL keyword list, so words like `cluster` (e.g. `--context prod-cluster`), `set`, `do` block reads such as `kubectl --context prod-cluster logs ...`. Design behaviour (fail closed); documented in README; I used `prod-main` in the allow fixture. Worth a call from Merwyn when the real context names are known.
- The deadline test and SIGALRM kill leave no reason line (wrapper's exit 2 still blocks), as designed.
- The K8S secret regex uses lazy `[\s\S]*?` with three segments; on a 1 MiB command it is slow but bounded by the 5 s deadline (-> exit 2).
- Verified on Linux only; the Windows no-SIGALRM path is not exercised.
- Merwyn open questions from Design (kubernetes MCP scope, SQL field names, Bytebase entries, read access to prod) are unchanged.

— Sebastian (engineer)

## Review log
- PASS — all 7 checks verified with crafted payloads through the README command form; 133 tests OK; secret reads and NIK-sentinel leak checks pass; 21 bypass attempts, 20 blocked (`sec''rets` quote-splitting gets through, now listed as a limit); all 7 deviations accepted; hygiene clean, nothing written outside the repo. — Cahyani (reviewer)
- Before merge: README limits now list shell quote-splitting. — Janice (pmo)
- Compliance: PASS — Revision 2 resolves every BLOCK item (fail-closed on all paths, k8s secret reads blocked, stderr leak-free, README limits, stricter allowlist, hygiene). Notes for build: match K8S_SECRET_BASH across newlines with a test; README adds that Write/Edit could weaken the installed config (recommend file permissions or managed settings) and that kubectl aliases are uncovered; every allowlist entry Merwyn adds needs human review. — Wulan (compliance)
- RAID R-6 verified 25 Nov 2026 against https://code.claude.com/docs/en/hooks: stdin has tool_name, tool_input, tool_use_id; exit 2 blocks and stderr is the reason; any other non-zero exit is non-blocking; default timeout 600 s, per-hook `timeout` in seconds; a timed-out PreToolUse hook does not block unless `"onFailure": "block"` is set (Claude Code v2.1.295+); matcher with non-plain characters is an unanchored regex on tool_name. Build: add `"onFailure": "block"` to the settings snippet alongside `|| exit 2`. — Janice (pmo)
- Compliance: BLOCK — fail-open path: only exceptions inside main() exit 2; a missing python3 (127), import/syntax error (1), stdin decode error or hook timeout would let a prod call through. Fix: settings command ends with `|| exit 2`; wrap the whole script incl. stdin read in the top-level handler; test broken import and undecodable stdin expect exit 2; README notes timeouts are non-blocking. — Wulan (compliance)
  - Also in the same revision: block `kubectl get secret(s)` in Bash and MCP read paths (credential leak); stderr names rule + tool only, never the command or SQL (WHERE may hold a NIK), with a test; README states the guard does not gate reads and is a safety net, not a security boundary, with its limits; Bytebase allowlist rejects `..` and only submits change issues; hygiene scan covers the test file; installed prod_guard.json never committed. — Wulan (compliance)
  - Escalated to Merwyn per human_gates (compliance BLOCK). Recommendation: accept all fixes, send back to Fang. — Janice (pmo)
  - 25 Nov 2026 21:47: Merwyn accepted all of Wulan's fixes. Back to Fang for a design revision. Default-deny with allowlist stays the working assumption; kubernetes scope and Bytebase allowlist contents remain open. — Janice (pmo)

## Decision
- The prod guard is a fail-closed PreToolUse hook covering Bash and MCP tool names; it is a safety net against agent mistakes, not a security boundary. Installing it, prod read access and a read-only DB role remain Merwyn's decisions. — April (curator)

## Open questions
- Spec-level questions are in Spec → Open questions; design-level ones in Design → Open questions. (Older duplicate removed by Fang.)
