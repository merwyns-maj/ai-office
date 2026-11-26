---
id: T-067
title: "Chat: composer warning overlaps the thread at minimum height; page-size headroom"
phase: 6-office
status: todo
priority: P2
owner: pmo
where: code
project: ai-office
depends_on: [T-066]
pr: null
---

> From Cahyani's T-066 Review 2 (26 Nov 2026): at minimum chat height, when a composer warning shows (offline, blocked send), the thread runs under the composer; on a phone about 4 px of thread shows and the last message shows through the "Not sent" warning. The warning stays readable and the send stays blocked.

## Facts (Janice)
- The committed `office.html` is 221,168 B of the 221,184 B (216 KB) limit after T-066: 16 B of headroom. Any page change needs trimming or an Architect decision on the limit.

## Done when
- [ ] With a composer warning shown at minimum height, the thread area is clipped above the composer (or the minimum re-measured) on 1280x800 and 390x844; nothing shows through the warning
- [ ] A size decision by the Architect is recorded (trim, raise the limit with a reason, or split the page), and the page fits it

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
