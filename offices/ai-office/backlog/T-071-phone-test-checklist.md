---
id: T-071
title: "A 2-minute phone checklist Merwyn runs after each UI change"
phase: 6-office
status: done
priority: P2
owner: pmo
where: repo
project: ai-office
depends_on: []
pr: 65
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

### Rework 1
Fixes for Review 1 (F1, F2 and notes).
- **F1.** Steps 3, 6, 10 rewritten for the phone as the template behaves: below 900px `#usage` and `#ticker` are hidden and latest events is the one-line `#tone` strip above the bar; below 600px usage opens from the gear (Settings), then Usage (`#msheet` to `#usheet`). Step 6 now checks the tone strip is readable and not under chat or bar. Step 9 mentions the strip, not panels.
- **F2.** "Not on top of each other" dropped. Step 6 and the pmo-playbook Phone check paragraph say T-067 adds a no-overlap step when it merges (follow-up for T-067's Design).
- **Notes.** Step 4 says chat (speech-bubble) button, no label on a phone. Step 2 says top strip shows initials; names are the 3D labels. Step 10 still equals step 3 until T-069 changes the usage source; T-069's Design should name this step. Still 10 steps, about 2 minutes (not timed on a real phone).
- **Verified.** Headless Chrome 390x844 screenshot of `office.html` (three.min.js copied under /tmp, not committed): initials strip, no usage or ticker panel, tone strip "Janice starts T-901" above the bar, chat icon with no label, gear. WebGL is unavailable headless, so the 3D labels were not seen; the screenshot says "3D view could not load".
- `python -m unittest discover -s tests`: Ran 411 tests, OK, exit 0. `python -m engine.runtime validate ai-office`: OK (8 agents, 5 stages, 71 tasks, 19 skills), exit 0.
— Sebastian (engineer)

### Rework 2
Merwyn decided on 26 Nov 2026 after review 2: "Fix and re-review". Fixed F3 with one line in phone-check SKILL.md: hold the phone upright (portrait); landscape is out of scope. Nothing else changed.

## Review log
**Review 1: REJECT** (26 Nov 2026). — Cahyani (reviewer)
Checked `git diff main...HEAD`, `skills/phone-check/SKILL.md`, the pmo-playbook paragraph, and `engine/app/office.template.html` (T-066 build), plus a headless Chrome screenshot of the committed `office.html` at 390x844.

| Done when | Result | Evidence |
|---|---|---|
| 1. Under 12 steps, each with Expect, every area named | pass | 10 numbered steps, each **Do/Expect**; open page, office, usage, chat open/close, handle, keyboard, panels, usage again all named |
| 2. About 2 minutes, timed once | not possible | no real phone here. Estimate: 10 short steps, about 2 min, plausible |
| 3. Playbook: when, who, where | pass | pmo-playbook "Phone check (T-071)": after a merged UI change is published; Merwyn; the task's Review log in a fixed note format. A FAIL opens a new `todo` task that quotes the step and links the original |
| 4. Matches T-066; no step relies on a missing feature | **fail** | see F1, F2 |
| 5. Tests and validate pass; no other file changes | pass | `python -m unittest discover -s tests`: "Ran 411 tests ... OK", exit 0. `python -m engine.runtime validate ai-office`: "ai-office: OK — 8 agents, 5 stages, 71 tasks, 19 skills", exit 0. T-071's own files are the skill, the playbook and this task. T-024 rides along, planning only |

**Fixes needed**
- F1 (steps 3, 6, 10 describe the desktop page, not the phone). At `max-width:899px` the template has `#usage{display:none}` and `#ticker{display:none}` (lines 272-273). On a phone, latest events is the one-line `#tone` strip above the bar. At under 600 px, usage opens only from the Settings gear: `#bar .opt{display:none}` hides `#ubtn`, and the gear's `#msheet` holds the "Usage" button that opens `#usheet` (line 1469). My 390x844 screenshot shows no usage panel and no events panel, only the tone strip, the bar and the gear. So step 3 ("read the usage panel") and step 10 cannot be done as written, and step 6 ("look at the usage and latest-events panels") has nothing to look at. Rewrite these for the phone: open Settings, then Usage, and expect the usage sheet's contents; for events, check the tone strip shows above the bar and is not under the chat.
- F2 (step 6 "not on top of each other" is T-067's rule). Panels never overlapping each other is T-067's Done when, and T-067 is still at `spec`. It comes from Merwyn's 18:48 report that the panels overlap when chat is expanded. T-066 only clamps panels to the stage. A step that expects it would fail on a known open issue and, under the new playbook rule, open a duplicate of T-067. Either drop the "each other" part until T-067 is merged (T-067's Design then adds it back), or mark it "after T-067".

**Notes (not reasons for rejection)**
- Step 4 says "tap Chat". At under 600 px the button shows only an icon (`#chatbtn .cl{display:none}`), so "tap the chat (speech-bubble) button" would be clearer.
- Step 2 "agents ... with names": at under 600 px the top strip shows initials (`.seg .nm` hidden). Check that the names the step means are the 3D labels.
- Step 10 "same numbers as step 3" holds today because the page is the ledger as of its build. T-069 (usage from the artifact db) may change that; T-069's Design should name this step.
- Build-notes deviation (a separate paragraph, not "§9 Publish, 3 lines") is fine: the playbook has no numbered sections.
- External skills design:accessibility-review and data:validate-data: not available in this session; not used.

**Review 2: REJECT (second rejection)** (26 Nov 2026). — Cahyani (reviewer)
Checked `git diff 1574988..HEAD` (4 files: T-071 task, T-024 task, `skills/phone-check/SKILL.md`, pmo-playbook), `engine/app/office.template.html`, and headless Chrome screenshots of the committed `office.html` at 390x844 (portrait) and 844x390 (landscape), three.min.js copied under /tmp, not committed. WebGL is unavailable headless, so the 3D labels were not seen.

Review 1 fixes:
- F1 fixed for portrait (under 600 px). Step 3/10: `#gear` is shown (line 304), `#bar .opt` hides `#ubtn` (line 302), the gear's `#msheet` gets a "Usage" button only when `HAS_MODELS` (line 1469), and it opens `#usheet` with an x (`#usx`, line 1374). So the "no Usage button means no usage data" note is right. Step 6: `#usage`/`#ticker` hidden below 900 px (lines 272-273); `#tone` sits at `bottom:var(--bb)` where `--bb` = bar + chat height (lines 15, 274), so it stays above the bar and chat. My 390x844 screenshot shows the initials strip, the tone strip "+00:00 Janice starts T-901" above the bar, the chat icon with no label, and the gear.
- F2 fixed. "Not on top of each other" is gone. Step 6 and the pmo-playbook "Phone check (T-071)" paragraph both say T-067 adds the no-overlap step when it merges. T-067 is still open and its Done when holds the rule.
- Notes from Review 1 handled: step 4 says speech-bubble with no label (line 409), step 2 says initials (line 297), and step 10 is handed to T-069's Design.

| Done when | Result | Evidence |
|---|---|---|
| 1. Under 12 steps, each with Expect, every area named | pass | 10 numbered **Do/Expect** steps covering open, office, usage, chat open/close, handle, keyboard, events strip, usage again. The no-overlap area is deferred to T-067 on purpose (F2) |
| 2. About 2 minutes | not possible | no real phone here. 10 short steps, about 2 min is plausible |
| 3. Playbook: when, who, where | pass | pmo-playbook line 85 |
| 4. Matches T-066; no step relies on a missing feature | **fail** | F3 below |
| 5. Tests, validate, no other file changes | pass | `python -m unittest discover -s tests`: "Ran 411 tests in 17.895s / OK", exit 0. `python -m engine.runtime validate ai-office`: "ai-office: OK — 8 agents, 5 stages, 71 tasks, 19 skills", exit 0. `board.py` exit 0, no Problems, board.md discarded. Other files are only the T-024 ride-along |

**Fix needed**
- F3 (the steps only hold in portrait; a phone held sideways falls in 600-899 px). In that band `#gear` is hidden (base `#gear{display:none}` at line 219; shown only at 900 px and up, line 250, and under 600 px, line 304). `#ubtn` "Usage" is in the bar (line 279), the chat button shows the "Chat" label (line 398; hidden only under 600 px, line 409), and the top strip shows full names (`.seg .nm` hidden only under 600 px, line 297). My 844x390 screenshot shows exactly this: names in the strip, then Motion, Follow, **Usage** and **Chat** in the bar, and no gear. So in landscape, steps 2, 3, 4 and 10 fail as written ("one initial per agent", "tap the gear", "no label"). Under the new playbook rule a false FAIL opens a needless task. The smallest fix is one line in the intro or step 1: "Hold the phone upright (portrait) for the whole check." Or else give the 600-899 variant for steps 2, 3, 4 and 10.

**Notes (not reasons for rejection)**
- This is the second REJECT, so per reviewer-playbook it goes through Janice. The fix is one line, so Janice may decide whether Merwyn needs to see it.
- T-024 ride-along (commit 4f342d6, PMO, planning only): fine. Frontmatter `status: parked` (a terminal status in workflow.yaml line 7), `owner: pmo`. The order note now matches Design line 70: the no-spend checks and the FakeProvider build need no gate, then Merwyn picks A/B/C, then gates 2-6 before any real run. Open questions gain the gate-4 item (push `t-xxx` branches to merwyns-maj/ai-office). That covers my Review 1 notes (a), (b) and (c).
- External skills design:accessibility-review and data:validate-data: not available in this session; not used.

**Review 3: PASS** (26 Nov 2026). — Cahyani (reviewer)
Merwyn decided after Review 2: "Fix and re-review". Checked `git diff HEAD~3 -- skills/phone-check/SKILL.md`, `git diff a243296..HEAD` (Review 2 commit to now), and `engine/app/office.template.html`.

F3 fix:
- `skills/phone-check/SKILL.md` line 9 now reads "Hold the phone upright (portrait) for the whole check. Landscape is out of scope." It sits in the intro, before step 1, so it covers every step.
- In portrait, a 390x844 phone is in the `@media (max-width:599px)` block (lines 286-311). Every step still matches: step 2 initials (`.seg .nm` hidden, `.seg .ini` shown, lines 297-298); step 3 and 10 gear and Usage (`#gear` shown line 304, `#bar .opt` hidden line 302, `#usheet` with x `#usx` lines 1374-1375); step 4 icon-only chat button (line 409); step 5 handle `#chgrip` at the chat top (lines 322-326); step 6 `#tone` at `bottom:var(--bb)` above bar and chat (lines 274, 310), `#usage`/`#ticker` hidden (lines 272-273); steps 7-8 keyboard via `visualViewport` (line 2778). The 600-899 px band from F3 (`#ubtn` in the bar, "Chat" label, names, no gear) is now excluded.
- The template is unchanged since Review 2: `git diff a243296 -- engine/` is empty, and main has no `engine/app/` changes since the merge base.

Nothing else changed since Review 2: `git diff a243296 --stat` shows only the SKILL.md line (+2) and this task file (frontmatter `build` to `review`, and the "Rework 2" Build notes). The pmo-playbook and the T-024 ride-along are untouched.

| Done when | Result | Evidence |
|---|---|---|
| 1. Under 12 steps, each with Expect, every area named | pass | 10 **Do/Expect** steps, unchanged from Review 2. No-overlap is left to T-067 on purpose |
| 2. About 2 minutes | not possible | no real phone here. One extra intro line, about 2 min is still plausible |
| 3. Playbook: when, who, where | pass | pmo-playbook "Phone check (T-071)" unchanged |
| 4. Matches T-066; no step relies on a missing feature | pass | F3 fixed (portrait only); every step matches the under-600 px layout, see above |
| 5. Tests, validate, no other file changes | pass | `python -m unittest discover -s tests`: "Ran 411 tests in 22.079s / OK", exit 0. `python -m engine.runtime validate ai-office`: "ai-office: OK — 8 agents, 5 stages, 71 tasks, 19 skills", exit 0. Branch files: the T-071 skill, pmo-playbook, this task, and the T-024 ride-along (planning only) |

**Notes (not reasons for rejection)**
- A phone held sideways, or a phone 600 px wide or more in portrait (a small tablet), is not covered. That is on purpose now. If Merwyn's phone ever reports the 600-899 layout, a follow-up task can add the variant.
- External skills design:accessibility-review and data:validate-data: not available in this session; not used.

Verdict: PASS. Status stays `review`, owner `pmo` for merge after Merwyn's approval.

## Decision
Merged after Cahyani's Review 3 PASS (Janice, 26 Nov 2026; after two rejections Merwyn chose "Fix and re-review"). The phone check is a skill (`skills/phone-check`), portrait only, 10 steps; T-067 adds a no-overlap step when it merges. T-024's planning sections (parked for Merwyn's gates) were reviewed on the same PR.

Recorded: offices/ai-office/decisions/2026-11-sprint-07.md, Smaller records. — April (curator)

## Open questions
- Which phone and browser does Merwyn use (iOS Safari, Android Chrome, the Claude app)? Unknown; steps may differ. For Merwyn.
- Should failures from the checklist reopen the task or open a new one? For the office (PMO decides).
