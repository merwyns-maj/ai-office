---
id: T-036
title: "Rename agents and adopt external skills"
phase: 0-office
status: review
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-035]
pr: null
---

> Requested by Merwyn 25 Nov 2026

## Done when
- [ ] Agents renamed everywhere (agents, org.yaml, theme.yaml, schema): Janice PMO, Emmy PM, Fang Architect, Sebastian Engineer, Cahyani Reviewer, Wulan Compliance, April Curator
- [ ] Agents can list external_skills as source:name; build_agents.py fails on a source not under skill_sources in workspaces.yaml
- [ ] Generated agents show an "External skills" section where set
- [ ] klik-workspace skills recorded as a pointer only (no company skill content copied)
- [ ] T-002 reopened with the reason

## Spec
As above (requested directly by Merwyn).

## Design
- external_skills mapped: Emmy skill-creator; Fang diagram-design; Sebastian frontend-design, dataviz, skill-creator; Cahyani accessibility-review, validate-data; April skill-creator.
- klik-workspace skills (prd-writer, backlog-writer, release-notes) stay in the company repo and are for company offices; not attached to the build office.

## Build notes
- Verify: python3 scripts/build_agents.py ai-office; grep old names; inspect .claude/agents/engineer.md.

## Review log

## Decision

## Open questions
- Reading klik-workspace's skill list needs T-002 (org app install) or the laptop link.
