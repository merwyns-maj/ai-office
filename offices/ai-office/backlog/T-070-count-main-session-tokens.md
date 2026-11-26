---
id: T-070
title: "Count the main session's own tokens in the usage ledger"
phase: 6-office
status: spec
priority: P2
owner: pm
where: code
project: ai-office
depends_on: []
pr: null
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- The ledger header lists `main_session` under `not_reported`: the harness reports tokens for agent runs only, not for the main session (Janice, pmo). The page shows it as "not reported".
- Unknown: whether any source in this environment reports the main session's tokens (for example the `explain-usage` skill). To find out first, read-only.

## Done when
- [ ] A finding, with its source, on whether main-session tokens can be read here
- [ ] If yes: the ledger records them (format in engine/schema/usage.md) and the page counts them; if no: the reason is recorded and the page wording says so

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
