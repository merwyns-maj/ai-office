---
id: T-068
title: "Lean path for small changes (one design step, then build and review)"
phase: 0-office
status: spec
priority: P1
owner: pm
where: repo
project: ai-office
depends_on: []
pr: null
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- T-066 (docked chat) took 7 agent runs and about 520k tokens: Emmy spec, Dinda UX, Fang design, Sebastian build, Cahyani review, Sebastian rework, Cahyani review 2.
- Stages and gates live in `offices/ai-office/workflow.yaml`; procedures in the pmo-playbook and pm-playbook skills.

## Done when
- [ ] workflow.yaml and the playbooks define a lean path with an entry rule a PMO can apply (for example: one surface, no new data, no compliance flag, no human gate), and what it skips (for example: a separate spec run; the Architect writes a short spec plus design)
- [ ] Review stays required (Reviewer PASS before merge); compliance flags and human gates still force the full path
- [ ] `python -m engine.runtime validate ai-office` accepts the new workflow; tests cover the rule

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
