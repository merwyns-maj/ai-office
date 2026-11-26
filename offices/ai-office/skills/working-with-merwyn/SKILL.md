---
name: working-with-merwyn
description: How the PMO and Curator read Merwyn's replies, offer him choices and record his decisions. Use before asking Merwyn anything and when recording his answer.
---
# Working with Merwyn
Status: proposed by April, 26 Nov 2026; approved by Merwyn (date and time filled in at approval).
Patterns that held up in at least two separate events in this repo. One-off sightings live in T-041's Decision ("watching").

## Patterns
- **W1 Offer numbered options with a recommendation.** Give context in a line, then 2 or 3 lettered or numbered options with cost and risk, and say which you recommend. He answers by picking.
  Evidence: `offices/ai-office/backlog/T-040-prod-guard-hook-script-and-tests-slice-of.md` § Review log, Escalated to Merwyn; `offices/ai-office/backlog/T-048-3d-animated-office-prototype.md` § Review log, Janice (pmo), 26 Nov; `offices/ai-office/backlog/T-001-define-the-office-schema-office-org-work.md` § Review log, 25 Nov 2026
- **W2 Read a short reply as the option it answers.** See the table below. Never stretch it to cover things the options did not say.
  Evidence: see the table.
- **W3 Record his decision with its date and time, where the work lives.** Put it in the task's Decision or Review log, and in the sprint's "Decisions recorded" when it spans tasks. Name who recorded it.
  Evidence: `offices/ai-office/backlog/T-040-prod-guard-hook-script-and-tests-slice-of.md` § Review log, 25 Nov 2026 21:47; `offices/ai-office/sprints/sprint-03.md` § Decisions recorded (Merwyn, 25 Nov 2026 22:44); `offices/ai-office/backlog/T-048-3d-animated-office-prototype.md` § Decision, 26 Nov 2026 09:01
- **W4 Stop and ask at the gate, with a recommendation.** A compliance BLOCK and a second Reviewer REJECT go to him, not around him. The rules are in workflow.yaml; this is about how to ask.
  Evidence: `offices/ai-office/sprints/sprint-01.md` § Retro (closed 25 Nov 2026), What got stuck: T-040; `offices/ai-office/backlog/T-048-3d-animated-office-prototype.md` § Review log, Janice (pmo), 26 Nov
- **W6 When he says go or accept as is, comply and record the leftover.** Do it, write it down, and move any gap to a named task. This never reaches past `human_gates` or a safety rule.
  Evidence: `offices/ai-office/sprints/sprint-04.md` § Decisions recorded (Merwyn, 25 Nov 2026); `offices/ai-office/backlog/T-048-3d-animated-office-prototype.md` § Decision, 26 Nov 2026 09:01; `offices/ai-office/research/T-012-chat-mining.md` § D. How we work together, D3

## Terse replies
| Reply seen | What it answered | Mapped to | Evidence |
|---|---|---|---|
| "accepted" (recorded as accepting all fixes) | A recommendation with options | The recommended option, in full | `offices/ai-office/backlog/T-040-prod-guard-hook-script-and-tests-slice-of.md` § Review log, 25 Nov 2026 21:47; `offices/ai-office/research/T-012-chat-mining.md` § D. How we work together, D1 |
| "Proceed ahead without waiting" and "Yes please proceed" | The plan for a sprint | Run the plan as written and stop only at `human_gates` | `offices/ai-office/sprints/sprint-04.md` § Decisions recorded (Merwyn, 25 Nov 2026); `offices/ai-office/sprints/sprint-05.md` § Decisions recorded (Merwyn, 26 Nov 2026) |
If a reply maps to no option or to more than one, ask again with the numbered options. Do not guess.

## Points elsewhere (not restated)
- Financial terms in English: partner-writing B2.
- Never untrue: partner-writing B5 and `offices/ai-office/research/T-012-chat-mining.md` § D. How we work together, D4.
- When to escalate: `offices/ai-office/workflow.yaml` `human_gates` and `escalation`.
