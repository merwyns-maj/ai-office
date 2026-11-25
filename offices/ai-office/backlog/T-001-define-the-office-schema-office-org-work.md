---
id: T-001
title: "Define the office schema (office, org, workflow, agents, theme, backlog)"
phase: 0-office
status: done
priority: P0
owner: curator
where: code
project: ai-office
depends_on: []
pr: null
---

> Approved by Merwyn 25 Nov 2026

## Done when
- [x] engine/schema/office.md covers every file an office needs
- [x] offices/ai-office/ validates against it by hand
- [x] Open questions in the schema answered

## Spec

## Design

## Build notes

## Review log
- 25 Nov 2026: Merwyn reviewed and approved the schema and both proposed answers. scripts/build_agents.py and scripts/board.py run cleanly on offices/ai-office. PASS.

## Decision
- Office schema v0 accepted (engine/schema/office.md).
- Skills use skills/<name>/SKILL.md.
- One task, one office; cross-office links via depends_on: <office-id>/T-xxx.

## Open questions
