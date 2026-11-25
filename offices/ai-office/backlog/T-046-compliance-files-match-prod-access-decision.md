---
id: T-046
title: "Compliance files match the 25 Nov prod access decision"
phase: 0-office
status: todo
priority: P0
owner: pmo
where: code
project: ai-office
depends_on: [T-043]
pr: null
---

> From Fang's incidental finding and Wulan's note 4 on T-043. Must be done before T-019 (guard install) and before any task is reviewed against these checklists.

## Done when
- [ ] base/agents/compliance.md, offices/ai-office/skills/compliance-playbook/SKILL.md and offices/ai-office/skills/uu-pdp-checklist/SKILL.md no longer name "Bytebase change issues" as the approved write path
- [ ] They state: prod writes only on Merwyn's instruction (guard asks, he confirms); agents never submit to Bytebase; read access approved by Merwyn 25 Nov (R-14); read-only DB role (R-8) is the real control
- [ ] python scripts/build_agents.py ai-office exits 0 and the regenerated compliance agent carries the new wording

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
