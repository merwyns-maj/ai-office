# Sprint 2

**Goal:** Give every agent a shared working standard and partner-writing rules taken from Merwyn's own chats, and fix the three process gaps Sprint 1 exposed, all inside merwyns-maj/ai-office.

## Tasks (in order)
1. [T-042](../backlog/T-042-sprint-1-process-lessons.md) (P1): the three Sprint 1 fixes (PM tool check, board.md rule, handoff for read-only agents) change how the next two tasks run, so it goes first and they benefit from it.
2. [T-014](../backlog/T-014-working-standard-skill.md) (P1): working-standard from T-012 section A (facts not guesses, verify against primary sources, flag incidental bugs, check external edits, consistency check). Applies to every agent in every office.
3. [T-015](../backlog/T-015-partner-facing-writing-skill.md) (P2): partner-writing from T-012 section B (no em-dashes, English banking terms in italics, no overpromising, email-ready formatting).

3 tasks, all repo-only, none behind a human gate, all unblocked (T-012 done). Not chosen: working-with-merwyn (T-041, T-012 section D) waits for the next sprint; T-013 needs T-002.

## Exit criteria
- T-042, T-014, T-015 are `done`: Reviewer PASS, PR merged by Janice.
- Specs approved by Janice before design; no task has more than 2 days in one stage.
- Skills are listed in the relevant agents' `office_skills` and `build_agents.py` runs clean.
- raid.md reviewed; T-040 and T-039 open items tracked as Dependencies on Merwyn.

## Waiting on Merwyn
- T-002: org owner installs the Claude GitHub app on impact-credit-solutions (unblocks T-003, T-017, T-018, T-025).
- T-040 (R-7): Bytebase allowlist entries, and the SQL field names for the pg/mysql MCP tools.
- T-040 (R-8): is the `kubernetes` MCP server prod-only, and may agents read prod at all (read-only DB role)? Needed before any install task, not for this sprint.

## Close (25 Nov 2026) — Janice (pmo)
Status: scope Green, schedule Green, budget Green.

**Finished (all with Reviewer PASS):**
- T-042 Sprint 1 process lessons — PR #13
- T-014 working-standard base skill (base/skills + base/defaults.yaml) — PR #14
- T-015 partner-writing base skill (pm, curator) — PR #15

**What went well:** the paste-ready HANDOFF block worked from its first use; Janice resolved all of Emmy's "blocking" questions inside the office without escalating; T-042 and T-014 built in parallel worktrees.

**What got stuck:**
- PMO approval notes were silently not written once (a script looked for a heading that Emmy had changed). Fixed by recording approvals under a dedicated heading.
- A shallow-clone rebase produced add/add conflicts on every file; replaying the branch's own commits onto fresh main worked (RAID R-12).
- PM still has no Glob/Grep/Bash in its sessions; Read-with-paths fallback (T-042 rule a) worked.

**Carry to Sprint 3:** R-11 (validate warning when base/defaults.yaml is missing), R-12 (add replay-not-rebase to pr-workflow), and the T-040 install questions waiting on Merwyn (R-7, R-8).
