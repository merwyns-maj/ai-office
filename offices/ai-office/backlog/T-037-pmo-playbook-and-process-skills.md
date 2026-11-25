---
id: T-037
title: "PMO playbook and process skills (pr-workflow, handoff, RAID log)"
phase: 0-office
status: done
priority: P0
owner: curator
where: code
project: ai-office
depends_on: [T-036]
pr: 6
---

> Requested by Merwyn 25 Nov 2026: teach the PMO from real PMO practice; add the two process skills before Sprint 1.

## Done when
- [x] skills/pmo-playbook/SKILL.md covers sprint planning, WIP limits and flow metrics, RAID log, RAG status, escalation, and lists its sources
- [x] Playbook is written in our own words (no copied passages from sources)
- [x] skills/pr-workflow/SKILL.md documents branch, commit, push, REST PR creation, waiting for mergeable, squash merge
- [x] skills/handoff/SKILL.md documents the end-of-step checklist
- [x] offices/ai-office/raid.md exists with current open items
- [x] Every agent's office_skills includes handoff; engineer, pmo and curator include pr-workflow; pmo includes pmo-playbook; build_agents.py succeeds

## Spec
As above.

## Design
- Sources: PMI, CIO, Atlassian, Scrum.org, Zoho, APM, Project Management Compass (links in the skill).

## Build notes
- status-report now starts with RAG for scope / schedule / budget.

## Review log
- PASS — playbook covers all areas with sources, own words; pr-workflow matches how the repo runs (loop passes bash -n); handoff and raid.md in place; build ok; no secrets. — Cahyani (reviewer)
- Notes fixed before merge: wait loop now stops if never mergeable; session URL made a placeholder; pr field set. — Janice (pmo)

## Decision
- Janice runs the office from pmo-playbook (WIP limits, flow metrics, RAID, RAG with decision requests). Every agent ends its step with the handoff skill. — April (curator)

## Open questions
- If Merwyn has a PMO ebook he owns, attach it and April can distil it into the playbook.
