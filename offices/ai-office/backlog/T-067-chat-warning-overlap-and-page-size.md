---
id: T-067
title: "No overlapping parts: panels, chat and bar never cover each other; composer warning; page-size headroom"
phase: 6-office
status: spec
priority: P1
owner: pm
where: code
project: ai-office
depends_on: [T-066]
pr: null
---

> From Cahyani's T-066 Review 2 (26 Nov 2026): at minimum chat height, when a composer warning shows (offline, blocked send), the thread runs under the composer; on a phone about 4 px of thread shows and the last message shows through the "Not sent" warning. The warning stays readable and the send stays blocked.

> Merwyn, 26 Nov 2026 18:48 WIB: "if i expand chats, the usage and latest events are overlapped. Can you ensure each components can't overlapped (aside from the office)". At 18:50 he said go past 80% of the 8M budget for this.

## Facts (Janice)
- The committed `office.html` is 221,168 B of the 221,184 B (216 KB) limit after T-066: 16 B of headroom. Any page change needs trimming or an Architect decision on the limit.

## Done when
- [ ] With chat open at any height, and at any window size, the usage panel, latest events, the focus card, menus and sheets never overlap each other, the bar or the chat; only the 3D office may sit behind them. This holds for the default (flow) layout and for moved or resized panels (T-059)
- [ ] With a composer warning shown at minimum height, the thread area is clipped above the composer (or the minimum re-measured) on 1280x800 and 390x844; nothing shows through the warning
- [ ] A size decision by the Architect is recorded (trim, raise the limit with a reason, or split the page), and the page fits it

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
