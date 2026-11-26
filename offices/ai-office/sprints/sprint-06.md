# Sprint 6

**Goal:** Add the first skill the office can use on partner documents, clear the review follow-ups, and show model and usage per agent in the 3D office, all inside merwyns-maj/ai-office.

## Tasks (in order)
1. [T-056](../backlog/T-056-model-and-usage-in-the-3d-office.md) (P1): model and usage per agent across providers in the 3D office. Merwyn asked on 26 Nov 10:35. Dinda consults (UI).
2. [T-050](../backlog/T-050-document-assessment-skill.md) (P1): partner or vendor document assessment skill, from the T-031 picks.
3. [T-054](../backlog/T-054-tooling-follow-ups-golden-and-metrics.md) (P2): golden zero-case exit, per-line owner check, metrics partial sums.

3 tasks, repo-only. Not chosen: T-051 to T-053 (behind T-002), T-019, T-005, T-024 (Merwyn).

## Exit criteria
- All three `done` with Reviewer PASS and merged; the republished 3D office artifact shows models and usage.
- Specs approved by Janice; at most 2 in build; tests and golden runner pass.

## Decisions recorded (Merwyn, 26 Nov 2026 10:35 WIB)
- "Just proceed without me on this! I'll resolve blockers later on." Sprint 6 runs end to end; blockers (T-002, T-019, T-005, T-024) stay with Merwyn.
- New request: track the model in use and usage across multiple LLM providers in the 3D office (T-056).

## Close (26 Nov 2026) — Janice (pmo)
Status: scope Green, schedule Green, budget Green.

**Finished (all with Reviewer PASS, first time):**
- T-050 document assessment skill (architect, compliance) — PR #35
- T-054 golden zero-case exit, per-line owner check, metrics partial marker; metrics/2026-11.md regenerated with Sprint 5 — PR #36
- T-056 model and usage per agent in the 3D office (event log v1, providers.yaml, synthetic multi-provider replay) — PR #37. Artifact republished 26 Nov: https://claude.ai/artifact/CkB5c3hEKfaK61kUuUjMku

**What went well:** Dinda's consult and Fang's design fed one build that passed review first time; Cahyani summed the fixture herself and matched every panel row.

**What got stuck:** nothing blocking. The build-slot rule (at most 2) held T-056 back about one build cycle.

**Carry forward (reviewer notes, not blocking):** events CLI ignores providers.yaml problems (build still fails); usage panel collapse is instant, not animated; template-agreement golden R5 severity should be medium; real per-token prices are "not set" until Merwyn or a task fills them from provider pricing pages with a date. Real usage arrives with T-024 and T-026.

**Waiting on Merwyn (he will resolve later):** T-002, T-019, T-005, T-024; R-8, R-7. Open small questions: phone chip-only enough? plan-share view later?
