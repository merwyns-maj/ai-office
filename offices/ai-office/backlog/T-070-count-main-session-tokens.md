---
id: T-070
title: "Count the main session's own tokens in the usage ledger"
phase: 6-office
status: build
priority: P2
owner: reviewer
where: code
project: ai-office
depends_on: []
pr: 70
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- The ledger header lists `main_session` under `not_reported`: the harness reports tokens for agent runs only, not for the main session (Janice, pmo). The page shows it as "not reported".
- Unknown: whether any source in this environment reports the main session's tokens (for example the `explain-usage` skill). To find out first, read-only.

## Done when
- [ ] A finding, with its source, on whether main-session tokens can be read here
- [ ] If yes: the ledger records them (format in engine/schema/usage.md) and the page counts them; if no: the reason is recorded and the page wording says so

## Spec
**Problem.** The ledger header lists `main_session` under `not_reported` (usage.md): the harness reports agent-run tokens only. The usage page therefore leaves out the main session's own tokens. We do not know whether any source here reports them.

**In scope**
- Step 1, read-only finding: find out whether main-session tokens can be read here, and from which source. Candidates: the `explain-usage` skill (a Claude app skill, not a repo file, so the finding means trying it in a session, an office step), and any other harness output visible in the session. Write the source, what it returned and its limits (whole session or since when) in the task.
- Step 2 depends on the finding. Yes: record the figure in the ledger and count it on the page. No: record the reason and make the page wording say so.

**Out of scope**
- Estimating or inferring tokens by any method: the PMO playbook says the report never estimates them.
- The input/output/cache split for agent runs (T-024 and T-026 supply it).
- Any paid resource, new connector or change outside this repo.

**Done when (reviewer can verify)**
1. The task holds a finding naming each source tried, the exact output or error, and the date; nothing was changed to get it.
2. If a source reports it: the ledger records the figure per the usage.md format (the format change, such as a new line kind or header field, is written in usage.md); `python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl` exits 0; the page shows the main-session figure in the totals and the ledger invariant still holds.
3. If no source reports it: the reason is recorded, `main_session` stays in `not_reported`, and the page wording says it is not reported and why; no number is shown.
4. Tests cover the changed ledger or page path; all tests, golden and `--check` pass.


**Finding, step 1** (Janice, 26 Nov 2026 20:05 WIB, read-only): the Claude app's `explain-usage` skill reports the main session's metered usage. Since the last context summary it showed 103 requests: input 250, cache write 211,583, cache read 26,678,886, output 52,012. It also gives a percent split by tool group. Limits: it counts only since the last summary (one earlier reply had no record), it gives no per-subagent figures, and the split is an estimate. The ledger's agent `tokens` are the harness's per-run totals, and whether those include cache reads is unknown. The Design must not add the two as if they were the same unit.

**Spec approved** (Janice, 26 Nov 2026 20:05 WIB).

## Design
**Approach.** Spec branch "yes" (Janice's finding: `explain-usage` reports it). A second line kind in the same ledger, kept apart from runs: `engine/runtime/ledger.py`, `engine/schema/usage.md`, `scripts/office_app.py`, `engine/app/office.template.html` (+ rebuilt `office.html`), `scripts/metrics.py` wording, tests. One comment edit in `workflow.yaml` (planning-only list: "appended run or main-session lines"); build after T-068, which edits the same file.

**Line format** (any line after the header; lines without `kind` stay runs):
```json
{"kind":"main_session","window":1,"date":"2026-11-26","source":"explain-usage skill","since":"last context summary","requests":103,"input":250,"cache_write":211583,"cache_read":26678886,"output":52012}
```
- Required: `kind`, `window` (int >= 1, never decreasing across lines; the PMO adds 1 after each context summary), `date`, `source` and `since` (1-200 chars, the window caveat), `input`, `cache_write`, `cache_read`, `output` (int 0..MAX); `requests` int or null; `note` optional. No `n`, `agent` or `tasks`.
- Errors: a `tokens` field ("main-session lines carry no tokens total; units differ from agent runs"); any of the four fields lower than the previous reading in the same window ("start a new window"); unknown kind. Data rule runs first, as for runs.
- Readings are cumulative: per window the last reading counts; windows add. The header `not_reported` keeps `main_session` (the harness still does not report it; append-only header) and usage.md says the metered lines are a different source.

**Code.** `parse_ledger_full(...) -> (header, runs, main, problems)`; `parse_ledger` stays a wrapper returning the old 3-tuple. `ledger.main_totals(main) -> {windows, readings, requests, input, cache_write, cache_read, output, since, last_date}` or None. `totals()` and `to_event_log()` see runs only, so the invariant is untouched. `build_data` sets `data.ledger.main = main_totals(...)`.

**Page (about +0.6 KB).** The existing `kind:'main'` row (template line ~1308) becomes, when `data.ledger.main` exists: name "Main session (metered)", cost text "in X · cache write Y · cache read Z · out W", second line dim "since <since>, <windows> window(s), <date>; explain-usage; not added to totals or budgets". No weighted single number: the four parts have different prices and providers.yaml prices are null, so weighting would be an estimate. Without lines it stays "Main session: not reported". aria-label carries the same text.

**PMO each explain-usage run** (pmo-playbook §8, 3 lines): run it at sprint close and before a known context summary; append one line with the four figures as shown, `since` copied from its window text, `window` +1 if a summary happened since the last reading; run `ledger`; never add it to a run line or estimate a missed window.

**Tests** (`test_ledger.py`, `test_office_app.py`): valid line parsed, runs totals and invariant unchanged with it present; `tokens` present, missing field, decrease in window, window decrease, unknown kind each error; two windows sum last-per-window; data-rule hit in `since` rejected; `to_event_log` ignores it; page data has `ledger.main`; built page shows "Main session (metered)" with lines and "not reported" without; `--check` and golden pass; page size stated in Build notes (limit 232 KB after T-067, leave room for T-069).

**Risks.** Overlap: unknown whether explain-usage includes subagent tokens, so it is never summed with agent `tokens` (row text says so). Earlier windows are lost: `since` states it. Not flagged for Compliance (counts only, no personal data).

**Decision record draft.** Decision: main-session usage is a separate `main_session` line kind, shown in its own row, never summed. Options: header field (header is append-only, cannot update); a run line with agent `pmo` (mixes units, breaks invariant meaning); separate kind (chosen).
— Fang (architect)

## Build notes
**What changed** (per the Design, no deviations in scope)
- `engine/runtime/ledger.py`: `kind:"main_session"` lines validated by `_check_main` (a `tokens` field, a missing or non-int figure, a lower figure in the same window, a lower `window`, an unknown kind, and `n`/`agent`/`tasks` are errors; the data rule runs first). New `parse_ledger_full` / `load_ledger_full` return `(header, runs, main, problems)`; `parse_ledger` / `load_ledger` keep the 3-tuple. `main_totals()`: last reading per window, windows add. `totals()` and `to_event_log()` take runs only, so the invariant is untouched.
- `scripts/office_app.py`: `data.ledger.main = main_totals(...)` (null without lines).
- `engine/app/office.template.html` (+ rebuilt `engine/app/office.html`): the main-session Detail row reads "Main session (metered)" with the four figures and the caveat line, aria-label the same; without lines it is unchanged ("Main session: not reported").
- `engine/schema/usage.md` (new section), `offices/ai-office/skills/pmo-playbook/SKILL.md` section 8 (explain-usage step), the `workflow.yaml` planning-only comment ("run or main-session lines"), `scripts/metrics.py` wording ("not reported here ... metered readings are in the ledger").
- Tests: `tests/test_ledger.py` (class `MainSession`, 7 tests) and `tests/test_office_app.py` (2 tests, fixture line in a temp copy). No real main-session line is appended to the session ledger; Janice does that after merge.

**Page size.** Committed `engine/app/office.html` 236,463 B (was 235,833 B, +630 B); limit 237,568 B (unchanged); headroom now 1,105 B. No trim needed. The template is 215,338 B before, see the diff for after. Published build with one fixture line: 252,312 B (100 events, the ledger has grown on main since T-067's 250,543 B).

**Deviation in layout, not scope.** My first row put the four figures in the right-hand `.cost` span (flex: none). In the headless check this squeezed the name to one character per line (row 377 px tall), overflowed the row, and made the usage panel auto-collapse (the T-067 no-overlap logic) at 1280x800 and 1280x1000. Fixed: the row is the name, then two dim `.l3` lines (figures; caveat). Row is 96 px tall at the desktop panel width. The figures are no longer in a right-aligned cost cell.

**How to verify**
- `python -m unittest discover -s tests` -> exit 0, 425 tests.
- `python -m engine.runtime validate ai-office` OK; `python scripts/office_app.py ai-office --chat --check` up to date; `python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl` -> 100 runs, 0 errors, 0 warnings, exit 0; `python scripts/board.py ai-office` ran, board.md discarded.
- Headless (Playwright with google-chrome, three.min.js routed from `engine/app/`): copy the ledger to /tmp, append the explain-usage figures from the Finding as a `main_session` line, build with `python scripts/office_app.py ai-office --ledger <copy> --chat --out /tmp/x.html`, open it, choose Detail in the usage panel. Result at 1280x800, 1280x1000, 1440x1200, 1920x1080, 768x900 and 390x844 (phone sheet via menu, Usage): the row shows "Main session (metered)", "in 250 · cache write 212k · cache read 26.7M · out 52k", "since last context summary, 1 window, 2026-11-26; explain-usage; not added to totals or budgets"; no overlap between the row's parts, no horizontal overflow, the panel stays expanded, zero console or page errors. No screenshots committed.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
- Does `explain-usage` or any harness output give the main session's tokens? Unknown; the finding answers it. For the office.
- If a figure exists, does it cover the whole session or a window, and does it overlap with agent-run tokens (the Sprint 7 close noted resumed-agent overlap)? For the office; the Architect decides how to avoid double counting.
- If the only source needs a connector, account or paid resource, that is a human gate. For Merwyn.
