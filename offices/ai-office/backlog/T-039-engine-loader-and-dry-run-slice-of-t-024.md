---
id: T-039
title: "Engine loader and dry-run (repo-only slice of T-024)"
phase: 6-office
status: spec
priority: P1
owner: pm
where: code
project: ai-office
depends_on: [T-001]
pr: null
---

> Slice of T-024. Covers load, validate and dry-run only. Live agent runs on the Agent SDK (which spend SDK credit) stay in T-024.

## Done when
- [ ] `engine/` loads offices/ai-office (office, org, workflow, agents, backlog) and fails with a clear message on schema errors
- [ ] A dry-run picks the next task and prints the stage, owner, agent profile and skills it would run, with no SDK call
- [ ] Tests run against offices/ai-office with no network and no credentials

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
- Which language and layout for the engine (Python beside scripts/ or TypeScript)? Owner: Fang (architect).
