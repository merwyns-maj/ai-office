---
id: T-019
title: "Prod-guard mod or hook"
phase: 4-code-tooling
status: todo
priority: P0
owner: pmo
where: code
project: ai-office
depends_on: []
pr: null
---

> Biggest risk reducer

## Done when
- [ ] Writes to nimbus-prod blocked outside Bytebase scripts

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions

## Merwyn decisions, 25 Nov 2026 (recorded by Janice)
- Prod reads allowed (read-only default); prod writes only on Merwyn's instruction; Bytebase never submitted by agents. Guard change: T-043 (Sprint 3). Installing in a company repo remains blocked on T-002 and a human gate. — Janice (pmo)
