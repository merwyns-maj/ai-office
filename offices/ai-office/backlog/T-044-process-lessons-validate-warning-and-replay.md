---
id: T-044
title: "Sprint 2 process lessons: validate warns on missing defaults, pr-workflow replay not rebase"
phase: 7-ways-of-working
status: design
priority: P1
owner: architect
where: code
project: ai-office
depends_on: []
pr: null
---

> Opened by Janice at Sprint 2 close; carries RAID R-11 and R-12.

## Done when
- [ ] R-11: given an office whose repo has no `base/defaults.yaml`, when `build_agents.py` validates (and `board.py`, if it loads offices the same way), then the output contains a warning that names `base/defaults.yaml` and says agents will get no base skills, and the exit code is what it is today for an otherwise clean office
- [ ] R-11: a test (fixture office without the file) asserts that warning; a second assertion shows no such warning when the file is present, and a run on this repo prints no such warning
- [ ] R-12: pr-workflow has a short rule: in a shallow clone, if `git rebase` reports add/add conflicts, do not resolve them; create a branch from fresh main, replay the branch's own commits with cherry-pick, then push
- [ ] R-12: the "`mergeable` false" rule and the "push rejected as too large" rule in pr-workflow each point to the replay rule, and neither still says only "rebase"
- [ ] workflow.yaml `merge.requires_planning_only` (and its comment) also allows PRs whose changes are limited to plan-stage backlog task files (see Open question 1), plus the existing `sprints/`, `board.md`, `raid.md`; pr-workflow's board.md section says the same; workflow.yaml still passes validate
- [ ] Nothing widens the Reviewer-free path beyond that: a PR touching a task file past the plan stage, or any other path, still needs a Reviewer PASS (stated in workflow.yaml or pr-workflow)
- [ ] No skill or workflow text contradicts another (the two planning-only statements agree); `build_agents.py` runs clean on the real office and the full test command exits 0

## Spec
**Problem.** Two Sprint 2 lessons are still open: if `base/defaults.yaml` is missing, build and validate pass while agents silently get no base skills (R-11), and in shallow clones `git rebase` produces false add/add conflicts, which pr-workflow still answers with "rebase" (R-12). Also, planning-only PRs may skip the Reviewer only for sprint files, so a PR that only writes plan-stage task files (specs) cannot merge on the same path, which Janice noted on PR #17.

**In scope**
- A clear warning from validate/build for a missing `base/defaults.yaml`, with tests.
- The replay-not-rebase rule in pr-workflow, with the two pointers.
- Widening the planning-only definition in workflow.yaml and pr-workflow to include plan-stage backlog task files.

**Out of scope**
- Making a missing `defaults.yaml` a hard failure; changing any other validate rule.
- Any other pr-workflow or merge-rule change; changing who merges; closing R-11/R-12 in raid.md (PMO does that).
- Reading or changing CLAUDE.md beyond keeping it consistent (it only says "see pr-workflow").

**Open questions**
1. Janice: the exact "plan-stage" definition. Proposed: task files whose `status` is `todo` or `spec`, changes limited to frontmatter and the Spec section. I could not read the PR #17 note; please paste it. Blocking for design.
2. Fang: the replay rule pushes under the same branch name, which needs a force push of a task branch (the rules only forbid it for `main`); decide same name versus new name plus PR link. Non-blocking for spec.
3. Fang: does `board.py` share the loader path, so one warning covers both? Tool note: Glob, Grep and Bash were unavailable, so I read only the files in the brief (not `build_agents.py` or `board.py`).

— Emmy (pm)

## Design

## Approvals (PMO)
- Spec approved. Q1: plan-stage task files = new task files at status todo or spec, plus status, owner, depends_on and dated decision notes on existing tasks, written by the PMO at sprint plan/close (as in PR #17, which also touched sprints/, raid.md, board.md). Q2 and Q3 are Fang's design calls; PMO preference for Q2: keep the same branch name and push with --force-with-lease (task branches only, never main). — Janice (pmo)

## Build notes

## Review log

## Decision

## Open questions
