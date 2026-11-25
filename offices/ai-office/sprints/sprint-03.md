# Sprint 3

**Goal:** Let agents read prod and make every prod write wait for Merwyn's confirmation, with Bytebase left to Merwyn, while clearing the two Sprint 2 process lessons and applying his partner-writing decision, all inside merwyns-maj/ai-office.

## Tasks (in order)
1. [T-043](../backlog/T-043-guard-ask-mode-for-prod-writes.md) (P0): Merwyn decided on 25 Nov how agents touch prod; the guard must match (writes "ask", Bytebase always blocked, reads and fail-closed unchanged). It touches prod access, so Wulan checks the design; it goes first because it carries the longest chain (spec, design, compliance, build, review).
2. [T-044](../backlog/T-044-process-lessons-validate-warning-and-replay.md) (P1): R-11 (validate warns when base/defaults.yaml is missing) and R-12 (replay a branch's own commits onto fresh main instead of rebasing in shallow clones). Small, and it can run beside T-043 while the guard waits on compliance.
3. [T-045](../backlog/T-045-partner-writing-b2-financial-terms.md) (P2): partner-writing B2 widened to financial terms (tenor, outstanding); *virtual account* example confirmed. One-rule edit.

3 tasks, all repo-only, none behind a human gate in this sprint (installing the guard is not part of it), all unblocked. Not chosen: T-041 working-with-merwyn; T-019 install and T-024 SDK runs (R-5); everything behind T-002.

## Exit criteria
- T-043, T-044, T-045 are `done`: Reviewer PASS, PR merged by Janice; T-043 also has Wulan's compliance pass on the design.
- Specs approved by Janice before design; no task more than 2 days in one stage; at most 2 in `build`.
- `build_agents.py` runs clean; R-11, R-12, R-15 closed or updated in raid.md.

## Decisions recorded (Merwyn, 25 Nov 2026 22:44)
1. Partner-writing keeps financial terms in English (R-13, T-045).
2. Prod: reads allowed, writes on Merwyn's instruction only, Bytebase handed to Merwyn (R-14, T-043, R-7 and R-8 narrowed).
3. T-002: keep waiting, no chasing (R-1).

## Waiting on Merwyn
- T-002: org owner installs the Claude GitHub app on impact-credit-solutions (unblocks T-003, T-017, T-018, T-025). No chasing.
- R-8: before any guard install, is the `kubernetes` MCP server prod-only, and will you commission a read-only DB role and scoped kube role? Not needed this sprint.
- R-7: the SQL key names of the pg/mysql MCP tools (Bytebase part is closed). Not blocking; confirmed when T-043 is built.
