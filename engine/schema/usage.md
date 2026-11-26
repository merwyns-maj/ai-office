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

## Main-session lines (T-070)
A second line kind, kept apart from runs. The header keeps `main_session` in `not_reported` (the harness does not report it, and the header is append-only); these lines come from another source, the Claude app's `explain-usage` skill, whose figures are metered cache and input/output counts and are not the harness's per-run `tokens`. Never add the two.
```json
{"kind":"main_session","window":1,"date":"2026-11-26","source":"explain-usage skill","since":"last context summary","requests":103,"input":250,"cache_write":211583,"cache_read":26678886,"output":52012}
```
- Required: `kind`, `window` (integer >= 1, never decreasing across lines; +1 after each context summary), `date`, `source` and `since` (1-200 characters, the window caveat), `input`, `cache_write`, `cache_read`, `output` (integer 0 to 999,999,999). `requests`: integer or null. `note` optional (1-200). No `n`, `agent`, `tasks` or `tokens`.
- Errors: a `tokens` field (units differ from agent runs); any of the four figures lower than the previous reading in the same window (start a new window); a lower `window`; an unknown `kind`. The data rule runs first, as for runs.
- Readings are cumulative: per window the last reading counts, windows add (`ledger.main_totals`). A window nobody read is lost and never estimated; `since` says so.
- Never in `totals()`, the invariant or the event log. The page shows its own row, "Main session (metered)", and without lines "Main session: not reported".

## Totals
`ledger.totals(runs)`: session, per agent, per sprint, per task. A null adds 0 to every sum and 1 to `not_reported`. A run with one task counts in that task's `solo_tokens`; a run with 2+ tasks, or none (a chat run), counts once under `shared` and in full in `tokens_with_shared` of each task it touched. It is never split between tasks. Invariant: sum over agents = sum over sprints = sum of `solo_tokens` + `shared` = session.

## Page
`python scripts/office_app.py ai-office --ledger <file>` (add `--chat` for the one published AI Office page, T-065) converts the ledger with `ledger.to_event_log` to a v1 event log (`usage_source: recorded`, `usage` events in the `total` shape, see `events.md`) and builds `engine/app/usage-<session>.html` (gitignored). Chat runs (no task) are not in the event log, which needs a task per usage event; they stay in the ledger totals. Since T-069 a `--ledger` build embeds no run events: `data.events` is empty and `data.usage.builtin` carries a fixed-size snapshot (see Artifact db).

Tests (T-072): the suite reads the live ledger only for invariants (clean parse, totals add up, chat runs not in events, main lines not in run totals, old lines unchanged); exact numbers come from `tests/fixtures/session_FIXTURE072.jsonl`. Appending a valid line must never break the suite; `RealLedgerAppended` checks this. The page's used figure excludes chat runs.

## Artifact db (T-069)
The published page reads the ledger from the artifact db so a ledger append shows without a republish. The repo stays the source of truth; the db is a one-way, re-runnable mirror that Janice writes with the db tools. `python -m engine.runtime usage plan <office> --ledger <file>` makes the plan; Python never touches the db.
- Docs (even segments are docs). Rule: `{path:"usage", read:"owner", write:"owner"}`, next to the unchanged `chat` rule.
  - `usage/office` (meta, written last, the commit point): `{v:1, by:"pmo", session, synced_at, runs, last_n, chunks:[{id, first_n, last_n, bytes, sha256}], header:{provider, not_reported, covers}, totals, main, budgets_sha256}`. `totals` is `ledger.totals(runs)`; `main` is `ledger.main_totals`.
  - `usage/office/chunks/<session>-<k:03>`: `{v:1, session, k, first_n, last_n, runs:[run lines, nulls kept]}`. Chunks are packed in file order by bytes and closed before the next run would pass 128 KiB, so a normal sync rewrites only the last chunk.
  - `usage/budgets`: the resolved `budgets.yaml`, the shape the page reads as `D.budgets`. No `budgets.yaml` means no doc and `budgets_sha256: null`.
- Limits (claude.ai db): 25,000 docs, 256 KiB per doc. The plan refuses, writing nothing, when `2 + chunks + other_docs` passes the first or any doc passes the second, and reports `docs` and `largest_doc_bytes` every time.
- Plan input (stdin only): `{"rules":[...], "docs":[{path|id, data, version}], "other_docs":<count of chat docs>}`; output `{"actions":[{op:"set"|"delete", path, doc, ifVersion}], "report":{docs, largest_doc_bytes, runs, chunks, writes, deletes, orphans, unknown, in_sync, synced_at}}`. Never redirect it into the repo. A doc whose content already matches gets no action, so a second run gives `writes:0, in_sync:true`; `synced_at` moves only on a sync that writes. Apply order: chunks, budgets, meta (so a half-applied sync shows the built-in copy and a re-run repairs it), then orphan deletes.
- Refused with exit 1 and no actions: ledger or budgets errors; the `usage` or `chat` rule missing, below owner, or a wider rule; a data-rule hit (`chat.scan` plus the forbidden terms of `workspaces.yaml`, on every string of every doc, kind only; the one exempt string is the validated session id in a doc's `session` field, which is 32 characters and would trip the long-token rule); a run with a field outside `RUN_KEYS` (U2); a doc over the byte limit; too many docs. The meta header copies only `provider`, `not_reported`, `covers`.
- Retention (U6): no clock purge. The sync mirrors the repo: a chunk (including another session's) or the budgets doc the repo no longer has is reported as an orphan and deleted with its `ifVersion`. Deleting db docs does not delete session transcripts. Purge `usage` when the artifact is shared or deleted.
- Page: the db copy is used when `meta.session` equals the build's, `meta.last_n >= build last_n` and the chunks add up to `meta.runs` and `last_n`. Stale means older than the build (lower `last_n`); there is no clock threshold. Otherwise the built-in copy shows, with the reason and the "last synced" time.

## Budgets (T-060)
The usage panel compares these totals with `offices/<office>/budgets.yaml` (per provider, and per agent inside a provider; format and rules in `engine/runtime/budgets.py`). A budget is set by Merwyn or whoever he names, every value has `set_by` and `set_on`, and the page never invents one: no budget reads "budget not set". Period today: the session.

Colour (T-062): `budgets.yaml` may carry `thresholds: { warn_at, alert_at, set_by, set_on }` (percent of a budget, `0 < warn_at < alert_at <= 100`, defaults 70 and 90). The rounded % the page shows picks the level: below `warn_at` green, from `warn_at` yellow with the word "near budget", from `alert_at` red with "at limit", over budget red with "over by X". The level is also in each row's aria-label. Colours are theme palette tokens (`accent`, `near`, `bad`, `bad_text`).
