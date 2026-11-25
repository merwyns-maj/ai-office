---
id: T-042
title: "Sprint 1 process lessons: tool check, board.md rule, handoff for read-only agents"
phase: 7-ways-of-working
status: design
priority: P1
owner: architect
where: code
project: ai-office
depends_on: []
pr: null
---

> Opened by Janice at Sprint 1 close (see sprints/sprint-01.md, Retro). Three lessons, one task.

## Done when
- [ ] pm-playbook (and spec-writing if needed) tells the PM to check at the start that it can read and search the backlog; if it cannot, stop and ask the PMO for the parent task text instead of writing the spec blind
- [ ] pr-workflow states one rule for the generated board.md (task branches do not commit it; PMO regenerates on main after merge, or a merge driver is added and tested) and scripts or CI do not contradict it
- [ ] handoff skill says read-only agents return paste-ready text (section body, signature, proposed status and owner) and the PMO records it in the task file; build_agents.py run so agent files match
- [ ] A reviewer can find each rule in one skill file; no skill contradicts another

## Spec

**Problem.** Sprint 1 showed three process gaps: the PM wrote a spec blind when its Glob/Grep were missing, two task branches both committed the generated `board.md` and hit rebase conflicts, and read-only agents returned chat text that the orchestrator had to turn into Review log entries and status changes. Each will recur unless it is written into a skill.

**In scope**
- (a) PM tool check: `pm-playbook` (and `spec-writing` if needed) tells the PM to confirm at the start that it can read and search the backlog and parent tasks; if not, stop and ask the PMO for the parent text.
- (b) `board.md` rule in `pr-workflow`. Recommendation: **option (a), task branches do not commit `board.md`; the PMO regenerates and commits it after each merge.** Reason: it needs no new tooling, whereas a `.gitattributes` merge driver also needs a per-clone `git config` entry that does not travel with the repo.
- (c) `handoff`: read-only agents (Reviewer, Compliance, Architect without write access) return paste-ready text (section body, signature, proposed status and owner); the PMO records it in the task file.
- Fix lines that contradict (b): `handoff` step 5 and `CLAUDE.md` line 12 currently say to run `board.py` and commit on the task branch.
- Run `python scripts/build_agents.py ai-office` so agent files match.

**Out of scope**
- A merge driver or `.gitattributes`.
- Changing `scripts/board.py` output, other offices, or recording per-stage timestamps.
- Rules for any agent not named above.

**Done when** (reviewer-verifiable)
- [ ] `pm-playbook/SKILL.md` has a start-of-task step naming Glob/Grep (or read and search) access and the instruction to stop and ask the PMO for parent task text. Check: open the file; `grep -n -i "parent" offices/ai-office/skills/pm-playbook/SKILL.md` finds it.
- [ ] `pr-workflow/SKILL.md` has one rule: task branches do not commit `board.md`; the PMO regenerates and commits it after merge. Check: `grep -n "board.md" offices/ai-office/skills/pr-workflow/SKILL.md`.
- [ ] `grep -rn "board.py" offices/ai-office/skills CLAUDE.md` shows no line that tells an agent to commit `board.md` on a task branch. Any `.github/` workflow that does so is also fixed (see Open questions).
- [ ] `handoff/SKILL.md` has a read-only-agent paragraph listing section body, signature, proposed status and owner, and saying the PMO records it. Check: open the file.
- [ ] `python scripts/build_agents.py ai-office` exits 0 and `git status` shows no unbuilt agent diffs afterwards.
- [ ] Each of the three rules appears in exactly one skill file, and no other skill states the opposite. Check: `grep -rn` for each rule keyword across `offices/ai-office/skills`.

**Open questions**
- Does the PMO's post-merge `board.md` commit count as a push to `main`? `CLAUDE.md` says never push to `main`; the Architect needs Merwyn's or the PMO's ruling (a small PR vs a permitted direct commit). Blocking for (b). Who: Merwyn.
- Does any CI workflow or hook commit or check `board.md`? Not verified (I could not list `.github/`). Who: Architect.
- Fact note: Glob/Grep were unavailable in my session too; I read the listed files directly.

— Emmy (pm)
