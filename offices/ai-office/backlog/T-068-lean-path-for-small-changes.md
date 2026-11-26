---
id: T-068
title: "Lean path for small changes (one design step, then build and review)"
phase: 0-office
status: build
priority: P1
owner: reviewer
where: repo
project: ai-office
depends_on: []
pr: PRNUM
---

> Merwyn, 26 Nov 2026 19:54 WIB, on Janice's improvement list: "Just start these all no worries except 6" (6 = the items waiting on him).

## Facts (Janice)
- T-066 (docked chat) took 7 agent runs and about 520k tokens: Emmy spec, Dinda UX, Fang design, Sebastian build, Cahyani review, Sebastian rework, Cahyani review 2.
- Stages and gates live in `offices/ai-office/workflow.yaml`; procedures in the pmo-playbook and pm-playbook skills.

## Done when
- [ ] workflow.yaml and the playbooks define a lean path with an entry rule a PMO can apply (for example: one surface, no new data, no compliance flag, no human gate), and what it skips (for example: a separate spec run; the Architect writes a short spec plus design)
- [ ] Review stays required (Reviewer PASS before merge); compliance flags and human gates still force the full path
- [ ] `python -m engine.runtime validate ai-office` accepts the new workflow; tests cover the rule

## Spec
**Problem.** A small UI change (T-066) went through the full path: 7 runs and about 520k tokens (Facts above). Small, low-risk changes need a shorter path, without weakening review or the gates.

**In scope**
- A lean path in `workflow.yaml` and in the pmo-playbook and pm-playbook: an entry rule the PMO can apply from the task file alone, and the steps it skips.
- Entry rule, all must hold: one surface (for example one page or one module); no new data or storage; no compliance flag; no human gate item (`human_gates` in workflow.yaml); the PMO writes "lean" with the reason in the task. Final thresholds are the Architect's.
- Skipped on the lean path: the separate PM spec run; the Architect writes a short spec plus design in one step. A Designer consult stays available when the change has UI.
- Unchanged: PMO approval of the spec, Reviewer PASS before merge, PMO merges, the Done-when checks.
- Escape: if the Architect, Reviewer or PMO finds the entry rule was wrong, the task goes back to the full path.

**Out of scope**
- Any change to the Reviewer gate, `human_gates`, compliance, or who merges.
- Lean path for tasks that touch company repos, prod, personal data or money.
- Changing past tasks or the token ledger format.

**Done when (reviewer can verify)**
1. `workflow.yaml` defines the lean path and the entry rule; `python -m engine.runtime validate ai-office` exits 0.
2. The lean path still ends in Reviewer PASS before merge: a test or schema check fails if the lean path has no review stage or no PASS gate.
3. A task with a compliance flag, or any `human_gates` item, is forced to the full path: a test shows the rule rejects it with the reason.
4. Tests cover at least: a qualifying task, one failing each entry condition (surface, new data, compliance flag, human gate), and an escape back to the full path.
5. pmo-playbook and pm-playbook describe when to use lean, who decides (PMO), and the escape; T-066 is quoted as the example (7 runs, about 520k tokens).
6. All tests, golden and `python scripts/board.py ai-office` pass; no other workflow rule changed.


**Spec approved** (Janice, 26 Nov 2026 20:05 WIB).

## Design
**Approach.** A data-only `paths.lean` block in `workflow.yaml`; the PMO records lean as an appended dated note in the task body (already planning-only, so the merge rule is unchanged); `engine/runtime/loader.py` gets one pure check used by `validate`. Files: `workflow.yaml`, `loader.py`, `tests/test_loader.py` (+ fixtures), pmo-, pm- and architect-playbook. Stages, gates, `human_gates`, merge and consults are not touched.

**workflow.yaml** (after `consults`):
```yaml
# Lean path (T-068): small changes skip the separate PM spec run. PMO decides at plan, from the task file.
paths:
  lean:
    skips: [spec]                 # todo -> design; the Architect writes a short Spec + Design in one run
    spec_by: architect            # must own the first stage not skipped
    spec_approver: pmo            # must equal the spec gate approver; PMO approves before build
    entry: [one_surface, no_new_data, no_compliance_flag, no_human_gate]
    never_skips: [design, build, review]
```
**Record (PMO, at plan).** `> Lean (Janice, pmo, 2026-11-27): <one surface>; no new data; no compliance flag; no human gate. Reason: <why>`. **Escape** (Architect, Reviewer or PMO): `> Full path (<name>, <agent>, <date>): <condition that failed>`, then the PMO sets status `spec`, owner `pm`. The last Lean/Full note wins.

**validate, new rules.** (5c, workflow) `paths` optional; only key `lean`; `skips` are stage ids and none is in `never_skips`; `review` stage and `{stage: done, approver: reviewer}` gate must exist when `paths` is present; `entry` is exactly the four ids; `spec_by` owns the first unskipped stage; `spec_approver` equals the spec gate approver. (7b, task) `loader.lean_problems(office, task) -> list[str]` (empty = qualifies) for a task whose last note is Lean: note has all four phrases; surface text has no `,`, ` and ` or `+` ("more than one surface"); `project` in office.yaml `projects` and `where` in (code, repo) ("company/chat/office work: full path"); no line matching `^(- )?Compliance: (flagged|PASS|BLOCK)` ("compliance flagged: full path"); no Open questions line containing `human gate` ("human gate: full path"); status not `spec`. Each reason is a validate problem, so `validate` exits 1.

**Playbooks.** pmo-playbook new §2a "Lean path" (5 lines): when (all four conditions), who decides (PMO), the note, the escape, "PMO still approves the Spec and Reviewer PASS is still required", example "T-066 took 7 runs and about 520k tokens". pm-playbook §0 one line: lean tasks have no PM run unless escaped. architect-playbook §2 one line: on lean, write a short Spec (problem, in/out, Done when) above the Design, then owner `pmo` for approval; when you flag Compliance write `Compliance: flagged`.

**Open questions answered (office).** One surface = PMO judgement, bounded by the text check above (one page or one module plus its tests). Saving: the PMO compares the first lean task's ledger runs and tokens with T-066 at sprint close and writes it in the sprint file.

**Tests** (`test_loader.py`): live workflow validates; fixture with `skips: [review]`, `[build]`, missing reviewer gate, unknown entry id each fail; qualifying task passes; one task per failing condition (two surfaces, missing "no new data", `Compliance: flagged` line, `human gate` question, `where: company`) fails with its reason; Lean then Full note = no lean checks, status `spec` OK; Lean task at `spec` fails. Golden and `board.py` pass.

**Risks.** Text checks are a floor, not proof: Architect and Reviewer escape. Conflict with T-070's `workflow.yaml` comment edit: build one after the other. Not flagged for Compliance (process text only).

**Decision record draft.** Decision: lean path = skip only the PM spec run, recorded as a PMO dated note. Options: new `lean` stage (changes status set and board); frontmatter `path:` key (needs a merge-rule change); appended note (chosen: no merge-rule change, checkable). Consequences: one fewer run per small task; text rules need upkeep.
— Fang (architect)

## Build notes
**Changed.** `workflow.yaml`: `paths.lean` block exactly as in the Design. `engine/runtime/loader.py`: validate rule 5c (paths checks) and 7b via `lean_problems(office, task)`; each reason is a validate problem. pmo-playbook §2a, pm-playbook (one paragraph before §1), architect-playbook (one paragraph before §3). `tests/test_loader.py`: class `LeanPath` (19 tests: live workflow; skips review, build, unknown stage; no reviewer gate; no review stage; unknown entry id; spec_by; spec_approver; extra path key; qualifying task; two surfaces; missing "no new data"; `Compliance: flagged`; human gate question; `where: company`; Lean task at spec; Lean then Full note at spec passes).
**Verify.** `python -m unittest discover -s tests` exit 0 (407 tests); `python -m engine.runtime validate ai-office` exit 0 (71 tasks, no problems); `python scripts/board.py ai-office` exit 0, board.md discarded.
**Deviations.** None from the Design. No `agents/` file was edited, so `build_agents.py` was not run. The Lean-note regex only matches a note at line start (`> Lean (...)`), so the example inside backticks in this task's Design is not read as a note. The "no new data / no compliance flag / no human gate" phrase check applies to the note text; the surface check reads the text before the first `;`.
Not covered by a test: the Open questions "human gate" scan only looks below `## Open questions`.
— Sebastian (engineer)

## Review log

## Decision

## Open questions
- Is a task "one surface" decided by the PMO's judgement or by a file-count rule? For the office (Architect proposes, PMO approves).
- Expected saving is unmeasured (T-066: 7 runs, about 520k tokens; the lean path would drop at least the PM run). Measure on the first lean task? For the office.
