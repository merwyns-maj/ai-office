# Sprint 7

**Goal:** Record real token usage per agent and per session, and show it in the metrics report and the 3D office.

## Tasks (in order)
1. [T-057](../backlog/T-057-token-usage-per-agent-per-session.md) (P1): Merwyn asked on 26 Nov 11:20 to evaluate each session's token use per agent. Dinda consults (usage panel).

1 task, repo-only. Everything else waits on Merwyn (T-002, T-019, T-005, T-024).

## Exit criteria
- T-057 `done` with Reviewer PASS and merged; metrics report and 3D office show this session's real per-agent tokens; the PMO records every later run.

## Decisions recorded (Merwyn, 26 Nov 2026 11:20 WIB)
- "Yes please do, evaluate in each session, each agents how much token they used" (answer to: per-agent usage of the Max plan).

## Close (26 Nov 2026) — Janice (pmo)
Status: scope Green, schedule Green, budget Green.

**Finished:** T-057 token usage per agent per session — PR #40 (one REJECT on the provider label reading as a Max-plan share, fixed; Reviewer PASS). Includes Merwyn's 11:31 request: provider bars with % of session, per-agent accordion expanded by default.

**Ledger:** runs 36–40 (Sprint 7 design, build, review, rework, re-review) appended to usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl: 40 runs, 1 not reported, 3,218,310 tokens as reported. Runs 39 and 40 were resumed agents; the harness figure may include their earlier run, so the session total may count up to 285,812 tokens twice (runs 37 and 38) (noted on each line).

**Published:** recorded usage page https://claude.ai/artifact/YL5g2LV4MgWL9n2PHQ6eP3; 3D office (synthetic demo) republished with the same bars and accordion.

**Carry forward:** usage.md example header still says claude-sdk; phone usage sheet cramped; unknown-agent error echoes the value on stderr; resumed-agent overlap needs a rule (prefer fresh agents for rework, or record the delta).

**PMO note, 26 Nov 2026 22:10 WIB (Janice):** Merwyn, at 7,347,373 agent tokens (92% of 8M): "np just proceed. budget is not a constraint". The `budget_used >= 0.8` gate is answered for this session's remaining work (T-070, T-069, chat replies); the 8M figure in budgets.yaml stays as the page's reference until Merwyn sets another, so the bar shows red past 8M. Chat messages m-mwxhmrx2-582l and m-mwxhs3dt-3w9c waited about 3 hours unanswered: the inbox was not checked during agent waits. From now on Janice checks the inbox after each merge.

**PMO note, 26 Nov 2026 23:35 WIB (Janice): T-069 live steps (U3, U4, sync), with Merwyn's approval of 22:30 WIB.**
- U4: before the re-declare, the 4 chat message docs (2 asks, 2 replies; ids only, as m-mwxhmrx2-582l, m-mwxhs3dt-3w9c, r-m-mwxhmrx2-582l-pmo, r-m-mwxhs3dt-3w9c-curator) plus the `chat/office` meta. `declare_capabilities` (version 1795710790-0c78) set `db` rules chat and usage, both owner/owner, plus `user`. After it, `db_rules_get` showed both rules and the 4 chat docs were unchanged.
- U3 / C7: `db_write` as `asLevel: view` was refused (404, nothing written) on `usage/office`, `usage/office/chunks/probe` and `usage/budgets`; `db_list` as view on `usage/office/chunks` returned no docs.
- First sync (`usage plan`, exit 0): 3 docs, largest 19,099 B, 114 runs in 1 chunk, 0 orphans, 0 unknown; written in order chunk, budgets, meta (each version 1). The second plan (in_sync check) was not run: it needs the stored docs fed back on stdin, which is a manual copy of 19 KB. Next sync will show in_sync.
- Open: whether `db_write` can create only when absent was not tested.
- Published "AI Office" version 1795710943-3e09 from the combined build: 221,670 B (216 KB), 114 runs built in, 0 events embedded.
