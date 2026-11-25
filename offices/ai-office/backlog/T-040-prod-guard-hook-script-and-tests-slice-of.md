---
id: T-040
title: "Prod-guard hook script and tests (repo-only slice of T-019)"
phase: 4-code-tooling
status: design
priority: P0
owner: architect
where: code
project: ai-office
depends_on: []
pr: null
---

> Slice of T-019 ("biggest risk reducer"). Builds and tests the guard here, using fixture commands only. Installing it in nimbus or klik-workspace is a write to a company repo and stays a Merwyn gate.

## Done when
- [ ] Given a fixture hook payload (JSON on stdin) whose Bash command writes to the prod target (e.g. INSERT/UPDATE/DELETE/DDL via a SQL client, or a deploy/migrate command), when the hook script runs, then it exits 2 and prints a reason naming the matched rule on stderr
- [ ] Given a fixture payload for a read-only command (e.g. SELECT, `git status`, `ls`), the script exits 0 with no stderr
- [ ] Given a fixture payload for a Bytebase script run that matches an entry in the allowlist file, the script exits 0; given one that matches no entry, it exits 2 (default deny)
- [ ] Given malformed or empty stdin, or a payload with no command, the script exits 2 (fail closed) and says why
- [ ] One test command (stated in the README) runs all fixture cases, exits 0, and the output lists at least 3 blocked, 3 allowed and 1 malformed case
- [ ] A scan of the repo files added by this task finds no real hostname, credential, connection string or data row (fixtures use obvious placeholders such as `prod.example.invalid`); the tests make no network call
- [ ] README (in the guard's folder) gives the settings snippet and steps a company repo would follow to install it, and states that installing is not done here

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

**Answers to the Spec's architect questions**
- *How prod is identified without hostnames:* by regex patterns over the MCP tool name (e.g. `-prod__`, `__kubernetes__`) and over the Bash command text (pg service names, kube contexts, client aliases). Patterns live in a JSON config. The repo ships `prod_guard.example.json` with tool-name patterns and `.invalid` placeholders only; the installed copy lives outside this repo (user `~/.claude/` or the company repo) and is where any local pattern is added.
- *Hook contract:* designed against the facts Janice gave (stdin JSON with `tool_name`, `tool_input`; `tool_input.command` for Bash; exit 2 blocks and stderr goes to Claude; exit 0 allows; `hooks.PreToolUse[].matcher` in settings.json). Not yet re-checked against current docs: logged as RAID R-6 (Assumption). Engineer verifies before opening the PR and notes the doc URL in Build notes.

**Approach**
- One self-contained hook script, stdlib only, copyable into any repo as a single file plus its config:
  - `engine/__init__.py`, `engine/guard/__init__.py` (empty, so tests can import)
  - `engine/guard/prod_guard.py` — the hook
  - `engine/guard/prod_guard.example.json` — starter config (tool-name patterns, placeholder command patterns, placeholder allowlist)
  - `engine/guard/README.md` — what it blocks, test command, settings snippet, install steps, and "installing is not done here"
  - `tests/__init__.py` (empty), `tests/test_prod_guard.py`, `tests/fixtures/guard/config.json`, `tests/fixtures/guard/cases.json`
- Policy is default-deny for anything identified as prod, fail-closed on any error. Nothing outside prod is touched: a non-prod call exits 0 silently.
- No change to `scripts/`, `.claude/settings.json` or any other repo. `engine/README.md` gets one row for `guard/` (whichever of T-039/T-040 merges second rebases; one-line change).

**Decision order (function `decide`)**

Input is the parsed payload. Rule ids below appear in the stderr message.

| Step | Bash (`tool_name == "Bash"`) | MCP (`tool_name` starts with `mcp__`) |
|---|---|---|
| 0 | Payload not a JSON object, no `tool_name`, or Bash without a string `tool_input.command` → **block** `malformed-input` | same; `tool_input` must be an object if present |
| 1 | No `bash.prod_targets` pattern matches the command → **allow** | No `mcp.prod_tools` pattern matches `tool_name` → **allow** |
| 2 | Command `re.fullmatch`es an `allowlist` entry with `tool: "Bash"` **and** contains no chaining characters (`;` `&` `\|` backtick `$(` newline) → **allow** `allowlist:<id>` | Tool name and SQL `re.fullmatch` an allowlist entry with that `tool` pattern → **allow** (starter allowlist has no MCP entries) |
| 3 | Any `bash.write` pattern matches, or `sql_write_keyword(command)` finds one → **block** `<rule id>` / `sql-write:<KEYWORD>` | `mcp.write_tools` matches → **block** `<rule id>` |
| 4 | Any `bash.read_only` pattern matches → **allow** | If a SQL text is found in `tool_input[f]` for `f` in `mcp.sql_fields` and `classify_sql` says write → **block** `sql-write:<KEYWORD>` / `sql-multi-statement` |
| 5 | → **block** `default-deny` | `mcp.read_tools` matches → **allow** |
| 6 | | `mcp.sql_tools` matches and SQL was found and is read-only → **allow**; matches but no SQL field → **block** `malformed-input` (fail closed) |
| 7 | | → **block** `default-deny` |
| — | Any other `tool_name` (not Bash, not `mcp__`) → **allow** (the matcher should not send them; out of scope) | |

SQL classifier (in code, not config, so a config cannot weaken it): strip `--` and `/* */` comments; `sql-multi-statement` if a `;` is followed by more non-space text; write if any whole word (case-insensitive) is in `INSERT UPDATE DELETE MERGE UPSERT REPLACE CREATE ALTER DROP TRUNCATE RENAME GRANT REVOKE COPY CALL DO EXEC EXECUTE SET RESET LOCK VACUUM REINDEX CLUSTER COMMENT REFRESH IMPORT LOAD INTO`, or the text contains `FOR UPDATE`/`FOR SHARE`, `nextval(`, `setval(`, `pg_terminate_backend`, `pg_cancel_backend`, `lo_import`, `lo_export`, `dblink`; otherwise read-only only if the first keyword is `SELECT`, `WITH`, `SHOW`, `EXPLAIN` (and not followed by `ANALYZE`), `DESCRIBE`, `DESC`, `TABLE` or `VALUES`; else `sql-not-read-only`. False positives (e.g. the word "update" inside a string literal) block, by design. For Bash only `sql_write_keyword` is used (no multi-statement rule, since `;` is normal shell).

**Interfaces**

CLI (`engine/guard/prod_guard.py`):
```
python3 prod_guard.py [--config PATH]          # hook mode: reads payload JSON on stdin
python3 prod_guard.py --check-config [--config PATH]   # validate config, print "prod-guard: config OK (<n> rules)"
```
Config lookup: `--config` → env `PROD_GUARD_CONFIG` → `prod_guard.json` in the script's folder. Not found, unreadable, invalid JSON, wrong `version`, missing key, or a regex that fails to compile → exit 2 with `prod-guard: config error: <reason>` (fail closed; a missing config blocks every matched call, and the message says how to fix it).

Exit codes: `0` allow (no stdout, no stderr). `2` block, malformed input, config error, or any unexpected exception (caught at top level). No other codes.

stderr on block (one line):
`prod-guard BLOCKED [rule=<rule-id>] <tool_name>: <reason>. Prod writes go through an allowlisted Bytebase script; ask Merwyn.`

Config (`prod_guard.example.json`; all patterns are Python regexes compiled with `re.IGNORECASE`; every rule has an `id`):
```json
{
  "version": 1,
  "bash": {
    "prod_targets": [
      {"id": "bash-prod-service", "pattern": "\\bservice=[\\w-]*prod\\b"},
      {"id": "bash-prod-kube-context", "pattern": "--context[= ]\\S*prod"},
      {"id": "bash-prod-placeholder-host", "pattern": "\\bprod\\.example\\.invalid\\b"}
    ],
    "write": [
      {"id": "bash-kubectl-write", "pattern": "\\bkubectl\\b.*\\b(apply|delete|create|patch|edit|replace|scale|rollout|set|label|annotate|drain|cordon|exec|cp)\\b"},
      {"id": "bash-helm-write", "pattern": "\\bhelm\\b.*\\b(install|upgrade|uninstall|rollback)\\b"},
      {"id": "bash-migrate-deploy", "pattern": "\\b(migrate|terraform\\s+apply|dbt\\s+(run|build|seed|snapshot)|make\\s+deploy)\\b|\\bdeploy\\S*\\.sh\\b"},
      {"id": "bash-sql-file", "pattern": "\\s(-f|--file)[= ]\\S+\\.sql\\b|<\\s*\\S+\\.sql\\b"}
    ],
    "read_only": [
      {"id": "bash-sql-client-command", "pattern": "\\b(psql|mysql|mariadb)\\b.*\\s(-c|-e|--command|--execute)[= ]"},
      {"id": "bash-kubectl-read", "pattern": "\\bkubectl\\b.*\\b(get|describe|logs|top)\\b"}
    ]
  },
  "mcp": {
    "prod_tools": [
      {"id": "mcp-prod-server", "pattern": "^mcp__.*-prod__"},
      {"id": "mcp-kubernetes", "pattern": "^mcp__.*__kubernetes__"}
    ],
    "write_tools": [
      {"id": "mcp-pg-write", "pattern": "__pg_(execute_mutation|manage_schema|import_table_data)$"},
      {"id": "mcp-kubectl-write", "pattern": "__kubectl_(apply|delete|create|patch|edit|replace|scale|rollout|exec|cp|label|annotate|drain|cordon)\\w*$"}
    ],
    "read_tools": [
      {"id": "mcp-pg-read", "pattern": "__pg_execute_query$"},
      {"id": "mcp-kubectl-read", "pattern": "__kubectl_(get|describe|logs|top)\\w*$"}
    ],
    "sql_tools": [
      {"id": "mcp-generic-sql", "pattern": "__(pg_execute_sql|mysql_query)$"}
    ],
    "sql_fields": ["sql", "query", "statement"]
  },
  "allowlist": [
    {"id": "bytebase-placeholder", "tool": "^Bash$",
     "command": "bytebase-run --project PLACEHOLDER --file migrations/[\\w./-]+\\.sql",
     "note": "Placeholder until Merwyn names the real Bytebase invocations (Spec open question)"}
  ]
}
```
Kubernetes is treated as prod by default (fail-safe) because the tool name does not say which cluster; see Open questions.

Python (`engine/guard/prod_guard.py`):
```python
class ConfigError(Exception): ...
Decision = NamedTuple("Decision", [("allow", bool), ("rule", str), ("reason", str)])
def load_config(path: pathlib.Path) -> dict          # validates + compiles; raises ConfigError
def find_config(cli_path: str | None) -> pathlib.Path
def classify_sql(sql: str) -> tuple[bool, str]       # (read_only, rule_id); rule_id "" when read-only
def sql_write_keyword(text: str) -> str | None       # first write keyword found, upper-case
def decide(payload: object, config: dict) -> Decision
def main(argv: list[str] | None = None, stdin=sys.stdin, stderr=sys.stderr) -> int
```
Imports allowed: `argparse, json, os, pathlib, re, sys, typing` only.

Settings snippet for the README (user-level `~/.claude/settings.json`, because MCP servers are session-wide, not per repo):
```json
{"hooks": {"PreToolUse": [{"matcher": "Bash|mcp__.*",
  "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/prod_guard.py --config ~/.claude/hooks/prod_guard.json"}]}]}}
```

**Tests** (`python -m unittest -v` from the repo root; stated in the README)
- `tests/fixtures/guard/cases.json`: list of `{name, expect: "allow"|"block"|"malformed", rule?: str, stdin: <payload object or raw string>}`. `test_prod_guard.py` generates one test method per case named `test_<expect>_<name>` (so `-v` output lists each), runs the script with `subprocess.run([sys.executable, script, "--config", fixture_config], input=...)`, and asserts exit code, empty stderr on allow, and `rule=<rule>` in stderr on block.
- Minimum cases: block — Bash `psql "service=nimbus-prod" -c "DELETE ..."`, Bash `kubectl --context prod-cluster apply -f x.yaml`, Bash `psql service=nimbus-prod -f fix.sql`, Bash allowlist-lookalike with `; psql ...` chained, MCP `..._nimbus-prod__pg_execute_mutation`, `..._pg_manage_schema`, `..._pg_import_table_data`, `..._kubernetes__kubectl_delete`, MCP `mysql_query` with `UPDATE`, MCP `pg_execute_sql` with `SELECT 1; DROP TABLE t`, MCP `pg_execute_query` whose SQL contains `DELETE`, unknown prod tool (`..._nimbus-prod__pg_something_new`) → `default-deny`, Bash Bytebase invocation not on allowlist → `default-deny`. Allow — `git status`, `ls -la`, Bash `psql service=nimbus-prod -c "SELECT count(*) FROM t"`, MCP `pg_execute_query` SELECT, MCP `mysql_query` SELECT, `kubectl_get`, non-prod MCP tool (`mcp__remote-devices__nimbus-staging__pg_execute_mutation`), Bytebase allowlisted invocation. Malformed — empty stdin, `not json`, `[]`, missing `tool_name`, Bash with no `command`, `sql_tools` call with no SQL field.
- Unit tests for `classify_sql` (comments, multi-statement, `EXPLAIN ANALYZE`, `SELECT ... INTO`, `FOR UPDATE`, CTE with `DELETE`).
- Config tests: missing file, bad JSON, bad regex → exit 2 with `config error`.
- `test_example_config_valid`: `--check-config --config engine/guard/prod_guard.example.json` exits 0.
- Hygiene test: scans `engine/guard/` and `tests/fixtures/guard/` and fails on any domain-like token not ending in `.invalid`/`.example`/`example.com`, any `://` URL with credentials, `password`/`passwd`/`secret`/`token` followed by `=` or `:` and a value, or an IPv4 address other than `127.0.0.1`/`0.0.0.0`.
- No-network test: parses `prod_guard.py` with `ast` and asserts its imports are within the allowed list above; tests themselves import nothing network-related.

**Risks**

| Risk | Handling |
|---|---|
| Regex guard is bypassable (a script file that calls psql, base64 piped into sh, env vars holding the target, a new MCP tool name) | Default-deny on anything that names prod; unknown prod MCP tools blocked. Stated plainly in README: this is a seatbelt against agent mistakes, not a security boundary. Real control is a read-only DB role for agent sessions (follow-up, Merwyn gate). |
| MCP `tool_input` field names for SQL are not confirmed | `sql_fields` is config; a `sql_tools` call with no recognised field is blocked. Open question below to confirm from a real payload (field names only, no data). |
| Hook payload / exit-code contract differs from assumption | RAID R-6; Engineer verifies against Claude Code hook docs before PR. |
| Missing or broken config blocks every Bash and MCP call | Clear `config error` message with the path searched; `--check-config` in install steps. Accepted: fail closed is the spec. |
| False positives on read queries | Accepted (fail closed). User rephrases or Merwyn adds an allowlist entry. |
| Allowlist entry too loose lets a chained write through | `fullmatch` + reject chaining characters before allowlist match; test case covers it. |
| Hook latency | One Python start per matched call (~30–50 ms). Acceptable. |

**Flags.** Touches access control to production data (nimbus-prod, MariaDB prod, Kubernetes): **Compliance (Wulan) must check this design before build.** Installing the hook anywhere (user settings, nimbus, klik-workspace) is a Merwyn human gate and is not part of this task.

**Decision record (draft for April)**
```
Decision: Guard prod with one stdlib PreToolUse hook covering Bash and MCP tools, default-deny and fail-closed, with prod identified by tool-name and command regexes in a JSON config.
Context: T-019/T-040. Agents can reach nimbus-prod, MariaDB prod and Kubernetes through MCP tools and Bash; nothing blocks writes today. No hostnames or credentials may live in this repo.
Options: A — hook script + JSON pattern config (pro: no dependency, one file to install, testable offline; con: regex is bypassable).
         B — per-server MCP permission deny rules in settings.json (pro: native; con: tool-level only, cannot tell SELECT from DELETE in a generic SQL tool, nothing for Bash).
         C — read-only DB roles for agent sessions (pro: real boundary; con: needs prod credential and DBA changes, a human gate, out of repo scope).
Chosen: A now, because it is buildable and testable here; C recommended as the follow-up real control; B can complement A at install time.
Consequences: Easier: one tested guard reused across repos. Harder: config must track new MCP tool names (unknown prod tools are blocked, so drift fails safe). Follow-ups: Merwyn's Bytebase allowlist; install task (gate); read-only DB role (gate).
Links: T-040, T-019, RAID R-6.
```

**Open questions (design)**
- Merwyn: is the `kubernetes` MCP server prod-only, or does it also reach staging? Design treats it as prod (fail-safe). Non-blocking.
- Merwyn: which `tool_input` key carries the SQL for `pg_execute_sql`, `pg_execute_query` and `mysql_query` (key names only, no query text or data)? Design assumes one of `sql`, `query`, `statement`. Non-blocking: unknown keys fail closed.
- Merwyn: Bytebase allowlist entries (from the Spec) still open; build ships the placeholder.

— Fang (architect)

## Build notes

## Review log
- Compliance: BLOCK — fail-open path: only exceptions inside main() exit 2; a missing python3 (127), import/syntax error (1), stdin decode error or hook timeout would let a prod call through. Fix: settings command ends with `|| exit 2`; wrap the whole script incl. stdin read in the top-level handler; test broken import and undecodable stdin expect exit 2; README notes timeouts are non-blocking. — Wulan (compliance)
  - Also in the same revision: block `kubectl get secret(s)` in Bash and MCP read paths (credential leak); stderr names rule + tool only, never the command or SQL (WHERE may hold a NIK), with a test; README states the guard does not gate reads and is a safety net, not a security boundary, with its limits; Bytebase allowlist rejects `..` and only submits change issues; hygiene scan covers the test file; installed prod_guard.json never committed. — Wulan (compliance)
  - Escalated to Merwyn per human_gates (compliance BLOCK). Recommendation: accept all fixes, send back to Fang. — Janice (pmo)
  - 25 Nov 2026 21:47: Merwyn accepted all of Wulan's fixes. Back to Fang for a design revision. Default-deny with allowlist stays the working assumption; kubernetes scope and Bytebase allowlist contents remain open. — Janice (pmo)

## Decision

## Open questions
- Spec-level questions are in Spec → Open questions; design-level ones in Design → Open questions. (Older duplicate removed by Fang.)
