---
id: T-032
title: "Adoption metrics (hours saved, reject rate, turnaround)"
phase: 7-ways-of-working
status: build
priority: P2
owner: reviewer
where: chat
project: ai-office
depends_on: []
pr: https://github.com/merwyns-maj/ai-office/pull/30
---

## Done when
- [ ] Tracked monthly

## Spec

**Problem.** Merwyn cannot tell from numbers whether the office is getting faster or cleaner: Sprint 1's retro says per-stage timestamps "were not recorded", and reject, escalation and first-time-approval counts live only in prose. Today "tracked monthly" has no data, no owner and no output.

**In scope**
- A stdlib-only script, run as `python scripts/metrics.py <office>`, that reads this repo's own history (git log of the office's backlog files, PR merge times, Review log and Decision text, sprint files) and writes one markdown report.
- Metrics: turnaround per stage and per task; reject rate (Review log REJECT entries, with compliance BLOCKs counted separately); escalations to Merwyn; specs approved first time; tasks per sprint.
- Handling of a shallow clone (history missing): the report states which numbers came from a partial history and which are not available. It never invents a value.
- Tests for the script and a first report covering Sprints 1 to 4 (Sprint 5 excluded, it is still running).
- Hours saved appears as a row showing "not set" until Merwyn supplies a per-task-type estimate.

**Out of scope**
- Fixing history that was never recorded (Sprint 1 has no per-stage timestamps); the report marks it "not recorded".
- Dashboards, charts, the 3D office page, cost or budget tracking.
- Choosing the estimate for hours saved, or any new frontmatter field.
- Company data of any kind (the report holds task ids and counts only).

**Done when**
- [ ] `python scripts/metrics.py ai-office` exits 0 and writes a markdown report under `offices/ai-office/metrics/`, naming the commit it was run at.
- [ ] The report has one row per Sprint 1 to 4 and per task, with columns for each metric above; where a value cannot be derived it reads "not recorded", never blank or 0.
- [ ] Spot check by a reviewer: T-040 shows one compliance BLOCK and no Reviewer REJECT; T-048 shows two Reviewer REJECTs and one escalation to Merwyn; Sprints 1 to 4 show 2, 3, 3 and 3 tasks (Sprint 1 also lists T-012 and others merged in its window only as a footnote, not as sprint tasks).
- [ ] Run in a shallow clone (`git rev-parse --is-shallow-repository` prints `true`), the script exits 0 and the report carries a visible "partial history" notice; it does not exit with a git error.
- [ ] The hours-saved row reads "not set" and names who supplies it (Merwyn).
- [ ] Tests pass (`python -m unittest` or the repo's test command), including a case with a fixture history and one with a missing-history case.
- [ ] A grep of the report and fixtures finds no email, run of 10+ digits, or name from workspaces.yaml outside the personal org.
- [ ] Documented: a short "how to run monthly" in the script's docstring or a README line, so the monthly step needs no other instructions.

**Open questions**
- Hours saved per task type: Merwyn gives the estimate. Not blocking; the report shows "not set".
- Is "specs approved first time" read from the PMO approval note under the dedicated heading (Sprint 2 fix)? Fang to confirm what is machine-readable; older tasks may need "not recorded". Not blocking.
- Where should the report live, `offices/ai-office/metrics/` or the sprint file? Spec assumes metrics/; Janice to confirm. Not blocking.
- Shallow clone: I could not run `git rev-parse --is-shallow-repository` (no Bash in this session), so it is unverified here. Fang to check; the design must work either way (gh API for PR times or `git fetch --unshallow` are Fang's choice, and `gh` may be unavailable in some sandboxes).
- Sprint 1 task count in the spot check is from the sprint file (2 tasks) and needs a reviewer re-check against history.

— Emmy (pm)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: report lives in offices/ai-office/metrics/ (one file per run, e.g. 2026-11.md); "approved first time" definition is Fang's call from what the task files actually hold (the "## Approvals (PMO)" heading exists from Sprint 2 on; earlier tasks read "not recorded"). Hours saved: asked of Merwyn at sprint close, "not set" until then. — Janice (pmo)

## Design

**What history exists (checked 26 Nov 2026, Fang).**
- The worktree is a shallow clone: `git rev-parse --is-shallow-repository` prints `true`, and `git log` reaches 11 commits (back to `bf643e3`, Sprint 3 plan). A full clone of origin has 28 commits on main, all squash merges, so main alone never shows the stages inside a task.
- The stages are in the PR branch commits. `git ls-remote origin 'refs/pull/*/head'` lists PR heads (PRs #1 to #27), and after `git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'` (tested in a scratch clone) `git log -p` on a task file shows every frontmatter `status:` change with its time. Example, T-048 on `pr/25`: todo, design 23:40, build 23:42, review 00:02, build 00:10, review 00:14, build 00:17 (escalated), done 09:01 (+07:00).
- Some tasks never had `status: spec` (T-048 went from todo straight to design in one commit). Their spec time reads "not recorded".
- Review log wording that a parser can read, tested on all 49 task files: Reviewer verdicts are lines like `- PASS —`, `- REJECT —`, `Review 1 of PR #25 (...): REJECT (...)` and `Verdict: PASS`. Compliance verdicts are `Compliance: PASS | PASS with conditions | BLOCK` in the Review log or in a `## Compliance` section (T-046). The prototype regexes below give T-040 0 REJECT, compliance BLOCK then PASS (1 BLOCK), 1 escalation; T-048 2 REJECT, 1 escalation; T-043 PASS; T-046 PASS with conditions. That matches the spot check.
- Approval headings: `## Approvals (PMO)` is used in 10 task files from Sprint 2 on (T-014 onward). T-039 and T-040 use `## Spec approval`. Tasks from before Sprint 1 have neither.
- Sprint files: each has `## Tasks (in order)` with numbered `[T-xxx](...)` lines, giving 2, 3, 3, 3 for Sprints 1 to 4. Closed sprints have a `## Retro` or `## Close` heading, and Sprint 5 has neither. Main commit subjects mark the sprint windows: `Sprint N plan ... (#n)`, then `Sprint N close ... (#n)`. Sprint 1 has no close commit; it was closed in `Sprint 2 plan: ...; close Sprint 1 (#12)`.
- Fact for the spot check: in the Sprint 1 window (Sprint 1 plan at 21:35:45 to Sprint 2 plan at 22:12:08, +07:00), the only merge outside the sprint list is T-012 (#10). The Sprint 1 retro also names T-037 and T-038 (#7), but #7 merged at 21:33:22, before the plan. The footnote follows merge times and lists T-012 only.

**Approach**
- New `scripts/metrics.py` (stdlib only). It reads git through `subprocess` and the task and sprint files directly, writes one markdown report, and never fetches or writes to git.
- New `tests/test_metrics.py`. The first report, `offices/ai-office/metrics/2026-11.md`, is generated from a fully fetched clone and committed.
- Reused: `scripts/_fm.py` `split()` for frontmatter. Stage ids come from `scripts/board.py` `stages()`; board.py's `main` is behind `__name__`, so importing it is safe. `engine/runtime/events.py` `DATA_PATTERNS`, `PATTERN_KINDS` and `forbidden_terms` serve as the self-check. Nothing is copied.
- PR merge time is the author date of the main squash commit whose subject ends `(#N)`. The script does not need `gh`. Use author dates throughout, because replay-not-rebase (R-12) rewrites committer dates.

**Interface**
```
python scripts/metrics.py <office> [--out PATH] [--repo PATH]
  default --out: offices/<office>/metrics/<YYYY-MM of run date>.md
  exit 0 on success, even with partial or no git history; exit 2 on usage error or office not found
```
The docstring is the monthly how-to. First run `git fetch --unshallow origin`, but only if `git rev-parse --is-shallow-repository` prints true. Then run `git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'`, then `python scripts/metrics.py ai-office`, then commit the report on a `t-xxx` branch. Without the fetches, the script still runs and the report says what is missing.

Functions, each pure apart from `git()`:
- `git(repo, *args) -> str | None`: returns None on any non-zero exit or missing git. It never raises.
- `history_state(repo) -> dict`: `{"shallow": bool|None, "pr_refs": int, "head": short_sha|None}`.
- `status_events(repo, office) -> dict[task_id, list[(datetime, status)]]`: runs `git log --format=%x00%H%x09%aI -p --unified=0 --no-renames HEAD refs/remotes/origin/pr/* -- offices/<office>/backlog/`, takes the task id from the `+++ b/.../T-NNN-*.md` path and the status from each `+status: X` line, then sorts by time and drops consecutive repeats.
- `stage_hours(events, stages) -> dict[stage, float|None]`: for each stage, the sum of (next event minus entry) over every visit, rework included. None if the stage never appears.
- `turnaround_hours(events) -> float|None`: from the first event in any stage other than `todo` to the first `done`.
- `merges(repo) -> list[(datetime, pr_no, subject)]`: from `git log --format=%aI%x09%s HEAD` lines matching `\(#(\d+)\)$`.
- `verdicts(task_text) -> {"reject": int, "block": int, "escalations": int}`: scans only the lines under `## Review log` and `## Compliance`. Reviewer REJECT is `^(?:- )?(?:(?:Review(?: \d+)?\b[^:\n]*|Verdict): )?REJECT\b` on lines that do not start with `Compliance`. Compliance is `^-?\s*Compliance:\s*(PASS with conditions|PASS|BLOCK)\b` (case-insensitive) and counts BLOCK. Escalation is `(?i)\bescalated to Merwyn\b`, one per line.
- `spec_first_time(task_text, events) -> "yes"|"no"|"not recorded"`. With no `## Approvals (PMO)` or `## Spec approval` heading, the value is "not recorded". The value is "no" if the events re-enter `spec` after leaving it, or if the section matches `(?i)spec (not approved|sent back|returned)`. Otherwise it is "yes".
- `sprints(office_dir) -> list[{n, closed, tasks}]`: from `sprints/sprint-NN.md`. `closed` means a `## Retro` or `## Close` heading exists; only closed sprints are reported, which excludes Sprint 5 today.
- `sprint_window(merges, n) -> (start, end)|None`: the start is the subject matching `^Sprint 0?N plan`. The end is the first later subject matching `(?i)^Sprint 0?N close|close Sprint 0?N`, or else the next sprint's plan. Merged task PRs (subject `^T-\d{3}`) inside the window and not in the sprint list become the footnote.

**Report format** (`metrics/2026-11.md`, task ids, counts and times only, no titles because titles can hold company names):
```
# Office metrics: ai-office, run 2026-11-26 at <short sha>
> History: full | PARTIAL HISTORY (shallow clone; N PR refs) | NO GIT HISTORY. <what this blanks out>
## Sprints
| Sprint | Tasks | Window (UTC) | Reviewer REJECTs | Compliance BLOCKs | Escalations to Merwyn | Specs approved first time | Median turnaround (h) |
## Tasks
| Task | Sprint | spec h | design h | build h | review h | Turnaround h | Reviewer REJECTs | Compliance BLOCKs | Escalations | Spec first time |
## Hours saved
| Hours saved | not set: Merwyn supplies a per-task-type estimate |
Footnotes: [1] Also merged in the Sprint 1 window, not a sprint task: T-012 (#10).
How these are measured: <one line per metric, naming its source and that stage times are commit times, not work time>
```
Any value that cannot be derived prints `not recorded`, never blank or 0. A real zero prints `0` only when its source exists, for example a Review log section with no REJECT line. Hours use one decimal. The sha is 7 characters, so no run of 10 or more digits can appear.

**Test plan** (`tests/test_metrics.py`, `unittest`, skipped if `git` is missing; the baseline is 200 tests, all passing)
1. Fixture history: in a temp dir, `git init` a mini repo holding a copied `workflow.yaml`, two sprint files and three tasks. Commit the status changes with fixed `GIT_AUTHOR_DATE`, put one on a `refs/remotes/origin/pr/1` ref, and add squash commits `T-901: x (#1)` and `Sprint 1 plan (#2)`. Assert exact stage hours, turnaround, merge window, footnote, and the sprint row.
2. Missing history: `git clone --depth 1 file://<fixture>`, then run. Expect exit 0, the "PARTIAL HISTORY" notice, and stage cells `not recorded`. Also run in a plain non-git copy and expect exit 0 and "NO GIT HISTORY".
3. Parsers on wording-shaped strings: the REJECT variants, `Compliance: PASS ... BLOCK item` counting as PASS, the escalation line, and both approval headings.
4. Real-file check, which needs no git: on this repo's backlog, T-040 gives 1 BLOCK, 0 REJECT and 1 escalation; T-048 gives 2 REJECT and 1 escalation; the sprint task counts are 2, 3, 3, 3.
5. Data self-check: the generated fixture report and the committed `metrics/2026-11.md` match no `DATA_PATTERNS` entry and no `forbidden_terms(REPO)` term.

**Risks**
| Risk | Handling |
|---|---|
| Stage time is when a commit was made, not when work happened (agents batch their commits) | The report says so under "How these are measured" |
| Review wording drifts and a REJECT is missed | Regexes are tested on the real files; a Review log with a `PASS`/`REJECT` word that matches no pattern gives a stderr warning naming the task |
| Unfetched PR refs make the report look complete | The notice names the PR ref count; with 0 refs, stage columns read `not recorded` |
| Including in-progress local branches | Only `HEAD` and `refs/remotes/origin/pr/*` are read, never `--all` |
| Titles leaking company names | Titles are left out; the self-check test enforces it |

**Flags.** Compliance: not flagged (repo metadata only, no prod, money or personal data). Dinda's UX consult: does not apply (no UI, visual or motion work; the output is a markdown table).

**Decision record draft (for April)**
```
Decision: metrics.py derives stage times from task-file status changes on PR head refs, read with local git only.
Context: main is squash-merged, so stage history lives only on PR branches; the worktree is shallow; gh may be missing in sandboxes.
Options: A, gh API per PR (online every run, no offline test); B, local git with PR refs fetched by a documented command (stdlib, testable with fixture repos, works offline after the fetch); C, main only (no stage times at all).
Chosen: B, because it is deterministic, testable and needs no gh. A missing fetch degrades to "not recorded" with a notice.
Consequences: the monthly run needs two git fetches first (in the docstring). Spec time is "not recorded" for tasks that skipped status spec. Committer dates are ignored because of R-12.
Links: T-032
```

**Open questions**
- Janice: the Sprint 1 retro says T-037 and T-038 merged in the sprint window, but #7 merged 2 minutes before the Sprint 1 plan. The report follows merge times (footnote: T-012 only). Not blocking.

— Fang (architect)

Janice (pmo), 26 Nov: Design accepted, moved to build. Answers: the metrics report states what history shows (Sprint 1 window: T-012 only, footnoted); the retro is not rewritten. W6 (overrides) is April's call on the evidence. Agreed: for T-041 and T-031 the Reviewer records PASS and leaves status at review; Janice sets done after Merwyn acts. Findings file now says "company repo, behind T-002" (no forbidden terms).

## Build notes

**What changed**
- `scripts/metrics.py` (new, stdlib only; docstring holds the "how to run monthly" steps). Reuses `_fm.split`, `board.stages`, and in tests `engine.runtime.events` `DATA_PATTERNS` and `forbidden_terms`.
- `tests/test_metrics.py` (new, 14 tests): parser cases, fixture history (exact stage hours, window, footnote, report rows), shallow clone, no-git copy, real-file spot checks, data self-check on fixture and committed report.
- `offices/ai-office/metrics/2026-11.md` (new): first report, generated from a full clone of origin (28 commits on main, 27 PR refs fetched into a scratch clone, nothing pushed) at `97a51b2`: `python scripts/metrics.py ai-office --repo <scratch clone> --out offices/ai-office/metrics/2026-11.md`.
- Task file: Fang's Design and Janice's approvals were uncommitted in the worktree; they ride in this PR.

**Headline numbers (Sprints 1 to 4)**
- Tasks per sprint: 2, 3, 3, 3. Footnote on Sprint 1: T-012 (#10).
- Reviewer REJECTs: S1 0, S2 0, S3 0, S4 2 (both T-048). Compliance BLOCKs: S1 1 (T-040), S2 to S4 0. Escalations: S1 1, S2 0, S3 0, S4 1. (Corrected in Rework 1: S2 was wrongly "not recorded".)
- Specs approved first time: 2/2, 3/3, 3/3, 3/3. Median turnaround (h): 0.3, 0.2, 0.3, 0.1. T-048 turnaround 9.4 h (build 9.1 h across the overnight gap: commit times, not work time).
- Hours saved: "not set", Merwyn supplies.

**How to verify**
- `python -m unittest` -> `Ran 214 tests ... OK` (baseline 200, +14).
- `python scripts/metrics.py ai-office` in this shallow worktree: exit 0, notice "PARTIAL HISTORY (shallow clone; 0 PR refs)", Sprint 1 and 2 windows "not recorded".
- `python -m engine.runtime validate ai-office` -> OK (49 tasks); `build_agents.py ai-office` clean; `board.py ai-office` no problems, board.md discarded.
- Spot check in the report: T-040 0 REJECT / 1 BLOCK / 1 escalation; T-048 2 REJECT / 1 escalation.
- `grep -nE '[A-Za-z0-9._-]+@|[0-9]{10,}' offices/ai-office/metrics/2026-11.md` prints nothing.

**Deviations and limits**
- Design says only closed sprints are reported, so Sprint 5 (no Retro or Close heading) is not in the report; I followed the Design over the "Sprint 5 so far" ask. It appears automatically once its Close heading exists.
- Design's `git log ... refs/remotes/origin/pr/*` does not expand in git; used `--glob=refs/remotes/origin/pr/*` instead. Same intent.
- Design guessed Sprint 1 has no stage timestamps; the PR branches do have status commits, so Sprint 1 tasks show stage hours. Sprint 1 turnaround is therefore recorded, not blank.
- Review log wording is read from task files at HEAD; T-042, T-014, T-015 have no Review log section, so their verdict cells read "not recorded".
- On a shallow clone with no PR refs, sprints whose plan commit is in the 11 visible commits still show derived values from main commits alone (e.g. Sprint 3 median 0.2 h); the PARTIAL HISTORY notice covers this.
- Design's Janice question (Sprint 1 retro vs T-037/T-038): followed merge times, footnote lists T-012 only.

— Sebastian (engineer)

**Rework 1** (Review 1 REJECT, 26 Nov)
- `scripts/metrics.py`: new `derive_without_review()` for tasks with no Review log or Compliance section (T-042, T-014, T-015). REJECTs = review -> build transitions in the PR-ref status history (fallback if no history: 0 when the sprint Close lists the task under "all with Reviewer PASS"); BLOCKs = 0 when the task says "Compliance: not flagged" (the T-042/T-014/T-015 wording is `**Compliance:** not flagged`, in the Design); escalations = "escalated to Merwyn" lines, else 0 when the sprint Close says "without escalating". New `sprint_close_text()`; "How these are measured" updated.
- `tests/test_metrics.py`: real-file test that Sprint 2 sums to 0 | 0 | 0 with no value None (no git needed, so it runs in the shallow worktree), plus a review -> build transition test. 216 tests.
- `metrics/2026-11.md` regenerated from /tmp/cmx (fresh fetch, detached at origin/main `eeafa84`, 31 PR refs): history "full (31 PR refs)".
- Output: `python -m unittest` -> `Ran 216 tests ... OK`; validate -> `OK - 8 agents, 5 stages, 49 tasks, 16 skills`; build_agents clean; board.py no problems, board.md discarded; shallow run exits 0 with PARTIAL HISTORY notice (Sprint 2 row still 0 | 0 | 0 from files alone); data grep prints nothing.
- New rows (Sprint | Tasks | REJECTs | BLOCKs | Escalations): 1 | 2 | 0 | 1 | 1; 2 | 3 | 0 | 0 | 0; 3 | 3 | 0 | 0 | 0; 4 | 3 | 2 | 0 | 1. T-048 still 2 REJECTs, 1 escalation.
- Status left at `build`; owner set to reviewer (status is the PMO's/Reviewer's to write).

— Sebastian (engineer)

## Review log
REJECT, Review 1 of PR #30 (head 8c1994e), 26 Nov 2026. Fails Done-when 2: Sprint 2 and T-042/T-014/T-015 show "not recorded" for REJECTs, BLOCKs and escalations, but they are derivable: sprint-02.md Close says "Finished (all with Reviewer PASS)" and "without escalating"; PR-ref status history has one review → done and no review → build for each; each Design says "Compliance: not flagged". Expected Sprint 2 row: 0 | 0 | 0.
Fix: with no Review log, derive REJECTs from review → build transitions (T-048 = 2, consistent); BLOCKs 0 when Design says "Compliance: not flagged"; escalations from "escalated to Merwyn" lines or the sprint Close. Add a real-file test for the Sprint 2 row; regenerate metrics/2026-11.md; correct the Build notes line.
Passing: 214 tests OK; validate and build_agents clean; scratch-clone rerun matches (bar PR ref count); shallow run exits 0 with notice; T-040 0/1/1 and T-048 2/0/1 by hand; sprint counts 2/3/3/3; T-012 footnote; hours saved "not set"; no data hits.
Notes: the engineer set status review himself (only PMO/Reviewer write status).
— Cahyani (reviewer), recorded by Janice (pmo)

## Decision

## Open questions
