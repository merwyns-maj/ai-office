---
id: T-066
title: "Chat as a docked section below the office; the office resizes"
phase: 6-office
status: spec
priority: P1
owner: pm
where: code
project: ai-office
depends_on: [T-065]
pr: null
---

> Merwyn, 26 Nov 2026 17:48 WIB: "for chat, i prefer a dedicated section (not in the front) when chat expanded (horizontal below) it will resize the office"

## Facts (Janice)
- Today (T-063) the chat is a floating panel over the 3D office (`#chat`, class `panel pp`, bottom right on desktop; a full-height sheet under 900 px). It is one of the movable panels of T-059 (`PANEL.IDS` has `chat`, layout saved in `office.layout.v1`).
- The Chat button in the bottom bar opens and closes it (`openChat`/`closeChat`; the open state is saved in `office.chat.v1`).
- The published page is the one "AI Office" artifact, built with `office_app.py ai-office --ledger <session ledger> --chat` (T-065).

## Done when
- [ ] Opening chat shows it as a full-width section below the office, not over it; the 3D view shrinks to the space left above it, and no panel or office content sits under the chat
- [ ] Closing chat gives the office its full height back
- [ ] Works on desktop and phone widths; keyboard, focus and screen-reader behaviour from T-063 stay
- [ ] Chat features from T-063 are unchanged (mentions, statuses, needs-you, scan, notice, Clear chat)

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
