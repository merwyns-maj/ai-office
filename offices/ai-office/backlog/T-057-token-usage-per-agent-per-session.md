---
id: T-057
title: "Record and show real token usage per agent, per session"
phase: 6-office
status: done
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-056]
pr: 40
---

> Merwyn, 26 Nov 2026 11:20 WIB: "Yes please do, evaluate in each session, each agents how much token they used." Today the only real numbers are the harness's per-run reports (total tokens, tool uses, duration) that the main session sees after each agent run; Janice has collected them for Sprints 4–6 of this session (/tmp/t057/session-runs.jsonl, outside the repo until built). The split into input, output and cache, and the main session's own tokens, are not reported to us. When the office runs on the SDK (T-024), each result message carries that split and this ledger fills itself.

## Done when
- [ ] A documented per-session agent-run ledger (one file per session under offices/ai-office/usage/) with agent, tasks, step, total tokens, tool uses, duration, source and an explicit "not reported" for what the harness does not give; this session's Sprints 4–6 recorded from the harness reports
- [ ] metrics.py adds a token section: per session, per agent, per sprint and per task (run count, total tokens, share of session, tokens per task), and the monthly report shows it
- [ ] The 3D office can replay a recorded ledger (usage_source: recorded): per-agent totals in the usage panel without the "synthetic" label, with "split not reported" where only totals exist
- [ ] Recording is part of the process: the PMO playbook says to append a ledger line after every agent run, and T-024/T-026 say the SDK runtime writes the same format with the split
- [ ] Share of the Max plan is not claimed unless a real limit is known; the report states why
- [ ] Tests for the ledger parser, totals and the report section; no company data in the ledger

## Spec

**Problem.** Merwyn wants to know how many tokens each agent used in each session, but today the numbers exist only as per-run harness reports in the main session's chat and are lost when it is summarised (Sprints 1-3 of this session are already gone). The panel in the 3D office shows only invented ("synthetic") numbers.

**Facts this spec rests on**
- The harness reports one total per agent run (tokens, tool uses, duration). It does not give the input/output/cache split, nor the model actually used. The main session's own tokens are not reported.
- Seed data: /tmp/t057/session-runs.jsonl (header + 33 runs, Sprints 4-6). Run 22 has null usage. Run 8 (designer) ran as a general-purpose agent, so its model was the session default, not the profile model.
- Max plan limits are not published as a fixed token number.
- Log v1 `usage` events (engine/schema/events.md) carry input/output/cache; the ledger here cannot, until the SDK runtime (T-024, T-026) writes them.

**In scope**
- Ledger: one JSONL file per session under offices/ai-office/usage/, named by the Claude session id (this session: session_01MDGJq3GfaeozLojJo8W5Td). A header line (session id, source, recorded_by, covers, date) then one line per agent run. A future session appends only to its own file; a new session id starts a new file.
- Fields per run: n, sprint, agent, tasks, step, tokens, tool_uses, duration_ms, optional note. Anything the harness does not give is written as an explicit "not reported" (split, main-session tokens, model used); a null-usage run stays in the ledger as "not reported", never as 0. Model is the profile model, labelled "assumed from profile"; a run with a known different model (run 8) carries a note.
- Seed the ledger from the 33 runs; state in its header that Sprints 1-3 and the main session's own tokens are missing.
- metrics.py token section (and in the monthly report offices/ai-office/metrics/2026-11.md): per session, per agent, per sprint, per task: run count, total tokens, share of session total, tokens per task. A multi-task run is split across its tasks in one stated way (open question 1).
- 3D page replays a ledger as a log with usage_source: recorded: per-agent totals in the usage panel with no "synthetic" label, and "split not reported" where only totals exist. Dinda consults on the panel wording and layout.
- Process: pmo-playbook gets a rule to append a ledger line after every agent run; T-024 and T-026 get a line saying the SDK runtime writes the same format, adding the split.
- Tests: ledger parser, totals, report section, data rule.

**Out of scope**
- Estimating the input/output split or the main session's tokens.
- Dollar cost, and any percentage of the Max plan (no real limit is known; the report says so in one sentence).
- Reconstructing Sprints 1-3.
- The SDK runtime writer itself (T-024, T-026).
- Changing the v1 event schema beyond what loading a recorded ledger needs.

**Done when**
1. offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl exists with a header and 33 run lines; the parser loads it with 0 errors, 1 run shown as "not reported", and run 8 carrying its model note.
2. Sum of `tokens` over the 32 runs with usage equals the sum the report prints for the session; per-agent, per-sprint and per-task tables each add up to that same total (a test checks it).
3. `python scripts/metrics.py ai-office` prints the token section, and offices/ai-office/metrics/2026-11.md contains it; the section says the main session is excluded and states why no plan share is shown.
4. Opening the page on a recorded ledger shows per-agent totals, no "synthetic" text anywhere in the panel, and "split not reported" next to each total; the synthetic demo still shows "synthetic".
5. grep finds the ledger-append rule in pmo-playbook, and the ledger format line in T-024 and T-026.
6. No "%" of plan, no dollar figure, and no company data (data rule passes) in the ledger or the report.
7. The new tests pass alongside the existing suite.

**Open questions**
1. How to apportion a run that covered several tasks (e.g. run 1 covered 3): equal split, or report such runs under "shared" only? Needed before build; Architect proposes, Merwyn confirms.
2. Does the harness report the model per run? Believed no; verify in the SDK docs. Nothing blocks on this (Architect).
3. Should usage/ files be committed per session or collected and committed at sprint close? Janice (pmo).
4. Panel layout for "split not reported" and for assumed-model labelling: Dinda (designer).

— Emmy (pm)

## Design

**Approach** (reuse first: events.py data rule and `LogProblem`, the T-056 usage panel and v1 `usage` type, metrics.py's report; no new service, no new dependency)
- New `engine/runtime/ledger.py` (stdlib): parse a ledger, compute totals, convert it to a v1 event log. New `engine/schema/usage.md` documents the format. `python -m engine.runtime ledger <office> <file>` checks a file (exit 0 clean, 1 errors, 2 usage or missing file), same shape as `events`.
- Ledger committed at `offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`: copy /tmp/t057/session-runs.jsonl line for line, then replace the header with the v1 header below (only the header changes; run lines stay as Janice wrote them). The seed now has **35** runs (34, 35 appended for T-057 spec and UX), 34 with usage, total **2,520,926** tokens.
- `scripts/metrics.py` gains a `## Token usage` section from every `offices/<office>/usage/*.jsonl`; regenerate `offices/ai-office/metrics/2026-11.md` with the docstring's monthly steps and commit it.
- `scripts/office_app.py --ledger PATH`: ledger -> v1 log with `usage_source: recorded` and a new `total` shape of `usage` -> the same `events.parse_log` -> page. Default out `engine/app/usage-<session>.html`, gitignored (`engine/app/usage-*.html`), not committed: it goes stale on every ledger append and nothing would catch it. `office.html` and its synthetic fixture are untouched; `--check` on the default page must still pass.
- Template (`engine/app/office.template.html`): recorded rendering per Dinda's UX, behind `REC = D.log.usage_source === 'recorded'`. Synthetic path unchanged.
- Process: workflow.yaml comment + `requires_planning_only`, pr-workflow line 70, pmo-playbook rule, dated notes in T-024 and T-026 Spec (same form as T-026's "Note from T-056").

**Interfaces**

Ledger file, UTF-8 JSONL, max 2000 chars a line, duplicate keys an error, blank lines ignored. File name stem must equal `session`.
```json
{"log":"agent-runs","v":1,"office":"ai-office","session":"session_01MDGJq3GfaeozLojJo8W5Td","source":"<as seed>","recorded_by":"Janice (pmo)","covers":"<as seed>","date":"2026-11-26","not_reported":["split","model","main_session"]}
{"n":1,"sprint":4,"agent":"pm","tasks":["T-046","T-047","T-048"],"step":"spec","tokens":43592,"tool_uses":19,"duration_ms":65582}
```
- Header (else file rejected): `log` = agent-runs; `v` = 1; `office` = the office id; `session` `^session_[A-Za-z0-9]{8,64}$`; `source`, `recorded_by`, `covers`: 1-300 chars, no newline; `date` YYYY-MM-DD; `not_reported`: list, subset of `split`, `model`, `main_session` (the explicit "not reported" for the whole file).
- Run: `n` int >= 1, strictly increasing (duplicate or decrease = error; gap = warning); `sprint` int >= 1; `agent` an org.yaml id; `tasks` 1-8 distinct `^T-\d{3}$`; `step` `^[a-z][a-z-]{0,23}$` (free slug: spec, ux, design, compliance, build, rework, review today); `tokens`, `tool_uses`, `duration_ms`: int 0..999,999,999 or `null` (= not reported, never 0); `note` TEXT? (1-200 chars); for T-026 later, optional `model` (MODEL_RE, the model actually used) and `input`, `output`, `cache_read`, `cache_write` (TOKENS): if any is present, `input` and `output` are required and `tokens` must equal the sum (else error). Unknown field: warning, kept.
- Data rule: `events._data_hit(obj, forbidden_terms(repo))` on the header and every line, first, exactly as events.py (header hit rejects the file). Keys and numbers are not scanned: that T-048 gap stays T-027's (as events.md says).
- `ledger.py` API:
  - `parse_ledger(text, *, agents, office=None, forbidden=()) -> (header|None, runs: list[dict], problems: list[events.LogProblem])`
  - `load_ledger(path, *, agents, office=None, forbidden=())` adds the file-stem = `session` check.
  - `totals(runs) -> {"session": Row, "agents": {id: Row}, "sprints": {n: Row}, "tasks": {tid: TaskRow}, "shared": Row}`. `Row` = `runs, not_reported, tokens, tool_uses, duration_ms, tasks` (sorted distinct ids). `TaskRow` = `runs, solo_runs, solo_tokens, shared_runs, tokens_with_shared, not_reported`. Null fields add 0 to sums and 1 to `not_reported`.
  - **Shared-run rule (Janice, Approvals 1):** no apportioning. A run with 1 task counts in that task's `solo_tokens`; a run with 2+ tasks counts once in `shared` and in full in `tokens_with_shared` of every task it touched. Invariant, tested: sum(agents.tokens) = sum(sprints.tokens) = sum(tasks.solo_tokens) + shared.tokens = session.tokens. Seed: solo 1,786,279 + shared 734,647 (11 runs) = 2,520,926.
  - `to_event_log(header, runs) -> str`: v1 lines: header `{"log":"office-events","v":1,"office":..,"clock":"synthetic","usage_source":"recorded","title":"Recorded agent runs, <session> (T-057)","covers":<covers>,"ledger":"offices/<office>/usage/<file>"}`; then one `usage` per run in order, `t` = 2 x (n - 1), `src` = `offices/<office>/usage/<file>#n=<n>`, `task` = tasks[0], `tasks`, `total`, `tool_uses`, `run`, plus `note` if present.
- events.py / events.md, v1 `usage` gets a second shape **total**: `agent, task, total: TOKENS|null, tasks: [TASK]?, tool_uses: COUNT|null?, run: INT?, note: TEXT?`. It must not carry provider, model, billing, input, output, cache_*, cost_usd (any of these with `total` = error); without `total` the T-056 split shape is checked unchanged. Header `covers`/`ledger` are allowed (headers are not field-checked today). v0 and the T-056 fixtures parse exactly as before (existing tests stay green).
- office_app: `--ledger PATH` (mutually exclusive with `--fixture`; exit 2 if both). Ledger errors and data-rule hits follow the same exit rules as log errors (data rule always exits 1, nothing written). `data.ledger = totals(...)` plus `header.not_reported` are added to the page data so the page shows run counts with no recomputation of the rule.
- Page (recorded): Total row = sum of `total`; one visible "split not reported" line under it; By agent only (no By provider), agents with at least one run, ranked tokens desc then name; row = name, `<planned_model> planned` in dim (`planned*` + note in `title` when any run has a note), `fmtTok` total with `title` "Input, output and cache split not reported", share `NN%` of the recorded session total, bar (aria-hidden), `n runs · m tool uses`, `1 not reported` when relevant; dim "Main session  not reported" last row; foot = header `covers` text + "Share is of this session's recorded tokens." Pill `recorded`. `#usum` `2.5M tokens · recorded`. Focus card lines as UX section 3. No `synthetic` string anywhere in the recorded panel, sheet or summary.
- metrics.py: `usage_section(office_dir, repo) -> list[str]`, inserted after "## Hours saved". Per ledger file, `### <session>`: covers, source, recorded_by/date; the sentences "Main session's own tokens: not reported (the harness reports agent runs only)." and "Share of the Max plan: not shown. The plan has no published fixed token limit, so any percentage of it would be a guess."; tables Session (runs, not reported, tokens, tool uses, hours); By agent (runs, not reported, tokens, share of session, tasks, tokens per task = tokens / distinct tasks, rounded); By sprint (same columns); By task (runs, solo tokens, shared runs, tokens incl. shared runs) with a last row "Shared runs (counted once)" and the line "Solo tokens plus the shared row equal the session total; the 'incl. shared' column adds up to more by design." Model column absent; "Model used: not reported." line. A ledger with errors prints its problems to stderr and "N lines skipped (errors)" in the section; a data-rule hit omits that session's tables and says so (no matched text). Two "How these are measured" bullets. Gets agent ids via `engine.runtime.loader.load_office`.
- workflow.yaml: add to the planning-only comment "- offices/<office>/usage/: appended run lines to a session ledger (existing lines never edited), checked with `python -m engine.runtime ledger`" and add `usage/` to `requires_planning_only`. pr-workflow line 70: add "usage/ (appended ledger lines)" to the list.
- pmo-playbook, new "## 8. Token ledger": after every agent run, append one line to `offices/<office>/usage/<session-id>.jsonl` from the harness report (n, sprint, agent, tasks, step, tokens, tool_uses, duration_ms; `null` where the report has no usage, never 0; a note when the model differs from the profile); a new session id starts a new file with the v1 header; run the ledger check; commit in the sprint close PR.
- T-024 and T-026 Spec, appended: "**Note from T-057 (26 Nov 2026):** the SDK runtime appends one line per agent run to `offices/<office>/usage/<session-id>.jsonl` in the format of `engine/schema/usage.md`, filling `model`, `input`, `output`, `cache_read`, `cache_write` from each result message (check field names against the SDK docs), and drops `split`/`model` from `not_reported`."

**Tests** (`tests/test_ledger.py`, plus additions to test_events, test_metrics, test_office_app)
- Committed ledger: 0 errors, header valid, >= 35 runs, run 22 not reported (null, not 0), run 8 has its note; sum over reported runs = 2,520,926 (or recomputed from the file, if Janice appends more before build).
- Totals invariant above on the real file and on a small synthetic fixture with a null run and a shared run.
- Parser edge fixture `tests/fixtures/ledger-edge.jsonl` (SYNTHETIC): bad header, duplicate n, bad task id, 0 vs null, split sum mismatch, unknown field warning, email / 16-digit / forbidden term in `note` (message names the field, never the text), stem mismatch.
- events: total shape accepted; total + provider = error; split shape and both existing fixtures unchanged.
- metrics: section present, totals match the parser, contains "not reported" and the plan sentence, no `$`, no "% of plan"/"of the plan" share.
- office_app: `--ledger` page data has `usage_source: recorded`; recorded panel code path has no "synthetic"; default page `--check` still passes; `--ledger` with a data-rule hit exits 1 and writes nothing.

**Risks**
| Risk | Handling |
|---|---|
| Spec Done-when 1 says 33 runs; the file has 35 and grows | Tests count from the file, not a literal; open question below for Janice |
| The total shape widens the v1 schema | Strict: either shape, never mixed; both T-056 fixtures re-parse identically (tested) |
| Recorded page goes stale vs the ledger | Not committed; regenerated on demand (README line) |
| Planning-only path lets ledger lines merge without review | Append-only, ledger check before merge, data rule always on; editing existing lines needs a Reviewer |
| A company string slips into `note` or `covers` | Same data rule as events.py, on every string, before anything else |
| Monthly report regeneration also changes other sections | Expected: it is a full regeneration from git; follow the docstring fetch steps |

**UX design (Dinda): accepted, two changes.** (a) No provider chip on recorded rows: the ledger has no provider, so the row shows `sonnet planned` as dim text only, not a `[plan]` chip. (b) Totals are `2.5M` for this seed, not the mock's 3.1M. Her questions: **1. Yes:** one visible "split not reported" line under the Total, plus that text in the `title` and `aria-label` of every total, meets Spec check 4; the Reviewer checks against this reading. **2. Confirmed:** agent share = agent tokens / session recorded tokens; the task rule does not affect it, because each run has exactly one agent.

**Compliance: not flagged.** No production systems, no money movement (token counts on a fixed plan, no cost shown), no personal data: agent ids, task ids and counts only, under the existing data rule. Seed checked with `events._data_hit` and the workspaces.yaml terms: 0 hits.

**Decision record (draft for April)**
```
Decision: Agent-run token usage is kept as one append-only JSONL ledger per Claude session under offices/<office>/usage/, totals only until the SDK runtime adds the split.
Context: Harness reports (total, tool uses, duration) were lost when the session context was summarised; Merwyn asked for per-agent, per-session numbers (T-057).
Options: A ledger file per session, own small format, converted to v1 events for the page - pro: holds totals and nulls honestly, one file per session; con: second format. B write v1 usage events directly - con: v1 usage needs a provider/model/split we do not have. C a column in board.md or the sprint files - con: not machine-checked, mixes planning and data.
Chosen: A, because it records only what the harness gives and reuses the events.py data rule and the T-056 panel.
Consequences: metrics and the 3D page read the same file; the PMO appends after each run (planning-only path); T-024/T-026 write the same format with the split; multi-task runs are never apportioned.
Links: T-057, T-056, T-048 (data rule), T-024, T-026
```

**Open questions**
- Done-when 1 and 2 say 33 runs / 32 with usage; the file now has 35 / 34 (Janice appended runs 34-35). Read them as "every run in the file, at least runs 1-33"? Janice (pmo).

— Fang (architect)

## UX design

**Question (playbook 1):** "How many tokens did each agent use this session, and which agent used most?" Audience: Merwyn alone, glancing. The needs-you state stays loudest (playbook 2); nothing here competes with it. Left out: cost, plan share, charts beyond one bar, input/output/cache columns (no data, so no empty columns). Reuses the T-056 `.panel`, `.ur`, `.mono`, `fmtTok`, chip, collapse and phone sheet; no new colours. Sizes are starting values (playbook 3). design-handoff skill not called; structure follows playbook 6 by hand.

**1. Usage panel, recorded ledger (`usage_source: recorded`)**
```
+- Usage ------------ [recorded] -+
| TOTAL  3.1M tokens  33 runs      |
|        split not reported        |
| BY AGENT, most tokens first      |
| Fang   [plan] sonnet  1.2M  38%  |
|        ######....  9 runs 140 tools |
| Janice ...                       |
| Run 22  tokens not reported      |
| Recorded from harness reports,   |
| Sprints 4-6. Main session not    |
| reported. Model shown is planned.|
+----------------------------------+
```
- Pill reads `recorded`, never `synthetic`. Source line (always visible, one block at the foot, replaces the synthetic footnote): "Recorded from harness reports, Sprints 4-6 of session_01MD... Main session and Sprints 1-3 not reported." The synthetic demo keeps its pill and footnote unchanged (spec check 4).
- Blocks: Total, By agent only (no By provider: one planned model per agent adds nothing). Ranked by total tokens, descending, ties by name; the ranking is the order, the bar is a second channel (playbook 5: no state by colour alone). Row: name, planned-model chip, total (`fmtTok`, exact in `title`), share of session total as a number (`38%`, share of recorded agent total, not of any plan), then a bar line: a 4px bar in `--text-dim` track and agent colour fill, width = share, plus `9 runs · 140 tool uses`. Share is of the session's recorded total only; the footnote says so. Do not write "% of plan".
- "split not reported": ONE line under the Total, dim, not repeated per row (spec check 4 asks it "next to each total": satisfy it with a `title` "Input, output and cache split not reported" on every total and the visible line once; Fang to confirm this reading). The columns in/out/cache are not drawn at all for recorded data.
- Model: chip shows the short name with the word `planned` in dim text after it in the row ("sonnet planned"); `title`: "Model from the agent profile; the harness does not report the model used." A run with a note (run 8, session default) shows `planned*` and the note in `title` and the focus card.
- Main session: a dim last row, "Main session  not reported", no number, no bar, so its absence is visible rather than silent.
- Empty state unchanged ("No usage yet") until a run with usage is reached in the replay.

**2. Run with no usage (run 22)**
Counts in runs, adds 0 tokens, never shows `0`. In the agent row: `n runs, 1 not reported` (dim). In the focus card for that step: "Tokens: not reported" . Not amber or red: it is missing data, not a fault.

**3. Focus card (agent clicked)**
Adds, under the model line: `Total 214k · 38% of session`, `9 runs · 140 tool uses`, `split not reported`, `Model: sonnet (planned)`. The last step's run shows its own total and tool uses; no-usage run shows "not reported". Same lines for synthetic data would be wrong, so these appear only when `recorded`.

**4. Phone (under 900px)**
Docked panel stays hidden (T-056). The existing `#usheet` carries the same renderer. The `#usum` strip reads `3.1M tokens · recorded` (no in+out split). Sheet rows are full width, 44px tap height, bar below the name, source line pinned at the foot of the sheet and not scrolled away. Row tap focuses the agent as today.

**5. Motion (playbook 3, 5)**
Only existing ones: bar width and total change while the replay runs, 200ms ease-out, purpose continuity. Reduced motion (`body.rm`): widths set instantly. Row re-order is instant in both modes (no travel animation, to avoid rows jumping under the cursor).

**6. Accessibility**
Rank order, numbers and share text carry the meaning; bar is decoration (`aria-hidden`). Dim text stays at T-056's contrast (use `--text-dim` only for notes of 11px or more, never for the total). Row `aria-label`: "Fang: 214k tokens, 38% of session, 9 runs, 140 tool uses, split not reported". Chip includes the code letters, not colour alone.

**Open questions**
- Does "split not reported next to each total" (spec check 4) accept one visible line plus a `title` per row? Fang.
- Share denominator when runs are shared across tasks: share is per agent over the session, so it is unaffected by the per-task rule. Confirm. Fang.

— Dinda (designer)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers (not business decisions, so Janice settles them): (1) Multi-task runs are not apportioned. The per-task table lists the runs that touched each task with their full tokens and marks shared runs; it says plainly that per-task rows can add up to more than the session total. No estimated split. (2) The harness does not report the model used; record the profile model as "planned", and the session-default note for the Sprint 4 designer run. (3) Cadence: Janice appends a ledger line after every agent run and commits the session's file in the sprint close PR; add offices/<office>/usage/ to the planning-only paths in workflow.yaml and pr-workflow (in scope here). (4) Panel wording: Dinda. Janice appended run 34 (this spec, 32,816 tokens) to the seed file. — Janice (pmo)

Janice (pmo), 26 Nov: Design accepted (Dinda's UX with Fang's two changes); moved to build. Answer: checks count every run in the file (tests count from the file, not a fixed 33/32). Copy /tmp/t057/session-runs.jsonl into the repo as it stands when you start; Janice appends later runs (Fang's design, this build, the review) in the Sprint 7 close per the new rule. Engineer: do not set status.

## Build notes

**What changed**
- `engine/runtime/ledger.py` (new): `parse_ledger`, `load_ledger`, `totals`, `to_event_log`, exactly the Design's API. Shared runs are never apportioned (`solo_tokens` / `shared` / `tokens_with_shared`).
- `python -m engine.runtime ledger <office> <file>` (exit 0 clean, 1 errors, 2 usage or missing file).
- `engine/runtime/events.py`: `usage` second shape `total` (`TOTAL_SPEC`); any of provider, model, billing, input, output, cache_*, cost_usd with `total` is an error. Split shape, v0 and both T-056 fixtures are unchanged (existing tests green).
- `engine/schema/usage.md` (new), `engine/schema/events.md` (total shape), `engine/app/README.md`.
- `offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`: Janice's seed copied line for line (runs 1-35 byte-identical to /tmp/t057/session-runs.jsonl, checked with `diff`), header converted to v1.
- `scripts/metrics.py`: `usage_section()` after "## Hours saved", plus two "How these are measured" bullets; `offices/ai-office/metrics/2026-11.md` regenerated from a full clone with 39 PR refs (`git clone` + `fetch '+refs/pull/*/head:refs/remotes/origin/pr/*'`, run with this branch's scripts overlaid; head shown in the report is main at b04bbd9... as the clone had it). Other sections changed too: expected, full regeneration.
- `scripts/office_app.py --ledger PATH` (mutually exclusive with `--fixture`, exit 2 if both; default out `engine/app/usage-<session>.html`, gitignored). `office.html` regenerated (template changed); `--check` passes.
- `engine/app/office.template.html`: recorded rendering behind `REC`; synthetic path unchanged apart from Merwyn's request below.
- Process: workflow.yaml comment and `requires_planning_only` (+ `usage/`), pr-workflow line, pmo-playbook "## 8. Token ledger", T-024 and T-026 notes.
- Tests: `tests/test_ledger.py` (new), `tests/fixtures/ledger-edge.jsonl` (SYNTHETIC), additions in test_events, test_metrics, test_office_app.

**Merwyn request 26 Nov 11:31** (relayed by Janice, both pages)
- By provider: one bar per provider with its `NN%` text beside the bar, colour from providers.yaml. Recorded page: "Claude Agent SDK (Max plan) 100%" and the line "1 provider recorded".
- By agent: an accordion, expanded by default; header is a real `<button aria-expanded>` (keyboard works, focus restored after re-render), no animation anywhere (so reduced motion is satisfied); inside, every run of that agent (recorded: `#n . Sprint step`, tasks, tokens or "not reported"; synthetic: task, provider code and model, tokens) and a "Show details" button that opens the focus card.
- Percentages are whole numbers by largest-remainder rounding (`OfficeCore.shares`) and add to exactly 100. Recorded page: runs with null tokens add 0 and are excluded, the Total block says "Percentages exclude the 1 run with tokens not reported."
- Tests: `shares ok` (hand cases plus 500 seeded random vectors: integers, sum 100, within 1 point of exact), recorded replay totals/percent/run-list vs the Python parser, synthetic percentages add to 100.

**Output (real)**
```
$ python -m unittest              -> Ran 309 tests ... OK   (277 before)
$ python scripts/golden.py ai-office -> golden: 13 cases, 75 checks, 0 problems
$ python -m engine.runtime validate ai-office -> ai-office: OK - 8 agents, 5 stages, 57 tasks, 18 skills
$ python scripts/build_agents.py ai-office -> built 8 agents
$ python scripts/office_app.py ai-office --check -> office.html: up to date (140 KB, 84 events)
$ python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
  35 runs kept (1 not reported), 2,520,926 tokens, 0 errors, 0 warnings
$ python scripts/board.py ai-office -> 57 tasks, no problems; board.md discarded
```
Per agent, as the report prints them (tokens, share of session): engineer 886,568 35.2% (10 runs, 1 not reported); reviewer 713,771 28.3%; architect 429,659 17.0%; pm 202,660 8.0%; designer 188,893 7.5%; curator 68,590 2.7%; compliance 30,785 1.2%. Session 2,520,926 tokens, 35 runs, 713 tool uses, shared runs 11 = 734,647, solo 1,786,279. (The report's table uses one-decimal shares; the page uses whole numbers that sum to 100.)

**How to verify**
```bash
python -m unittest
python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
python scripts/metrics.py ai-office --out /tmp/m.md      # then read "## Token usage"
cd /tmp && npm pack three@0.128.0 && tar xzf three-0.128.0.tgz && cp package/build/three.min.js <repo>/engine/app/
python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
google-chrome --headless=new --use-gl=swiftshader --enable-unsafe-swiftshader --window-size=1280,800 --screenshot=/tmp/x.png "file://<repo>/engine/app/usage-session_01MDGJq3GfaeozLojJo8W5Td.html?t=999"
```
Screenshots (read and fixed until clean; no console errors, only swiftshader INFO "GPU stall" messages): /tmp/t057-shots/ desktop-recorded-expanded, desktop-recorded-two-collapsed, desktop-recorded-focus-card, phone-recorded-sheet, phone-recorded-focus-card, desktop-synthetic, phone-synthetic-sheet (1280x800 and 390x844). Fixed on the way: panel rows clipped (compacted, panel may use more height), phone sheet rows squashed (flex-shrink), pinned foot overlapping rows, wrong notes in the focus card (now per run), model chips ("--") on 3D tags removed for recorded data.

**Deviations from the Design (please check)**
1. Header `covers` says "Sprints 4-7" instead of the seed's "4-6": runs 34 and 35 are Sprint 7, so the seed text would be false on the page. Only the header text changed.
2. New optional header field `provider` ("claude-sdk" in the seed), needed for Merwyn's By provider bar. It rests on Janice's statement that all runs were SDK/plan runs; the harness itself reports no provider. Janice to confirm.
3. `total`-shape events also carry optional `sprint` and `step` (needed for the run list inside the accordion).
4. Metrics By task: the column is "Tokens counted once" (task rows = solo tokens, last row = shared tokens) so that it adds to the session total as the Design requires.
5. Bar fill is the existing `--accent` for agents (the Design said agent colour; agents have no colour token and Dinda said no new colours). Provider bars use the providers.yaml colour.
6. Recorded page has a By provider block (the UX design said none) because of Merwyn's request.

**Known limits**
- The recorded page is not committed and is stale after any ledger append (regenerate).
- Clock label on the recorded page still reads "(synth)": replay time is authored, not real; not part of the panel.
- Data rule does not scan keys or numbers (T-027, as in events.md).
- Not verified: the Claude SDK result-message field names (T-026), and whether the harness reports the model (open question 2, believed no).

— Sebastian (engineer)

Janice (pmo), 26 Nov: moved to review. On deviation 2 (header `provider`): these runs were Claude Code subagents in a claude.ai session on Merwyn's Max plan, not the Agent SDK runtime (T-024 is not built). Plan billing is right; the label "Claude Agent SDK" is not. Reviewer: judge whether the recorded page must say so. Merwyn's 11:31 request (provider bars with %, agent accordion expanded) is part of this task's scope.

### Rework 1 (after Cahyani's REJECT, round 1)
- Provider: new `claude-code` entry in `offices/ai-office/providers.yaml` (label "Claude Code subagents (Max plan)", code CC, billing plan, models opus and sonnet; colour #8e9bf5, chosen to pass the provider-colour test). The ledger header now says `"provider":"claude-code"` (header only; the 35 run lines are still byte-identical to the seed, checked with `diff`). The provider bar % now reads "100% of session" on the recorded page and "NN% of session" on the synthetic page, so it cannot be read as a plan share.
- Parser: `parse_ledger` / `load_ledger` take `providers` (ids from providers.yaml); a header provider outside them rejects the file with an error. The CLI, `office_app --ledger` and `metrics.py` pass the catalogue. Test: `test_header_provider_must_be_in_providers_yaml`.
- Polish: recorded clock reads "(replay)"; `planned*` and its title use only model notes (a note on a not-reported run is a usage note, documented in usage.md); workflow.yaml and pr-workflow say "existing lines never edited or deleted; a new session file starts with its header line"; task ids in the run list no longer wrap (each id is nowrap, the run label and "not reported" too).
- Left for later (Open questions): unknown-agent error echoes the value; phone sheet is cramped.
- Output: 310 tests OK; golden 13 cases, 75 checks, 0 problems; validate OK; office_app --check up to date; ledger CLI 35 runs, 0 errors; board.py clean (board.md discarded); report regenerated from the full clone (head b04bbd9, 39 PR refs); screenshots re-taken in /tmp/t057-shots/ (no console errors).

## Review log
REJECT (round 1), 26 Nov 2026, PR #40 head 2de5b8c. Pass: ledger runs byte-identical to the seed; hand totals 2,520,926 per agent, per sprint and solo + shared; run 22 "not reported"; page shares sum to 100; 309 tests; report from a full clone matches; 17 break cases caught without echo; process rules and T-024/T-026 notes present; synthetic page unchanged; headless renders clean, accordion works by keyboard.
Fail (no Max-plan share claim; ledger states facts only): header provider "claude-sdk" shows as "Claude Agent SDK (Max plan) 100%"; the runs were Claude Code subagents, and "(Max plan) 100%" reads as plan share. Fix: a providers.yaml entry for Claude Code subagents (Max plan), header points at it, bar % labelled as share of session; check header provider against providers.yaml ids, with a test.
Notes: clock "(synth)" on recorded page; "planned*" set by a usage note; planning-only wording should say "never deleted"; unknown-agent error echoes the value; phone sheet cramped.
— Cahyani (reviewer), recorded by Janice (pmo)

PASS (Review 2), 26 Nov 2026, PR #40 head 5de23d2. Header provider now "claude-code" ("Claude Code subagents (Max plan)"); run lines still byte-identical to the seed; header provider checked against providers.yaml in CLI, metrics and office_app ("zz-weird" rejected, new test); bars read "100% of session" / "N% of session". Recorded clock "(replay)"; planned* only for model notes; planning-only wording "never edited or deleted"; ids no longer wrap. 310 tests; ledger CLI 35 runs, 1 not reported, 2,520,926 tokens; office.html --check up to date; headless renders clean, accordions expanded, keyboard works, 0 console errors.
Notes: usage.md example header still says claude-sdk; phone sheet cramped; unknown-agent error echoes the value on stderr.
— Cahyani (reviewer), recorded by Janice (pmo)

## Decision

## Open questions
- Later (Cahyani, round 1 notes): the ledger parser's unknown-agent error echoes the offending value; the phone usage sheet is cramped. (Sebastian)
- Done-when 1-2 say 33 runs / 32 with usage; the seed now has 35 / 34. Count every run in the file? Janice (pmo). (Fang, Design)
