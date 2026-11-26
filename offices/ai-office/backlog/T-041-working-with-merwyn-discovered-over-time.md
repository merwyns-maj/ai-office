---
id: T-041
title: "working-with-merwyn skill, discovered over time"
phase: 7-ways-of-working
status: build
priority: P2
owner: reviewer
where: office
project: ai-office
depends_on: [T-012]
pr: 29
---

> Merwyn 25 Nov 2026: "we can discover what's best for us". Seed from T-012 section D; grow it from sprint retros.

## Done when
- [ ] After at least 2 sprints, April proposes a skill from the governance patterns that actually held up (escalation format, decision recording, terse-reply handling, overrides)
- [ ] Merwyn approves it

## Spec

**Problem.** Each agent learns Merwyn's style (terse replies, decisions, when to stop and ask) from scratch or from scattered notes, so the PMO and others may mis-read an answer like "b" or miss when he expects a recorded decision. Four sprints have run, so patterns now have evidence; T-012 section D only has single sightings.

**In scope**
- April writes a proposed office skill `offices/ai-office/skills/working-with-merwyn/SKILL.md` (Merwyn-specific, so office level, not `base/skills`), listed in the relevant agents' `office_skills`.
- Only patterns evidenced at least twice, each with an evidence pointer (file and section or date, no chat content). Sources: T-012 section D, sprint-01 to 05 retros and "Decisions recorded", task Approvals and Decision sections.
- Candidates to test against that bar: terse replies mapped to numbered options ("b", "accept", "1 just merge, 2 all good"); numbered option menus with a recommendation; decisions recorded with his time; escalate when stuck; "don't chase"; financial terms in English (the last also lives in partner-writing B2, so the skill points to it).
- Patterns with one sighting go in a short "watching" list in the task's Decision section, not the skill.
- Merwyn's approval is the last step.

**Out of scope**
- Rewriting working-standard or partner-writing; chat-derived claims that cannot be pointed to; any company data or names; changing escalation rules in workflow.yaml.

**Done when**
- [ ] The SKILL.md exists with name and description frontmatter, and `python scripts/build_agents.py ai-office` exits 0 after it is added to `office_skills`.
- [ ] Every pattern in it has at least 2 evidence pointers that a reviewer can open; a pattern with fewer is absent.
- [ ] Terse-reply handling lists each reply form seen with the option it mapped to, and says to ask when the reply is ambiguous.
- [ ] A reviewer scan finds no email, run of 10+ digits or company name; no em-dashes (partner-writing B1).
- [ ] The task's Decision section holds the "watching" list and Merwyn's approval with date and time, recorded by April or the PMO.
- [ ] Status does not reach `done` until Merwyn's approval is recorded (human step, last).

**Open questions**
- Is "overrides" (D3, he lets the office skip process) evidenced twice in the repo? Sprint 4 "proceed ahead without waiting" is one; April to check for a second, else it goes to "watching". Not blocking.
- Does Merwyn want the skill loaded by all agents or only the PMO and curator? Janice to propose; Merwyn confirms with approval.
- I could not list the repo to confirm approval-note headings in task files (no Glob in this session); April to search them.

— Emmy (pm)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: "overrides" has a second sighting: Merwyn's 26 Nov 09:01 "b" chose to accept T-048 over two Reviewer REJECTs (sprint-05.md Decisions recorded), after Sprint 4's "proceed ahead without waiting". The skill is loaded by the PMO (Janice) and the Curator (April) only; others reach Merwyn through Janice. — Janice (pmo)

## Design

**Approach**
- New file `offices/ai-office/skills/working-with-merwyn/SKILL.md`, at office level, written by **April (curator)**, because the Curator owns office knowledge and the content needs her evidence search.
- **Sebastian (engineer)** wires it in and opens the PR:
  - add `working-with-merwyn` to `office_skills` in `offices/ai-office/agents/pmo.md` and `offices/ai-office/agents/curator.md` (only those two, per the approval)
  - run `python scripts/build_agents.py ai-office` and commit the regenerated `.claude/agents/` files
  - run the tests
- Build order, inside the build stage: Janice calls April first, and April commits the SKILL.md and the Decision-section "watching" list on branch `t-041-working-with-merwyn`. Then Sebastian wires it in, writes Build notes and opens the PR. The owner moves to engineer now, because build is his stage; April's step is a call made inside that stage.
- No code and no schema change. `workflow.yaml` escalation rules are untouched. The skill points to them and does not restate them.

**SKILL.md structure** (one screen, about 40 lines; tags W1, W2 and so on, following the A and B tags in working-standard and partner-writing)
```
---
name: working-with-merwyn
description: How the PMO and Curator read Merwyn's replies, offer him choices and record his decisions. Use before asking Merwyn anything and when recording his answer.
---
# Working with Merwyn
Status line: proposed by April <date>; approved by Merwyn <date time> (filled in at approval).
Patterns that held up at least twice in this repo. Each has its evidence; one-off sightings live in T-041's Decision ("watching").

## Patterns
- **W1 <short title>.** <rule, 1 to 2 lines, imperative>.
  Evidence: <pointer>; <pointer>[; ...]
...
## Terse replies
| Reply seen | What it answered | Mapped to | Evidence |
|---|---|---|---|
| "b" | numbered options (a)/(b) | option b | <pointer> |
If a reply maps to no option or to more than one, ask again with the numbered options. Do not guess.

## Points elsewhere (not restated)
- Financial terms in English: partner-writing B2.  - Never untrue: partner-writing B5 / T-012 D4.
- When to escalate: workflow.yaml `human_gates` and `escalation`.
```
- Candidate patterns for April to test against the two-pointer bar: W1, numbered options with a recommendation; W2, terse reply maps to an option; W3, record a decision with his date and time, where the work lives; W4, stop and ask at human gates and the second REJECT; W5, "no chasing"; W6, override for speed, recorded and never against a safety rule. A candidate with one pointer goes to "watching".
- No names of other people, companies or repos. No chat text: quote only Merwyn's short replies (for example "b", "accept") that are already recorded in this repo. No em-dashes or en-dashes (B1).

**Evidence-pointer format** (one per pointer; a reviewer must be able to open each)
```
`<repo-relative path>` § <exact section heading>[, <item id or date time>]
```
Examples:
- `` `offices/ai-office/sprints/sprint-05.md` § Decisions recorded (Merwyn, 26 Nov 2026), 09:01 ``
- `` `offices/ai-office/research/T-012-chat-mining.md` § D. How we work together, D1 ``
- `` `offices/ai-office/raid.md` § R-14 ``

Rules for pointers:
- Headings, not line numbers, because line numbers drift.
- A T-012 row counts as one sighting, however many chats it lists. It is a summary pointer, and the chat behind it is not opened or quoted.
- Two pointers to the same event (for example a sprint file and a task file both recording the 26 Nov 09:01 "b") count as **one** sighting. The bar is two separate events.

**Test plan** (the Reviewer runs these)
1. `python scripts/build_agents.py ai-office` exits 0, and the generated pmo and curator agents list `offices/ai-office/skills/working-with-merwyn/SKILL.md`. No other agent lists it: `grep -l working-with-merwyn .claude/agents/*`.
2. Every `Evidence:` line and table row has at least 2 pointers to separate events, and each opens to the named heading. Check with `grep -n "^#" <file>` per pointer.
3. Data scan: `python -c` with `DATA_PATTERNS` and `forbidden_terms` from `engine/runtime/events.py` over the SKILL.md prints no hit. `grep -nP '[\x{2013}\x{2014}]'` finds nothing.
4. `python -m unittest` still passes (200 tests at baseline on main).
5. The Decision section holds the "watching" list, and Merwyn's approval with its date and time once given.

**Risks**
| Risk | Handling |
|---|---|
| A single event counted twice (sprint file and task file record the same decision) | The pointer rule above: same event, one sighting |
| "Overrides" (W6) is weaker than it looks. The 26 Nov 09:01 "b" was Merwyn choosing an option at an escalation the workflow requires, not skipping a process. The Sprint 4 "proceed ahead without waiting" is a real override | April decides with this in mind. If only one real override is found, W6 goes to "watching" (see Open questions) |
| The skill drifts into restating workflow.yaml or partner-writing | The "Points elsewhere" section; the Reviewer checks for duplicated rules |
| Done before Merwyn approves | `status_writers` lets the Reviewer set `done` on PASS. For this task the Reviewer records PASS and leaves status at `review`, with "waiting on Merwyn approval". Janice sets `done` after his approval is recorded |

**Flags.** Compliance: not flagged (no prod, money or third-party personal data; the content is Merwyn's working preferences, which he approves himself). Dinda's UX consult: does not apply (no UI, visual or motion work).

**Decision record draft (for April)**
```
Decision: working-with-merwyn is an office skill loaded by the PMO and Curator only, holding patterns with 2+ separate in-repo sightings, each cited as path § heading.
Context: T-012 section D had single sightings; four sprints now give repo evidence; other agents reach Merwyn through Janice.
Options: A, office skill for pmo and curator (small blast radius, matches the approval); B, base skill for every agent (Merwyn-specific text in base/, loaded where it is not used); C, a section in pmo-playbook (hides it from the curator, mixes evidence with method).
Chosen: A.
Consequences: other agents never read it directly. Patterns grow at sprint close through April; the watching list lives in T-041 Decision until a second sighting.
Links: T-041, T-012
```

**Open questions**
- April / Janice: is choosing an escalation option (26 Nov 09:01 "b") an "override" in the D3 sense? My reading is that it is not: it is the escalation gate working. If April agrees and no second override exists, W6 goes to "watching". Not blocking.

— Fang (architect)

Janice (pmo), 26 Nov: Design accepted, moved to build. Answers: the metrics report states what history shows (Sprint 1 window: T-012 only, footnoted); the retro is not rewritten. W6 (overrides) is April's call on the evidence. Agreed: for T-041 and T-031 the Reviewer records PASS and leaves status at review; Janice sets done after Merwyn acts. Findings file now says "company repo, behind T-002" (no forbidden terms).

## Build notes
**What changed**
- `working-with-merwyn` added to `office_skills` in `offices/ai-office/agents/pmo.md` and `curator.md` only.
- `python scripts/build_agents.py ai-office` regenerated `.claude/agents/pmo.md` and `curator.md` (one line each).
- SKILL.md and the Decision "watching" list are April's, unchanged by me.

**How to verify (output from this build)**
- `python scripts/build_agents.py ai-office`: "ai-office: built 8 agents", exit 0.
- `grep -l working-with-merwyn .claude/agents/*`: `curator.md`, `pmo.md` only.
- `python -m unittest`: Ran 200 tests, OK.
- `python scripts/board.py ai-office`: ran, no problems reported; board.md discarded.
- Data scan (`DATA_PATTERNS` and `forbidden_terms` from `engine/runtime/events.py`, 5 terms, plus en/em-dash check) over SKILL.md: 0 hits.
- Evidence pointers: all 16 `path` + heading pairs open (file exists, heading text present). I did not judge whether two pointers are separate events; that is the Reviewer's check.

**Deviations from the design:** none. Status left at `build`/unchanged per instruction; approval from Merwyn is still pending (Decision section).

— Sebastian (engineer)

## Review log

## Decision

**Proposal for Merwyn (April, 26 Nov 2026). Not approved yet.**

Decision: working-with-merwyn is an office skill loaded by the PMO and Curator only. It holds five patterns, each with 2 or more separate in-repo sightings cited as path and heading, and one table of terse replies.
Why: T-012 section D had single sightings; Sprints 1 to 5 now give repo evidence; other agents reach Merwyn through Janice.
Options considered: A, office skill for pmo and curator (chosen, small blast radius); B, base skill for every agent (Merwyn-specific text loaded where unused); C, a section in pmo-playbook (hides it from the curator).
Links: T-041, T-012; skill at `offices/ai-office/skills/working-with-merwyn/SKILL.md`; PR to be linked by Sebastian.

Which patterns made it: W1 numbered options with a recommendation (T-040, T-048, T-001); W2 terse replies (table, two rows); W3 record with date and time (T-040, Sprint 3, T-048); W4 stop and ask at the gate (Sprint 1 retro, T-048); W6 go or accept as is, then record the leftover (Sprint 4, T-048, T-012 D3).

W6 call: kept. Two repo events (Sprint 4 "proceed ahead", T-048 accept over two REJECTs) plus the T-012 D3 summary. I agree with Fang that the T-048 choice was the escalation gate working, so I worded W6 as "comply and record the leftover", not "skip process". It is the weakest pattern; say if you would rather it sit in watching.

Watching (one sighting each, not in the skill):
- W5 "no chasing": one decision on 25 Nov 22:44, restated in R-1, T-002, and the Sprint 3 and 4 waiting lists. Restating is not a new event. Needs a second, separate case.
- Terse reply "b" (option letter): one event (T-048, 26 Nov 09:01). The sprint file and task file record the same event.
- "1 just merge, 2 all good" (named in the Spec): no recorded sighting in this repo; it came from outside the repo, so it is left out.
- D2 (iterate in artifact comments and reply in the thread) and D4 (never untrue): D2 has one T-012 pointer; D4 is already partner-writing B5, so the skill points to it.

Approve or change (reply with numbers):
1. Approve the skill as written (recommended).
2. Approve, but move W6 to watching.
3. Approve, but load it for all agents, not only PMO and Curator.
4. Change something else (say what).

Merwyn's approval: pending (date and time to be recorded here by April or Janice).
Status stays at `review` until approval is recorded.

— April (curator)

## Open questions
