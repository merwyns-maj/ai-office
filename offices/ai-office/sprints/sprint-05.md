# Sprint 5

**Goal:** Measure how the office actually performs, prove skills with golden examples, and turn what has held up between Merwyn and the office into skills, all inside merwyns-maj/ai-office.

## Tasks (in order)
1. [T-032](../backlog/T-032-adoption-metrics-hours-saved-reject-rate.md) (P2→P1 this sprint): adoption metrics from this repo's own history (turnaround per stage, reject rate, escalations) with a script, first report for Sprints 1–4. Hours saved needs Merwyn's estimate per task type; asked as an open question, not blocking.
2. [T-049](../backlog/T-049-golden-examples-for-office-skills-slice-of-t-016.md) (P1): golden examples and a runner for the office's own skills, slice of T-016 (company skills stay behind T-002).
3. [T-041](../backlog/T-041-working-with-merwyn-discovered-over-time.md) (P2): four sprints have run; April proposes the working-with-merwyn skill from what held up. Merwyn approves it (his step).
4. [T-031](../backlog/T-031-monthly-chat-to-office-review.md) (P1): first monthly chat-to-office review (3+ repeats and a clear done). Runs from the main session, which can search chats; findings as pointers, never company data.

4 tasks, repo-only. Human steps: Merwyn approves T-041 and picks which T-031 findings become backlog. Not chosen: T-019, T-005, T-024 (need Merwyn), everything behind T-002.

## Exit criteria
- T-032, T-049 `done` with Reviewer PASS and merged; T-041 proposal and T-031 findings in front of Merwyn.
- Specs approved by Janice; at most 2 in build; tests pass; build_agents clean.

## Decisions recorded (Merwyn, 26 Nov 2026)
- 09:01: T-048 option (b), accept; data-rule gap to T-027.
- 09:07: the 3D office artifact renders, and the laptop frame rate is good (T-048 Done-when 6 and 8 confirmed). "Yes please proceed" to Sprint 5.

## Close (26 Nov 2026) — Janice (pmo)
Status: scope Green, schedule Green, budget Green.

**Finished:**
- T-049 golden examples and runner for partner-writing, spec-writing, review-checklist — PR #28 (Reviewer PASS)
- T-041 working-with-merwyn skill, loaded by Janice and April — PR #29 (Reviewer PASS; Merwyn approved option 1, 26 Nov ~09:45 WIB)
- T-032 adoption metrics, first report metrics/2026-11.md — PR #30 (one REJECT on Sprint 2 "not recorded", fixed; Reviewer PASS)
- T-031 first monthly chat-to-office review — PR #31 (Reviewer PASS; Merwyn picked all four items, 26 Nov ~09:45 WIB)

**What went well:** four tasks in parallel worktrees; Cahyani caught a metric that said "not recorded" where the record existed; Merwyn's two decisions came in one question card.

**What got stuck:** an engineer set status himself once (process note); a bad worktree loop briefly targeted the wrong task file (no change made).

**Decisions recorded (Merwyn, 26 Nov 2026 ~09:45 WIB):** approve working-with-merwyn as written; turn all four T-031 items into backlog (T-050 now; T-051, T-052, T-053 behind T-002).

**Carry forward:** T-050 document assessment skill (unblocked); T-054 tooling follow-ups; hours-saved estimates from Merwyn for the metrics; T-002, R-8, R-7, T-019 unchanged.
