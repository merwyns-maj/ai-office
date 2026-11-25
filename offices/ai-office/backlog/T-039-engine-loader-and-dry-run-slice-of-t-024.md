---
id: T-039
title: "Engine loader and dry-run (repo-only slice of T-024)"
phase: 6-office
status: design
priority: P1
owner: architect
where: code
project: ai-office
depends_on: [T-001]
pr: null
---

> Slice of T-024. Covers load, validate and dry-run only. Live agent runs on the Agent SDK (which spend SDK credit) stay in T-024.

## Done when
- [ ] Given `offices/ai-office`, when the engine's validate command runs, it exits 0 and reports counts of agents, stages and tasks loaded (office.yaml, org.yaml, workflow.yaml, agents/*.md, backlog/T-*.md)
- [ ] Given a copy of an office with one defect each (missing required file; org agent id with no agents/ file; task `status` not in workflow stages; task `depends_on` pointing to a missing task; agent listing a skill with no skills/<name>/SKILL.md), validate exits 1 and the message names the file and the problem; one test per defect
- [ ] Given `offices/ai-office`, when dry-run runs, it exits 0 and prints, for the task it picks: task id, stage, owner, the owner's agent profile path, its skills (office and external), and the workflow output section it would write
- [ ] Dry-run picks deterministically: a test with a fixture backlog shows highest priority first, then lowest task id, skipping tasks that are terminal or whose `depends_on` are not done; with nothing eligible it exits 0 and prints "nothing to run"
- [ ] Dry-run makes no SDK call, no network call and reads no credential: tests pass with network disabled and no API key in the environment, and no SDK package is imported by the loader or dry-run
- [ ] Dry-run does not modify any file (a test compares the office folder before and after)
- [ ] One test command (stated in the README) runs all of the above and exits 0 on a clean checkout

## Spec
**Problem.** Nothing in the repo can read an office folder and check it against the schema, so mistakes in an office (bad status, missing agent or skill) are found only when an agent trips on them. Before spending SDK credit on live runs (T-024), Merwyn and the team need to see what a run would do.

**In scope**
- Load `offices/<id>/` per `engine/schema/office.md` (v0): office.yaml, org.yaml, workflow.yaml, agents/*.md, skills/, backlog/T-*.md; theme is optional and may be ignored.
- Validate and report errors with file and reason, exit 1.
- Dry-run: pick the next eligible task and print what a run would do.
- Tests and a short README with the commands.

**Out of scope**
- Any Agent SDK call, live agent run, token or cost logging, or budget enforcement (T-024 remainder).
- Changing task status or owner, writing board.md, git or PR actions.
- Validating `extends` base agents beyond existence, theme rendering, the app, BAU workflows, and other offices' special cases.
- Reading `workspaces.yaml` projects or brains.

**Open questions**
- Fang (architect): language and layout for the engine (Python beside scripts/ or TypeScript). Non-blocking for spec; settle in Design.
- Janice: priority and eligibility rules above (priority, then id; dependencies done) are the PM's proposal; confirm at spec approval.
- Janice: T-024 and T-019 parent files could not be read in this pass (filenames not found); parent-level constraints are unchecked.

— Emmy (pm)

## Spec approval
- Approved for design. Pick rule (priority, then lowest id, dependencies done) confirmed. Parent tasks are T-019 / T-024 in backlog/. — Janice (pmo)

## Design

## Build notes

## Review log

## Decision

## Open questions
- Which language and layout for the engine (Python beside scripts/ or TypeScript)? Owner: Fang (architect).
