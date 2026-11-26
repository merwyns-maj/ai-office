---
id: T-027
title: "Office visualization renderer (reads theme/)"
phase: 6-office
status: todo
priority: P2
owner: pmo
where: code
project: ai-office
depends_on: [T-024]
pr: null
---

> PixiJS or Phaser, Tauri wrapper

## Done when
- [ ] Agents animate from runtime events
- [ ] Two offices render with different themes

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
- 2026-11-26 (Janice, Sprint 4 close): carried from T-048 on Merwyn's decision: the event data rule checks string values only; it must also scan key names and numbers (or the whole rendered data blob before writing) and never echo a hit key. Also: phone numbers with separators, phone layout under 600px. First slice: engine/app/ (T-048).
