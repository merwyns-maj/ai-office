---
id: T-061
title: "Hotfix: budget test breaks when the ledger grows"
phase: 6-office
status: review
priority: P0
owner: reviewer
where: code
project: ai-office
depends_on: [T-060]
pr: null
---

> Found by Janice after appending runs 49-53 (PR #48): main is red. tests/test_budgets.py test_starting_use_is_76_percent_of_the_budget used the whole ledger, which grows after every agent run. Same class as T-055.

## Done when
- [ ] The test checks the starting values against the first 48 runs (the data they were set from) and stays green as runs are appended
- [ ] All tests pass on main after merge
- [ ] pr-workflow says planning-only PRs that append to usage/ run the test suite before merge

## Spec
Hotfix, spec by Janice (P0, main is red). — Janice (pmo)

## Design
Filter runs to n <= 48 in the test; one line in pr-workflow. — Janice (pmo), standing in for Fang

## Build notes
```
Ran 339 tests in 11.335s

OK
```
— Janice (pmo), building a P0 hotfix; Cahyani reviews

## Review log

## Decision

## Open questions
