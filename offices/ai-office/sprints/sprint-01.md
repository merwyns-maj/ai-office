# Sprint 1

**Goal:** Put two safeguards for running agents in place, a prod-write guard and an engine that can load and dry-run this office, entirely inside merwyns-maj/ai-office.

## Tasks (in order)
1. [T-040](../backlog/T-040-prod-guard-hook-script-and-tests-slice-of.md) (P0): the biggest risk reducer; build and test the guard with fixtures before agents touch anything near prod. Repo-only slice of T-019.
2. [T-039](../backlog/T-039-engine-loader-and-dry-run-slice-of-t-024.md) (P1): the engine loader and dry-run is the base for cost logging, BAU workflows and the app, and spends no SDK credit. Repo-only slice of T-024.

Only 2 tasks: the other unblocked tasks (T-012, T-031, T-032 chat-only; T-016 needs company skills) are not repo-only, and everything else depends on T-002 or on tasks not yet built.

## Exit criteria
- T-040 and T-039 are `done`: Reviewer PASS, PR merged by Janice.
- Both specs approved by Janice before design.
- raid.md reviewed; remainders of T-019 and T-024 re-planned in sprint 2.

## Waiting on Merwyn
- T-002: org owner installs the Claude GitHub app on impact-credit-solutions (unblocks T-003, T-017, T-018, T-025).
- T-040: confirm what counts as an allowed Bytebase script, or accept default-deny with an allowlist.

## Retro (closed 25 Nov 2026)

**Finished**
- T-040 prod-guard hook and tests: PR #11, Reviewer PASS, merged. 133 tests.
- T-039 engine loader and dry-run: PR #9, Reviewer PASS, merged. 46 tests.
- Also merged in the sprint window: T-012 chat-mining (PR #10), T-037 and T-038 playbooks (PR #7).

**Cycle notes.** Sprint ran in one day (25 Nov); per-stage timestamps were not recorded, so cycle time per task is not measured. T-040 took the longest because of one Design revision. Rework: T-040 one compliance BLOCK; neither task had a Reviewer REJECT. WIP never exceeded 2.

**What got stuck: T-040.** Compliance (Wulan) BLOCKed Design Rev 1: fail-open paths (missing python3, import error, stdin decode error, hook timeout), `kubectl get secret` reads, stderr that could echo a NIK, a loose allowlist, and no statement of what the guard does not do. Escalated to Merwyn per human_gates; he accepted all fixes the same day (21:47). Fang issued Rev 2, Wulan passed it, build and review followed. Resolution held: Reviewer found 20 of 21 bypass attempts blocked; the one that passes (shell quote-splitting) is listed as a README limit. R-6 (hook contract) was verified against the Claude Code docs and closed.

**Lessons (each becomes work in T-042)**
1. The PM agent's Glob/Grep were unavailable in its session, so it wrote the T-040 spec without reading the parent tasks T-019/T-024 (its Open questions say so). Fix: PM checks tool access at the start and, if it cannot read the parents, stops and tells the PMO, who pastes the parent text.
2. Two task branches both edited the generated `board.md`, causing rebase conflicts. Proposed rule: do not commit `board.md` on task branches; the PMO regenerates and commits it on main after each merge (or a `.gitattributes` merge driver that takes main's copy). T-042 picks one and writes it into `pr-workflow`.
3. Reviews and handoffs came back as chat text and the orchestrator wrote the Review log and status. Fix: the `handoff` skill says read-only agents (Reviewer, Compliance, Architect without write access) return paste-ready text (section, signature, proposed status/owner) and the PMO records it. No agent is left half-finished.

**Carried to Sprint 2:** R-5 remainders of T-019 and T-024 stay blocked: T-019 install needs Merwyn gates; T-024 needs paid SDK runs. T-002 still open.
