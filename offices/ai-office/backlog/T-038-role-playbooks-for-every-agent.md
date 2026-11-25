---
id: T-038
title: "Role playbooks for every agent"
phase: 0-office
status: review
priority: P0
owner: reviewer
where: code
project: ai-office
depends_on: [T-037]
pr: null
---

> Requested by Merwyn 25 Nov 2026: prepare proper skills for each team member before Sprint 1.

## Done when
- [ ] A playbook skill exists for PM, Architect, Engineer, Reviewer, Compliance and Curator, each grounded in named sources with URLs and written in our own words
- [ ] Each agent lists its playbook first in office_skills; build_agents.py succeeds
- [ ] Compliance playbook states it is not legal advice and routes legal questions to KlikA2C legal via Merwyn
- [ ] pr-workflow merge check waits for the PR head to match the local HEAD (lesson from T-037)

## Spec
As above.

## Design
- Sources: Atlassian, Nulab, ClickUp, Lucid (PM); Fowler, AWS, Red Hat, ADR tips (Architect); DORA, Microsoft, Zalando, Swarmia (Engineer); Google eng-practices (Reviewer); Chambers, PwC, Norton Rose, CMS, Linklaters (Compliance); AWS Well-Architected, O'Reilly, Thoughtworks (Curator).

## Build notes

## Review log

## Decision

## Open questions
