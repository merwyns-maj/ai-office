---
id: T-061
title: "Hotfix: budget test breaks when the ledger grows"
phase: 6-office
status: done
priority: P0
owner: pmo
where: code
project: ai-office
depends_on: [T-060]
pr: 49
---

> Found by Janice after appending runs 49-53 (PR #48): main is red. tests/test_budgets.py test_starting_use_is_76_percent_of_the_budget used the whole ledger, which grows after every agent run. Same class as T-055.

## Done when
- [x] The test checks the starting values against the first 48 runs (the data they were set from) and stays green as runs are appended
- [x] All tests pass on main after merge
- [x] pr-workflow says planning-only PRs that append to usage/ run the test suite before merge

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
Review of PR #49, head 000eaed (confirmed via gh api pulls/49), branched from origin/main 0fe04c4 (merge base = origin/main, so the branch is main after merge).

1. **Starting values checked against the first 48 runs, green as runs are appended: PASS**
   - origin/main is red: `python -m unittest tests.test_budgets` on a detached worktree at 0fe04c4 -> `AssertionError: 84 != 76`, `Ran 18 tests ... FAILED (failures=1)`.
   - Branch: `Ran 18 tests in 0.250s OK`.
   - Appended a fake run 54 (engineer, 900,000 tokens) to the ledger in a scratch worktree -> test `OK`.
   - Test still bites on the first 48 runs: run 9 tokens 80387 -> 80388 gives `AssertionError: 3813703 != 3813702`; deleting run 9 gives `3733315 != 3813702`; run 9 +900,000 gives `4713702 != 3813702`.
   - Test still bites on the budget: budgets.yaml claude-code tokens 5000000 -> 4000000 gives `AssertionError: 95 != 76`.
2. **All tests pass on main after merge: PASS** - branch full suite `python -m unittest discover -s tests` -> `Ran 339 tests in 10.685s OK`.
3. **pr-workflow says planning-only PRs that append to usage/ run the test suite before merge: PASS** - skills/pr-workflow/SKILL.md, board.md section, "Check before merge" line now adds "and the full test suite passes on the branch (tests read the ledger and sprint files ...; T-055, T-061)". Accurate: T-055 was tests/test_metrics.py breaking on a sprint close; tests/test_budgets.py reads usage/; test_metrics, test_office_app and test_events reference sprint files.

Scope: diff vs origin/main is tests/test_budgets.py, skills/pr-workflow/SKILL.md and this task file only. `python scripts/build_agents.py ai-office` -> "built 8 agents", `git status` clean, so generated agent files are unchanged.

Notes (not blocking): the new sum uses `r["tokens"] or 0` instead of `ledger.totals`; the pinned 3,813,702 makes any difference visible. The workflow.yaml comment defining planning-only does not itself mention the test run; the check lives in pr-workflow, which is what the spec asked for.

External skills design:accessibility-review and data:validate-data not available in this session; not relevant to a test-only change.

**Verdict: PASS** -> status done, owner pmo, awaiting PMO merge.
— Cahyani (reviewer)

## Decision

## Open questions
