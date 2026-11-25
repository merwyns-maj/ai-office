---
id: T-048
title: "3D animated office: design and three.js prototype (slice of T-027)"
phase: 6-office
status: todo
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-047]
pr: null
---

> Merwyn, 25 Nov 2026: "start designing my 3d animated office". A first slice of T-027 that does not wait on the SDK runtime (T-024): it plays a recorded event log instead of live events.

## Done when
- [ ] Dinda's design: scene layout (rooms = workflow stages from theme.yaml), avatar look per agent, animation for each event type, idle/active/needs-Merwyn states, camera, palette, reduced-motion behaviour
- [ ] An event log format v0 (documented) and a fixture that replays a real sprint from this repo's history, no company data
- [ ] engine/app/ holds a single self-contained three.js page that renders the office from theme.yaml data and animates the fixture: agents walk between rooms on handoff, show what they hold, and a "waiting for Merwyn" state is visible at a glance
- [ ] Runs from a static file server with no build step; works with reduced motion; holds a smooth frame rate with 8 agents on a laptop
- [ ] Tests cover the event-log parser or generator; all tests pass
- [ ] Merwyn can open it as an artifact

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
