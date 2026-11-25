---
id: T-035
title: "Agent names, personas and skills"
phase: 0-office
status: review
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-001]
pr: null
---

> Requested by Merwyn 25 Nov 2026

## Done when
- [ ] Each of the 7 agents in offices/ai-office/agents/ has display_name, personality, role_title and office_skills
- [ ] Every skill named in office_skills exists at offices/ai-office/skills/<name>/SKILL.md, and build_agents.py exits with an error if one is missing
- [ ] Generated .claude/agents/*.md carry the name in the description and a Skills section listing the SKILL.md paths
- [ ] org.yaml and theme.yaml show the agent names
- [ ] engine/schema/office.md documents the persona keys

## Spec
As above (requested directly by Merwyn).

## Design
- Persona keys are flat frontmatter keys in the office agent file (the stdlib parser reads key: value only).
- build_agents.py prefixes the description with "Name (Role)." and appends a Skills section; it validates skill paths.
- Names: Sari (PMO, ESTJ), Ayu (PM, ENFJ), Bima (Architect, INTJ), Raka (Engineer, ISTP), Laras (Reviewer, INTP), Hendra (Compliance, ISTJ), Nadia (Curator, INFJ).

## Build notes
- Skills added: status-report, spec-writing, decision-record, build-conventions, review-checklist, uu-pdp-checklist.
- Verify: python scripts/build_agents.py ai-office; inspect .claude/agents/pm.md.

## Review log

## Decision

## Open questions
