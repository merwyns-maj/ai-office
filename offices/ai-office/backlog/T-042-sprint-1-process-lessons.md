---
id: T-042
title: "Sprint 1 process lessons: tool check, board.md rule, handoff for read-only agents"
phase: 7-ways-of-working
status: spec
priority: P1
owner: pm
where: code
project: ai-office
depends_on: []
pr: null
---

> Opened by Janice at Sprint 1 close (see sprints/sprint-01.md, Retro). Three lessons, one task.

## Done when
- [ ] pm-playbook (and spec-writing if needed) tells the PM to check at the start that it can read and search the backlog; if it cannot, stop and ask the PMO for the parent task text instead of writing the spec blind
- [ ] pr-workflow states one rule for the generated board.md (task branches do not commit it; PMO regenerates on main after merge, or a merge driver is added and tested) and scripts or CI do not contradict it
- [ ] handoff skill says read-only agents return paste-ready text (section body, signature, proposed status and owner) and the PMO records it in the task file; build_agents.py run so agent files match
- [ ] A reviewer can find each rule in one skill file; no skill contradicts another

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
- Which board.md option: (a) not committed on task branches, (b) merge driver. Spec should recommend one.
