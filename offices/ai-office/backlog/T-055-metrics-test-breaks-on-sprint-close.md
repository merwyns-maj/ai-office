---
id: T-055
title: "Hotfix: metrics test breaks when a new sprint closes"
phase: 3-skills
status: review
priority: P0
owner: reviewer
where: code
project: ai-office
depends_on: [T-032]
pr: null
---

> Found by Janice after the Sprint 5 close (PR #32): main is red. tests/test_metrics.py RealFiles.test_sprint_task_counts asserts the exact dict {1: 2, 2: 3, 3: 3, 4: 3}; closing Sprint 5 adds 5: 4.

## Done when
- [ ] The real-file test checks Sprints 1 to 4 only (their counts are history and cannot change) and stays green as later sprints close
- [ ] All tests pass on main after merge

## Spec
Hotfix, spec by Janice (P0, main is red): change only the assertion so it compares the Sprint 1–4 entries; no change to scripts/metrics.py. — Janice (pmo)

## Design
One-line test change; no compliance flag; no UX. — Janice (pmo), standing in for Fang on a one-line hotfix

## Build notes
Changed only the assertion in tests/test_metrics.py RealFiles.test_sprint_task_counts to compare Sprints 1–4. `python -m unittest discover -s tests`:
```
Ran 240 tests in 10.862s

OK
```
— Janice (pmo), building a one-line P0 hotfix; Cahyani reviews

## Review log

## Decision

## Open questions
