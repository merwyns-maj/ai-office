---
name: uu-pdp-checklist
description: Data-protection and safety check for designs and PRs. Use when the Architect flags a task, or anything mentions prod, money, credentials or personal data.
---
# UU PDP and safety checklist

Block if any is true:
- Personal data (names, NIK, phone, email, address, bank account numbers) of borrowers, lenders or staff appears in the repo, a brain, logs or fixtures.
- Production rows or exports are copied anywhere; pointers to where they live are fine.
- Secrets, tokens or connection strings are committed.
- A write path to production exists that does not wait for Merwyn's instruction and confirmation (the guard asks, he confirms), or an agent submits to Bytebase itself (agents never submit; they hand the plan to Merwyn).
- Company content would land in a personal repo.

Write `Compliance: PASS` or `Compliance: BLOCK — <item> — <fix>` in the Review log. A BLOCK always goes to Merwyn.
