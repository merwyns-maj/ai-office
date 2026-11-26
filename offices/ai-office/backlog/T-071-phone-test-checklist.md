---
id: T-071
title: "A 2-minute phone checklist Merwyn runs after each UI change"
phase: 6-office
status: build
priority: P2
owner: reviewer
where: repo
project: ai-office
depends_on: []
pr: PRN
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- T-066 and T-067 were tested in headless Chrome only; the phone keyboard and touch were simulated, never on a real device.

## Done when
- [ ] A short checklist (under 12 steps, about 2 minutes) for the AI Office artifact on a phone: open, chat open and close, resize by touch, type with the keyboard up, panels never overlap, usage reads
- [ ] The pmo-playbook says when Janice asks Merwyn to run it (after a merged UI change is published) and where his result is recorded (the task's Review log, as Merwyn's note)

## Spec
**Problem.** UI changes to the AI Office artifact are tested only in headless Chrome; the phone keyboard and touch were simulated (T-066 notes: fake `visualViewport`, no real touch device). Merwyn needs a short way to check the real thing on his phone.

**In scope**
- A checklist file in this repo (location chosen by the Architect), under 12 steps, about 2 minutes, for the published AI Office artifact on a phone. Each step is an action and an expected result Merwyn can answer pass or fail.
- Steps cover: open the page; usage and the office read correctly; open and close chat; resize chat by touch (handle); type in the composer with the keyboard up (composer visible, office strip returns when it closes); panels never overlap each other or sit under the chat or bar; usage reads.
- A pmo-playbook addition: Janice asks Merwyn to run it after a merged UI change is published; Merwyn's result is recorded in that task's Review log as his note (pass, or which step failed).

**Out of scope**
- Automating phone tests or buying a device farm (paid resource, a human gate).
- New UI features, and desktop checks (headless Chrome covers those).
- Changing the Reviewer's checks; the phone result does not replace a Reviewer PASS.

**Done when (reviewer can verify)**
1. The checklist has fewer than 12 numbered steps, each with an expected result, and names every area in In scope.
2. A reader can run it in about 2 minutes: the Reviewer times it once against the published page, or notes that this was not possible.
3. The pmo-playbook states when Janice asks (after a merged UI change is published), who runs it (Merwyn), and where the result goes (the task's Review log, as Merwyn's note).
4. Steps for chat height and keyboard match T-066 behaviour (handle at chat top, panels stay inside the office area); no step relies on a feature that does not exist.
5. All tests and `python -m engine.runtime validate ai-office` pass; no other file changes.


**Spec approved** (Janice, 26 Nov 2026 20:05 WIB).

## Design
**Approach.** New skill file `offices/ai-office/skills/phone-check/SKILL.md` (repo convention: procedures live in skills; there is no docs folder). Not added to any agent profile, so no `agents/` or `build_agents.py` change. Janice reads it and pastes the steps to Merwyn. Plus one pmo-playbook paragraph. No other file changes.

**Checklist** (frontmatter `name: phone-check`, `description: 2-minute phone check Merwyn runs on the published AI Office page after a merged UI change`; then steps, each "Do / Expect", answer pass or fail):
1. Open the published AI Office page on your phone. Expect: office view, top strip with agents, bar at the bottom, no error text, within about 5 s.
2. Look at the office. Expect: agents at their desks with names; nothing cut off at the sides.
3. Read the usage panel. Expect: session total and agent rows with numbers, budget word or "budget not set", main-session row text.
4. Tap Chat in the bar. Expect: chat opens below the bar, full width; the office shrinks above it and is still visible.
5. Drag the handle at the chat's top edge up, then down. Expect: chat follows your finger; the office re-fits without stretching; it stops at a minimum (header, 2 lines, composer) and leaves an office strip at the top.
6. With chat tall, look at the usage and latest-events panels. Expect: both inside the office area, not under the chat or bar, not on top of each other.
7. Tap the composer and type a few letters (do not send). Expect: keyboard up, composer and your text visible above it.
8. Delete the letters and close the keyboard. Expect: the office strip comes back; chat at the height you left it.
9. Close chat. Expect: chat gone, office full height, panels where they were.
10. Read usage once more. Expect: same numbers as step 3.
Reply: "phone check pass", or "fail step N: what you saw", plus phone and browser.

**pmo-playbook** (§9 "Publish", 3 lines): after a merged UI change is published, Janice asks Merwyn to run `skills/phone-check` and name his phone and browser. She records his reply in that task's Review log as `Merwyn (human), phone check <date WIB>, <phone/browser>: PASS | FAIL step N: <his words>`. It does not replace Reviewer PASS.

**Open questions answered (office).** A FAIL does not reopen the done task: the PMO opens a new task at `todo` quoting the failed step and linking the original (history stays intact). Merge-rule fact: a Review log line is not planning-only, so it goes into the next `t-xxx` PR Janice opens (the follow-up task's PR on a FAIL), where the Reviewer checks it is Merwyn's words. Still for Merwyn: which phone and browser; steps are written browser-neutral.

**Tests.** No code. Reviewer checks: 10 steps (< 12), each with Expect; areas in scope all named; steps 5 to 8 match T-066 (handle at chat top, panels clamped to the stage, keyboard collapses the office strip); `validate` and the test suite pass (the new skill folder must not upset `validate`: an unreferenced office skill is allowed today).

**Risks.** Step wording drifts from the page after later UI tasks: any UI task's Design names checklist steps it changes. Not flagged for Compliance (step 7 never sends, so no chat data is created).

**Decision record draft.** Decision: phone checklist is an unreferenced office skill. Options: doc folder (new convention); agent-referenced skill (profile and build changes); unreferenced skill (chosen).
— Fang (architect)

## Build notes
**What changed.** New `offices/ai-office/skills/phone-check/SKILL.md`: 10 Do/Expect steps exactly as in the Design, plus the reply format. New "Phone check (T-071)" paragraph in `skills/pmo-playbook/SKILL.md` after the Publish paragraph: when (after a merged UI change is published), who (Merwyn), where (task Review log, Merwyn's note format), not a Reviewer PASS replacement, FAIL opens a new task, Review log line rides the next t-xxx PR. No code, no test, no agent profile change (unreferenced skill, per Design).
**Deviation.** The Design says "§9 Publish, 3 lines"; the playbook has no numbered section, so I added a separate paragraph right after the Publish paragraph. It is longer than 3 lines because it also carries the answered FAIL handling from the Design.
**Rides along.** T-024's task file (Spec, Design, Compliance sections, planning only for that task) is on this branch; not edited by me. Reviewer: ignore it for T-071.
**How to verify.**
- `python -m unittest discover -s tests`: Ran 411 tests, OK, exit 0.
- `python -m engine.runtime validate ai-office`: OK, 8 agents, 5 stages, 71 tasks, 19 skills.
- `python scripts/board.py ai-office`: no Problems; board.md discarded.
- Read the skill: 10 numbered steps (< 12), each with Expect; steps 5 to 8 are behaviour-level (handle at chat top, panels inside the office area, keyboard returns the office strip).
- Not done: timing the run on a real phone (Reviewer may note not possible).
— Sebastian (engineer)

## Review log

## Decision

## Open questions
- Which phone and browser does Merwyn use (iOS Safari, Android Chrome, the Claude app)? Unknown; steps may differ. For Merwyn.
- Should failures from the checklist reopen the task or open a new one? For the office (PMO decides).
