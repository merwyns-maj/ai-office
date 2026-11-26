---
id: T-056
title: "Show which model each agent uses, and usage, in the 3D office (multi-provider)"
phase: 6-office
status: todo
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-048]
pr: null
---

> Merwyn, 26 Nov 2026 10:35: "in the 3d AI office, can we also track which model is currently being used, the usage as well. Let's say if i have multiple LLM (Claude SDK, Anthropic API, ChatGPT, Deepseek, etc.)". Prototype slice on the recorded log; real numbers arrive with the runtime (T-024) and cost logging (T-026).

## Done when
- [ ] Event log v1 (documented, v0 logs still load) carries, per agent step, a provider (e.g. claude-sdk, anthropic-api, openai, deepseek), a model id, and usage (input, output and cached tokens; cost where the provider prices per token; "plan" where it runs on a subscription)
- [ ] The 3D office shows at a glance which model each agent is on (avatar badge or desk label, colour plus text) and a usage panel: per agent, per provider and total, for the replay so far
- [ ] Providers and prices live in office config (not hard-coded), with a dated source note; unknown provider or model still renders
- [ ] A fixture exercises at least three providers; its usage numbers are marked synthetic in the log header and on screen
- [ ] Tests for the parser, totals and the pricing config; T-026 updated to emit this format

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
