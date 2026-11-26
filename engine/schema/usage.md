# Agent-run ledger (T-057)

One append-only file per Claude session, `offices/<office>/usage/<session-id>.jsonl`, recording what each agent run used. The file name stem must equal the header `session`. Parser: `engine/runtime/ledger.py`. Check a file with:

```bash
python -m engine.runtime ledger ai-office offices/ai-office/usage/<session-id>.jsonl   # 0 clean, 1 errors, 2 usage or missing file
```

UTF-8 JSONL, a line is at most 2000 characters, blank lines are ignored, a duplicate key is an error.

## Header (line 1, else the file is rejected)
```json
{"log":"agent-runs","v":1,"office":"ai-office","session":"session_01ABC...","source":"harness subagent report ...","recorded_by":"Janice (pmo)","covers":"...","date":"2026-11-26","provider":"claude-sdk","not_reported":["split","model","main_session"]}
```
`log` = agent-runs; `v` = 1; `office` = the office id; `session` matches `^session_[A-Za-z0-9]{8,64}$`; `source`, `recorded_by`, `covers`: 1-300 characters, no newline; `date` YYYY-MM-DD; `provider` (optional): the provider id from `providers.yaml` the runs went through (an id not in the catalogue is an error), shown by the page as the one provider recorded; `not_reported`: list drawn from `split` (input/output/cache), `model` (the model actually used) and `main_session` (the main session's own tokens): what this whole file does not report.

## Run lines
```json
{"n":1,"sprint":4,"agent":"pm","tasks":["T-046","T-047","T-048"],"step":"spec","tokens":43592,"tool_uses":19,"duration_ms":65582}
```
- `n` integer >= 1, strictly increasing (a repeat or decrease is an error, a gap a warning); `sprint` integer >= 1; `agent` an `org.yaml` id; `tasks` 1-8 distinct `T-nnn`; `step` a lowercase slug (spec, ux, design, compliance, build, rework, review, chat today). A run with `step: "chat"` (T-063) may have `tasks: []` and then must carry `note: "chat message <id>"` (the pointer to the artifact db message; never the chat text). `tasks: []` is an error for any other step.
- `tokens`, `tool_uses`, `duration_ms`: integer 0 to 999,999,999, or `null` = **not reported**. A run whose harness report had no usage stays in the file with `null`, never 0.
- `date` (optional, T-060): the day the run happened, YYYY-MM-DD. New run lines should carry it so a budget period (day, week, month) can be applied later; until every line has one, the usage panel's period is the session. A bad date is an error.
- `note` (optional, 1-200 characters). On a run with `tokens: null` it explains the missing usage; on any other run it records a caveat such as the model differing from the profile (the page marks `planned*` only for the latter).
- Later, written by the SDK runtime (T-024, T-026): `model`, `input`, `output`, `cache_read`, `cache_write`. If any of the four token fields is present, `input` and `output` are required and `tokens` must equal their sum.
- An unknown field is a warning and is kept.
- Data rule: the `events.py` rule (email, 16-digit run, 10+ digit run, forbidden term from `workspaces.yaml`) runs first on every string of the header and every line; a header hit rejects the file. Keys and numbers are not scanned.

## Totals
`ledger.totals(runs)`: session, per agent, per sprint, per task. A null adds 0 to every sum and 1 to `not_reported`. A run with one task counts in that task's `solo_tokens`; a run with 2+ tasks, or none (a chat run), counts once under `shared` and in full in `tokens_with_shared` of each task it touched. It is never split between tasks. Invariant: sum over agents = sum over sprints = sum of `solo_tokens` + `shared` = session.

## Page
`python scripts/office_app.py ai-office --ledger <file>` (add `--chat` for the one published AI Office page, T-065) converts the ledger with `ledger.to_event_log` to a v1 event log (`usage_source: recorded`, `usage` events in the `total` shape, see `events.md`) and builds `engine/app/usage-<session>.html` (gitignored). Chat runs (no task) are not in the event log, which needs a task per usage event; they stay in the ledger totals.

## Budgets (T-060)
The usage panel compares these totals with `offices/<office>/budgets.yaml` (per provider, and per agent inside a provider; format and rules in `engine/runtime/budgets.py`). A budget is set by Merwyn or whoever he names, every value has `set_by` and `set_on`, and the page never invents one: no budget reads "budget not set". Period today: the session.

Colour (T-062): `budgets.yaml` may carry `thresholds: { warn_at, alert_at, set_by, set_on }` (percent of a budget, `0 < warn_at < alert_at <= 100`, defaults 70 and 90). The rounded % the page shows picks the level: below `warn_at` green, from `warn_at` yellow with the word "near budget", from `alert_at` red with "at limit", over budget red with "over by X". The level is also in each row's aria-label. Colours are theme palette tokens (`accent`, `near`, `bad`, `bad_text`).
