---
id: T-046
title: "Compliance files match the 25 Nov prod access decision"
phase: 0-office
status: review
priority: P0
owner: reviewer
where: code
project: ai-office
depends_on: [T-043]
pr: https://github.com/merwyns-maj/ai-office/pull/23
---

> From Fang's incidental finding and Wulan's note 4 on T-043. Must be done before T-019 (guard install) and before any task is reviewed against these checklists.

## Done when
- [ ] base/agents/compliance.md, offices/ai-office/skills/compliance-playbook/SKILL.md and offices/ai-office/skills/uu-pdp-checklist/SKILL.md no longer name "Bytebase change issues" as the approved write path
- [ ] They state: prod writes only on Merwyn's instruction (guard asks, he confirms); agents never submit to Bytebase; read access approved by Merwyn 25 Nov (R-14); read-only DB role (R-8) is the real control
- [ ] python scripts/build_agents.py ai-office exits 0 and the regenerated compliance agent carries the new wording

## Spec

**Problem.** Wulan's three guidance files still say prod writes are allowed "through Bytebase change issues". Merwyn decided on 25 Nov (R-14) that agents never submit to Bytebase and that writes happen only on his instruction. Until the files match, Wulan would PASS or BLOCK designs against the wrong rule.

**In scope**
- Reword the three lines only: `base/agents/compliance.md:13`, `offices/ai-office/skills/compliance-playbook/SKILL.md:20`, `offices/ai-office/skills/uu-pdp-checklist/SKILL.md:11`.
- New wording says: agents read prod read-only by default (approved by Merwyn 25 Nov, R-14); prod writes only when Merwyn instructs (guard asks, he confirms); agents never submit to Bytebase, they hand the plan to Merwyn; the read-only DB role (R-8) is the real control, the guard a safety net (R-9).
- Regenerate agents with `python scripts/build_agents.py ai-office`.

**Out of scope**
- Installing the guard (T-019, human gate) and commissioning the read-only DB or kube role (R-8, Merwyn).
- Any other line in the three files, including playbook line 21 (no prod personal data as cloud context without Merwyn and legal approval), unless Merwyn says otherwise (see Open questions).
- Changing the guard code, README or raid.md.

**Done when**
- [ ] `grep -rni bytebase base/agents/compliance.md offices/ai-office/skills/compliance-playbook/SKILL.md offices/ai-office/skills/uu-pdp-checklist/SKILL.md` returns no line that names Bytebase change issues as an approved write path; any remaining Bytebase mention says agents never submit.
- [ ] Each of the three files states, in its own words: prod writes only on Merwyn's instruction (guard asks, he confirms); agents never submit to Bytebase and hand the plan to Merwyn. Reviewer can find both in each file.
- [ ] The playbook (and base compliance file) states that read access was approved by Merwyn on 25 Nov (cites R-14) and that the read-only DB role (R-8) is the real control. It does not claim the role or the guard is already installed (R-8 is still open).
- [ ] The checklist still BLOCKs a write path to prod that bypasses Merwyn's confirmation; it does not become silent about prod writes.
- [ ] `python scripts/build_agents.py ai-office` exits 0, and `.claude/agents/compliance.md` contains the new wording and not the old "Bytebase change issues" text.
- [ ] `git diff --stat` shows changes only in the three source files plus the regenerated agent file(s), and this task file.

**Risks**
- Wording that sounds like reads are unconditionally safe. Keep "read-only default" and name R-8 as the control.
- Prod data fed to cloud agents as context is still limited by line 21; do not erase it by accident.

**Open questions**
- Does playbook line 21 stay as is, now that reads are approved? Answer: Merwyn (Wulan can advise). Not blocking: default is leave unchanged.
- Does the playbook's "Read access to prod is still flagged for review" stay? Answer: Wulan via Janice. Not blocking: default is keep flagged, with the approval cited.

— Emmy (pm)

## Design

**Approach** (wording only: 3 lines replaced, no logic or data changes)
- Replace exactly one line in each of `base/agents/compliance.md` (line 13), `offices/ai-office/skills/compliance-playbook/SKILL.md` (line 20) and `offices/ai-office/skills/uu-pdp-checklist/SKILL.md` (line 11). Every other line stays as it is, including playbook line 21 (approval: unchanged).
- Run `python scripts/build_agents.py ai-office`. Only `.claude/agents/compliance.md` changes in content, because it inlines the base body. The two skills are linked by path, not inlined, so no other generated file changes. Build rewrites all 7 files, and the other 6 must come out byte-identical.
- Cite R-14 and R-8 by id, plus `offices/ai-office/raid.md` in the base file, because base/ is shared by every office. I checked raid.md on 25 Nov: R-14 is the closed decision (Merwyn, 25 Nov 22:44) and R-8 is "Open (narrowed)".

**Exact replacement lines**

1. `base/agents/compliance.md:13`
   - old: `- No writes to production outside the approved path (e.g. Bytebase change issues)`
   - new: `- No writes to production unless Merwyn instructs them (the guard asks, he confirms); agents never submit to Bytebase, they hand the plan to Merwyn. Prod reads are read-only by default (approved by Merwyn 25 Nov, offices/ai-office/raid.md R-14); the real control is a read-only DB role (R-8, still open), the guard only a safety net (R-9)`

2. `offices/ai-office/skills/compliance-playbook/SKILL.md:20`
   - old: `- Production writes only through the approved path (Bytebase change issues). Read access to prod is still flagged for review.`
   - new: `- Production writes happen only when Merwyn instructs them: the guard asks and he confirms. Agents never submit to Bytebase; they prepare the plan (change, target, rollback) and hand it to Merwyn. Read access to prod, read-only by default, was approved by Merwyn on 25 Nov (raid.md R-14) and is still flagged for review: the real control is a read-only DB role (R-8, still open), and the guard is a safety net, not a security boundary (R-9).`

3. `offices/ai-office/skills/uu-pdp-checklist/SKILL.md:11`
   - old: `- A write path to production exists outside the approved route (Bytebase change issues).`
   - new: `- A write path to production exists that does not wait for Merwyn's instruction and confirmation (the guard asks, he confirms), or an agent submits to Bytebase itself (agents never submit; they hand the plan to Merwyn).`

How the lines map to the Spec's Done when:

| Done when | 1 base | 2 playbook | 3 checklist |
|---|---|---|---|
| Writes only on Merwyn's instruction, guard asks / he confirms | yes | yes | yes (as a BLOCK condition) |
| Never submit to Bytebase, hand the plan to Merwyn | yes | yes | yes |
| Read approved 25 Nov (R-14); R-8 is the real control; not claimed as installed | yes ("still open") | yes ("still open", "flagged for review" kept per approval) | not required |
| Checklist still BLOCKs a write that bypasses confirmation | — | — | yes |
| Remaining Bytebase mentions say agents never submit | yes | yes | yes |

**Test plan** (Engineer pastes the output into Build notes)
- `grep -rni bytebase base/agents/compliance.md offices/ai-office/skills/compliance-playbook/SKILL.md offices/ai-office/skills/uu-pdp-checklist/SKILL.md .claude/agents/compliance.md` returns 4 lines, each containing "never submit". `grep -rn "change issues" <same files>` returns nothing.
- `grep -n "R-14\|R-8" base/agents/compliance.md offices/ai-office/skills/compliance-playbook/SKILL.md` finds a hit in both files.
- `grep -n "cloud infrastructure" offices/ai-office/skills/compliance-playbook/SKILL.md` still returns line 21, unchanged.
- `python scripts/build_agents.py ai-office` exits 0. `git diff --stat` lists only the 3 source files, `.claude/agents/compliance.md` and this task file.
- `python -m unittest discover -s tests` passes. No test reads these lines; this is a regression check only.

**Risks**
- *"Read-only by default" read as "reads are safe".* Both longer lines name R-8 as the real control and say it is still open. Line 21 still limits feeding prod personal data to cloud agents.
- *"Still open" goes stale when Merwyn commissions R-8.* Whoever closes R-8 updates these two lines. The Curator adds that follow-up to R-8 in raid.md (this task does not edit raid.md: out of scope).
- *The base file cites an ai-office RAID id.* It is the only office today. A second office would need its own wording through its office profile, which is a known limit and does not block now.

**Compliance flag: yes, Wulan checks before build.** This changes the rules she enforces, and it touches the prod-access policy (a human-gate area), although the change is wording only. She checks:
1. The three new lines match R-14 exactly: writes only on Merwyn's instruction, the guard asks and he confirms, Bytebase never submitted by agents, the plan handed to Merwyn.
2. The checklist line still produces a BLOCK for any prod write path that skips Merwyn's confirmation, including an agent submitting to Bytebase.
3. Nothing claims that the read-only DB role or the guard is installed (R-8 and T-019 are open).
4. Playbook line 21 (personal data as cloud context) is untouched, and "flagged for review" survives.
5. Nothing loosens the pointers-only or no-secrets rules.
She is read-only, so she returns her verdict as a HANDOFF block for Janice to record. On PASS: owner goes to engineer. On BLOCK: to Merwyn (human gate).

**Decision record draft (for April)**
```
Decision: The compliance guidance files state R-14: prod writes only on Merwyn's instruction (the guard asks, he confirms), agents never submit to Bytebase, prod reads are read-only by default with R-8 as the real control.
Context: The three files still named "Bytebase change issues" as the approved write path, which R-14 (25 Nov) reversed. T-043 already changed the guard.
Options: A — replace the three lines only (smallest change, matches the Spec); B — rewrite the prod sections of both skills (more consistent wording, but out of scope and riskier for Wulan's checks).
Chosen: A, because it fixes the wrong rule with the smallest diff and leaves line 21 and all other checks as they are.
Consequences: Wulan's checks match the guard. Two lines say "R-8 still open" and must be updated when R-8 closes. This supersedes the earlier "Bytebase change issues" wording (T-040 era).
Links: T-046, T-043, raid.md R-8, R-9, R-14
```

— Fang (architect)

## Approvals (PMO)
Spec approved 25 Nov 2026. Answers: compliance-playbook line 21 (personal data as cloud context) stays unchanged; keep the "read access flagged for review" idea, reworded to cite Merwyn's 25 Nov approval (R-14). No design consult needed (no UI). — Janice (pmo)

## Compliance
Compliance: PASS with conditions (25 Nov 2026). Checked Fang's five points against R-14, R-8, R-9 and the three target files.
1. Lines match R-14: PASS.
2. Checklist still BLOCKs any prod write path that skips Merwyn's confirmation, including an agent submitting to Bytebase: PASS.
3. No claim that the read-only DB role or the guard is installed: PASS, with condition 1.
4. Playbook line 21 unchanged and "flagged for review" kept: PASS, with condition 2.
5. Pointers-only and no-secrets rules untouched: PASS.
Conditions for the Engineer:
- C1: in the base line 13 and playbook line 20, write that the guard asks "once installed (T-019, still open)" and that until then the rule is by process. Exact base text: `- No writes to production unless Merwyn instructs them: once the guard is installed (T-019, still open) it asks and he confirms; until then this is a process rule. Agents never submit to Bytebase, they hand the plan to Merwyn. Prod reads are read-only by default (approved by Merwyn 25 Nov, offices/ai-office/raid.md R-14); the real control is a read-only DB role (R-8, still open), the guard only a safety net (R-9)`
- C2: in playbook line 20, state that the 25 Nov approval is Merwyn's and not a legal sign-off, and that line 21 still applies. Line 21 stays byte-identical.
- Checklist line 11 stays as Fang wrote it.
Reviewer: re-check the real diff after build (grep per the Test plan; line 21 unchanged; only the 3 source files, `.claude/agents/compliance.md` and this task file in git diff --stat). Follow-up for the Curator: update both "R-8 still open" mentions when R-8 closes.
— Wulan (compliance), recorded by Janice (pmo)

## Build notes
**What changed.** One line replaced in each of `base/agents/compliance.md:13`, `offices/ai-office/skills/compliance-playbook/SKILL.md:20`, `offices/ai-office/skills/uu-pdp-checklist/SKILL.md:11`, plus the regenerated `.claude/agents/compliance.md`. Wording per Fang's Design with Wulan's C1 (guard "once installed (T-019, still open)", process rule until then; base text exactly as she gave it) and C2 (playbook: approval is Merwyn's, not a legal sign-off, line 21 still applies). Checklist line 11 is as Fang wrote it. Playbook line 21 untouched. No deviations from the Design beyond C1/C2.

**How to verify** (output from my run, long lines cut to 120 chars)
```
$ python scripts/build_agents.py ai-office
ai-office: built 7 agents -> .claude/agents/ (architect, compliance, curator, engineer, pm, pmo, reviewer)   (exit 0)
$ grep -rni bytebase <3 source files> .claude/agents/compliance.md   -> 4 lines (base:13, playbook:20, checklist:11, agent:14), each says "never submit"
$ grep -rn "change issues" <same files>   -> no output
$ grep -n "R-14\|R-8" base/agents/compliance.md playbook   -> hit in both (base:13, playbook:20)
$ grep -n "cloud infrastructure" playbook   -> 21:- Agents running on cloud infrastructure must not be fed personal data from production as context unless Merwyn and legal have approved that flow.
$ python -m unittest discover -s tests   -> Ran 158 tests in 5.157s, OK
$ python scripts/board.py ai-office   -> ai-office: 48 tasks -> offices/ai-office/board.md (no problems; board.md discarded)
$ git diff --stat (before this notes edit): .claude/agents/compliance.md, base/agents/compliance.md, this task file, compliance-playbook/SKILL.md, uu-pdp-checklist/SKILL.md
```
Playbook diff is a single line (20); the other 6 generated agents are unchanged.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
