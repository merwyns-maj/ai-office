---
id: T-069
title: "Usage numbers from the artifact db, so the page needs no republish per ledger append"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-067, T-070]
pr: 73
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- Today the ledger totals are baked into the page at build time (`office_app.py --ledger ... --chat`), so every ledger append needs a rebuild and republish of "AI Office", and the page grows about 245 B per run (T-065 Design).
- The artifact already declares `db` with one owner-only rule on `chat` (T-063).

## Done when
- [ ] The page reads ledger runs and budgets from the artifact db (owner-only), and the office writes new runs there when it appends the ledger; the repo ledger stays the source of truth (one-way sync, re-runnable)
- [ ] A ledger append shows on the page without a republish; the page size no longer grows with runs
- [ ] Compliance check (new data in the db; no personal data, owner-only), and the C1-C8 chat rules unchanged

## Spec
**Problem.** The published "AI Office" page has the ledger totals baked in at build time, so every ledger append needs a republish and the page grows about 245 B per run (T-065, T-067 size note: 250,543 B and rising). Merwyn wants usage current without a republish.

**In scope**
- The page reads ledger runs (T-070's main-session lines included) and the budgets from the artifact db, owner-only. A new run shows without a republish; the built page no longer contains run rows, so its size does not grow with runs.
- The repo stays the source of truth: `usage/<session>.jsonl` and `budgets.yaml`. Janice syncs them one-way (repo to db) with the db tools after each ledger merge. The sync can be re-run any number of times with the same result (no duplicates, no drift).
- A `budgets.yaml` change (value, thresholds, `set_by`, `set_on`) syncs too, and the page shows it after a sync.
- Empty, unavailable or stale db: the page shows the data built into it (the ledger as of its build) with a visible "last synced" time and a note that it is the built-in copy. It never shows a blank or an error in place of usage.
- Limits: 25,000 docs and 256 KiB per doc. The sync stops with a clear message, and writes nothing partial, if it would pass either; it reports how many docs and the largest doc size each time.
- Compliance check (Wulan) before build: new data class in the db, owner-only, no personal data, C1-C8 unchanged.

**Out of scope.** Writing the ledger from the page; two-way sync; a second session ledger (T-065 risk 1); new usage features or panels; changing chat rules, retention or the inbox; changing the committed synthetic `office.html` data; sharing the artifact.

**Done when (checks a reviewer can run)**
- [ ] With the db declared, a rule on the usage data reads and writes `owner` only, and a `db_write` as `asLevel: view` is refused (recorded in Build notes, as C7). The `chat` rule is unchanged.
- [ ] After the sync, the page's run count, per-agent, per-sprint and per-task totals and budget bars equal those of a `--ledger` build of the same file, including T-070 lines (`step` main-session lines, `null` tokens still read as not reported).
- [ ] Append one run to the ledger, sync, reload without republishing: the new run and totals show. Run the sync twice: the db is identical (doc count and content).
- [ ] Change `budgets.yaml` (test value), sync, reload: the page shows the new budget and colours; the test value is reverted.
- [ ] Empty db, a db error (stub `unavailable`, `not_granted`) and a stale db (last sync older than the Design's threshold): the page shows the built-in data, the "last synced" time or "never synced", and 0 console errors, at 1280x800 and 390x844.
- [ ] The built page size is flat when runs are added (built with 67 and with 96+ runs differ by under 1 KB); the committed-page size limit and `--check` still pass.
- [ ] A test or sync dry-run fails when docs would pass 25,000 or one doc would pass 256 KiB.
- [ ] No ledger text is written to the repo by the sync; the data rule (`events.py` scan, forbidden terms) runs on every doc before it is written.

**Open questions**
- Stale after how long, and where does the "last synced" time come from? Fang.
- Do chat runs and T-070 main-session lines (no task) show on the page as they do in the totals today? Fang, with Dinda if visible.
- Are 25,000 docs and 256 KiB per doc confirmed in the db tool docs, and how many docs does the ledger need at about 245 B per run? Fang.
- Does T-070 land first, so its line shape is fixed before the Design? Janice (T-069 depends_on lists only T-067).

— Emmy (pm)

**Spec approved** (Janice, 26 Nov 2026 22:15 WIB). T-070 lands first (its main-session lines are in the sync); `depends_on` now includes T-070. The Architect confirms the db limits from describe_capabilities and flags Compliance (new data in the db).

## Design
**Approach.** Reuse the chat's db and store pattern; no new service. Files: new `engine/runtime/usage_sync.py` (pure) + `usage` subcommand in `engine/runtime/__main__.py`; `chat.rules_problem(rules, path="chat")` (path argument added, chat behaviour unchanged); `scripts/office_app.py`; `engine/app/office.template.html` (+ rebuilt `office.html`); `engine/schema/usage.md` (new "Artifact db" section); pmo-playbook §8, §9 and Publish; tests. T-070's line is `kind:"main_session"` (not a `step`); its `main_totals()` output goes into the meta doc.

**db layout** (even segments = doc; rule `{path:"usage", read:"owner", write:"owner"}` declared next to the unchanged `chat` rule).
- `usage/office` (meta, written last = commit point): `{v:1, by:"pmo", session, synced_at:<ISO UTC>, runs, last_n, chunks:[{id, first_n, last_n, bytes, sha256}], header:{provider, not_reported, covers}, totals:<ledger.totals(runs)>, main:<main_totals or null>, budgets_sha256}`.
- `usage/office/chunks/<session>-<k:03>`: `{v:1, session, k, first_n, last_n, runs:[run lines as parsed, nulls kept]}`.
- `usage/budgets`: the resolved `load_budgets()` dict, the same shape the page reads today as `D.budgets`.
- **Chunked, not one doc per run.** One doc per run means 25,000 runs max and one `db_write` per run (about 30 tool calls per sprint for Janice). Chunks are packed in file order and closed before the next run would take the doc past 128 KiB (half of 256 KiB; a line can be up to 2,000 characters, so the packing counts bytes, not runs). Today's 100 runs (18.6 KB file) make 1 chunk of about 20 KB. Because the ledger is append-only, only the last chunk changes. A normal sync is 2 writes (last chunk + meta), or 3 when budgets change. Doc count = 2 + chunks, far below 25,000.

**Sync (Janice, after each ledger merge on main, and after a `budgets.yaml` change).** (1) `db_get` `usage/office` and `usage/budgets`, `db_list` `usage/office/chunks`, and count the `chat` docs. (2) Pipe `{"rules":[...], "docs":[{id|path, data, version}], "other_docs":<int>}` into `python -m engine.runtime usage plan ai-office --ledger offices/ai-office/usage/<session>.jsonl [--now ISO]` (stdin only; output never redirected into the repo). (3) Apply `actions` in order with `db_write`, each with its `ifVersion` (omitted for a doc that does not exist yet), chunks then budgets then meta. A conflict means stop and re-plan.
- Output: `{"actions":[{op:"set", path, doc, ifVersion}], "report":{docs, largest_doc_bytes, runs, chunks, writes, in_sync}}`. A doc whose content (meta minus `synced_at`) already matches gets no action, so a second run gives `writes:0, in_sync:true` and leaves the db identical. `synced_at` changes only on a sync that writes.
- Exit 1, with no actions and the reason: ledger errors; the `usage` rule missing or below owner (or a wider rule, as C7); a data-rule hit (`events._data_hit` + forbidden terms) on any string of any doc, including budgets `set_by`/`note`, kind only; a doc over 262,144 B; `2 + chunks + other_docs` over 25,000. Always prints `docs` and `largest_doc_bytes`.

**Page.** `usageStore(db)` next to `chatStore` (the only db code): `meta(cb, err)` = `onSnapshot` on `usage/office` (one subscription; three of 64 with chat), `chunk(id)` and `budgets()` = `get`. `claude.use('db')` is called once and shared with chat. Data comes from `D.usage = {v:1, session, builtin}`, only in `--ledger` builds.
- Pick (pure `C.usagePick(builtin, meta, chunks)`): use the db when meta exists, `meta.session === builtin.session`, `meta.last_n >= builtin.last_n`, and the chunks add up to `meta.runs` and `last_n`. Otherwise use the built-in copy. **Stale = older than the build** (lower `last_n`). There is no clock threshold: the office runs in bursts, so days without a sync is normal, and showing a db copy older than the built-in one would show less. Note under the usage panel: db, "Synced <WIB time>"; built-in, "Built-in copy as of run #<n> (<date>)" plus "never synced" (empty db), "synced copy is older" (stale), "sync incomplete" (counts mismatch), or "synced data not available" (`unavailable`, `not_granted`, timeout). It never shows a blank or an error.
- On the db: `D.events = C.ledger.toEvents(header, runs)` (JS port of `to_event_log`; chat runs skipped as today), `D.budgets`, `D.ledger.main = meta.main`. Then rebuild `EV`, `TL`, `TOTAL`, `TI` and the scrub marks (the marks loop at ~1536 becomes a function) and `seek(T)`, or `TOTAL` if the replay had ended. A meta snapshot change re-gets only chunks whose `sha256` changed.
- Chat runs and main-session lines show as today: chat runs are in `meta.totals` (shared) but not in the per-agent bars (no task, same as a `--ledger` build); main-session lines are in their own T-070 row and never summed.

**What the build embeds.** `--ledger` no longer embeds run events or `data.ledger` (its tasks and sprints grow). It embeds a fixed-size `builtin = {session, last_n, last_date, runs, not_reported, session_totals, agents:{id:{runs, nr, tokens, tools, last}}, main}` (bounded by org size; no notes, no per-task rows) plus `D.budgets`. With no db, `initState` seeds `s.rec` from `builtin.agents`, and the scrubber shows no runs. The build stays deterministic (no build time), so `--check` still works.

**Bytes.** Committed page after T-070: 236,405 B against 237,568 B (1,163 B headroom). T-069 page code is an estimated +3.5 KB, so it does not fit. Options: raise the limit again (the test comment says the next raise needs a split or minify decision), or strip comments in `render()`. Chosen: `render()` drops whole-line comments only (`^[ \t]*/\*.*\*/[ \t]*$`, plus the 3 multi-line whole-line blocks; never inside the data line). I measured 7.7 KB of these on the T-070 template; the template keeps its comments. Estimate: committed page about 232.2 KB (about 5.4 KB headroom), limit unchanged at 232 KB. Published page today 251,565 B (24.8 KB of it events, 5.5 KB `ledger`); estimate about 221 KB, flat with runs. Build notes record the real figures; if headroom is under 2 KB, the Engineer stops and comes back to me rather than raising the limit.

**Tests.** `tests/test_usage_sync.py` with an invented fixture ledger that includes T-070 lines and null tokens:
- empty db gives chunk + budgets + meta;
- re-planning from those docs gives 0 writes;
- appending a run gives last chunk + meta only;
- a budgets change gives budgets + meta;
- packing at the 128 KiB boundary (long notes);
- refusals: over 256 KiB, over 25,000 docs (via `other_docs`), a scan hit, and rules missing, below owner or wide;
- `meta.totals == ledger.totals` and `meta.main == main_totals`;
- the chat rule tests are unchanged.

Node parity: `C.ledger.toEvents` vs `to_event_log`, and `C.usagePick` cases (empty, error, stale, other session, incomplete, ok). `test_office_app`: no run events and no `data.ledger` in a `--ledger` build; builds with 67 and 96+ runs differ by under 1 KB; committed page within the limit; no whole-line comment is left and the scripts still parse; `--check` passes. Screenshots (stub `claude`, `/tmp` only) at 1280x800 and 390x844: db ok, empty, `unavailable`, `not_granted`, stale, and a live append; 0 console errors. C7-style check: `db_write` as `asLevel: view` on `usage/office` and on a chunk is refused, recorded in Build notes.

**Risks.**
- R1, partial sync: meta is written last and the page checks counts, so a half-applied sync shows the built-in copy and a re-run repairs it.
- R2, forgotten sync: the note shows the time, and a newer build wins.
- R3, unknown: whether `db_write` supports create-only, and whether re-declaring `db` with a second rule keeps the chat data. Build confirms both with `describe_capabilities` / a test write before the real declare; one office session at a time (§9 step 11).
- R4, rebuilding the replay at runtime can break the scrubber: covered by the parity and screenshot tests.
- R5, a new data class on claude.ai: run lines (agent and task ids, counts, notes of up to 200 characters) and budgets (`set_by` names such as "Merwyn", "Janice (pmo)"). They are scanned before writing. No personal data is expected.
- A4, an existing gap: chat runs are not in the page's per-agent budget bars (event log needs a task). The gap is unchanged here.

Compliance: flagged. For Wulan: a new data class in the artifact db (ledger runs, budgets with `set_by` names, notes); owner-only `usage` rule; scan before write; C1-C8 unchanged; the db copy's retention is open (it mirrors the repo and has no purge).

**Decision record draft.** Decision: usage reaches the page from the artifact db as byte-packed chunks, synced one-way by a stdin-only plan and written by Janice. The build embeds only a fixed-size snapshot and strips whole-line comments. Context: every ledger append needed a republish, and the page grew by about 256 B per run. Options: one doc per run (simple diff, one write per run, 25k-run cap); chunks (2 writes per sync; the last chunk is rewritten); keep republishing (no db, page keeps growing). Chosen: chunks, because there are fewer writes and the limits stay far away. Consequences: the page depends on a sync step, and staleness is defined against the build; the size guard moves to the template code. Links: T-069, T-063, T-065, T-070.
— Fang (architect)

## Compliance
Compliance: PASS with conditions (T-069 design, 26 Nov 2026). New data class in the artifact db: ledger runs (agent and task ids, step, counts, durations, notes of at most 200 characters) and budgets (`set_by` names). No personal data, no prod rows, no secrets are expected. The design stands only if U1 to U7 are built. If U1, U2, U4 or U5 is declined, this becomes a BLOCK and goes to Merwyn.
- U1 Scan before every write: `usage plan` runs `chat.scan` (a superset of `events._data_hit`: phone numbers, long numbers with separators, secret-like tokens, non-ASCII digits) plus the `workspaces.yaml` forbidden terms on every string of every doc, including `session`, header `covers`, run `note` and budgets `set_by`/`note`. Any hit exits 1 with the kind only, never the value, and writes nothing. Test with the shared invented fixtures.
- U2 Allowlist, not copy: chunk runs keep only the known fields (n, sprint, agent, tasks, step, tokens, tool_uses, duration_ms, date, note, and the SDK fields model, input, output, cache_read, cache_write). The plan refuses a run with an unknown field. The meta header copies only provider, not_reported and covers, never `source` or `recorded_by`. `set_by` is Merwyn or an office agent label. Notes stay captions and pointers; a chat run note is only `chat message <id>`.
- U3 Owner-only: the `usage` rule is `read:"owner", write:"owner"`; the plan refuses if it is missing, below owner, or covered by a wider rule (path `""`, `/` or `*`). The chat rule and `rules_problem(rules)` default behave exactly as in T-063, with the T-063 tests unchanged. The sync also requires the `chat` rule to be owner-only. Record in Build notes `db_write` as `asLevel: view` refused on `usage/office`, on a chunk and on `usage/budgets`, and `db_list` as view returning nothing (as C7).
- U4 Re-declare: `declare_capabilities` is a whole declaration, so it must repeat `user`, `db` and the unchanged `chat` rule, plus `usage`. Before it, Janice records the count and ids of the `chat` docs (no text). After it, she confirms `db_rules_get` shows both rules and the chat doc count is unchanged. Do this before any usage write. If chat docs are lost, stop and tell Merwyn. Merwyn confirms this declare and the publish, as he did the first (C7).
- U5 Private: the artifact stays private. The built-in snapshot in the page is the same aggregate data the page already carries. Sharing it, or widening any rule to view or higher, needs a new compliance check and a `usage` purge first (C7 stands). The README says so.
- U6 Retention (answers Fang's open question): the db copy is a disposable mirror of the repo ledger, with no clock purge. The sync mirrors the repo, so a run or session ledger removed from the repo is deleted from the db on the next sync (delete with ifVersion, chunks of other sessions included). The plan reports orphans. If a scan miss is ever found: delete the doc, fix the repo line, re-sync. The playbook states that deleting db docs does not delete session transcripts. Purge it when the artifact is shared or deleted.
- U7 Repo: the plan is stdin-only and its output is never redirected into the repo; fixtures are invented (no realistic NIK or phone); the Review log runs one scan test and one orphan-delete test.
Not legal advice. Retention for personal data does not arise here because none is allowed (T-063 C6 covers chat, 30 days).
— Wulan (compliance), pasted by Janice

**Design accepted** (Janice, 26 Nov 2026 22:30 WIB). Build starts after T-070 merges. U4: Janice asks Merwyn to confirm the re-declare and publish before doing them.

## Build notes
**What changed** (branch `t-069-usage-from-db`, built exactly to the Design and U1 to U7):
- `engine/runtime/usage_sync.py` (new, pure, no I/O) and `python -m engine.runtime usage plan <office> --ledger <file> [--now ISO]`: stdin only, output never a repo file. Refuses with exit 1, no actions and `report.docs` / `largest_doc_bytes` for: ledger or budgets errors, the `usage` or `chat` rule missing, below owner or wide (U3), a scan hit (U1: `chat.scan` plus forbidden terms on every string of every doc, kind only), an unknown run field (U2 allowlist `ledger.RUN_KEYS`), a doc over 256 KiB, and `docs + other_docs` over 25,000. Idempotent: matching docs get no action (second plan `writes:0, in_sync:true`); orphan chunks and a stale budgets doc are reported and deleted with `ifVersion` (U6).
- `chat.rules_problem(rules, path="chat")`: path argument added; chat default and messages unchanged, T-063 tests untouched.
- db layout: `usage/office` meta (last, commit point), `usage/office/chunks/<session>-<k:03>` (byte-packed to 128 KiB), `usage/budgets`. Today's 109 runs: 1 chunk, 3 docs, largest 18,200 B.
- Page (`engine/app/office.template.html`): `OfficeCore.ledger.toEvents` (port of `to_event_log`), `OfficeCore.usagePick` (db / built-in, stale = lower `last_n`), `initState` seeds the built-in per-agent totals, `getDb()` is the one `claude.use('db')` (chat shares it), `usageStore(db)` (`onSnapshot` on meta, `get` for chunks and budgets; reads only), `usageApply` rebuilds `EV`, `TL`, `TOTAL`, `TI`, marks and calls `seek`. A note under the usage panel: `Synced <WIB>` or `Built-in copy as of run #n (date): <reason>.`
- `scripts/office_app.py`: `--ledger` builds embed `data.usage.builtin` (fixed size, bounded by the org) and `events: []`, no `data.ledger`. `render()` strips whole-line comments from the built page only (`strip_comments`; the template keeps them; 86 lines, 7.8 KB).
- Docs: `engine/app/README.md`, `engine/schema/usage.md` (Artifact db), pmo-playbook section 8 (sync procedure, U3, U4, U5, U6) and Publish.
- Tests: `tests/test_usage_sync.py` (23 tests, invented fixture `tests/fixtures/session_FIXTURE069.jsonl` with a main-session line, null tokens and a chat run; one scan test, one orphan-delete test, per U7); in `tests/test_office_app.py` node parity for `toEvents` vs `to_event_log`, `usagePick` cases, built-in copy == synced copy (budget view deep-equal, on the fixture and the live ledger), flat size, no whole-line comment left, all scripts parse, usage store reads only. Existing recorded/chat-ledger tests now rebuild events from the synced docs. `tests/test_dryrun.py` allowlist gained `hashlib` (stdlib, used for the chunk `sha256`).

**Figures.** Committed `office.html` 234,993 B (limit 237,568 B, unchanged; headroom 2,575 B, over the 2 KB bar). Published build (109 runs, `--ledger --chat`) 221,669 B (was 251,565 B). Same build with 50 synthetic runs added to a temp ledger: 221,721 B (+52 B, flat). Builds with 67 and 109 runs differ by under 1 KB (test).

**How to verify.**
```
python -m unittest discover -s tests            # 483 tests, exit 0
python -m engine.runtime validate ai-office
python scripts/office_app.py ai-office --chat --check
python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
python scripts/board.py ai-office               # board.md discarded
echo '{"rules":[{"path":"chat","read":"owner","write":"owner"},{"path":"usage","read":"owner","write":"owner"}],"docs":[],"other_docs":0}' \
  | python -m engine.runtime usage plan ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
```
**Headless check** (published build, stub `claude` whose db returns the docs; Chrome headless, software GL; screenshots in /tmp only, not committed). At 1280x800 and 390x844 (phone: the usage sheet from the gear menu), 0 console errors and 0 overlaps between usage, events, card, bar, top strip, chat and tone for each state:
- (a) synced docs (a ledger with 2 more runs and a second main reading than the build): `Synced 27 Nov 08:00 WIB`, main row "in 458 ... out 103k" (newer than the built-in 448 / 102k), so the db copy is what shows; a pushed snapshot with a new `synced_at` updates the note live without reload.
- (b) empty db: built-in copy, `Built-in copy as of run #109 (2026-11-26): never synced.`
- (c) stale copy (67-run ledger): built-in, `synced copy is older (synced 27 Nov 08:00 WIB)`.
- (d) unavailable: `use('db')` rejecting, `onSnapshot` error `unavailable`, and error `not_granted`: built-in, `synced data not available`.
In every state the Summary and Detail figures are present (never blank). Detail at 1280x800 can auto-collapse the usage panel into its one-line summary when the longer built-in note adds a line; that is the existing placement ladder, not a new overlap.

**Deviations from the Design (for Reviewer and Wulan).**
1. U1 and the session id. A real session id (`session_` plus 24 characters) is 32 characters and `chat.scan` reports it as a "secret-like token" (long-token rule), so scanning "every string including `session`" would refuse every real ledger. Exemption, in `usage_sync.scan_doc` only: the validated session id in a doc's top-level `session` field gets the `events.py` data patterns and the forbidden terms but not the long-token rule. The same text in any other field (a run `note`, covers) is still a hit (test). Generated hashes and chunk ids are not scanned (they are not ledger text). Wulan, please confirm.
2. Committed page is 234,993 B, not the Design estimate 232.2 KB (the page code is about 6 KB, not 3.5). Headroom is 2,575 B, above the 2 KB stop line; the limit is unchanged.
3. First db copy shows its final totals and does not auto-play (the built-in page has no events, so nothing was playing); a later snapshot keeps the viewer's place, or the end if the replay had ended. `usagePick` has one more reason than the Design, `other` ("synced copy is another session").
4. Docs under `usage/` that are neither a planned doc nor a chunk or the budgets doc are reported as `unknown` and not deleted.
5. Not done, by instruction: no artifact or db tool was called. So C7 for `usage` (`db_write` as `asLevel: view` refused on `usage/office`, a chunk and `usage/budgets`; `db_list` as view empty), the Design R3 questions (does `db_write` support create-only; does re-declaring keep the chat docs) and U4 are for Janice with Merwyn's approval, before the first usage write (playbook section 8).

**Open questions (unchanged, for Janice at first sync).** Create-only `db_write`; chat docs survive the re-declare; C7 view-level refusals for `usage`.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
- Does `db_write` support create-only (no doc yet), and does re-declaring `db` with the added `usage` rule keep the existing chat docs? Engineer, from describe_capabilities and a test write before the real declare (Design R3).
- Retention of the db copy of usage (it mirrors the repo ledger and has no purge): keep as is, or purge on session end? Wulan.
- Answered in the Design (Fang): stale = older than the build (no clock threshold), "last synced" from `usage/office.synced_at`; chat runs and main-session lines show as today; limits are as confirmed in chat.md, and today's 100 runs need 3 docs.
