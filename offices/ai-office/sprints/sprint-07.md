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
