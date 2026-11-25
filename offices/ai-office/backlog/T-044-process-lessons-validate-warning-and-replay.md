---
id: T-044
title: "Sprint 2 process lessons: validate warns on missing defaults, pr-workflow replay not rebase"
phase: 7-ways-of-working
status: spec
priority: P1
owner: pm
where: code
project: ai-office
depends_on: []
pr: null
---

> Opened by Janice at Sprint 2 close; carries RAID R-11 and R-12.

## Done when
- [ ] R-11: when `base/defaults.yaml` is missing, `build_agents.py` validate (and `board.py` if it validates) prints a warning that agents will get no base skills; a test or fixture shows the warning; with the file present there is no warning
- [ ] R-12: pr-workflow has a short rule: in a shallow clone, if `git rebase` reports add/add conflicts, do not resolve them; create a branch from fresh main and replay the branch's own commits (cherry-pick), then push; the "mergeable false" and "push rejected" lines point to it
- [ ] No skill contradicts another; `build_agents.py` runs clean

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
