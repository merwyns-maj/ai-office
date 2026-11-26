---
id: T-068
title: "Lean path for small changes (one design step, then build and review)"
phase: 0-office
status: done
priority: P1
owner: pmo
where: repo
project: ai-office
depends_on: []
pr: 64
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

### Rework 1
**Fixed (Review 1 point 1).** Rule 5c in `engine/runtime/loader.py` now always rejects `review` or `build` in `paths.lean.skips` (hard-coded, independent of `never_skips`) and requires `never_skips` to contain `build` and `review`. Tests added in `LeanPath`: `skips: [spec, review]` with `never_skips` edited; same with `never_skips` removed; `skips: [spec, build, review]` with `never_skips: []`.
**Floor notes hardened.** `Compliance:` line now matches bold (`**Compliance:** flagged`); `/` counts as a surface separator. One test covers both.
**Verify.** `python -m unittest discover -s tests` exit 0 (411 tests); `validate ai-office` and `board.py ai-office` run, board.md discarded.
**Not done.** An Open question about production without the words "human gate" still passes (floor; escape covers it).
— Sebastian (engineer)

## Review log
**Review 1 (Cahyani, 26 Nov 2026): REJECT.** One spec item fails (Done when 2). Everything else passes.

Commands run on `t-068-lean-path` at b525c17:
- `python -m unittest discover -s tests`: `Ran 407 tests ... OK`, exit 0.
- `python -m engine.runtime validate ai-office`: `ai-office: OK — 8 agents, 5 stages, 71 tasks, 18 skills`, exit 0.
- `python scripts/board.py ai-office`: exit 0 (board.md discarded).

Done-when checks (spec numbering):
1. PASS. `paths.lean` with the entry rule is in `workflow.yaml` (lines 14-21), and validate exits 0.
2. **FAIL.** The lean path itself can skip review and validate still passes. In a temp copy:
   - removing the `{stage: done, approver: reviewer}` gate gives "paths needs a gate ... (Reviewer PASS before merge)", exit 1 (good);
   - removing the `review` stage gives "paths needs a 'review' stage", exit 1 (good);
   - `skips: [spec, review]` with `review` taken out of `never_skips` (or `never_skips` deleted) gives `ai-office: OK`, **exit 0**;
   - `skips: [spec, build, review]` with `never_skips: []` gives `ai-office: OK`, **exit 0**.
   So the protection is only as strong as the editable `never_skips` list. The review-stage and gate checks look at the whole workflow, not at the lean path. `test_skip_review_rejected` passes only because `never_skips` still lists review. With `[review]` alone, the failure comes from a `spec_by` mismatch, not from a review check.
3. PASS. With a `Compliance: flagged` or `- Compliance: BLOCK` line, validate exits 1 with "compliance flagged: full path". A "human gate" line under Open questions exits 1 with "human gate: full path". `where: office` and `where: chat` exit 1 with "company/chat/office work: full path". "X and Y" as the surface exits 1 with "more than one surface: full path".
4. PASS. `LeanPath` covers a qualifying task, two surfaces, missing "no new data", `Compliance: flagged`, a human-gate question, `where: company`, a Lean task at spec, and Lean then Full note.
5. PASS. pmo-playbook §2a covers when to use lean, who decides (PMO), the note format, the escape, what still holds, and the T-066 figures (7 runs, about 520k tokens). pm-playbook has its paragraph, and architect-playbook has its line. A PMO can follow it from the task file alone.
6. PASS for tests and board. No other workflow rule changed: the diff touches only the new `paths` block in workflow.yaml. `gates`, `human_gates`, `merge` and pr-workflow are untouched. The merge and planning-only rules are not loosened, because the PMO's Lean note plus todo->design counts as "status, owner, dated PMO decision notes", which is already planning-only.

**Fixes needed (to pass Done when 2):**
- In 5c, reject any `paths.lean.skips` entry that is `review` or `build`, hard-coded, whatever `never_skips` says. Also require `never_skips` to contain `review`. Either one closes the hole; doing both is cleanest.
- Add a test for `skips: [spec, review]` with `never_skips: [design, build]`, and one for a missing `never_skips`. Both should exit 1 with a review-specific message.

**Notes (non-blocking):**
- The text checks are a floor, as the Design says: `**Compliance:** flagged`, surfaces split by `/`, and an Open question about production that doesn't use the words "human gate" all pass. The Architect and Reviewer escape covers these. Consider widening the compliance regex to allow `**`.
- If the whole `paths` block and the reviewer gate are both removed, validate passes, because the gate check only runs when `paths` is present. Behaviour before this PR was the same, so this is out of scope. A later task could make the done/reviewer gate always required.
— Cahyani (reviewer)

**Review 2 (Cahyani, 26 Nov 2026): PASS.** The Review 1 REJECT point is fixed. All six Done-when items pass.

Commands run on `t-068-lean-path` at bb4e4a4:
- `python -m unittest discover -s tests`: `Ran 411 tests ... OK`, exit 0. Golden tests are part of this suite.
- `python -m engine.runtime validate ai-office`: `ai-office: OK — 8 agents, 5 stages, 71 tasks, 18 skills`, exit 0.
- `python scripts/board.py ai-office`: exit 0 (board.md discarded).

Review 1 point (Done when 2), re-tested in a temp copy of the repo. Each case below gives validate exit 1:
- `skips: [spec, review]` with `never_skips: [design, build]`: "must not skip 'review' (hard rule ...)" and "never_skips must contain 'review'".
- `skips: [spec, review]` with `never_skips` removed: the same two messages, plus "must contain 'build'".
- `skips: [spec, build, review]` with `never_skips: []`: hard-rule messages for both build and review.
- `skips: [spec, build]` with `never_skips: [design, review]`: hard-rule message for build.
- `never_skips` removed, or missing build, or missing review (with `skips: [spec]`): "never_skips must contain ...".
- Case and whitespace variants (`Review`, `REVIEW`, `" review"`, `"review "`, `never_skips: [Design, Build, Review]`): "is not a workflow stage" and/or "must contain".
- Other shapes: scalar `skips: review`, scalar `never_skips: "design, build, review"`, block-list skips, a flow-map `lean: {...}`: all rejected.
- YAML anchor/alias (`&s` / `*s`): rejected by miniyaml ("unsupported YAML construct"). Duplicate `skips` or `lean` keys: "duplicate key". An extra path (`fast:`) or `Lean:`: "only the key 'lean'".
- Renaming the review stage to `qa` and skipping it: "paths needs a 'review' stage". Gate approver `Reviewer`: rejected.

Two edits still give exit 0, but neither makes the lean path skip review or build:
- An unknown sibling key such as `skip: [spec, review]` next to `skips: [spec]`. No code reads it. `grep` shows `skips` is read only in loader.py 5c, and `paths.lean.skips` still keeps review.
- Renaming `paths:` to `Paths:`. This removes the lean path; it does not loosen it. Unknown top-level keys were accepted before this PR too (`foo_bar: [review]` also gives exit 0).

Done-when checks:
1. PASS. `paths.lean` is in workflow.yaml, and validate exits 0.
2. PASS. The hard-coded review/build rule and the required `never_skips` entries are covered by the three new `LeanPath` tests, and they hold against every variant listed above.
3. PASS. Re-run with a probe task: `Compliance: PASS`, `**Compliance:** flagged`, `**Compliance: flagged**` and `- **Compliance:** BLOCK` all exit 1 with "compliance flagged: full path". The human-gate case was confirmed in Review 1 and the code is unchanged.
4. PASS. `LeanPath` covers the qualifying task, each failing condition, and the escape. `test_bold_compliance_and_slash_surface` was added.
5. PASS. The playbooks are unchanged since Review 1 (the rework touched only loader.py, test_loader.py and this file).
6. PASS. Against origin/main, workflow.yaml changes only by the new `paths` block. `gates`, `human_gates`, `merge` and pr-workflow are untouched.

Hardenings: `**Compliance:** flagged` exits 1. "chat page/settings page" and "chat page / settings page" exit 1 with "more than one surface".

**Notes (non-blocking):**
- Text checks are still a floor. These pass: `compliance: flagged` (lower case), `Compliance:  flagged` (two spaces), `* Compliance: flagged`, and surfaces joined with `&`. The Architect and Reviewer escape covers them.
- Consider rejecting unknown keys inside `paths.lean`, so that a stray `skip:` key can't mislead a human or agent reading the file.
- External skills design:accessibility-review and data:validate-data were not used: there is no UI and no dataset in this change.
— Cahyani (reviewer)

## Decision
Merged after Cahyani's Review 2 PASS (Janice, 26 Nov 2026). The lean path skips only the separate spec step; build and review can never be skipped (hard rule 5c). Follow-ups noted, not tasks yet: text checks are a floor (lower-case `compliance:`, `&` surfaces), unknown keys inside `paths.lean`, and the reviewer-gate check when the whole `paths` block is removed.

Recorded: offices/ai-office/decisions/2026-11-sprint-07.md, D4. — April (curator)

## Open questions
- Is a task "one surface" decided by the PMO's judgement or by a file-count rule? For the office (Architect proposes, PMO approves).
- Expected saving is unmeasured (T-066: 7 runs, about 520k tokens; the lean path would drop at least the PM run). Measure on the first lean task? For the office.
- Follow-up (out of scope here): if the whole `paths` block and the reviewer gate are both removed, validate passes; make the done/reviewer gate always required. For the office.
