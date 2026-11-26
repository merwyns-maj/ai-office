---
id: T-057
title: "Record and show real token usage per agent, per session"
phase: 6-office
status: todo
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-056]
pr: null
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

## Design

## Build notes

## Review log

## Decision

## Open questions
