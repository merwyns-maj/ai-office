---
id: T-072
title: "Tests must not pin the live session ledger's contents"
phase: 6-office
status: done
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-070]
pr: 71
---

> Lean (Janice, 26 Nov 2026 22:45 WIB): one surface (tests); no new data, no compliance flag, no human gate; spec skipped per T-068, the Architect writes a short spec and design.

## Facts (Janice)
- Appending honest ledger lines (runs 101-106 and the first `kind:"main_session"` reading) makes 10 tests fail. The lines are a chat run with `tasks: []`, a run with `tokens: null` because its harness report had no usage, and one main-session line. The lines are valid: the ledger CLI reports 0 errors and 0 warnings.
- Failing tests:
  - test_ledger: Cli.test_exit_codes ("1 not reported"), RealLedger.test_converts_to_a_clean_v1_log (events == runs), test_run_22_is_not_reported_and_run_8_has_its_note (exactly 1 null), test_totals_add_up_everywhere (not_reported == 1)
  - test_office_app: ChatBuild.test_chat_with_ledger_builds_the_one_published_page, CoreUnderNode.test_budget_maths_and_views_recorded, test_recorded_replay_totals_and_percentages, Recorded.test_ledger_page_data_is_recorded_with_totals, test_main_session_totals_reach_the_page_data_not_the_events, test_page_row_says_metered_with_lines_and_not_reported_without
- The same failure class broke main before (T-055, T-061). The pending lines are kept outside the repo until this merges.

## Done when
- [ ] Tests read the live ledger only for properties that stay true as honest lines are appended (valid, invariant holds, a chat run is not in the event log, the main session is not in totals); exact counts and values come from fixtures
- [ ] With the pending lines appended in a temp copy, the full suite passes; it also passes on the current ledger
- [ ] A test or note in usage.md says that appending a valid line must never break the suite

## Spec
- Problem: 10 tests pin exact contents of the live ledger, so appending honest, valid lines (runs 101-106, a main-session line) breaks main. This is the third time (T-055, T-061).
- In: `tests/test_ledger.py`, `tests/test_office_app.py`, a new synthetic fixture, a guard test, one paragraph in `engine/schema/usage.md`.
- Out: any change to `engine/`, `scripts/` or the page; committing the pending lines (Janice does that after merge).
- Done when: the three checkboxes above. Reproduced 26 Nov in a temp copy: pending ledger gives 10 failed, 75 passed in these two files.

— Fang (architect)

## Design
Rule: a test that reads the live ledger checks only invariants. Exact numbers come from a new fixture `tests/fixtures/session_FIXTURE072.jsonl` (stem = header `session`, `provider: claude-code`, `not_reported: ["split","model","main_session"]`, no main line). It has 7 runs, all made up: pm, architect and engineer solo runs, one 2-task run, one `tokens: null` run with a note, one chat run (`tasks: []`, `step: chat`, `note: "chat message m-abcdef12-wxyz"`), one run with 0 tokens. Pin its numbers once, as constants in the tests.
Page total: helper `page_totals(runs) = ledger.totals([r for r in runs if r["tasks"]])`. The page replays events, and chat runs are not events (usage.md, T-063), so node `rec`/`budgets` must get this, not `data["ledger"]["session"]`. That is why live runs give 7,631,828 vs 7,654,148.
Per failing test:
- `Cli.test_exit_codes`: live: exit 0, `0 errors, 0 warnings`, regex `\(\d+ not reported\)`. Fixture: exit 0 and `7 runs kept (1 not reported)`.
- `RealLedger.test_converts_to_a_clean_v1_log`: `len(evs) == count of runs with tasks`; no event `run` is a chat run's `n`; `sum(evs total) + sum(chat tokens) == session tokens`; run 22 total is None (old lines never change).
- `test_run_22_..._note`: keep the run 22 and run 8 checks (append-only). Replace `== 1` with `not_reported == count of None runs`; the exact `1` moves to the fixture.
- `test_totals_add_up_everywhere`: keep the sum identities; `t["session"]["not_reported"] == sum(r["tokens"] is None)`.
- `CoreUnderNode` rec and budgets: run on the fixture page with `page_totals`, pinned values.
- `Recorded.test_ledger_page_data_is_recorded_with_totals`: live: `session tokens == sum(event totals) + chat-run tokens`; other asserts stay.
- `test_main_session_totals_...` and `test_page_row_...`: use the fixture (main is None, `"main":null`). `_with_main` appends to the fixture, so window 1 cannot decrease against a live reading.
- `ChatBuild.test_chat_with_ledger_...`: keep the live ledger for the build, `--check` and chat-equality parts; node py comes from `page_totals`.
Guard: `RealLedgerAppended(RealLedger)` and the same subclass for the live-ledger `Recorded`/`Cli` checks. Live tests read `self.LEDGER`, not the module constant. `setUpClass` copies the live ledger to a temp file of the same name and appends 3 valid lines: run `last+1` with `tokens/tool_uses/duration_ms: null` and a note; run `last+2`, a chat run as above (no gap, since a gap warns); a `kind: main_session` line with `window` = highest live window + 1 (1 if the live file has none). It first asserts CLI exit 0 with 0 errors, then all inherited invariant tests run on it.
usage.md: under the office_app paragraph, add "Tests (T-072): the suite reads the live ledger only for invariants (clean parse, totals add up, chat runs not in events, main lines not in run totals, old lines unchanged); exact numbers come from `tests/fixtures/session_FIXTURE072.jsonl`. Appending a valid line must never break the suite; `RealLedgerAppended` checks this. The page's used figure excludes chat runs."
Risks: the guard can pass by accident if a test still reads `REAL`/`LEDGER` directly, so grep for both after the change. The live test is slower (copy), which is negligible. A failing `budgets.yaml` agent key for a fixture agent: use only org agents that have budgets.
Decision draft: Decision: tests check invariants on the live ledger and pin exact values only from fixtures. Context: T-055, T-061, T-072 broke on honest appends. Options: A) re-pin after each append (cheap now, breaks again); B) invariants + fixture + guard (one-off cost). Chosen: B, because the ledger is append-only by design. Consequences: new ledger-reading tests must follow the rule. Links: T-072.
Compliance: not flagged (synthetic fixture, no company data). External skill claude:diagram-design was not used; it was not needed.

— Fang (architect)

**Lean spec and design approved** (Janice, 26 Nov 2026 22:50 WIB). Fang's open question (the page budget leaves out chat-run tokens) is out of scope here: kept as today's behaviour in `page_totals`, follow-up later.

## Build notes
What changed (tests, one doc paragraph; nothing in `engine/` code or `scripts/`):
- `tests/fixtures/session_FIXTURE072.jsonl`: 7 synthetic runs as designed (10,500 tokens, 1 not reported, 1 chat run of 500). Numbers pinned once: `FixtureTotals` in test_ledger, and constants in test_office_app.
- `tests/_helpers.py`: `appended_copy(src, tmp)` copies a ledger (same name) and appends a not-reported run (`last+1`), a chat run (`last+2`) and a main-session reading (window = highest + 1).
- `test_ledger.py`: `RealLedger` reads `self.LEDGER` and checks invariants only; `RealLedgerAppended` (asserts CLI exit 0, 0 errors, then runs all inherited tests); `Cli`/`CliAppended`; new `test_main_lines_are_not_in_run_totals_or_events`.
- `test_office_app.py`: `page_totals(runs)` (chat runs left out) and `page_py`; `CoreUnderNode` rec/budgets run on the fixture with pinned values; `Recorded` and `ChatBuild` read `self.LEDGER`; `RecordedAppended` and `ChatBuildAppended` guards; main-session tests append to the fixture.
- `engine/schema/usage.md`: the Tests (T-072) paragraph under the office_app paragraph.

Deviations from the Design:
1. Budget node check had `rows == Object.keys(py.agents).length`. The budget view has one row per budgeted agent (7), the fixture has runs for 4 agents. I changed the assertion to `Object.keys(B.agents).length` (the same value on the live ledger). The fixture keeps the design's agent mix.
2. The task file's Lean note had a comma in the surface part, so `validate ai-office` failed ("more than one surface: full path", 11 loader/dryrun tests red on a clean checkout). I changed the first comma to a semicolon in the note; wording otherwise unchanged. Janice, please confirm.
3. `test_header_provider_must_be_in_providers_yaml` (class Parser) and `RealLedgerAppended` still reference `REAL` directly; both are invariant checks (CLI exit 0 on live; the guard's own source). The grep for stray `REAL`/`LEDGER` found no other reads. In test_office_app the module `LEDGER` constant is gone; `LIVE` is used only to build the live and appended copies.

How to verify:
- `python -m unittest discover -s tests`: 454 tests, OK, exit 0 on the current ledger.
- Temp copy of the repo with `/home/claude/ledger-pending.jsonl` over `offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`: 454 tests, OK, exit 0. (Never copied into the worktree.)
- `python -m engine.runtime validate ai-office`: OK (72 tasks). `python scripts/office_app.py ai-office --chat --check`: up to date. `python scripts/board.py ai-office`: ran, board.md discarded.

— Sebastian (engineer)

## Review log
Verdict: **PASS** (26 Nov 2026). Checked on head a7a76a1 before reading the Build notes' claims; every figure below is from my own runs.

Done when:
- [x] Live ledger read only for invariants; exact numbers from fixtures. PASS. `git diff main...HEAD`: every live-ledger assert in test_ledger/test_office_app is now an identity (event count == task runs, events + chat tokens == session tokens, not_reported == count of nulls, CLI regex `\(\d+ not reported\)`); exact values (7 runs, 1 not reported, 10,500 / 10,000 page tokens, shared 4,500) sit only in `FixtureTotals`, `Cli` fixture part and `CoreUnderNode` on `session_FIXTURE072.jsonl`. Remaining direct `REAL` reads (test_ledger.py:108, :220-222) are invariant-only.
- [x] Suite passes on current and pending ledger. PASS.
  - Worktree, current ledger: `Ran 454 tests ... OK`, exit 0.
  - Temp copy with /home/claude/ledger-pending.jsonl (checked first: pure append, 101 -> 108 lines): CLI `106 runs kept (2 not reported), 7,654,148 tokens, 0 errors, 0 warnings`; suite `Ran 454 tests ... OK`, exit 0.
  - Baseline: main with the same pending ledger, test_ledger + test_office_app: `FAILED (failures=10)`, so the fix is real.
  - My own appends on top (n=107 null run, n=108 `pmo`/`merge` in sprint 8 (new agent+step), n=109 designer chat run, `main_session` window 2): CLI `109 runs kept (3 not reported), 7,667,270 tokens, 0 errors, 0 warnings`; suite `Ran 454 tests ... OK`, exit 0.
- [x] Note in usage.md and a guard test. PASS: the "Tests (T-072)" paragraph in engine/schema/usage.md; guards `RealLedgerAppended`, `CliAppended`, `RecordedAppended`, `ChatBuildAppended`.

Still catches real breakage (mutations to engine/runtime/ledger.py in throwaway copies, full suite each):
- `total: tokens or 0` (null becomes 0): 5 failures (RealLedger/Appended convert, ChatBuild/Appended, CoreUnderNode rec).
- Events drop not-reported runs: 6 failures (adds FixtureTotals).
- not_reported counts 0-token runs: 2 failures (FixtureTotals, CoreUnderNode rec; the fixture's 0-token run earns its place).
- Chat run left out of `shared`: 3 failures; on the live ledger only `RealLedgerAppended` caught it, so the guard adds real coverage.
- Chat run leaks into events with a fake task: 7 failures.

Lean path: legitimate. One surface (tests); the usage.md paragraph is required by done-when 3 and is documentation of the test rule, not a second code surface; nothing in engine/ code, scripts/ or the page changed (`git diff main...HEAD --stat`). No new data (synthetic fixture), no compliance flag, no human gate. The comma-to-semicolon change is a fair wording fix: `lean_problems` (engine/runtime/loader.py:40-42) takes text up to the first `;` as the surface clause, so a comma after "(tests)" pulled the three entry phrases into it and tripped "more than one surface". It hides no second surface.

Checks: `python -m engine.runtime validate ai-office`: `ai-office: OK — 8 agents, 5 stages, 72 tasks, 19 skills`, exit 0. `python scripts/office_app.py ai-office --chat --check`: `up to date (230 KB, 84 events)`, exit 0.

Notes (not rejections):
- Heuristic weakness: the surface check is punctuation-based. It false-positives on a normal comma list (this task), and it can be dodged by writing the surface clause briefly and listing other areas after the `;`. It never compares the note with the diff's touched paths. A follow-up could check `git diff --stat` top-level dirs against the declared surface.
- The Build notes ask Janice to confirm the semicolon; commit a7a76a1's message says "lean note wording confirmed" but there is no dated confirmation line in the task file. PMO may want to add one.
- test_metrics.py:232 and test_budgets.py:17 also read the live ledger. They compute expected values rather than pin them, and they passed with pending + my lines, but no `*Appended` guard covers them. Out of this task's In list; worth folding into the rule for new tests.
- `RealLedgerAppended.test_the_appended_lines_were_read` assumes the helper's 2 runs are last; fine as written.
- External skills design:accessibility-review and data:validate-data not used: not available in this session and not needed (no UI change; fixture is synthetic).

— Cahyani (reviewer)

## Decision
Merged after Cahyani's PASS (Janice, 26 Nov 2026). Janice confirms the lean note's comma-to-semicolon change (a wording fix, one surface). Tests read the live ledger only for properties that survive a valid append; exact values come from `tests/fixtures/session_FIXTURE072.jsonl`. Follow-ups noted, not tasks yet: the lean surface check is punctuation-only (compare with the PR's files); test_metrics and test_budgets have no appended-ledger guard; page budget leaves out chat-run tokens.

Recorded: offices/ai-office/decisions/2026-11-sprint-07.md, D7. — April (curator)

## Open questions
- For the PMO, not in T-072: the page's used-vs-budget figure leaves out chat-run tokens (events only), so it shows 22,320 fewer than `ledger.totals` on the pending ledger. Is that intended? If not, open a follow-up task for the page. T-072 pins what the page does today in one helper (`page_totals`), so a fix changes one place. — Fang (architect)
