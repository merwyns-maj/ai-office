---
id: T-038
title: "Role playbooks for every agent"
phase: 0-office
status: done
priority: P0
owner: curator
where: code
project: ai-office
depends_on: [T-037]
pr: 7
---

> Requested by Merwyn 25 Nov 2026: prepare proper skills for each team member before Sprint 1.

## Done when
- [x] A playbook skill exists for PM, Architect, Engineer, Reviewer, Compliance and Curator, each grounded in named sources with URLs and written in our own words
- [x] Each agent lists its playbook first in office_skills; build_agents.py succeeds
- [x] Compliance playbook states it is not legal advice and routes legal questions to KlikA2C legal via Merwyn
- [x] pr-workflow merge check waits for the PR head to match the local HEAD (lesson from T-037)

## Spec
As above.

## Design
- Sources: Atlassian, Nulab, ClickUp, Lucid (PM); Fowler, AWS, Red Hat, ADR tips (Architect); DORA, Microsoft, Zalando, Swarmia (Engineer); Google eng-practices (Reviewer); Chambers, PwC, Norton Rose, CMS, Linklaters (Compliance); AWS Well-Architected, O'Reilly, Thoughtworks (Curator).

## Build notes
- Six playbooks added under skills/*-playbook; each agent lists its playbook first. pr-workflow merge check now matches PR head to local HEAD.

## Review log
- PASS — six playbooks with sources, own words; compliance disclaimer and routing present; build ok, generated agents list playbooks first; wait loop passes bash -n and rejects a stale head; no secrets. — Cahyani (reviewer)
- Fixed before merge: compliance wording softened (DPIA/DPO 'can trigger, depending on scale and risk'), transition to Oct 2024 added; pr field and Build notes filled. — Janice (pmo)

## Decision
- Every agent has a researched playbook as its first skill; role skills stay short and point to it. Lessons from sprints become edits to these playbooks. — April (curator)

## Open questions
