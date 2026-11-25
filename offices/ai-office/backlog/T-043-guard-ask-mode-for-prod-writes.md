---
id: T-043
title: "Prod-guard mode change: prod writes ask Merwyn, Bytebase always blocked"
phase: 4-code-tooling
status: review
priority: P0
owner: reviewer
where: code
project: ai-office
depends_on: [T-040]
pr: null
---

> Follow-up to T-040 (done, PR #11) after Merwyn's decision of 25 Nov 2026 22:44. Repo-only: changes the guard here. Installing it in nimbus or klik-workspace stays a human gate. Touches prod access, so Compliance (Wulan) must check the design.

## Decision to implement (Merwyn, 25 Nov 2026)
- Agents may read prod. Read-only is the default.
- Prod writes only when Merwyn instructs. Bytebase: agents never submit; they prepare the plan and hand it to Merwyn, who submits it himself.
- Verified fact (Claude Code docs, https://code.claude.com/docs/en/hooks, PreToolUse decision control): `permissionDecision` "ask" prompts the user to confirm and shows `permissionDecisionReason` in the prompt; in a `-p` run where no one can answer, the call is denied and Claude reads the reason. Precedence: deny > defer > ask > allow.

## Done when
- [ ] Given a fixture prod write (Bash or MCP) that a write rule blocks today (see Open question 1 for the exact set), when the hook runs, then it exits 0, stderr is empty, and stdout is one JSON object with `hookSpecificOutput.hookEventName` "PreToolUse", `permissionDecision` "ask" and a fixed, non-empty `permissionDecisionReason` that names the rule id and says Merwyn must confirm
- [ ] Given any Bash command containing the word `bytebase`, or any MCP tool whose name contains `bytebase`, whether or not it names prod or looks like a read, when the hook runs, then it exits 2, stdout is empty, and the stderr reason tells the agent not to submit, to prepare the plan and hand it to Merwyn, who submits it himself
- [ ] The allowlist is empty in `prod_guard.example.json` and in the test fixtures; given a config with any allowlist entry, `load_config` fails and the hook exits 2 with `rule=config-error`; the old allowlist-allow tests are removed or turned into this check
- [ ] Unchanged, shown by the existing fixture cases still passing: reads exit 0 with empty stdout and stderr; every `k8s-secret-read` case exits 2; every fail-closed case (malformed input, input too large, config error, internal error, deadline, broken import, missing interpreter, through the `|| exit 2` wrapper) exits 2 with empty stdout (no "ask" JSON on any error path)
- [ ] Given any ask, block or malformed case, neither stdout nor stderr contains the command or any SQL field value; the `PII_SENTINEL_X` test also covers an ask case (a write whose SQL holds the sentinel)
- [ ] The old reason text "Prod writes go through an allowlisted Bytebase change issue" no longer appears in `engine/guard/` (code, config, README, tests)
- [ ] `python -m unittest -v` from the repo root exits 0 and lists at least: 1 Bash ask, 1 MCP write-tool ask, 1 MCP SQL-write ask, 1 Bash and 1 MCP Bytebase block, and the unchanged read, secret and fail-closed cases
- [ ] `engine/guard/README.md` states: prod writes ask Merwyn; Bytebase is always blocked and left to Merwyn; in `-p`/headless runs "ask" ends as a denial with the reason shown to Claude (cites https://code.claude.com/docs/en/hooks); Merwyn's confirmation in the prompt is his instruction; which settings (permission mode, allow rules) could auto-approve an "ask" (R-15); installing is not done here
- [ ] Wulan (compliance) has passed the design

## Spec
**Problem.** Merwyn decided on 25 Nov 2026 that agents may read prod, that prod writes happen only on his instruction, and that agents never submit to Bytebase. The T-040 guard hard-blocks every prod write and routes writes to an allowlisted Bytebase submission, so it contradicts that decision.

**In scope** (`engine/guard/prod_guard.py`, `prod_guard.example.json`, `tests/test_prod_guard.py`, `tests/fixtures/guard/`, `engine/guard/README.md`)
- Prod writes change from block to "ask" with a fixed reason shown to Merwyn.
- Bytebase (Bash and MCP) always blocked, allowlist empty and rejected if non-empty.
- Remove the stale "allowlisted Bytebase change issue" wording.

**Out of scope**
- Installing the guard anywhere (human gate); creating a read-only DB role or scoped kube role (R-8).
- Any change to read handling, `k8s-secret-read`, fail-closed paths, the deadline or the settings snippet.
- Confirming the SQL key names of the pg/mysql MCP tools (R-7; non-blocking).

**Open questions**
1. Which blocks become "ask"? Proposed: write-rule matches (Bash write rules, `sql-write:*`, MCP write tools). Proposed to stay blocks: `default-deny`, `sql-multi-statement`, `sql-not-read-only`, because they are unclear rather than clear writes. Merwyn (via Janice) confirms. Blocking for design.
2. Can an "ask" be auto-approved (permission mode such as bypass, or an allow rule)? Engineer re-checks the docs and lists every case in the README (R-15). Fang designs for it; blocking for design only if an auto-approve path exists.
3. Tool note: Glob, Grep and Bash were not available in this session; I read the files at the paths in the PMO's brief. The T-043 text of the 25 Nov decision was taken from the task, sprint-03 and raid.md R-14 and R-15; I did not re-fetch the docs URL (Engineer does, R-15).

— Emmy (pm)

## Design
**Approach** (logic change in the guard; files: `engine/guard/prod_guard.py`, `engine/guard/prod_guard.example.json`, `engine/guard/README.md`, `tests/test_prod_guard.py`, `tests/fixtures/guard/cases.json`, `tests/fixtures/guard/config.json`; `slow_config.json` already has `"allowlist": []` and stays as is)
- `decide()` returns one of three actions: allow, ask, block. Only clear writes become ask (Janice Q1): a `bash.write` rule match, a Bash `sql-write:*` keyword, an `mcp.write_tools` match, an MCP `sql-write:*`. Everything else that blocks today still blocks.
- Bytebase moves out of config into code, like `k8s-secret-read`, so a config cannot weaken it: any Bash command or MCP tool name containing `bytebase` (any case) blocks with `rule=bytebase`, before the prod-target check.
- The allowlist machinery is deleted. The `allowlist` key stays required and must be `[]`; a non-empty list is a config error, so an old T-040 config with entries fails loudly instead of being silently ignored.
- Output: ask writes exactly one JSON line to stdout and exits 0; block writes one line to stderr and exits 2; allow writes nothing and exits 0. All stdout writing happens at one point, after the decision is final.

**Interfaces**

1. `Decision = NamedTuple("Decision", [("action", str), ("rule", str), ("reason", str)])`, with `ALLOW, ASK, BLOCK = "allow", "ask", "block"`. Helpers `_allow(rule)`, `_ask(rule)`, `_block(rule)`. `reason` is `REASONS[...]` for block, `ASK_TEXT` for ask, `""` for allow.

2. Constants (in code):
```python
_BYTEBASE = re.compile(r"bytebase", re.IGNORECASE)   # substring: also catches bytebase-cli, bytebase_x, mcp__bytebase__*
ASK_TEXT = ("This is a prod write and runs only if Merwyn confirms it. Merwyn: read the full command, "
            "and any file it runs, before you confirm. If it is denied, do not try another way; "
            "hand the change to Merwyn.")
REASONS["bytebase"] = ("Agents never submit to Bytebase. Do not try another way: prepare the plan "
                       "(change, target, rollback) and hand it to Merwyn, who submits it himself.")
REASONS["default-deny"] = "The call targets prod and is not recognised as read-only."   # "nor on the allowlist" removed
```
Delete `ALLOWLIST_ACTION`, `CHAIN_CHARS`, `_APPLY_WORDS`, `allowlist_eligible`, `_allowlisted`.

3. `decide()` order, first match wins:
   - Bash: malformed checks (unchanged) → `k8s-secret-read` block (unchanged) → `_BYTEBASE.search(cmd)` block `bytebase` → no prod target: allow → `bash.write` rule: **ask** `<rule id>` → `sql_write_keyword`: **ask** `sql-write:<KW>` → `bash.read_only`: allow → block `default-deny`.
   - MCP: `tool_input` not a dict: block `malformed-input` (unchanged) → `k8s-secret-read` (unchanged) → `_BYTEBASE.search(name)` block `bytebase` → no prod tool: allow → classify every SQL field value; if any gives `sql-multi-statement` or `sql-not-read-only`, block with that rule → `mcp.write_tools` match: **ask** `<rule id>` → any SQL field gave `sql-write:<KW>`: **ask** that rule → `read_tools`: allow → `sql_tools`: allow if SQL present else block `malformed-input` → block `default-deny`.
   - One new behaviour to note: a write tool (`pg_execute_mutation`) whose SQL has two statements blocks `sql-multi-statement` instead of asking, so Merwyn always confirms one statement at a time. Before T-043 it blocked anyway, so nothing that blocked now passes. (For write tools, `sql-not-read-only` on e.g. `BEGIN` also blocks; that is the "cannot tell, so block" rule.)

4. `load_config`: `allow = data["allowlist"]`; `if not isinstance(allow, list) or allow: raise ConfigError("allowlist must be empty: agents never submit to Bytebase and no prod write is pre-approved")`. `cfg["allowlist"]` is dropped; `n_rules` counts only bash and mcp rules. Example and fixture configs: `"allowlist": []` and the `bash-bytebase` entry removed from `bash.prod_targets` (dead once the code rule runs first).

5. Formatters (no payload text, ever):
```python
def _tool_label(tool_name) -> str            # moved out of format_block: "<unknown>" | "<invalid>" | name if _TOOL_OK
def format_block(rule, tool_name, extra="") -> str
    # "prod-guard BLOCKED [rule=<rule>] tool=<tool>. <reason>[ (<extra>)] Do not try another way; ask Merwyn."
    # the old suffix "Prod writes go through an allowlisted Bytebase change issue; ask Merwyn." is gone
def format_ask(rule, tool_name) -> str       # returns the whole stdout text, newline-terminated
    reason = f"prod-guard ASK [rule={_clean(rule)}] tool={_tool_label(tool_name)}. {ASK_TEXT}"
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "ask",
                                              "permissionDecisionReason": reason}},
                      separators=(",", ":")) + "\n"
```
Exact stdout for the fixture `bash_kubectl_apply_prod` (one line):
```
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"prod-guard ASK [rule=bash-kubectl-write] tool=Bash. This is a prod write and runs only if Merwyn confirms it. Merwyn: read the full command, and any file it runs, before you confirm. If it is denied, do not try another way; hand the change to Merwyn."}}
```
`sql-write:DELETE` appears as the rule id; the keyword comes from the guard's fixed list, not from the payload.

6. Single write point, so a crash never ends as "ask JSON, then fail open":
   - `_run(args, stdin, stderr) -> tuple[int, str]` returns `(code, stdout_text)` and never writes stdout itself: `(0, "")` allow, `(0, format_ask(...))` ask, `(2, "")` after writing the stderr line for a block. `--check-config` returns `(0, "prod-guard: config OK (N rules)\n")`.
   - `main(argv=None, stdin=None, stderr=None, stdout=None)`: inside the existing `try` (deadline still armed): `code, out = _run(...)`; `if out: stdout.write(out); stdout.flush()`; `return code`. Nothing that can raise runs after the flush except `signal.alarm(0)` in `finally`.
   - `_entry()` unchanged: any exception, including one from `format_ask`, `write` or `flush`, becomes the `internal-error` stderr line and exit 2.
   - Why this holds: every error path (malformed, too large, config error, internal error, deadline, broken import, missing interpreter) returns or dies before the only stdout write, so stdout is empty. If the process dies after the write (signal, a flush error at interpreter shutdown, which gives exit 120), the exit is non-zero, the `|| exit 2` wrapper makes it 2, and on exit 2 Claude Code blocks and ignores stdout JSON. Fail-open would need exit 0 with no JSON; the ask path cannot return 0 before the write and flush succeed.

7. Tests (`tests/test_prod_guard.py`, `cases.json`):
   - `CaseMixin.check` gains `expect == "ask"`: exit 0, stderr `""`, stdout is one line, `json.loads` equals exactly `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": <reason>}}` with `f"rule={case['rule']}"` and `"Merwyn confirms"` in the reason; the payload-echo check runs on stdout and stderr for ask and block. Block and malformed keep "stdout empty".
   - Fixtures turned from block to ask (same names, rule unchanged): `bash_psql_delete_prod`, `bash_kubectl_apply_prod`, `bash_kubectl_apply_prod_multiline`, `bash_psql_file_prod`, `bash_helm_upgrade_prod`, `bash_migrate_prod`, `bash_placeholder_host_update`, `mcp_pg_execute_mutation`, `mcp_pg_manage_schema`, `mcp_pg_import_table_data`, `mcp_kubectl_delete`, `mcp_mysql_query_update`, `mcp_pg_execute_query_with_delete`, `mcp_pg_execute_query_select_into`.
   - Bytebase, block `rule=bytebase`: the six existing Bytebase cases (`bash_allowlist_lookalike_chained`, `bash_bytebase_not_on_allowlist`, `bash_bytebase_dotdot`, `bash_bytebase_apply`, `bash_bytebase_redirect`, and `bash_bytebase_allowlisted` renamed `bash_bytebase_submit_blocked`, expect block); new `bash_bytebase_read_like` (`bytebase-cli list issues`, no prod word), `bash_bytebase_mixed_case` (`ByteBase issue create`), `mcp_bytebase_tool` (`mcp__bytebase__create_issue`), `mcp_bytebase_read_tool` (`mcp__remote-devices__bytebase__list_projects`). Stderr of each contains "hand it to Merwyn".
   - New block `mcp_pg_mutation_multi_statement` (`pg_execute_mutation`, `UPDATE t SET a=1; DROP TABLE t`) → `sql-multi-statement`.
   - Unchanged (still block, same rule): `mcp_pg_execute_sql_multi`, `mcp_pg_execute_sql_explain_analyze`, `mcp_unknown_prod_tool`, `mcp_sql_tool_pii_sentinel`, all `k8s_*` and `mcp_kubectl_get_*secret*`, all allow and malformed cases, all `TestFailClosed` tests.
   - `TestCaseCoverage`: ask >= 3, and asserts at least one Bash ask, one MCP write-tool ask, one MCP `sql-write:` ask, one Bash and one MCP `bytebase` block.
   - `TestSentinelLeak.test_pii_sentinel_never_echoed_on_ask`: `pg_execute_mutation` with `UPDATE t SET a=1 WHERE nik = 'PII_SENTINEL_X'`, and Bash `psql service=nimbus-prod -c "DELETE FROM t WHERE nik='PII_SENTINEL_X'"`; exit 0 and `PII_SENTINEL_X`, `nik` absent from stdout and stderr.
   - `TestFailClosed.test_ask_crash_exits_2`: patch `prod_guard.format_ask` to raise `RuntimeError("PII_SENTINEL_X")`, run `_entry()` with an ask payload and a `StringIO` stdout: exit 2, stdout `""`, `rule=internal-error` on stderr, sentinel absent. `test_ask_flush_failure_exits_2`: stdout object whose `flush` raises `OSError`: exit 2, `rule=internal-error`.
   - `TestConfig`: delete `test_allowlist_action_apply_rejected`, `test_allowlist_without_action_rejected`, `test_allowlist_eligibility_enforced_in_decide`; add `test_allowlist_nonempty_rejected` (append the old placeholder entry: hook exits 2 with `rule=config-error`, and `--check-config` exits 2). `test_example_config_valid` stays.
   - `TestUnits`: delete `test_allowlist_eligible`; `test_decide_in_process` uses `d.action`; add `test_format_ask` (valid JSON, exact keys, hostile tool name gives `tool=<invalid>`, no newline inside the line); `test_format_block_has_no_payload_text` also asserts `"Bytebase change issue"` not in the line.
   - `TestHygiene.test_no_old_allowlist_wording`: for every file in `engine/guard/` and `tests/` guard files, `("allow" "listed Bytebase") not in text` (built by concatenation so the test does not match itself).

8. README (`engine/guard/README.md`), replace or add:
   - Intro and Files table: exit 0 with no output allows; exit 0 with one JSON line on stdout asks Merwyn; exit 2 with one stderr line blocks.
   - Decision order as in 3 above, naming which rules ask and which block, and why `default-deny`, `sql-multi-statement`, `sql-not-read-only` block (cannot tell what it does).
   - Bytebase: always blocked in code, any context; the agent prepares the plan and hands it to Merwyn, who submits it himself. Allowlist: must be empty; any entry is a config error. Delete the "Allowlist entries are for submitting a Bytebase change issue only..." paragraph and "Every allowlist entry needs human review" from Known limits.
   - Ask semantics, citing https://code.claude.com/docs/en/hooks (PreToolUse decision control): the prompt shows the reason; precedence deny > defer > ask > allow; in `-p`/headless runs nobody can answer, so the call is denied and Claude reads the reason. Merwyn's confirmation in the prompt is his instruction (R-14).
   - "What could auto-approve an ask" (R-15, Janice Q2): every permission mode and allow-rule case the docs give, each with what install must set to prevent it. Re-checked against the docs page, URL and date in Build notes.
   - Known limits, add: `bash-sql-file` asks without the file's SQL in the prompt (the reason tells Merwyn to read the file); Bash SQL-word false positives (`set`, `do`, `cluster`) now ask instead of block; Bytebase match is a substring, so any command that only mentions it (for example a grep in docs) blocks (fails closed); `byte''base` quote-splitting is the same gap as `sec''rets`; Bytebase MCP is matched on the tool name only, not on arguments.
   - Install step 6: in a throwaway session try a placeholder write (expect a prompt), a Bytebase call (expect a block with the hand-to-Merwyn reason), and a read (passes). The settings snippet is unchanged: `|| exit 2` keeps exit 0 (with or without JSON) as is.

**Risks**
| Risk | Handling |
|---|---|
| An ask is auto-approved by a permission mode or allow rule (R-15) | Engineer re-checks the docs before the PR. If any path auto-approves, stop and hand back to Fang and Wulan before the PR, with the install setting that closes it (candidate to verify: managed `permissions.disableBypassPermissionsMode`) |
| Crash after deciding ask | Single write point; any failure is exit 2, which blocks and ignores stdout (interface 6); two tests |
| Merwyn approves without reading (long SQL, a `.sql` file not shown) | Reason tells him to read the command and any file; multi-statement SQL blocks; known limit in README |
| Payload leaks into stdout via the reason | Reason built only from rule id, sanitised tool name, fixed text; sentinel tests on ask |
| Old config with allowlist entries silently ignored | Non-empty allowlist is a config error, so every call blocks until fixed |
| Bytebase false positives | Intended (fail closed); README names it |
| Weakening: write-rule false positives now ask instead of block | Accepted under Merwyn's 25 Nov decision; README names it; Wulan to confirm |

**Flags for Compliance (Wulan).** Prod access and prod writes: this design turns hard blocks into Merwyn-confirmed writes. Please check: the ask/block split (3), the crash handling (6), the auto-approve question (R-15), and the weakening row above.

**Incidental (A4, out of scope, for Janice).** Three files still name "Bytebase change issues" as the approved prod-write path, which contradicts R-14: `base/agents/compliance.md` line 13 (and generated `.claude/agents/compliance.md` line 14), `offices/ai-office/skills/compliance-playbook/SKILL.md` line 20, `offices/ai-office/skills/uu-pdp-checklist/SKILL.md` line 11. T-043 is limited to `engine/guard/`, so I propose a small follow-up task; Wulan should know her own checklist still says it.

**Decision record draft (for Curator)**
```
Decision: The prod guard asks Merwyn (PreToolUse permissionDecision "ask", exit 0) for clear prod writes, blocks (exit 2) Bytebase always and anything it cannot classify, and keeps reads, k8s-secret-read and fail-closed unchanged; the allowlist must be empty.
Context: Merwyn, 25 Nov 2026 (R-14): agents may read prod, write only on his instruction, never submit to Bytebase. The T-040 guard hard-blocked writes and routed them to an allowlisted Bytebase submission. Supersedes that part of T-040's design.
Options: A, ask for clear writes, block the rest (Janice Q1); B, ask for every non-read prod call (also default-deny, multi-statement); C, keep hard blocks and let Merwyn run writes himself.
Chosen: A, because Merwyn's confirmation is his instruction and a prompt is only meaningful when the guard knows the call is a write; B asks him to approve things nobody classified; C contradicts his decision.
Consequences: The control now depends on Merwyn reading the prompt and on no auto-approve path (R-15). In -p runs every write is denied with the reason. Bytebase is in code. Follow-up: compliance skills still name Bytebase change issues (incidental above).
Links: T-043, T-040 (PR #11), R-7, R-14, R-15, PR (tbd)
```

— Fang (architect)

## Approvals (PMO)
- Spec approved. Q1: only clear write rules (Bash write rules, sql-write, MCP write tools) become "ask"; default-deny, sql-multi-statement and sql-not-read-only stay hard blocks (when the guard cannot tell what a statement does, it blocks). This applies Merwyn's 25 Nov decision; Merwyn is told and can widen it. Q2: the engineer documents every path that could auto-approve an "ask" (permission modes, allow rules) in the README. — Janice (pmo)

## Approvals (PMO)
- R-15 checked 25 Nov 2026 against https://code.claude.com/docs/en/permissions (Precedence among rules, hooks, and mods) and https://code.claude.com/docs/en/permission-modes: (1) deny and ask rules are evaluated regardless of what a PreToolUse hook returns, so settings can only make the guard stricter; no allow-rule override of a hook "ask" is documented. (2) Auto mode cannot silently approve a hook-forced prompt. (3) BYPASS: without managed settings or a Team/Enterprise login (Merwyn's personal Max login), an installed mod handling tool.check can approve a call a PreToolUse hook blocked or would prompt for. README must list this and recommend no tool.check mods on machines where the guard is installed (or managed settings). (4) bypassPermissions behaviour for hook "ask" is not documented: test with claude --debug before any install (install is already a human gate). — Janice (pmo)

## Build notes
**What changed** (branch `t-043-guard-ask-mode`; files in `engine/guard/`, `tests/`, `tests/fixtures/guard/`)
- `prod_guard.py`: `decide()` returns allow / ask / block. Clear writes (Bash write rule, Bash `sql-write:*`, MCP write tool, MCP `sql-write:*`) ask; `default-deny`, `sql-multi-statement`, `sql-not-read-only` still block. Bytebase is in code (`_BYTEBASE`, substring, any case, Bash command or MCP tool name, `rule=bytebase`, after `k8s-secret-read`, before the prod-target check). Allowlist machinery deleted; `allowlist` must be `[]` or `config-error`. `_run` returns `(code, stdout_text)`; `main` writes stdout once at the end and flushes; `_entry` unchanged.
- Example and fixture configs: `"allowlist": []`, `bash-bytebase` prod target removed.
- README rewritten for ask/Bytebase/allowlist, ask semantics, R-15 list, Wulan notes 1 and 2 (bypass, tool.check mods, no bypassPermissions for engine/SDK runs, install step 0 `claude --debug` ask test per permission mode, `|| exit 2` + `onFailure: block` + throwaway-session check mandatory, R-14 read approval, legal sign-off his to confirm, R-8 read-only role the real control, no prod rows in repo/brains/logs). Cites https://code.claude.com/docs/en/hooks and https://code.claude.com/docs/en/permissions.
- Tests: 14 fixtures turned to ask; 6 Bytebase fixtures now `bytebase` block (`bash_bytebase_allowlisted` renamed `bash_bytebase_submit_blocked`) plus 4 new; new `mcp_pg_mutation_multi_statement`; new ask-crash, flush-failure, ask-through-wrapper, ask sentinel, `test_format_ask`, `test_allowlist_nonempty_rejected`, `test_no_old_allowlist_wording`, `test_required_kinds_present`; three old allowlist tests and `test_allowlist_eligible` removed.

**How to verify**
```
python3 -m unittest -v          # Ran 154 tests ... OK (60 guard case tests; 14 ask)
```
Command form from the README (`python3 engine/guard/prod_guard.py --config engine/guard/prod_guard.example.json || exit 2`), real output:
```
ask   {"tool_name":"Bash","tool_input":{"command":"kubectl --context prod-cluster apply -f x.yaml"}}
 -> {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"prod-guard ASK [rule=bash-kubectl-write] tool=Bash. This is a prod write and runs only if Merwyn confirms it. Merwyn: read the full command, and any file it runs, before you confirm. If it is denied, do not try another way; hand the change to Merwyn."}}   exit=0
block {"tool_name":"mcp__bytebase__create_issue","tool_input":{}}
 -> prod-guard BLOCKED [rule=bytebase] tool=mcp__bytebase__create_issue. Agents never submit to Bytebase. Do not try another way: prepare the plan (change, target, rollback) and hand it to Merwyn, who submits it himself. Do not try another way; ask Merwyn.   exit=2
allow {"tool_name":"Bash","tool_input":{"command":"ls"}}  -> (no output) exit=0   (covered by the allow cases)
```
Note: `kubectl --context prod-cluster get pods` asks (`sql-write:CLUSTER`): the word "cluster" in the context name trips the SQL-word scan. It blocked before T-043; it is the documented false-positive limit, not a new gap.

**Done-when -> evidence**
1. Ask fixtures: `test_ask_*` (14 cases): exit 0, stderr empty, one JSON line with exact keys, reason has rule id and "Merwyn confirms" (`CaseMixin.check`). Pass.
2. Bytebase: `test_block_bash_bytebase_*` (6), `test_block_mcp_bytebase_tool`, `test_block_mcp_bytebase_read_tool`: exit 2, stdout empty, stderr contains "hand it to Merwyn". Pass.
3. Allowlist: `test_allowlist_nonempty_rejected` (hook and `--check-config` exit 2, `rule=config-error`), `test_allowlist_empty_in_shipped_configs`. Pass.
4. Unchanged: read/allow, all `k8s-secret*` and fail-closed tests pass untouched; `test_ask_crash_exits_2`, `test_ask_flush_failure_exits_2` added (stdout empty, exit 2, `rule=internal-error`). Pass.
5. No payload echo: `CaseMixin.check` asserts on stdout and stderr; `test_pii_sentinel_never_echoed_on_ask` (SQL and Bash) and the old block sentinel test. Pass.
6. Old wording: `test_no_old_allowlist_wording`; `grep` of `engine/guard/` and `tests/` finds none. Pass.
7. `python3 -m unittest -v`: 154 tests, OK; includes Bash ask, MCP write-tool ask (`mcp_pg_execute_mutation`), MCP SQL-write ask (`mcp_mysql_query_update`), Bash and MCP Bytebase blocks, read, secret and fail-closed cases (`test_required_kinds_present` asserts the kinds).
8. README states all listed points. Pass (reviewer to read).
9. Wulan conditional PASS: notes 1 and 2 in README; note 3 for the Reviewer.

**Deviations / not done**
- R-15 re-check of the docs pages: I could not fetch https://code.claude.com/docs/en/* from the build sandbox (proxy returned 403 on all three pages). The README R-15 list therefore rests on Janice's 25 Nov check (Approvals block) and says so. Reviewer or Merwyn should confirm on a machine with access, and the install step 0 `claude --debug` test is the real proof. No auto-approve path was found that I could add beyond those Janice listed; bypassPermissions stays "treat as auto-approve".
- `format_block` suffix is now "Do not try another way; ask Merwyn." (design said the old suffix is gone, new text not specified). Bytebase block lines therefore say "Do not try another way" twice; harmless.
- Nothing installed, `~/.claude` untouched, `board.md` not committed.

— Sebastian (engineer)

## Review log
- Compliance: PASS — T-043 design: every fail-open path (stdout, JSON, flush) closed, no payload in ask or block output, Bytebase moved to code, allowlist forced empty. PASS is conditional on notes 1 to 3 being in the README or install gate. — Wulan (compliance)
  1. README + install gate: never run bypassPermissions / --dangerously-skip-permissions on a guarded machine (treat bypass as auto-approving an ask until the claude --debug test shows otherwise); no tool.check mods unless managed settings; engine/SDK runs must not set bypassPermissions; install step 0 = claude --debug ask test in each permission mode; `|| exit 2`, onFailure: block and the throwaway-session prompt check are mandatory.
  2. README read-access line: Merwyn approved agent reads 25 Nov (R-14); legal sign-off for cloud contexts is his to confirm; read-only DB role (R-8) is still the real control; no prod rows in repo, brains or logs.
  3. Reviewer checks the README states findings 3 and 4 and that sentinel tests pass on ask and block.
  4. Follow-up (Janice, before T-019 install): update base/agents/compliance.md, compliance-playbook, uu-pdp-checklist away from "Bytebase change issues"; rebuild agents. Not in this PR.
  - Recorded by Janice (pmo) from Wulan's HANDOFF block.

## Decision

## Open questions
- Compliance flag: prod access. Wulan checks the design before build.
- R-15 auto-approve paths: Engineer lists them from the docs before the PR; if any path auto-approves an ask, back to Fang and Wulan (design section, Risks). Who: Sebastian (engineer).
- Compliance skills still name Bytebase change issues as the write path (incidental in Design). Who: Janice decides on a follow-up task.
