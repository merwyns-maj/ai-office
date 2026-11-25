---
id: T-036
title: "Rename agents and adopt external skills"
phase: 0-office
status: done
priority: P1
owner: curator
where: code
project: ai-office
depends_on: [T-035]
pr: 5
---

> Requested by Merwyn 25 Nov 2026

## Done when
- [x] Agents renamed everywhere (agents, org.yaml, theme.yaml, schema): Janice PMO, Emmy PM, Fang Architect, Sebastian Engineer, Cahyani Reviewer, Wulan Compliance, April Curator
- [x] Agents can list external_skills as source:name; build_agents.py fails on a source not under skill_sources in workspaces.yaml
- [x] Generated agents show an "External skills" section where set
- [x] klik-workspace skills recorded as a pointer only (no company skill content copied)
- [x] T-002 reopened with the reason

## Spec
As above (requested directly by Merwyn).

## Design
- external_skills mapped: Emmy skill-creator; Fang diagram-design; Sebastian frontend-design, dataviz, skill-creator; Cahyani accessibility-review, validate-data; April skill-creator.
- klik-workspace skills (prd-writer, backlog-writer, release-notes) stay in the company repo and are for company offices; not attached to the build office.

## Build notes
- Verify: python3 scripts/build_agents.py ai-office; grep old names; inspect .claude/agents/engineer.md.

## Review log
- PASS — build ok, no old names left, unknown skill source fails the build (exit 1), External skills sections match the design, klik-workspace kept as a pointer only, T-002 reopened with reason. Note: skill_sources parsing is text-based; move to a YAML parser when the engine lands. — Cahyani (reviewer)

## Decision
- Agent names set by Merwyn. Skills outside the repo are referenced as source:name, never copied; company skills attach only to company offices. — April (curator)

## Open questions
- Reading klik-workspace's skill list needs T-002 (org app install) or the laptop link.
