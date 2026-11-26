---
id: T-069
title: "Usage numbers from the artifact db, so the page needs no republish per ledger append"
phase: 6-office
status: todo
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-067]
pr: null
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- Today the ledger totals are baked into the page at build time (`office_app.py --ledger ... --chat`), so every ledger append needs a rebuild and republish of "AI Office", and the page grows about 245 B per run (T-065 Design).
- The artifact already declares `db` with one owner-only rule on `chat` (T-063).

## Done when
- [ ] The page reads ledger runs and budgets from the artifact db (owner-only), and the office writes new runs there when it appends the ledger; the repo ledger stays the source of truth (one-way sync, re-runnable)
- [ ] A ledger append shows on the page without a republish; the page size no longer grows with runs
- [ ] Compliance check (new data in the db; no personal data, owner-only), and the C1-C8 chat rules unchanged

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
