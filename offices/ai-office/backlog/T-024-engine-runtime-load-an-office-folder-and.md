---
id: T-024
title: "Engine runtime: load an office folder and run its agents on the Agent SDK"
phase: 6-office
status: design
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-001]
pr: null
---

> Replaces the Claude Code subagent phase

> Merwyn, 26 Nov 2026 19:54 WIB: "Just start these all no worries except 6". Started as planning only (spec and design). Where the runtime runs, hosting, sign-in, keys and any paid resource are human gates: listed for Merwyn, nothing created. Goal from T-063: agents reply to chat without an open Claude session.

## Done when
- [ ] Runs offices/ai-office end to end on one task
- [ ] Uses Max SDK credit (ANTHROPIC_API_KEY unset)

## Spec

**Note from T-057 (26 Nov 2026):** the SDK runtime appends one line per agent run to `offices/<office>/usage/<session-id>.jsonl` in the format of `engine/schema/usage.md`, filling `model`, `input`, `output`, `cache_read`, `cache_write` from each result message (check field names against the SDK docs), and drops `split`/`model` from `not_reported`.

**Problem.** The office's agents run only inside an open Claude session. T-064 states the goal: agents reply to chat and an installable app without an open Claude session, which needs an engine runtime that loads an office folder and runs its agents on the Agent SDK. Merwyn's 26 Nov 19:54 note: planning only; hosting, where it runs, sign-in, keys and any paid resource are human gates.

**Why chat needs it (facts from T-063).** The published 3D office page cannot start an agent. Chat is a shared inbox in the artifact's own database; replies come only while an office session is running (today the main Claude session; "later, the SDK runtime, T-024, continuously"). The db tools (db_get, db_list, db_write) are MCP tools used from a Claude session, and pmo-playbook section 9 says T-024 must keep "one office session processes the inbox at a time". T-063's decision draft says the runtime can later run the same `chat plan` / `chat reply` loop unchanged.
- In scope addition: the plan says how the runtime would run that inbox loop (including the 30-day purge and ledger line per chat run, `step:"chat"`) and keeps one processor at a time.
- Unknown: whether a runtime outside a Claude session can reach the artifact database at all (see Open questions).

**In scope (this task, planning only)**
- Plan the runtime: load `offices/<office>/`, run an agent from its profile and skills, write results to the task file, append one usage line per run (T-057 note above).
- List the hosting and sign-in options with trade-offs for Merwyn (see Open questions). Name the cost risk in RAID R-2 (loops overspend SDK credit) and R-3 (Claude app skills may not exist in the SDK engine).
- Reuse the existing loader and dry-run from T-039.

**Out of scope**
- Creating any host, repo, account, key, connector or paid resource; any SDK run that spends credit.
- The app (T-064), Telegram bridge (T-029), cost cap and logging (T-026), BAU workflows (T-025).
- Choosing the option: Merwyn decides, then the Architect designs.

**Done when (planning slice, each checkable by a reviewer)**
1. The Design section lists at least three hosting or run-location options, each with cost, sign-in or key need, and risk, and ends with no option chosen.
2. Every human gate item (hosting, where it runs, keys or sign-in, paid resource) appears as a question marked "Merwyn".
3. A plan states how a run is recorded in `usage/<session-id>.jsonl` per `engine/schema/usage.md`, with SDK field names to be verified against the SDK docs.
4. The plan states how "ANTHROPIC_API_KEY unset" (original Done when) will be checked, or flags it as blocked on the sign-in decision.
5. `git diff` shows no change outside this task file and no created resource.
6. The full build (end to end on one task, on Max SDK credit) is not claimed done; it stays open behind Merwyn's answers.


**Spec approved** (Janice, 26 Nov 2026 20:05 WIB).

## Design
**Compliance: flagged** for Wulan before any build: chat text (personal-data risk, C1-C8), a stored sign-in token or API key, and prod tools (R-8, T-043). Planning only; nothing created; no option chosen.

**Runtime shape (same for every option).** `engine/runtime/run.py` + CLI `python -m engine.runtime run <office> [--task T-xxx] [--provider fake|sdk]`. Reuses `loader.load_office`, `validate`, `dryrun.pick_next`/`plan`. Builds the system prompt from `agents/<id>.md` and its skills, runs one stage step, writes only that stage's section and `owner` (status stays with the PMO step), appends one ledger line. A `FakeProvider` (no network, canned result) lets all of this be built and tested with zero spend; the `sdk` provider is wired only after Merwyn's answers.
- **Ledger.** New file `usage/session_<sdk session id, hyphens removed>.jsonl` (the SDK id is a UUID; the schema regex has no hyphens), header `provider: claude-sdk`, `not_reported` without `split`/`model`. From the result message (field names to verify against SDK docs): `input`=usage.input_tokens, `output`=usage.output_tokens, `cache_write`=usage.cache_creation_input_tokens, `cache_read`=usage.cache_read_input_tokens, `tokens`=their sum, `duration_ms`, `tool_uses`=count of tool-use blocks, `model` from the assistant messages, `date`. Checked with `python -m engine.runtime ledger` after each append.
- **API key check.** Blocked on the sign-in decision. If Max: `run` refuses to start when `ANTHROPIC_API_KEY` is set and records the auth mode in the header `source`; a test covers the refusal.
- **Chat loop.** The runtime runs pmo-playbook §9 unchanged (`chat plan`, claims by `ifVersion`, `chat reply`, `chat purge`, ledger `step:"chat"`), only if it can reach the db tools. One processor: it claims `chat/office` `running` by `ifVersion` and exits if another holder wrote `last_inbox_at` under 30 minutes ago.
- **Skills (R-3).** Office skills are repo files, injected into the prompt; Claude app skills (for example `claude:diagram-design`) are unverified in the SDK: verify in docs, else the run notes "not available" as agents already do.

| Option | Reaches artifact db | Cost | Sign-in / key | Main risk |
|---|---|---|---|---|
| A. Merwyn's Mac, Claude desktop app or Claude Code on a schedule | Only if the artifact MCP connector is exposed there (unverified) | Plan credit; Mac must be awake | Merwyn's Max login on the Mac | Token stored locally; runs stop when the Mac sleeps |
| B. Scheduled cloud Claude session (like this one) | Likely, the same connectors as this session (to verify) | Plan credit, if scheduled sessions use it (unverified) | Merwyn's claude.ai account | Feature availability and limits unverified; unattended permission prompts |
| C. Small hosted service (VPS or Cloud Run) + Agent SDK | No known HTTP API for the db: needs a new store (new resource, chat data moves) | Host fee + per-token API (prices null in providers.yaml; not estimated) | API key, or Max token if allowed (unverified) | Paid resource, key custody, chat data in a new place |

**Security conditions for any option.** C2 scan in `chat plan` before spawn; C4 no approvals from chat, and an unattended run treats every permission "ask" as deny; C5 allowlist set in the SDK `allowed_tools` per spawn, not in the prompt; C6 purge and C7 rules check every inbox run; C8 pointers only; no prod, kubernetes, database MCP or Bytebase servers in the runtime's MCP config until R-8 closes and the T-043 guard is installed as a PreToolUse hook (SDK hook support to verify) and re-checked; fail-closed. Writes only to merwyns-maj/ai-office on `t-xxx` branches; never `main`. Key or token in the OS keychain or a host secret, never in the repo. Budget: no unattended run before the T-026 cap; stop at `budget_used >= 0.8` (R-2).

**Recommended first step (no spend, no resource).** (1) Office checks, read-only, in a session: does the artifact db MCP appear in Claude Code's or a scheduled session's tool list; SDK docs on auth (Max login vs API key), hooks, `allowed_tools`, skills. (2) Build `run.py` with `FakeProvider` and tests through the normal workflow as a new task. Then Merwyn picks A, B or C.

**Human gates for Merwyn.** 1. Where it runs: A, B or C. 2. Paid resource and monthly limit (C, or any API spend). 3. Sign-in: Max login or an API key, and where the token is kept. 4. May the runtime push branches to merwyns-maj/ai-office (a GitHub credential)? Other repos stay a gate. 5. If the db is unreachable: a new chat store (new resource, needs Compliance). 6. Spend cap value before the first paid run (T-026).

**Decision record draft.** Decision (proposed): build the runtime against a provider interface with a fake first; hosting decided by Merwyn. Options: A, B, C above. Consequences: the code is reusable on any option; real runs wait on gates 1-3 and 6.
— Fang (architect)

## Compliance
Compliance: PASS with conditions for planning, the runtime shape and the FakeProvider build (T-024 Design, 26 Nov 2026). No option is chosen, nothing is created, no spend. Per option: A PASS with conditions, B PASS with conditions, C BLOCK until its conditions are met. K1-K6 apply to A and B; C needs K1-K6 plus C-1 to C-4.
Reasoning: chat stays in the owner-only artifact db (T-063 C1-C8), which is outside company systems and not approved for personal data or prod rows (playbook s2). The runtime adds an unattended caller, a stored credential and a prod-tool config.
- K1 Chat data (gates 1, 5): reuse the T-063 store and `chat plan`/`reply`/`purge` unchanged; C1-C8 stay (C2 scan before spawn, C4 never an approval, C5 read-only allowlist per spawn in `allowed_tools`, C7 refuse unless `chat` is owner-only). No chat text in repo, logs, `usage/` notes or task files (pointers only, C8). No real run until Janice verifies the runtime can reach the db (open question 5).
- K2 Credentials (gates 3, 4): no token or key in repo, task files, logs or MCP config; Max login in the OS keychain or host secret store; `run` refuses if `ANTHROPIC_API_KEY` is set (test). GitHub credential only as gate 4 approves: merwyns-maj/ai-office, `t-xxx` branches, never `main`. Other repos need a new gate.
- K3 Prod tools (gate 1, R-8, T-043): no prod, kubernetes, DB or Bytebase MCP servers in the runtime config until R-8 closes (read-only DB role, scoped kube role, whether `kubernetes` is prod-only) and the T-043 guard is installed (Merwyn gate). R-7 stays open (real SQL key names unconfirmed). After install, verify SDK hook support and re-check the guard, fail-closed (R-15). Any permission "ask" in an unattended run is a deny. The guard is a safety net (R-9); the read-only role is the control.
- K4 Personal data / UU PDP (gates 1, 5): no prod personal data as agent context until Merwyn and KlikA2C legal approve that flow (none exists). Chat to the SDK is a transfer outside Indonesia, acceptable for operational chat only; whether it may ever carry personal data is for Merwyn and legal.
- K5 Retention and logging (gates 1, 6): 30-day `chat purge` on every inbox run (C6); ledger line per run with `step:"chat"` and the pointer only; run logs hold no chat text. The playbook says db deletion does not delete SDK transcripts; where they sit (A: Mac session files, B: claude.ai, C: host disk) is named once Merwyn picks.
- K6 Budget (gate 6, R-2): no unattended run before the T-026 cap; stop at `budget_used >= 0.8`; one processor at a time (`ifVersion` claim, `last_inbox_at` lease).
Option A (Mac / desktop app): PASS with K1-K6, plus A-1 Max login stays on Merwyn's Mac with disk encryption, nothing leaves it except SDK and GitHub calls (gate 3); A-2 if the artifact MCP is exposed there, scope it to `chat`, and check K3 against the local MCP and connector set, which may include prod tools (gate 1).
Option B (scheduled cloud session): PASS with K1-K6, plus B-1 a cloud session inherits the account's connectors (mail, drive, chat, databases): restrict it to the artifact db and GitHub and record the connector list in Build notes before the first run (gates 1, 3); B-2 no unattended approvals; verify scheduled-run permission behaviour, else deny (gate 1).
Option C (hosted service): BLOCK for any real chat or credential until gates 2, 3 and 5 are answered. C-1 separate compliance review of the new chat store (host, region, access, encryption, 30-day purge, log scrubbing) before any chat moves (gate 5); C-2 key custody in a host secret store, rotation, named owner, never in repo (gate 3); C-3 MCP allowlist and K3 guard on the host before prod tools are reachable (gate 1); C-4 a monthly spend limit in writing (gates 2, 6).
Open for legal, not Wulan: whether lending personal data may ever be processed here; until then barred. Not legal advice.
— Wulan (compliance), pasted by Janice

**Design accepted, parked for Merwyn's gates** (Janice, 26 Nov 2026 20:20 WIB): Merwyn said to leave the items waiting on him for later ("except 6"). Next step when he is ready: answer gates 1-6 above; the no-spend FakeProvider build can start once gate 1 is picked.

## Build notes

## Review log

## Decision

## Open questions
- Where does the runtime run (Merwyn's laptop, a small server, a cloud service)? For Merwyn (human gate).
- Hosting and any paid resource: which is acceptable, and what monthly limit? For Merwyn (human gate: cost).
- Sign-in or keys: does it run on Max SDK credit with a signed-in session (original Done when), or an API key? Whether Max credit can be used from a hosted runtime is unverified. For Merwyn (human gate), with the Architect checking the SDK docs.
- Is the runtime allowed to write to repos other than merwyns-maj/ai-office? For Merwyn (human gate).
- Can a runtime outside a Claude session read and write the artifact database (T-063 facts: db tools are MCP tools used from a session)? If not, chat replies without an open session need another store, which is a new resource. For the office to verify; any new store is for Merwyn (human gate).
- Do skills from the Claude app (R-3) load in the SDK engine? For the office (Architect verifies at design).
- Review-round and spend cap before the first paid run (T-026)? For the office, cap value for Merwyn.
