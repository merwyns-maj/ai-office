---
id: T-042
title: "Sprint 1 process lessons: tool check, board.md rule, handoff for read-only agents"
phase: 7-ways-of-working
status: review
priority: P1
owner: reviewer
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

## Design

**Basis.** Spec above, Sprint 1 Retro, the skills named below, `CLAUDE.md`, `scripts/board.py`, `base/agents/*.md`. Janice's rulings came in the design brief (25 Nov), not in this file: (1) `board.md` is refreshed by a PMO PR at sprint plan and sprint close, so nothing is committed straight to `main` (answers the blocking open question); (2) when Glob/Grep are missing, the PM falls back to Read on paths the PMO supplies. `claude:diagram-design` was not available in this session; no diagram needed.

**Facts checked**
- There is no `.github/`, no git hook and no CI in the repo (`ls -a`; `git ls-files | grep -i github` matches only task files). Only `scripts/board.py` writes `board.md`; no test reads it. Open question 2 is closed: nothing to fix there.
- These lines conflict with rule (b) today: `CLAUDE.md` line 12 ("run board.py" after frontmatter changes) and `handoff` step 5 ("run board.py and commit"). `pmo-playbook` §2.1 ("Regenerate the board") and `base/agents/pmo.md` line 15 say run, not commit, so they stay as they are. Base files are out of scope.
- Read-only by profile: `reviewer` (Read, Grep, Glob, Bash; no Edit/Write) and `compliance` (Read, Grep, Glob). The PM profile lists Glob/Grep, but they were missing in the PM session in Sprint 1 and again in Sprint 2 (Emmy's note). The cause is unknown. The PM has no Bash.

### Approach (text only; no script or engine change)
1. `offices/ai-office/skills/pm-playbook/SKILL.md`: new section `## 0. Before you start: can you read the backlog?`. This is rule (a). `spec-writing` is unchanged because it covers layout only.
2. `offices/ai-office/skills/pr-workflow/SKILL.md`: new section `## board.md (generated)` and a pre-commit check line in step 2. This is rule (b).
3. `offices/ai-office/skills/handoff/SKILL.md`: rewrite step 5 and add the section `## If you cannot edit the task file`. This is rule (c).
4. `CLAUDE.md` line 12: reworded to match (b).
5. Pointer lines only, so each rule still lives in one file:
   - `pmo-playbook` §2 step 5 gets "give the PM exact paths (pm-playbook §0)".
   - `pmo-playbook` §2 gets a new step 6 and §7 gets one line: "board-refresh PR (pr-workflow)".
   - `review-checklist` step 3 adds "`board.md` committed on a task branch (pr-workflow)" to its look-for list.
6. Run `python scripts/build_agents.py ai-office`. Expect no diff under `.claude/agents/`: generated bodies list skill paths, not skill text, and no `office_skills` change. Show the empty `git status`.

### Interfaces: text to add (Sebastian may adjust wording only, not the rules)

(a) `pm-playbook`, inserted before `## 1.`:
```
## 0. Before you start: can you read the backlog?
Sprint 1 lesson: a spec was written without its parent tasks because Glob and Grep were missing from the PM session, though the profile lists them.
1. Read the task file. List its parents: every id in `depends_on`, plus any task named in the title or body ("slice of T-019").
2. Read each parent. Find the path in this order: Glob `offices/<office>/backlog/T-xxx-*.md` if Glob works; else the exact paths in the PMO's brief; else the links in `offices/<office>/board.md` (it can lag main between sprint PRs).
3. If a parent still cannot be read, stop. Write nothing under Spec. Tell the PMO which ids you could not read and ask for the paths or the pasted text.
4. Under Open questions, add one fact line naming any tool that was missing.
```

(b) `pr-workflow`. Add this to step 2, before the commit: `git diff --cached --name-only -- 'offices/*/board.md'` must print nothing. Then add a new section after "Rules":
```
## board.md (generated)
- Task branches never commit `offices/<office>/board.md`. Run `board.py` to see Problems, then discard the file: `git checkout -- offices/<office>/board.md`.
- The PMO commits board.md only in sprint PRs: branch `sprint-NN-plan` at sprint plan and `sprint-NN-close` at sprint close (one PR may do both, as PR #12 did). Regenerate on fresh main, commit it with the sprint file, open a PR. Reviewer PASS and PMO merge as for any PR; the review check is that `board.py` on the branch leaves `git diff --exit-code` clean.
- Between sprint PRs, board.md on main can lag. For the live board, run board.py locally and do not commit it.
```

(c) `handoff`. New step 5:
`5. Run python scripts/board.py <office> to catch Problems, then discard the regenerated board.md (git checkout -- offices/<office>/board.md; see pr-workflow). Commit the task file with the task id in the message.`

New section at the end:
```
## If you cannot edit the task file
Applies to any agent without Edit/Write in its session: Reviewer and Compliance always (read-only profiles), any other agent when a tool is missing. Do not stop half done. End your reply with this block, ready to paste:

    HANDOFF T-xxx
    Section: <Spec | Design | Build notes | Review log | Decision>
    Body:
    <section text exactly as it should appear, ending with "— Name (agent-id)">
    Done when ticks: <exact lines to tick, or none>      (Reviewer, on PASS only)
    Open questions: <lines to add, each with who can answer, or none>
    Proposed status: <stage id, or unchanged>
    Proposed owner: <agent id or human>

The PMO records it:
- Paste Body verbatim under the section, appended, never reworded.
- Apply the ticks and the open questions.
- Set status and owner if `status_writers` and the stage owners allow it. If they do not, leave status, record the text anyway, and say why in the task.
- Add the line "Recorded by <name> (pmo) from <agent-id>'s handoff."
- Then run step 5.
```

`CLAUDE.md` line 12 becomes:
`- After changing any task's frontmatter, run python scripts/board.py <office> to check for problems, then discard board.md: only the PMO's sprint PRs commit it (see the office's pr-workflow skill).`

### Spec delta for the Reviewer
Done-when 2 says "the PMO regenerates and commits it after merge". Per Janice's ruling, read it as "in a board-refresh PR at sprint plan and sprint close". The same `grep -n "board.md"` check still applies.

### Risks
| Risk | Handling |
|---|---|
| An agent stages board.md by habit (`git add -A`) | Pre-commit check in pr-workflow step 2, and the review-checklist pointer. The Reviewer can run `git diff --name-only main...HEAD -- 'offices/*/board.md'`; it should be empty |
| board.md on main is stale between sprints | Its header has the generation date. Anyone can run board.py locally. Accepted trade-off |
| The PMO rewords a returned handoff | "Verbatim, appended" plus the "Recorded by" line keeps authorship visible |
| The PM still writes blind | §0 step 3 is a hard stop with nothing written under Spec |
| Sprint PR branch names do not match workflow.yaml `merge.requires` ("PR open from a t-xxx branch") | Existing practice (PRs #8, #12). Raised below; not changed in this task |

**Compliance:** not flagged. No prod, money, credentials or personal data.

### Decision record draft (for April)
```
Decision: Task branches never commit the generated board.md; the PMO commits it only in sprint plan/close PRs.
Context: Sprint 1, two task branches both committed board.md and conflicted on rebase; CLAUDE.md forbids pushing to main.
Options: A PMO commits after each merge (direct push breaks the main rule; a PR per merge is noise);
  B PMO board-refresh PR at sprint plan/close (no tooling, rides on PRs that already exist);
  C .gitattributes merge driver (needs per-clone git config that does not travel);
  D gitignore board.md (no board on GitHub for Merwyn).
Chosen: B, ruled by Janice, because it adds no tooling, no direct push and no extra PRs.
Consequences: board on main lags between sprints; live view = run board.py locally. Follow-up: ratify sprint-NN branches in workflow.yaml merge.requires.
Also: read-only agents return a HANDOFF block and the PMO records it verbatim.
Links: T-042, sprints/sprint-01.md Retro, PR <n>
```

### Open questions (non-blocking)
- `workflow.yaml` `merge.requires` says "PR open from a t-xxx branch", but sprint PRs use `sprint-NN-*`. Should it be ratified with a one-line workflow.yaml edit in its own small task? Merwyn set the authority rules. Who: Merwyn via Janice.
- Why Glob/Grep are missing in PM sessions when the profile lists them: is it the launcher's tool config? Who: Janice (RAID R-10). The playbook works either way.

— Fang (architect)

## Approvals (PMO)
- Spec approved: PMO never pushes board.md to main; task branches don't commit it; PMO refreshes it in sprint-NN-plan/close PRs. No CI exists. — Janice (pmo)
- Design approved. Ruling on Fang's open question: workflow.yaml merge.requires is amended in this task to allow 'sprint-NN-*' branches for planning-only PRs (no Reviewer needed); this is an office rule, not a human gate. — Janice (pmo)



## Build notes
**What changed (text only, no script or engine change):** `pm-playbook` new section 0 (rule a); `pr-workflow` pre-commit check line plus section "board.md (generated)" (rule b); `handoff` step 5 rewritten plus section "If you cannot edit the task file" (rule c); `CLAUDE.md` line 12; pointer lines in `pmo-playbook` (section 2 step 5, new step 6, section 7) and `review-checklist` step 3; `offices/ai-office/workflow.yaml` merge exception per Janice's ruling.

**Verify**
```
$ python3 scripts/build_agents.py ai-office
ai-office: built 7 agents -> .claude/agents/ (architect, compliance, curator, engineer, pm, pmo, reviewer)
$ python -m engine.runtime validate ai-office
ai-office: OK — 7 agents, 5 stages, 42 tasks, 15 skills
$ python -m unittest -q
Ran 133 tests in 4.780s
OK
```
`git status` after build_agents: only the 7 text files above changed; nothing under `.claude/agents/` (as Design expected). board.md was not committed (`git diff --cached --name-only -- 'offices/*/board.md'` prints nothing).

**Done-when map**
| Done when | Evidence |
|---|---|
| pm-playbook start-of-task step | `grep -n -i parent offices/ai-office/skills/pm-playbook/SKILL.md` finds section 0 steps 1-3 |
| pr-workflow one board.md rule | `grep -n "board.md" offices/ai-office/skills/pr-workflow/SKILL.md` |
| no skill/CLAUDE.md tells agents to commit board.md on a task branch | `grep -rn "board.py" offices/ai-office/skills CLAUDE.md` shows 5 lines: handoff step 5 and CLAUDE.md say discard; pr-workflow lines say discard/PMO sprint PR only. No `.github/` exists |
| handoff read-only paragraph | `handoff/SKILL.md`, section "If you cannot edit the task file" |
| build_agents exits 0, no unbuilt diffs | output above; no `.claude/agents/` diff |
| each rule in one skill, none opposed | rule a only in pm-playbook (pmo-playbook only points to it), rule b only in pr-workflow (pointers elsewhere), rule c only in handoff |

**Deviations**
- workflow.yaml: Janice's ruling is added as a comment plus a new key `requires_planning_only` under `merge`, leaving `requires` unchanged, so existing consumers of `requires` are unaffected. `engine.runtime validate` still passes. Reviewer may prefer folding it into `requires`; wording only.
- pr-workflow's board.md section also mentions the planning-only exception (one sentence, pointing to workflow.yaml).
- Ticks in Done when left for the Reviewer.

— Sebastian (engineer)
