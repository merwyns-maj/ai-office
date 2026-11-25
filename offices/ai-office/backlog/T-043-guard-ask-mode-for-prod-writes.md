---
id: T-043
title: "Prod-guard mode change: prod writes ask Merwyn, Bytebase always blocked"
phase: 4-code-tooling
status: spec
priority: P0
owner: pm
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
- [ ] Given a fixture prod write (Bash or MCP) that today exits 2, the hook exits 0 and prints JSON on stdout with `hookSpecificOutput.hookEventName` "PreToolUse", `permissionDecision` "ask" and a fixed `permissionDecisionReason` naming the rule id and saying Merwyn must confirm
- [ ] Given any Bash command or MCP tool that invokes Bytebase, the hook blocks (exit 2) with a reason telling the agent to prepare the plan and hand it to Merwyn, who submits it himself; the Bytebase allowlist in the config is empty and `load_config` rejects any entry
- [ ] Reads are unchanged (exit 0, no output); `k8s-secret-read` stays a hard block; every fail-closed path (malformed input, config error, internal error, deadline, wrapper `|| exit 2`) still exits 2
- [ ] The reason text never contains payload text (the sentinel test still passes for both the stderr and the JSON paths)
- [ ] The test command runs all cases including new ask, Bytebase-block and unchanged cases, and exits 0
- [ ] README states the new behaviour, that "ask" in a non-interactive run means denied, that Merwyn's confirmation in the prompt is his instruction, and that installing is not done here
- [ ] Wulan (compliance) has passed the design

## Spec
Written by the PM. Scope: `engine/guard/prod_guard.py`, its example config, tests, fixtures and README. Out of scope: installing anywhere; creating a read-only DB role (R-8).

## Design

## Build notes

## Review log

## Decision

## Open questions
- Compliance flag: prod access. Wulan checks the design before build.
