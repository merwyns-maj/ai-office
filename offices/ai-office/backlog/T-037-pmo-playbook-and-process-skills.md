---
id: T-037
title: "PMO playbook and process skills (pr-workflow, handoff, RAID log)"
phase: 0-office
status: review
priority: P0
owner: reviewer
where: code
project: ai-office
depends_on: [T-036]
pr: null
---

> Requested by Merwyn 25 Nov 2026: teach the PMO from real PMO practice; add the two process skills before Sprint 1.

## Done when
- [ ] skills/pmo-playbook/SKILL.md covers sprint planning, WIP limits and flow metrics, RAID log, RAG status, escalation, and lists its sources
- [ ] Playbook is written in our own words (no copied passages from sources)
- [ ] skills/pr-workflow/SKILL.md documents branch, commit, push, REST PR creation, waiting for mergeable, squash merge
- [ ] skills/handoff/SKILL.md documents the end-of-step checklist
- [ ] offices/ai-office/raid.md exists with current open items
- [ ] Every agent's office_skills includes handoff; engineer, pmo and curator include pr-workflow; pmo includes pmo-playbook; build_agents.py succeeds

## Spec
As above.

## Design
- Sources: PMI, CIO, Atlassian, Scrum.org, Zoho, APM, Project Management Compass (links in the skill).

## Build notes
- status-report now starts with RAG for scope / schedule / budget.

## Review log

## Decision

## Open questions
- If Merwyn has a PMO ebook he owns, attach it and April can distil it into the playbook.
