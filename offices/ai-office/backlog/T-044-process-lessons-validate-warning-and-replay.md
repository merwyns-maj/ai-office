---
id: T-044
title: "Sprint 2 process lessons: validate warns on missing defaults, pr-workflow replay not rebase"
phase: 7-ways-of-working
status: review
priority: P1
owner: reviewer
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
**Approach** (three parts; part 1 changes logic, parts 2 and 3 are wording-only)

1. **R-11 warning** (logic). `base/defaults.yaml` is read in two places today, both silently treating a missing file as "no defaults": `scripts/build_agents.py` (via `_fm.read_flat`, which returns `{}`) and `engine/runtime/loader.py` `load_office` (`if defaults.is_file():`). Both get the same warning. Q3: `scripts/board.py` does not read `defaults.yaml`, skills or agents (it reads only `workflow.yaml` and `backlog/`), so it needs no warning and stays untouched.
   - Files: `scripts/build_agents.py`, `engine/runtime/loader.py`, `engine/runtime/__main__.py`, `tests/test_build_agents.py`, `tests/test_loader.py`.
2. **R-12 replay rule** (wording). `offices/ai-office/skills/pr-workflow/SKILL.md`: new section "Replay, not rebase (shallow clones)", and the two existing rules point to it.
3. **Planning-only widening** (wording, merge rule). `offices/ai-office/workflow.yaml` `merge` block, and the matching sentence in pr-workflow's "board.md (generated)" section.

**Interfaces**

Part 1, warning text, identical in both tools, printed to **stderr**, never counted as a problem, exit code unchanged:
```
warning: base/defaults.yaml is missing, so agents will get no base skills
```
- `build_agents.py`: module constant `DEFAULTS_MISSING = "warning: base/defaults.yaml is missing, so agents will get no base skills"`. In `build()`, after the office check and before the agent loop, once per run: `if not (root / "base" / "defaults.yaml").is_file(): print(DEFAULTS_MISSING, file=sys.stderr)`. Not inside `skill_paths` (that runs once per agent and would repeat it).
- `loader.py`: add `warnings: list = field(default_factory=list)` to `Office` (list of `Problem`). In `load_office`, the `if defaults.is_file():` gets `else: office.warnings.append(Problem("base/defaults.yaml", "is missing, so agents will get no base skills"))`. `Problem.__str__` gives `base/defaults.yaml: is missing, ...`; to keep one text, `__main__` prints `f"warning: {w.file} {w.message}"`, which yields exactly the line above.
- `__main__.py` `main()`: right after `_load_and_validate`, `if office is not None: for w in office.warnings: print(f"warning: {w.file} {w.message}", file=sys.stderr)`, for both `validate` and `dry-run`. stdout and the exit code are as today (the `RealOffice.test_validate_clean` regex on stdout still holds).
- Tests:
  - `tests/test_build_agents.py` (class `Build`, uses `TempRepo`): `test_missing_defaults_warns`: unlink `self.root/"base/defaults.yaml"`, run `self.build()` under `redirect_stderr`, assert the exact line is in stderr and no `SystemExit`. `test_defaults_present_no_warning`: same without unlinking, assert `"base/defaults.yaml is missing"` not in stderr.
  - `tests/test_loader.py`: `Defects.test_missing_defaults_warns_only`: unlink `self.c.root.parents[1]/"base/defaults.yaml"`; `code, out, err = run("validate", str(self.c.root))`; assert `code == 0`, the line in `err`, and `out` ends with the usual `ai-office: OK` line. `RealOffice.test_real_repo_no_defaults_warning`: `run("validate", "ai-office")`, assert `"defaults.yaml is missing"` not in `err`. Do not add a test that runs `build_agents.py` on the real repo (it rewrites `.claude/agents/`); the TempRepo present case covers build.

Part 2, pr-workflow text. Add this section after "Rules":
````
## Replay, not rebase (shallow clones)
Our clones are shallow (`--depth=5`). There `git rebase` can report add/add conflicts on files only your branch added, because the shared base commit is missing. Do not resolve those. Replay instead:

```bash
b=t-xxx-short-name
git fetch --depth=50 origin main
git log --oneline --reverse origin/main..$b   # must list only this task's commits; if not: git fetch --deepen=50 origin main, check again
commits=$(git rev-list --reverse origin/main..$b)
old=$(git ls-remote origin refs/heads/$b | cut -f1)
git branch -f $b-backup $b
git checkout -B $b origin/main
git cherry-pick $commits                      # a conflict here is real: resolve it, then git cherry-pick --continue
git -c push.negotiate=true push --force-with-lease=$b:$old origin $b
git branch -D $b-backup                       # once the PR shows the new head
```
- Same branch name, so the open PR and `pr: <n>` stay. `--force-with-lease=$b:$old` refuses the push if someone else pushed to the branch since `$old`.
- Force-push only a `t-xxx` task branch, only this way. Never `main`, never a `sprint-NN-*` branch with someone else's commits.
- If GitHub rejects the force push (branch protection), push as `$b-r2`, open a new PR, close the old one with a link to the new one, and update `pr:`.
- If you resolved a real conflict after a Reviewer PASS, say so in the PR; the Reviewer re-checks the changed files before the PMO merges.
````
Replace in "Rules":
- "`false` means a conflict: rebase on main and push again." with "`false` means a conflict: replay the branch onto fresh main and push again (see Replay, not rebase)."
- "If a push is rejected as too large: `git fetch --depth=50 origin main` and rebase onto `origin/main`." with "If a push is rejected as too large: replay the branch onto `origin/main` (see Replay, not rebase); its first step fetches with `--depth=50`."
- "Never force-push `main`." becomes "Never force-push `main`; task branches only as in Replay, not rebase."

Part 3, workflow.yaml `merge` block becomes (validate must still pass; no `:` inside the flow list items):
```yaml
  # Exception (Janice, T-042; widened in T-044): planning-only PRs from sprint-NN-* branches may merge
  # without a Reviewer; the PMO merges them. Planning-only means every change is one of:
  #   - sprints/, board.md, raid.md
  #   - a new backlog task file at status todo or spec
  #   - on an existing task file, only the frontmatter keys status, owner, depends_on (status never set to done)
  #     and appended dated decision notes, written by the PMO at sprint plan or close
  # Anything else (Spec, Design, Build notes, Review log or Decision text, Done when, other frontmatter keys,
  # any other path) needs a Reviewer PASS.
  requires_planning_only: [PR open from a sprint-NN-* branch, changes limited to sprints/, board.md, raid.md and plan-stage task edits (see comment)]
```
pr-workflow "board.md (generated)", replace "Planning-only sprint PRs need no Reviewer (workflow.yaml `merge.requires_planning_only`); the PMO merges them." with: "Planning-only sprint PRs need no Reviewer; the PMO merges them. Planning-only is defined once, in the comment on `merge.requires_planning_only` in workflow.yaml: sprints/, board.md, raid.md, new task files at todo or spec, and on existing tasks only status, owner, depends_on (never to done) plus dated PMO decision notes. Any other change needs a Reviewer PASS." Step 5's comment ("planning-only sprint PRs excepted, see below") stays as is; it already points to this section.

**Decisions on the open questions**
- Q2: same branch name plus `--force-with-lease=<branch>:<sha>` (PMO preference), task branches only. I see one problem with plain `--force-with-lease`: with no expected sha it compares against the remote-tracking ref, which a later `git fetch` silently updates, so it can overwrite someone's push. The explicit `:$old` from `ls-remote` fixes that. Fallback name `-r2` only if GitHub refuses force pushes (unknown today; nothing in this repo sets branch protection).
- Q3: one warning per tool. `board.py` does not load offices through the loader and never touches skills, so it gets none.
- `status` may not be set to `done` in a planning-only PR, since done needs Reviewer PASS (workflow.yaml `gates`); this is inside Janice's Q1 answer, stated so the two paths cannot contradict.

**Risks**
| Risk | Handling |
|---|---|
| Warning on stdout would break the `RealOffice` stdout regex and parsers of `validate` output | stderr only; tests assert stdout unchanged |
| Warning repeats per agent in build | printed once in `build()`, not in `skill_paths` |
| `origin/main..$b` lists main's commits when history is too shallow | the rule says to read the list first and deepen; `-backup` branch keeps the old head until the PR updates |
| Force push clobbers another push | `--force-with-lease` with an explicit sha |
| Widened planning-only path lets content through unreviewed | allowed edits are enumerated; anything else needs PASS; `done` excluded |
| workflow.yaml flow list misparsed | no colons in items; engineer runs `python -m engine.runtime validate ai-office` and the full tests |

**Flags.** None for Compliance (no prod, money movement or personal data).

**Build checks.** `python -m unittest -v` exits 0; `python scripts/build_agents.py ai-office` prints no warning and no `.claude/agents/` diff (no agent file changes); `python -m engine.runtime validate ai-office` is OK with empty stderr.

**Decision record draft (for Curator)**
```
Decision: In shallow clones, task branches are updated by replaying their own commits onto fresh main (cherry-pick) and pushing the same branch with --force-with-lease=<branch>:<sha>; never main.
Context: R-12, Sprint 2: git rebase in --depth=5 clones gave false add/add conflicts; replay worked.
Options: A, same name + force-with-lease (PR and pr: stay; needs force push on task branches); B, new branch name + new PR (no force push; PR history splits, pr: changes); C, unshallow clones (slow, large fetches that were already rejected).
Chosen: A, with explicit lease sha, because it keeps one PR per task and the lease stops clobbering. B is the fallback if GitHub refuses force pushes.
Consequences: pr-workflow allows force push on t-xxx branches only; Reviewer re-checks if a real conflict was resolved after PASS. Also in T-044: missing base/defaults.yaml warns (stderr, exit unchanged) in build_agents and validate; planning-only PRs may include plan-stage task edits as defined in workflow.yaml.
Links: T-044, R-11, R-12, T-042, PR #17, PR (tbd)
```

— Fang (architect)

## Approvals (PMO)
- Spec approved. Q1: plan-stage task files = new task files at status todo or spec, plus status, owner, depends_on and dated decision notes on existing tasks, written by the PMO at sprint plan/close (as in PR #17, which also touched sprints/, raid.md, board.md). Q2 and Q3 are Fang's design calls; PMO preference for Q2: keep the same branch name and push with --force-with-lease (task branches only, never main). — Janice (pmo)

## Build notes
**What changed**
- `scripts/build_agents.py`: `DEFAULTS_MISSING` constant; `build()` prints it once to stderr when `base/defaults.yaml` is absent. Exit code unchanged.
- `engine/runtime/loader.py`: `Office.warnings`, filled when defaults.yaml is missing. `engine/runtime/__main__.py` prints `warning: <file> <message>` to stderr for validate and dry-run. stdout and exit code unchanged. `board.py` untouched (it never reads defaults.yaml).
- Tests: `test_missing_defaults_warns`, `test_defaults_present_no_warning` (test_build_agents.py); `test_missing_defaults_warns_only`, `test_real_repo_no_defaults_warning` (test_loader.py).
- `pr-workflow/SKILL.md`: new "Replay, not rebase (shallow clones)" section (`--force-with-lease=$b:$old`, backup branch, `-r2` fallback); the mergeable-false and too-large rules point to it; "Never force-push main" clarified; board.md section now points to the single planning-only definition.
- `workflow.yaml`: planning-only defined once in the `merge` comment (sprints/, board.md, raid.md, new task files at todo/spec, PMO edits to status/owner/depends_on never to done, dated notes; anything else needs Reviewer PASS). `requires_planning_only` list updated.

**How to verify**
```
python3 scripts/build_agents.py ai-office   -> ai-office: built 7 agents -> .claude/agents/ (...); no warning; git status shows no .claude/agents diff
python3 -m engine.runtime validate ai-office -> ai-office: OK — 7 agents, 5 stages, 45 tasks, 15 skills (stderr empty)
python3 -m unittest -q                       -> Ran 148 tests in 5.276s / OK
```
(The unittest run also prints a `demo: built 1 agents` line from an existing test; not new.)

**Done when -> evidence**
- R-11 warning, exit code unchanged: both tools; tests assert exit 0 and the exact line.
- R-11 tests present/absent/real repo: the four tests above, all pass.
- R-12 rule and two pointers: pr-workflow sections "Rules" and "Replay, not rebase".
- Planning-only widening + no wider Reviewer-free path: workflow.yaml comment, pr-workflow board.md section; validate OK.
- No contradictions: planning-only defined only in workflow.yaml, pr-workflow summarises and points to it. build_agents clean, tests exit 0.

**Deviations.** None from the design. I did not exercise the replay commands against a real shallow clone; the text is as designed.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
