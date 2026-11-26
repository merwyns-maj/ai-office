---
id: T-065
title: "One office artifact: the real usage ledger and the chat on one page"
phase: 6-office
status: spec
priority: P1
owner: pm
where: code
project: ai-office
depends_on: [T-063]
pr: null
---

> Merwyn, 26 Nov 2026 17:14 WIB: "I don't see the chat", then "Keep only 1 artifact, clean up. Have only 1 SSOT".

## Facts (Janice)
- Today there are two artifacts. "AI Office" (5f1bb811-1633-4bfb-8285-9bcb2408dec2) is built with `scripts/office_app.py ai-office --chat`. It replays the synthetic fixture and has the chat with its db (owner-only rule on `chat`). "AI Office token usage" (fdb54f4f-d1f4-4f23-b1d4-2e67b9b0296a) is built with `--ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`. It replays the real ledger and has no chat.
- `office_app.py` refuses `--chat` with `--ledger` (T-063 design: "the recorded usage page never has chat").
- Keep the "AI Office" artifact: its db already holds the chat rules and the `chat/office` meta doc. Deleting "AI Office token usage" is done by Janice after the merge, with Merwyn confirming the delete.

- Merwyn, 26 Nov 2026 17:20 WIB, at 5,201,744 tokens used (104% of 5M): "Raise budget to 8M". `budgets.yaml` claude-code `tokens: 8000000`, `set_by: Merwyn`. Three tests in `tests/test_budgets.py` pin the shipped 5,000,000 and the 76% start, so this change rides with this task's build (not a planning PR).

## Done when
- [ ] `budgets.yaml` claude-code is 8,000,000 set by Merwyn; tests no longer pin the shipped budget value (they check the file is valid and dated, and use their own numbers for maths)
- [ ] One build gives the page that replays the real ledger (usage panel, Summary and Detail, budgets and colours as on the token usage page today) and has the chat, as on the AI Office page today
- [ ] The README and the pmo-playbook say which single command builds the published page, and which artifact it goes to
- [ ] Tests cover the combined build; the existing synthetic and ledger builds still pass
- [ ] After merge: "AI Office" is republished from the combined build, and "AI Office token usage" is deleted once Merwyn confirms

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
