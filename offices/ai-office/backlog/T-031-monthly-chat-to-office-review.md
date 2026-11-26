---
id: T-031
title: "Monthly chat-to-office review"
phase: 7-ways-of-working
status: review
priority: P1
owner: reviewer
where: chat
project: ai-office
depends_on: []
pr: 31
---

> Rule: 3+ repeats and a clear 'done'

## Done when
- [ ] Repeated chats turned into skills or workflows

## Spec

**Problem.** Work Merwyn repeats in chats is never turned into office skills or workflows, and no step exists to look for it. Only the main session can search his chats, so the review has to be a repeatable hand-off between the main session (finds) and April (writes up).

**In scope**
- The main session searches his chats and gives April topic-level findings only: topic, chat count, pointer (chat title or date), whether a clear "done" exists. No company data, no borrower or lender names, no production numbers, no chat content.
- April writes `offices/ai-office/research/T-031-2026-11.md`: for each repeat (3 or more chats and a clear done), a proposal as candidate skill, workflow or office task, with chat count and pointer. Items below the bar are listed as "below threshold" with their count.
- A reusable monthly procedure, written as an office skill or a section in curator-playbook (April's choice, one place only), covering who searches, what the main session hands over, the bar, the output file name pattern (T-031-YYYY-MM) and the data rule.
- The report is a proposal. Merwyn picks which items become backlog tasks (human step).

**Out of scope**
- Creating backlog tasks or skills from the findings; searching Project chats; any pass beyond Nov 2026; scheduling or automating the monthly run.

**Done when**
- [ ] `offices/ai-office/research/T-031-2026-11.md` exists; every proposal states a chat count of 3 or more, a pointer and a done-condition; any item under 3 sits only under "below threshold".
- [ ] A reviewer scan of the file finds no email, run of 10+ digits, company or borrower or lender name, or quoted chat text (pointers are titles or dates).
- [ ] The procedure exists in one place (named in the report), and a reader who has not seen this task can follow it to do the December run: it names the handoff fields and the output path.
- [ ] If the chosen place is curator-playbook or a new skill, `python scripts/build_agents.py ai-office` exits 0.
- [ ] The report ends with a numbered pick-list with a recommendation, so Merwyn can answer with numbers; his picks are recorded in the Decision section with date and time.
- [ ] Status does not reach `done` until Merwyn's picks are recorded.

**Open questions**
- Search scope: T-012 searched chats outside Projects only. Does this month include Project chats from inside each Project, or the same scope? Merwyn or Janice to confirm; I assume the same scope as T-012 (not blocking).
- Overlap with T-012 (done): are findings already in section A to D excluded or re-listed? Assumed excluded; April to confirm.
- Time window: which dates count as "this month" (1 to 30 Nov, or last 30 days)? Main session to state it in the report header.
- Who verifies the data-rule scan of the findings before April writes them? Janice to assign (main session suggested).

— Emmy (pm)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: scope is chats outside Projects (what the main session can search), window 26 Oct – 26 Nov 2026. Topics already turned into skills by T-012 are listed as "already covered", not re-proposed. The data-rule scan on the findings file is run by the Engineer in build and re-run by the Reviewer. — Janice (pmo)

## Design

**Input as it exists** (read 26 Nov 2026). `/tmp/t031-findings.md` is outside the repo and stays there; it is never committed. It contains:
- a 7-row table with columns #, topic, chats, pointer dates, clear "done", where it belongs
- the window 26 Oct to 26 Nov 2026, with scope "outside Projects, ~49 chats"
- pointers that are dates (MM-DD, with "(x2)" or "(x3)"), not titles, because the main session found titles naming borrowers or partners

Fact checks done:
- The listed dates add up to the stated chat counts in every row (12, 6, 7, 3, 9, 11, 1).
- The file names a company repo from `workspaces.yaml` (the company workspace repo) in rows 1, 2, 3 and 5 and in the notes. Copied as is, the report would fail the forbidden-terms scan, so the report must say "company repo, behind T-002" instead.

**Approach**
- **April (curator)** writes `offices/ai-office/research/T-031-2026-11.md` from the findings file, and adds the procedure as a new `## 5. Monthly chat-to-office review` section in `offices/ai-office/skills/curator-playbook/SKILL.md`.
- I recommend the playbook section over a new skill. curator-playbook §3 says "keep the skill set lean", April already loads it, and one place satisfies the spec. April may still choose otherwise, per the spec.
- **Sebastian (engineer)** runs the data scan, runs `build_agents.py`, writes Build notes and opens the PR on `t-031-chat-review`. The owner moves to engineer now (the build stage owner), and Janice calls April first inside the stage.
- The scan runs over the findings file too, as a check on the input, but only the report is committed.
- No script is added. The scan is a fixed command (below), the same command lives in the procedure, and it imports the T-048 rule. A shared `scripts/datascan.py` would also serve T-032, T-041 and T-049, but it would tie four parallel tasks together. I suggest it as a follow-up task (Open questions).

**Report format** (`research/T-031-YYYY-MM.md`; follows the table style of `research/T-012-chat-mining.md`)
```
# T-031: chat-to-office review, November 2026
Window 26 Oct to 26 Nov 2026. Scope: chats outside claude.ai Projects (~49). Findings handed over by the main session on 26 Nov 2026; topic level only.
Bar: 3 or more chats AND a clear "done". Procedure: offices/ai-office/skills/curator-playbook/SKILL.md § 5.
Pointers are chat dates (MM-DD, xN = N chats that day), never titles.

## Proposals (meet the bar)
| # | Topic (generic) | Chats | Pointer dates | Done condition | Proposed as | Belongs in |
   Proposed as: skill | workflow | office task.  Belongs in: this office | company repo, behind T-002
## Already covered
| Topic | Chats | Covered by (task or skill id) |
## Below threshold
| Topic | Chats | Why below (fewer than 3 chats / no clear done) |
## Pick-list for Merwyn
1. <action> (recommended) ...
2. ...
Reply with numbers, e.g. "1, 3". April or Janice records the picks in T-031 § Decision with date and time.
## Data scan
<command output line: "data scan: clean (N files)">
```
How this month's findings sort:
- Proposals: topics 1, 2, 3 and 4 (3 or more chats, done "Yes").
- Already covered: topic 5 (T-013, PRD skills).
- Below threshold: topic 6 (done is "Mixed", not clear) and topic 7 (1 chat).
- April confirms each placement against T-012 sections A to D, and any match is listed as "already covered".
- The overlap of topic 3 with T-016 goes in "Belongs in" as a pointer to T-016.

**Procedure** (the curator-playbook § 5 content, about 10 lines):
1. Who and when: at the month's sprint close, Janice asks the main session to search chats outside Projects for the window (the last 30 days, stated as dates).
2. Hand-off: the main session writes `/tmp/t031-findings.md` outside the repo, with columns topic (generic), chats, pointer dates, clear done (Yes, No or Mixed), where it belongs. It also states the window and scope, and includes no titles, names, figures, IDs or quotes.
3. Bar: 3 or more chats and a clear done. Check each row's dates against its count.
4. Output: `offices/ai-office/research/T-031-YYYY-MM.md` in the format above. Replace company repo names with "company repo, behind T-002".
5. Data scan: the Engineer runs the command below over the findings file and the report; the Reviewer re-runs it.
6. Merwyn picks from the numbered list, and his picks and their time go in the task's Decision section. Picks become backlog only through the PMO.

**Data scan command** (stdlib, imports the T-048 rule, prints file, line and kind, never the text):
```
python -c "import sys,pathlib; sys.path.insert(0,'.'); from engine.runtime.events import DATA_PATTERNS as P, PATTERN_KINDS as K, forbidden_terms as F; t=F('.'); n=0
for f in sys.argv[1:]:
  for i,l in enumerate(pathlib.Path(f).read_text(encoding='utf-8').splitlines(),1):
    for p,k in zip(P,K):
      if p.search(l): print(f'{f}:{i}: {k}'); n+=1
    if any(x in l.lower() for x in t): print(f'{f}:{i}: forbidden term'); n+=1
print('data scan:', 'clean' if not n else f'{n} hits'); sys.exit(1 if n else 0)" offices/ai-office/research/T-031-2026-11.md
```
- Expected today: the report gives exit 0. `/tmp/t031-findings.md` gives forbidden-term hits on its company-repo mentions, which is the reason for the rewording rule.
- Quoted chat text cannot be found by a pattern. The Reviewer checks that by reading.

**Test plan** (the Reviewer runs these)
1. The scan command on the report exits 0.
2. Every Proposals row has Chats of 3 or more, a pointer, and a done condition, and its dates add up to its count. Rows under 3 chats appear only under "Below threshold".
3. The report names the procedure location, and that section exists: `grep -n "## 5. Monthly chat-to-office review"`.
4. `python scripts/build_agents.py ai-office` exits 0.
5. `python -m unittest` passes (200 tests at baseline).
6. The report ends with the numbered pick-list. Status stays short of `done` until Merwyn's picks are recorded: the Reviewer records PASS and leaves status at `review`, and Janice sets `done` after his picks.

**Risks**
| Risk | Handling |
|---|---|
| A company repo or partner name gets in by copying the findings | The rewording rule plus the forbidden-terms scan |
| Chat titles reveal borrowers | Date pointers only (already done by the main session) |
| Re-proposing what T-012 or existing tasks cover | The "Already covered" section, with the task id |
| The findings file disappears from /tmp before build | The Engineer runs the scan over it first; if it is gone, Janice asks the main session to rewrite it. The report is the record |

**Flags.**
- Compliance: not flagged. The chats searched hold company and personal data, but that search is the main session's job under Merwyn's own session. Nothing that crosses into the repo is more than topic level, dates and counts, and two scans (Engineer, Reviewer) check it.
- If Janice wants a second pair of eyes, Wulan can review the report before merge; that is optional.
- Dinda's UX consult: does not apply (no UI, visual or motion work).

**Decision record draft (for April)**
```
Decision: the monthly chat review procedure lives in curator-playbook § 5; output is research/T-031-YYYY-MM.md, checked by a fixed data-scan command that imports the T-048 rule.
Context: only the main session can search chats; April writes; the procedure must be repeatable without this task.
Options: A, curator-playbook section (one place April already loads, lean skill set); B, new chat-review skill (one more skill to wire in, same content); C, a script for the scan (one more file now, could serve 4 tasks later).
Chosen: A, with the command inline rather than C, to keep four parallel tasks independent.
Consequences: December's run follows § 5. A later datascan script can replace the inline command in one edit.
Links: T-031, T-012, T-048
```

**Open questions**
- Janice: open a small follow-up task for `scripts/datascan.py` (one data scan for research, golden cases, metrics and skills)? Not blocking.

— Fang (architect)

Janice (pmo), 26 Nov: Design accepted, moved to build. Answers: the metrics report states what history shows (Sprint 1 window: T-012 only, footnoted); the retro is not rewritten. W6 (overrides) is April's call on the evidence. Agreed: for T-041 and T-031 the Reviewer records PASS and leaves status at review; Janice sets done after Merwyn acts. Findings file now says "company repo, behind T-002" (no forbidden terms).

## Build notes

April (curator), 26 Nov 2026. Report: `offices/ai-office/research/T-031-2026-11.md`. Procedure: `offices/ai-office/skills/curator-playbook/SKILL.md` § 5 (one place, as Fang recommended).
Placement checked against T-012 A to D: topics 1 to 3 not covered; topic 4 not a skill there; topic 5 already covered (T-013, T-012 C); topics 6 and 7 below threshold.
Data scan on the report (command from § 5), output pasted:
```
data scan: clean
exit=0
```
The findings file (outside the repo) was not committed. Sebastian still runs `build_agents.py` and the tests, and the Reviewer re-runs the scan.

— April (curator)

Sebastian (engineer), 26 Nov 2026, outputs from this worktree:
- `python scripts/build_agents.py ai-office`: "ai-office: built 8 agents", exit 0 (no `.claude/agents/` diff; the playbook body is not copied into agents).
- `python -m unittest`: Ran 200 tests, OK.
- Data scan (command from playbook § 5) on `offices/ai-office/research/T-031-2026-11.md`: "data scan: clean", exit 0. My own scan with the same patterns plus forbidden terms (5) over the report and the playbook found nothing on added lines; the only flags are the signature em-dash and pre-existing source URLs and dashes in the playbook's older sections.
- `grep -n "## 5. Monthly chat-to-office review"` finds the section at line 28.
- `python scripts/board.py ai-office`: ran, no problems reported; board.md discarded.
- Proposal rows: counts 12, 6, 7, 3 meet the bar; below-threshold rows hold 11 (mixed) and 1.
- Deviations from the design: none. Quoted-chat-text check is for the Reviewer to read. Status unchanged; Merwyn's picks are pending.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
