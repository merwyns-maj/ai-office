---
id: T-054
title: "Follow-ups: golden zero-case exit, per-line owner check, metrics partial sums"
phase: 3-skills
status: build
priority: P2
owner: reviewer
where: code
project: ai-office
depends_on: []
pr: 36
---

> Reviewer notes from T-049 and T-032 (Sprint 5).

## Done when
- [ ] scripts/golden.py exits 1 when no cases are found
- [ ] spec-writing open-question case checks an owner on every question line
- [ ] scripts/metrics.py marks a sprint sum as partial when some tasks are not recorded

## Spec

**Problem.** Cahyani's notes on T-049 and T-032 found three places where a tool passes when it should not or hides uncertainty: golden.py exits 0 when it finds no cases, one open-question case passes if any single line names an owner, and metrics.py sums known values without saying some tasks were not recorded.

**In scope**
- `scripts/golden.py`: no cases found for the office gives exit 1 with a message saying so.
- The spec-writing `open-question-owner` golden case: every question line under Open questions must name an owner, not just one line.
- `scripts/metrics.py`: when a sprint sum (REJECTs, BLOCKs, escalations, hours) includes tasks whose value is not recorded, the cell is marked partial (for example the sum with a "partial" marker and how many tasks are missing).
- Tests for each, and regenerating the committed metrics report if its output changes.

**Out of scope**
- Other review notes: the "Notes" check in review-checklist (heading exists only) stays as is.
- New golden cases or new metrics.
- Changing how "not recorded" is derived (T-032 Rework 1).

**Done when**
- [ ] With no `golden/*.json` under an office, `python scripts/golden.py <office>` exits 1 and prints a line naming the problem; with the shipped cases it still exits 0 (10 cases, 0 problems).
- [ ] Given the open-question case's `expected_output` with one question line lacking an owner, `golden.py` exits 1 naming the check; the shipped expected output passes; a `bad_output` with one ownerless line fails the check.
- [ ] Given a sprint where some tasks are not recorded, the metrics report cell for that sprint is marked partial and says how many tasks are missing; a sprint with all tasks recorded shows a plain number; a sprint with none recorded shows "not recorded".
- [ ] New tests cover the three cases above and `python -m unittest` passes; any test that assumed exit 0 on zero cases is updated.
- [ ] If the report changes, `offices/ai-office/metrics/` is regenerated and a grep for 10+ digit runs or emails finds nothing.

**Open questions**
- How to check "every question line" with the runner's current check types (regex over multiline text): Fang's choice; may need a new check type. Not blocking.
- Is the zero-case exit meant for a missing office folder too (that is exit 2 today)? Keep exit 2 for that; Fang to confirm.
- Does "partial" apply to the median turnaround column? Fang and Janice; not blocking, default: mark it too.

— Emmy (pm)

## Design

Baseline (26 Nov, this worktree at 95cc937): `python -m unittest` 240 tests OK; `python scripts/golden.py ai-office` exit 0, "10 cases, 41 checks, 0 problems".

**Approach** (three small changes, no new component, no new check type)
1. `scripts/golden.py` `main()`: right after `files = discover(repo, office)`, if `files` is empty print `golden: no cases found under base/skills/*/golden/ or offices/<office>/skills/*/golden/` (stdout, like other problems) and `return 1`. A missing office folder stays exit 2 (confirmed: that is a usage error, not an empty office). Update the module docstring's exit-code lines.
2. `offices/ai-office/skills/spec-writing/golden/open-question-owner.json`: add one check, keep the existing three.
3. `scripts/metrics.py`: sprint-row cells for REJECTs, BLOCKs, escalations and median turnaround carry a partial marker when some, not all, tasks are recorded.

**Interfaces**
- New check (appended as check 4, so the failure message reads `check 4 (must_not_match, Open questions) failed on expected_output`):
  ```json
  {"type": "must_not_match",
   "pattern": "^- (?!.*(?:\\((?:pmo|pm|architect|engineer|reviewer|curator|compliance|designer)\\)|Merwyn)).*$",
   "rule": "Open questions"}
  ```
  It matches any `- ` line with no owner, so one ownerless line fails it. Check 2 (must_match) stays, so an empty list cannot pass. I ran this regex: shipped `expected_output` gives no match (pass); the shipped `bad_output` matches (fail).
- Replace `bad_output` with one owned line plus one ownerless line, so it passes the old "any line" check and fails only the new one: `"**Open questions**\n- Which format should the report use? Fang (architect) can answer; blocks the build.\n- Does a second office need it? Not blocking."` (verified: check 2 passes, check 4 fails).
- `metrics.py`: replace `agg()` with `agg(ts, key) -> (total | None, missing: int)` and add
  `fmt_partial(value: str | None, missing: int) -> str`:
  - `missing == 0` gives the plain value (`"2"`, `"0.3"`)
  - nothing recorded (value None) gives `"not recorded"`
  - otherwise `f"{value} (partial, {missing} not recorded)"`, for example `1 (partial, 1 not recorded)`.
  The median uses the same rule over the known turnarounds: `0.3 (partial, 2 not recorded)`. Answer to the open question: yes, the median is marked too, same rule.
  The "Specs approved first time" cell already says `X of N (k not recorded)`; it stays as is (out of scope). The sprint table has no hours sum today (stage hours are per task only), so "hours" in the Spec maps to the median turnaround column.
- Add one line to "How these are measured": `- A sprint cell 'N (partial, k not recorded)' sums, or takes the median of, only the tasks with a recorded value; k tasks are missing.`

**Check type decision** (open question 1)

| Option | Code change | Reuse by other cases | Risk |
|---|---|---|---|
| A. `must_not_match` with a per-line negative lookahead (chosen) | none | any case (T-050 uses the same form for risk severity) | the regex is harder to read; the `rule` field and the `why` explain it |
| B. New `every_line` type (`select` regex plus `pattern`) | `_check_problems`, `run_check`, tests, docstring | same | more code to review; no second user today |

A is enough because `re.MULTILINE` with `.` (no DOTALL) keeps the lookahead to one line. If a third case needs per-line logic that a lookahead cannot express, add B then.

**Test plan** (in `tests/test_golden.py` and `tests/test_metrics.py`)
- Zero cases: temp repo with `workspaces.yaml` and an empty `offices/ai-office/` folder gives exit 1 and output containing `no cases found`. `run(["no-such-office"])` still gives 2.
- Shipped run: keep the `0 problems` assertion; do not hard-code `10 cases` (T-050 adds 3 cases in the same sprint; whichever merges second would break). If a count is asserted, use `len(golden.discover(REPO, "ai-office"))`.
- Per-line: copy `spec-writing/golden` into a temp repo; append `\n- Is a third format needed? Not blocking.` to `expected_output`; expect exit 1 and `check 4 (must_not_match, Open questions)`. The shipped case passes (covered by the shipped run).
- Metrics, unit: `fmt_partial` for (all recorded), (none), (some), for both an int sum and a median string.
- Metrics, fixture: `test_report` currently expects `| 1 | 2 [1] | ... | 1 | 1 | 1 |`, but that sprint has T-901 recorded and T-902 not, so it is already a partial sum. Update the expected row to `1 (partial, 1 not recorded)` for the three counts and `4.0 (partial, 1 not recorded)` for the median. Add one fixture sprint, or a direct `build_report` call, where every task is recorded, to show a plain number.

**Committed report.** `offices/ai-office/metrics/2026-11.md` is already stale: it was written before the Sprint 5 close and has no Sprint 5 row. In this worktree (shallow clone, 0 PR refs) a run gives PARTIAL HISTORY and many "not recorded" cells, so do not regenerate from a shallow clone. Follow steps 1 to 3 in the `metrics.py` docstring (unshallow, fetch PR refs), then regenerate, and run the grep for 10+ digit runs and emails. These are read-only fetches from this repo's own origin.

**Risks**
- The lookahead regex could match a non-question `- ` line in a future case. It only applies to this case's text, which is the Open questions list alone.
- Other tests may assert old sprint-row text. Engineer: `grep -n "| 1 | 2" tests/` before changing the format.
- Merge order with T-050 (cases count): handled by not hard-coding 10 (see Test plan).

**Flags.** Compliance: not flagged (repo scripts and test fixtures only; no prod, money or personal data). UX consult: not needed (no UI; the report text change is a table cell).

**Decision record draft (for Curator)**
```
Decision: Per-line golden checks use must_not_match with a per-line negative lookahead; no new check type.
Context: T-054; the open-question case passed when only one line named an owner.
Options: A lookahead regex, no code; B new every_line type, more code and tests, no second user yet.
Chosen: A because the existing runner already expresses it and T-050 can use the same form.
Consequences: Regexes are denser; add B if a case needs logic a lookahead cannot express.
Also: metrics sprint cells show "N (partial, k not recorded)" for sums and the median.
Links: T-054, T-049, T-032
```

— Fang (architect)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: Fang decides the check type for "every question line" and whether "partial" applies to the median too (recommend yes, same rule). — Janice (pmo)

Janice (pmo), 26 Nov: Design accepted, moved to build. Indonesian-language assessments: write in English by default; when asked in Indonesian, follow partner-writing (financial terms stay English). Not blocking. Engineer: do not set status.

## Build notes

**What changed**
- `scripts/golden.py`: no cases found for an existing office prints `golden: no cases found under base/skills/*/golden/ or offices/<office>/skills/*/golden/` and exits 1; unknown office stays exit 2; docstring updated.
- `spec-writing/golden/open-question-owner.json`: added check 4 (`must_not_match`, per-line negative lookahead, exact regex from the Design); `bad_output` is now one owned line plus one ownerless line; `why` explains the check.
- `scripts/metrics.py`: new `fmt_partial(value, missing)`; `agg()` returns `(total, missing)`; sprint cells for REJECTs, BLOCKs, escalations and the median turnaround show `N (partial, k not recorded)`; one line added to "How these are measured".
- `offices/ai-office/metrics/2026-11.md` regenerated from a full clone with PR refs: `git clone https://github.com/merwyns-maj/ai-office /tmp/cmx6`, fetched `+refs/pull/*/head:refs/remotes/origin/pr/*`, then `python scripts/metrics.py ai-office --repo /tmp/cmx6 --out offices/ai-office/metrics/2026-11.md` (is-shallow false, 35 PR refs, run at 95cc937). Header: `History: full (35 PR refs)`. Now has Sprints 1 to 5; all sprint cells are plain numbers (every task recorded), so no partial marker appears in this report. Grep for 10+ digit runs and emails: no hits.
- Tests: `tests/test_golden.py` (zero cases exit 1 with message, unknown office still 2, shipped count compared with `len(golden.discover(...))`, per-line check on a temp copy: ownerless line gives exit 1 and `check 4 (must_not_match, Open questions)`, bad_output fails only check 4). `tests/test_metrics.py` (`fmt_partial` all/none/some for int and median string; `test_report` row updated to the partial form for the fixture sprint). No total case count hard-coded.

**How to verify**
```
python scripts/golden.py ai-office           -> golden: 10 cases, 42 checks, 0 problems (exit 0)
python scripts/build_agents.py ai-office     -> built 8 agents
python -m engine.runtime validate ai-office  -> OK — 8 agents, 5 stages, 56 tasks, 17 skills
python -m unittest                           -> Ran 246 tests ... OK (was 240)
python scripts/board.py ai-office            -> 56 tasks (board.md discarded)
```

**Deviations from the Design**
- None in code. Design asked for a fixture sprint where every task is recorded; I covered "plain number" with `fmt_partial` unit tests instead, because the fixture cannot record T-902 without rebuilding its git history. The real regenerated report shows plain numbers for all five sprints.
- The task file was already at status build / owner engineer (uncommitted, from the PMO); committed as is with owner set to reviewer and pr set. Status not touched by me.

**Known limits**: the lookahead regex applies to every `- ` line in this case's text only. "hours" in the Spec maps to the median turnaround column, as in the Design.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
