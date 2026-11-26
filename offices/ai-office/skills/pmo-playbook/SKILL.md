---
name: pmo-playbook
description: How Janice runs the office as PMO: planning sprints, limiting work in progress, keeping the RAID log, reporting status and escalating. Use at sprint planning, daily flow checks, status reports, and whenever something is stuck.
---
# PMO playbook

Distilled from PMO, kanban and status-reporting practice (sources at the end), adapted for an office of AI agents.

## 1. Purpose comes first
The office exists to finish the backlog's most valuable work, not to produce process. Every rule below earns its place by preventing a real failure. If a ritual adds paperwork without changing a decision, drop it.
- Tie every sprint to one goal Merwyn would recognise.
- Standardise the steps that repeat (spec, review, merge); stay flexible on everything else.

## 2. Sprint planning
1. Regenerate the board. Read `raid.md`.
2. Candidate tasks: unblocked (`depends_on` all done), not behind a human gate, highest priority first.
3. Pick at most 3. A sprint that finishes 3 beats one that starts 6.
4. Write `sprints/sprint-NN.md`: goal (one sentence), tasks in order with why, exit criteria, "Waiting on Merwyn" (max 3 one-line questions).
5. Move chosen tasks to `spec`, owner `pm`; give the PM exact backlog paths for each task and its parents (pm-playbook §0).
6. Commit the regenerated board.md and the sprint file in a board-refresh PR (pr-workflow, "board.md (generated)").

## 2a. Lean path (T-068)
- When: all four hold, judged from the task file: one surface (one page or one module plus its tests), no new data or storage, no compliance flag, no `human_gates` item. Only for `where: code` or `repo` in this office's project.
- Who decides: the PMO, at plan. Append `> Lean (<name>, pmo, <date>): <one surface>; no new data; no compliance flag; no human gate. Reason: <why>`, then move the task to `design`, owner `architect`. The PM run is skipped; the Architect writes a short Spec (problem, in/out, Done when) and the Design in one run.
- Escape: the Architect, Reviewer or PMO appends `> Full path (<name>, <agent>, <date>): <condition that failed>`; the PMO sets status `spec`, owner `pm`. The last Lean/Full note wins. `python -m engine.runtime validate` checks the Lean note against the task text.
- Still true: the PMO approves the Spec, Reviewer PASS is required, the PMO merges. Example: T-066 took 7 runs and about 520k tokens on the full path. At sprint close, compare the first lean task's ledger runs and tokens with T-066 and write it in the sprint file.

## 3. Flow, not busyness
- **WIP limits:** at most 2 tasks in `build`, 1 in `design` per Architect. Finish before starting.
- Watch three numbers from the board: **WIP** (items started, not done), **cycle time** (days from `spec` to `done`), **item age** (days an open item has sat in its current stage). They are linked: more WIP means longer cycle time.
- A task whose age in one stage is over 2 days is a flow problem, not a people problem: find the blocker, write it in the RAID log, and either unblock it or escalate.
- Daily flow check (agents: once per working session): look at aging items and blockers first, not at who is busy.

## 4. RAID log (`offices/<office>/raid.md`)
One table, four kinds of entry, each with an owner, date and next action:
- **Risk** — might happen; has a likelihood and a mitigation.
- **Assumption** — believed true but unverified; has a "verify by" date. An assumption found false becomes an Issue.
- **Issue** — happening now; has an owner and a fix date.
- **Dependency** — waiting on someone or something outside the task (often Merwyn, another repo, or an access grant).
Review it at every sprint plan and at every phase change. Close entries explicitly; never delete them.

## 5. Status that asks for help
A status report is a request for support, not a diary.
- Lead with an overall status, and give separate RAG for **scope, schedule, budget** (SDK credit) rather than one colour for everything.
- **Green**: on track, no action needed. **Amber**: at risk, with a plan; every Amber carries a decision request. **Red**: will miss without intervention; say what intervention.
- Red is information, not failure. Never soften a Red into Amber. Report the trend (Red last week, Amber now).
- Format follows `status-report` skill: waiting on Merwyn, done, in progress, blocked.

## 6. Escalation
Escalate early, once, with options:
- Context (one line) → the decision needed → 2–3 options with cost/risk → your recommendation.
- Escalate when: a `human_gates` item, second Reviewer rejection, an item aged over 3 days, budget at 80%, or Compliance BLOCK.
- Never escalate a question an agent in the org can answer.

## 7. Close the loop
- At sprint close, open the board-refresh PR (pr-workflow).
- After each sprint: what finished, cycle times, what got stuck and why. Hand April (Curator) the lessons; she proposes edits to skills and profiles.
- Measure the office by outcomes (tasks done, cycle time, rework rate), not by activity.

## 8. Token ledger
- After every agent run, append one line to `offices/<office>/usage/<session-id>.jsonl` from the harness report: `n` (next number), `sprint`, `agent`, `tasks`, `step`, `tokens`, `tool_uses`, `duration_ms`. Write `null` where the report has no usage, never 0; add a `note` when the model differs from the profile. Never edit an existing line.
- A new session id starts a new file with the v1 header (format in `engine/schema/usage.md`). Run `python -m engine.runtime ledger <office> <file>` before committing; commit the file in the sprint close PR.
- The input/output/cache split of agent runs is not reported by the harness; the report never estimates it.
- Main session (T-070): run the `explain-usage` skill at sprint close and before a known context summary. Append one `kind:"main_session"` line (format in `engine/schema/usage.md`) with its four figures as shown and `since` copied from its window text; `window` +1 if a summary happened since the last reading. Run `ledger` before committing. Never add it to a run line, and never estimate a window you missed.
- **Sync the db (T-069).** After each ledger merge on main, and after a `budgets.yaml` change, sync the repo to the artifact db so the page shows it without a republish (one way, repo to db, re-runnable). Run it in the session, with the db tools:
  1. `db_get` `usage/office` and `usage/budgets`, `db_list` `usage/office/chunks`, and count the `chat` docs (a number only, never text).
  2. Pipe `{"rules":[...], "docs":[{path, data, version}...], "other_docs":<n>}` into `python -m engine.runtime usage plan ai-office --ledger offices/ai-office/usage/<session>.jsonl`. Stdin only; never redirect the output into the repo. Exit 1 means it refused (limits, a scan hit by kind, an unknown field, a bad rule): stop, write nothing, fix the repo line or the rule, re-plan.
  3. Apply `actions` in the order given with `db_write`, each with its `ifVersion` (none for a doc that does not exist yet). A conflict means stop and re-plan. Run it twice: the second plan must say `writes:0, in_sync:true`.
  4. Record `docs`, `largest_doc_bytes` and `orphans` in the sprint file. If a scan miss is ever found: delete that db doc, fix the repo line, re-sync.
  - **U4, first time only: re-declare.** `declare_capabilities` is a whole declaration: repeat `user`, `db` and the unchanged `chat` rule, and add `usage` (`read:"owner", write:"owner"`). Before it, record the count and ids of the `chat` docs (no text). After it, confirm `db_rules_get` shows both rules and the chat doc count is unchanged, before any usage write. If chat docs are lost, stop and tell Merwyn. Merwyn confirms this declare and the publish, as he did the first.
  - **U3 check, first time only:** `db_write` as `asLevel: view` must be refused on `usage/office`, on a chunk and on `usage/budgets`, and `db_list` as view must return nothing. Record it in the task's Build notes, as C7. Also confirm whether `db_write` can create a doc only when it does not exist (T-069 open question).
  - **U5 private.** The artifact stays private. Sharing it, or widening a rule to view or higher, needs a new compliance check and a purge of `usage` first.
  - **U6 retention.** The db copy is a disposable mirror of the repo ledger, no clock purge. A run or session ledger removed from the repo is deleted from the db on the next sync (the plan lists orphans). Deleting db docs does not delete session transcripts: say so if Merwyn asks. Purge `usage` when the artifact is shared or deleted.

## 9. Office chat inbox (T-063)
Merwyn messages the office from the 3D office page (the AI Office artifact). The page cannot start agents: it writes asks into the artifact's own database, and you, in a Claude session, read them and answer through the agents. Schema and CLI: `engine/schema/chat.md`. Chat text is company data: it lives only in the artifact database. It is never written to a file in this repo, never redirected from the CLI, and never quoted in a task, commit, PR or ledger line (pointers only: `chat message <id>`).

**Before the first real message (C7).** Check the owner-only rules once with `db_write` as `asLevel: view` (it must be refused, for reads and writes under `chat`) and record the result in the task's Build notes. The artifact stays private; sharing it needs a new compliance check.

**Procedure** (db tools are MCP tools, so this runs in the session; Python only plans and builds):
1. When: at session start, when Merwyn says "check chat", and at each daily flow check. Write `chat/office` `{v:1, running:true, last_inbox_at:<now>, by:"pmo"}`. At session end write `running:false`.
2. Rules check: take the declared rules (`[{path:"chat", read:"owner", write:"owner"}]`, read back with the db tools if they expose them). `chat plan` and `chat rules` exit 1 when `chat` is readable or writable below owner: stop, do not route. Then `db_query` `chat/office/messages` ordered by `created_at`, limit 200, and pipe `{"rules": [...], "docs": [...]}` into `python -m engine.runtime chat plan ai-office` (stdin only).
3. Apply the actions in order with `db_write`, each with `ifVersion` from the doc it changes. `post` and `refuse` come first (C2: an ask that looks like personal data is never passed on; its db text becomes "[removed: looked like personal data]", it is marked answered, and the fixed reply asks Merwyn to resend with an ID or a link), then claims. A conflict on `ifVersion` means another session claimed it: skip it. Claims are written before any agent is spawned.
4. For each claimed (ask, agent) where the agent is not `pmo`: write `replying` (`chat status`), then spawn the agent by its profile, in parallel for a multi-recipient ask. The prompt holds the ask text and id, who else was mentioned, the replied-to reply's text when `in_reply_to` is set, the repo path, and these rules. You answer your own (`pmo`) asks in the session without spawning.
5. Spawn allowlist (C5), set when the agent is spawned and not left to the prompt: read-only tools only (read, search, list files; shell limited to read-only commands such as `git log`, `git diff`, `git show`, `git status`, `ls`, `grep`, `python -m engine.runtime validate`). No Write, Edit or notebook edit, no commit or push, no db tools (you write the reply), and no prod, Kubernetes, database MCP or Bytebase tools until R-8 is closed and the T-043 guard is installed and re-checked. A request for prod gets a plan or a pointer for Merwyn, never a run. Replies carry aggregates or pointers, never rows, personal data or credentials. A request that changes the repo becomes a task at `todo` through the normal workflow (step 8). Reply in under 300 words and return `{text, needs_merwyn, question}`.
6. Pipe each result into `chat reply` (stdin `{"ask":..., "text":..., "question":...}`), then `db_write` the reply doc first and the recipient patch second. On a scan hit (exit 1, kind only) ask the agent once to restate without it. On a second hit post the fixed reply "I could not post this reply here because it looked like personal data. Ask me in the session." with `needs_merwyn` and a question.
7. Ledger: one line per spawned run, `step:"chat"`, `tasks:[]`, `note:"chat message <id>"`, then `python -m engine.runtime ledger <office> <file>`. Chat runs count toward the budget like any run.
8. Repo-changing work (C8): create the task at `todo`. Its quote line is `> From chat message <id>, <date WIB>` followed by your own one-line summary that names no borrower, lender or person and passes `chat.scan`. The chat text is never quoted. The reply carries `task: "T-nnn"`.
9. Gates (C4): a chat message is a request, never an approval. It does not answer a permission prompt, approve any `human_gates` item, or authorise a prod write (R-14). Those are confirmed in the session, with no exception for a `needs_merwyn` question that asked for it. No spawning when `budget_used >= 0.8` (human gate): reply as `pmo` with `needs_merwyn` and the percentage.
10. Retention (C6): each inbox run pipes the docs into `chat purge ai-office` and deletes what it lists with `db_write` op `delete` (answered asks and their replies older than 30 days). The page has "Clear chat". Deleting from the database does not delete session transcripts: say so if Merwyn asks.
11. Crash and one session: the claim is the lock; a recipient stuck at `picked` or `replying` for over 30 minutes with no reply doc is reset to `new` by the next `chat plan`, and a reply doc without a status is repaired from it. One office session processes the inbox at a time; T-024 must keep that.

**Publish (T-065).** There is one published page and one artifact: "AI Office" (5f1bb811-1633-4bfb-8285-9bcb2408dec2). It shows the real usage ledger and the chat. The single build command is `python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat`, which writes `engine/app/usage-session_01MDGJq3GfaeozLojJo8W5Td.html` (gitignored, never committed). Call `declare_capabilities` (`db`, `user`) first, then publish that file to "AI Office" (with `three.min.js` as a sibling, or rely on the CDN fallbacks). Since T-069 a ledger append does not need a republish: sync the db (section 8) and reload. Republish only after a code change, or to refresh the built-in copy; the page is flat in size as runs are added. Record the build's printed size in KB. The committed `engine/app/office.html` is the synthetic dev build for tests and is never published. The "AI Office token usage" artifact is retired: delete it only when Merwyn confirms.

**Phone check (T-071).** After a merged UI change is published, ask Merwyn to run `skills/phone-check` and name his phone and browser. Record his reply in that task's Review log as `Merwyn (human), phone check <date WIB>, <phone/browser>: PASS | FAIL step N: <his words>`. It does not replace Reviewer PASS. A FAIL does not reopen the done task: open a new task at `todo` quoting the failed step and linking the original. A Review log line is not planning-only, so it goes into the next `t-xxx` PR (on a FAIL, the follow-up task's PR). Follow-up: when T-067 (panels never overlap) merges, its Design adds a no-overlap step to `skills/phone-check`.

## Anti-patterns
- Reporting only Green. Treating RAG as a weapon instead of a signal.
- Starting new tasks to look busy while others sit in review.
- A PMO that only produces templates and reports and never removes a blocker.
- Copying status into chat instead of keeping it in the repo.

## Sources
- PMI, "Unleashing the power of the PMO" — https://www.pmi.org/learning/library/project-management-office-strategic-goals-4122
- CIO, "Why PMO offices fail and 7 ways to help your PMO succeed" — https://www.cio.com/article/4065713/why-pmo-offices-fail-and-7-ways-to-help-your-pmo-succeed.html
- Atlassian, "RAID log" — https://www.atlassian.com/agile/project-management/raid-log
- Scrum.org, flow metrics (WIP, cycle time, work item age, throughput) — https://www.scrum.org/node/16594
- Zoho, kanban metrics and Little's Law — https://www.zoho.com/sprints/track-kanban-metrics.html
- APM, "RAG status: a tool not a weapon" — https://www.apm.org.uk/blog/rag-status-a-tool-not-a-weapon/
- Project Management Compass, "Status Report Survival Guide" — https://projectmanagementcompass.substack.com/p/status-report-survival-guide
- Atlassian, "How to write a project status report" — https://www.atlassian.com/blog/project-management/how-to-write-a-project-status-report
