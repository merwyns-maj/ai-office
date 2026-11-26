---
id: T-024
title: "Engine runtime: load an office folder and run its agents on the Agent SDK"
phase: 6-office
status: todo
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-001]
pr: null
---

> Replaces the Claude Code subagent phase

## Done when
- [ ] Runs offices/ai-office end to end on one task
- [ ] Uses Max SDK credit (ANTHROPIC_API_KEY unset)

## Spec

**Note from T-057 (26 Nov 2026):** the SDK runtime appends one line per agent run to `offices/<office>/usage/<session-id>.jsonl` in the format of `engine/schema/usage.md`, filling `model`, `input`, `output`, `cache_read`, `cache_write` from each result message (check field names against the SDK docs), and drops `split`/`model` from `not_reported`.

## Design

## Build notes

## Review log

## Decision

## Open questions
