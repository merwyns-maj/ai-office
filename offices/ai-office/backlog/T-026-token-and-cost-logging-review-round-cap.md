---
id: T-026
title: "Token and cost logging, review-round cap"
phase: 6-office
status: todo
priority: P1
owner: pmo
where: office
project: ai-office
depends_on: [T-024]
pr: null
---

## Done when
- [ ] Cost per run and per agent visible
- [ ] Cap enforced from office.yaml

## Spec

**Note from T-056 (26 Nov 2026): emit the event log v1 format.** Cost logging writes per-step `usage` events as documented in `engine/schema/events.md` ("v1: model and usage"), with header `usage_source: recorded`: `provider`, `model`, `billing` (`plan` or `per_token`), `input` (uncached tokens), `output`, `cache_read`, `cache_write`, and `cost_usd` only for `per_token` steps (a `plan` step with a cost is a parse error). Also put `provider` and `model` on each `step_started`. Normalise each provider's token fields to those meanings and check the field names against that provider's API docs (providers differ on whether cached tokens count inside input). The 3D page estimates cost from `offices/<office>/providers.yaml` (prices are null until someone fills them with a source and date), so reconcile `cost_usd` (for budgets) with the config estimate (for the page). Add the model ids the office really runs to `providers.yaml`.

## Design

## Build notes

## Review log

## Decision

## Open questions
