---
id: T-072
title: "Tests must not pin the live session ledger's contents"
phase: 6-office
status: build
priority: P1
owner: reviewer
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

## Decision

## Open questions
- For the PMO, not in T-072: the page's used-vs-budget figure leaves out chat-run tokens (events only), so it shows 22,320 fewer than `ledger.totals` on the pending ledger. Is that intended? If not, open a follow-up task for the page. T-072 pins what the page does today in one helper (`page_totals`), so a fix changes one place. — Fang (architect)
