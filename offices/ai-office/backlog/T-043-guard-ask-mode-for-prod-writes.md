---
id: T-043
title: "Prod-guard mode change: prod writes ask Merwyn, Bytebase always blocked"
phase: 4-code-tooling
status: design
priority: P0
owner: architect
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

## Approvals (PMO)
- Spec approved. Q1: only clear write rules (Bash write rules, sql-write, MCP write tools) become "ask"; default-deny, sql-multi-statement and sql-not-read-only stay hard blocks (when the guard cannot tell what a statement does, it blocks). This applies Merwyn's 25 Nov decision; Merwyn is told and can widen it. Q2: the engineer documents every path that could auto-approve an "ask" (permission modes, allow rules) in the README. — Janice (pmo)

## Build notes

## Review log

## Decision

## Open questions
- Compliance flag: prod access. Wulan checks the design before build.
