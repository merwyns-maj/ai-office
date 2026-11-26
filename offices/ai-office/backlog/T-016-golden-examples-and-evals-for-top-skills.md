---
id: T-016
title: "Golden examples and evals for top skills (SLIK, recon, PRD)"
phase: 3-skills
status: todo
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: []
pr: null
---

## Done when
- [ ] 3-5 cases each
- [ ] skill-creator eval passes

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions

## Note (T-049, 26 Nov 2026)
Method proven on the office's own skills: golden cases are JSON in `<skill>/golden/`, checked by `python scripts/golden.py <office>`; see the "Golden examples" section of the root README. Still needed here: the company skills (SLIK, recon, PRD) live in the company repo behind T-002, so their cases cannot be written until that is reachable; they must hold invented examples only. The Done when above is unchanged.
