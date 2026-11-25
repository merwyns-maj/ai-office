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
