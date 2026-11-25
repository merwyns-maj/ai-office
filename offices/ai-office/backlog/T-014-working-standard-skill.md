---
id: T-014
title: "Working-standard skill"
phase: 3-skills
status: design
priority: P1
owner: engineer
where: chat
project: ai-office
depends_on: [T-012]
pr: null
---

> Source: research/T-012-chat-mining.md section A (A1-A10). Picked by Merwyn for Sprint 2 (25 Nov 2026). Skill lives in this repo; no company data.

## Done when
- [ ] Verify vs prod, flag incidental bugs, check external edits, state fact not guesses
- [ ] Used by PRD and recon skills

## Spec

**Problem.** Merwyn's standards for how work is done (T-012 section A) exist only as chat patterns, so each agent works to its own habits: inferred values reported as facts, summaries defended instead of re-verified, incidental bugs left unmentioned, shared files overwritten.

**In scope**
- One skill, `working-standard`, covering A1 to A10: state facts not guesses (A1); verify against primary sources and re-verify when challenged (A2); back recommendations with data (A3); flag incidental bugs with evidence (A4); check for external edits before overwriting shared work (A5); use the team's conventions (A6); scope precisely, wording vs data/logic (A7); stay in the asked lens (A8); start simple, iterate (A9); consistency check before delivery (A10).
- Location: base level, so every office inherits it and no office copies it.
- Every agent in every office receives it automatically, with no per-agent edit.
- No company data in the skill (CLAUDE.md rule).

**Out of scope**
- Editing company PRD or recon skills (they live outside this repo; see Open questions).
- Partner-writing rules (T-015) and Merwyn-interaction rules (T-041).
- Choosing the base-level mechanism (Architect).

**Done when**
- [ ] Exactly one `SKILL.md` has `name: working-standard`. Check: `grep -rl "name: working-standard" offices/ | wc -l` prints 1, at a base-level path every office can reach.
- [ ] The file contains A1 to A10 each as one short rule. Check: open it; ten distinct rules, each citing its A-number.
- [ ] A new agent built for a second office gets the skill without editing its own profile. Check: run the build for any office and `grep -l "working-standard"` on the generated agent files for every agent in it; the count equals the agent count.
- [ ] `python scripts/build_agents.py <office>` exits 0 for every office that exists.
- [ ] `grep -rn "working-standard" offices/*/agents` lists no agent file as the source of truth (the skill is not copy-pasted into agents).
- [ ] The skill contains no borrower, lender, NIK, account numbers or amounts. Check: open the file.

**Open questions**
- Does a base-level skills location exist today, and how do `office_skills` and `build_agents.py` treat it? Not verified. Who: Architect. Blocking for design.
- How many offices exist besides ai-office? I read only that office. Who: Architect.
- Original check "used by PRD and recon skills": those are company skills (klik-workspace), outside this repo, so a repo write is a human gate. Drop it, or open a follow-up task once T-002 lands? Who: Merwyn.

— Emmy (pm)

## Design

**Basis.** Spec above; `research/T-012-chat-mining.md` §A; `engine/schema/office.md`; `scripts/build_agents.py`, `scripts/_fm.py`; `engine/runtime/loader.py`, `dryrun.py`; `tests/`. `claude:diagram-design` was not available in this session; no diagram needed.

**Answers to the Spec's open questions (checked)**
- Is there a base-level skills location today? No. `base/` has only `agents/`. `build_agents.py` and `loader.py` only resolve `offices/<office>/skills/<name>/SKILL.md`, through `office_skills`.
- How many offices are there? One: `ls offices` shows `ai-office` only. `workspaces.yaml` has a company office commented out.
- The PRD/recon check is still Merwyn's call (see below). This design does not cover it.

### Approach
1. Add the shared skill library at `base/skills/<name>/SKILL.md`, in Agent Skills format like the office skills. First entry: `base/skills/working-standard/SKILL.md`.
2. Add `base/defaults.yaml`, one place for repo-wide defaults:
   ```yaml
   # Repo-wide defaults every office inherits. Flat `key: [list]` lines only.
   # Read by scripts/build_agents.py and engine/runtime.
   base_skills: [working-standard]   # every agent in every office follows these
   ```
3. Add an optional agent frontmatter key, `base_skills: [...]`, for extra base skills one agent opts into. T-015 needs it next (partner-writing for pm and curator only). It shares the resolver, so it is built and tested here once and T-015 becomes content only.
4. An agent's effective skill list, in order, de-duplicated (first wins):
   - `base/defaults.yaml` `base_skills`
   - then the agent's `base_skills`
   - then its `office_skills`
   There is no opt-out (out of scope).
5. A skill name lives in `base/skills/` or in an office's `skills/`, never both. Both build and validate fail on a clash, so a skill has one source of truth.
6. Update the docs: `engine/schema/office.md` (base layout, the `base_skills` key, the clash rule; additive, so existing offices stay valid) and the `README.md` layout block.
7. Run `python scripts/build_agents.py ai-office` and commit the regenerated `.claude/agents/*.md`. All 7 change: each gains the working-standard line.

### Interfaces
**`base/skills/working-standard/SKILL.md`**: frontmatter `name: working-standard` plus a `description` ("How every agent works: facts not guesses, primary sources, flag bugs, check edits, consistency. Use on every task, before delivering anything."). The body is ten one-line rules, each tagged with its A-number. No company names, systems, labels or figures: A6's "klik-workspace skills, `ai-drafted`" becomes generic. Wording to start from:
- A1 State facts, not guesses. A value not in a source is "unknown"; name the source that would settle it and read it.
- A2 Verify against the primary source (database, full file or page, actual code) before documenting or concluding; when challenged, re-check the source instead of defending the summary.
- A3 Back a recommendation with the numbers that test it; revise it if they disagree.
- A4 Flag incidental bugs found along the way, with evidence (file, line, output); do not fix them silently outside scope.
- A5 Before overwriting shared work, check for edits since you read it (git log/diff, page history, comments); merge, do not clobber.
- A6 Use the conventions of the team and repo you are in (templates, skills, labels, boards); do not invent a format.
- A7 Say whether a change is wording-only or changes data/logic; keep the two apart.
- A8 Stay in the lens you were asked for; give legal or risk opinions only when asked, and name who should answer.
- A9 Start simple: ship the simplest shape that works, then iterate.
- A10 Before delivering, check consistency: counts, cross-references, leftover placeholders, and summary order against body order.

**`scripts/_fm.py`**: add
```python
def read_flat(path):
    """Flat `key: value` file without --- fences -> dict; {} if missing."""
```
It reuses `split()`, so `" #"` comments are stripped the same way.

**`scripts/build_agents.py`**
- Change the signature to `build(office, root=ROOT)`. Every path, including `root/".claude"/"agents"` and `root/"workspaces.yaml"`, derives from `root`, so tests can build into a temp repo.
- New `def skill_paths(fm, office, root, fname) -> list[str]`. It returns repo-relative SKILL.md paths in the order above and exits 1 with one of:
  - `base/defaults.yaml: base_skills names '<sk>', but base/skills/<sk>/SKILL.md is missing`
  - `<fname>: base_skills names '<sk>', but base/skills/<sk>/SKILL.md is missing`
  - `skill '<sk>' exists in both base/skills/ and offices/<office>/skills/; keep one`
  - the existing `office_skills` message, unchanged
- Call it for every agent in the first loop, before `.claude/agents/*.md` is deleted. A bad name must never leave the folder empty.
- The `## Skills` block lists every path with the same lead line ("Before your step, read and follow:"). Base paths are `base/skills/<sk>/SKILL.md`. `base_skills` is not written to the generated frontmatter (`KEYS` unchanged).

**`engine/runtime/loader.py`**
- `Agent.base_skills: list`, from frontmatter.
- `Office.base_skills: set`: names with `repo_root/base/skills/<n>/SKILL.md`.
- `Office.default_base_skills: list`: from `repo_root/base/defaults.yaml`, parsed with `_parse_file`. A missing file means `[]`; a non-mapping file is a problem.
- `Office.skill_files(agent) -> list[str]`: same order and de-duplication as the build.
- `validate()` §6 adds these problems:
  - `base/defaults.yaml: base_skills '<sk>' has no base/skills/<sk>/SKILL.md`
  - `<agent path>: base_skills '<sk>' has no base/skills/<sk>/SKILL.md`
  - `offices/<o>/skills/<sk>: skill '<sk>' also exists in base/skills/; keep one`
- The `validate` OK line is unchanged (it counts office skills).

**`engine/runtime/dryrun.py`**: insert the row `("base_skills", <defaults + agent base_skills, or "none">)` right after `profile`. `skill_files` uses `office.skill_files(agent)`, so base paths come first.

**Tests** (stdlib `unittest`)
- New `tests/test_build_agents.py`, run against a temp repo (copies of `base/`, `workspaces.yaml`, `offices/ai-office/`):
  - (1) For ai-office, every generated file contains `base/skills/working-standard/SKILL.md`, and the count equals the agent count.
  - (2) A **second office**, `offices/demo/agents/solo.md` with only `name` and `description`, builds with the working-standard line (done-when 3).
  - (3) An unknown name in `defaults.yaml` exits with the message, and a pre-existing file in the temp `.claude/agents/` is still there.
  - (4) An unknown agent `base_skills` name exits.
  - (5) A clash exits.
- `tests/test_loader.py` `Defects`: the same three cases through `validate`. `OfficeCopy` already copies `base/`.
- `tests/test_dryrun.py`: add `"base_skills"` to `KEYS` after `"profile"`, and assert `base_skills: working-standard` in `test_plan_content`.
- `python -m unittest` exits 0.

### Spec deltas for the Reviewer (mechanical, same intent)
- Check 1: the skill is at base level, so grep both trees: `grep -rl "name: working-standard" base/ offices/ | wc -l` prints 1. Emmy's `offices/`-only grep prints 0 by design.
- Check 3: only one office exists. The "second office" is the temp office in `test_build_agents.py` (2). Also run `grep -l "base/skills/working-standard" .claude/agents/*.md | wc -l`; it prints 7.
- Check 5: `grep -rn "working-standard" offices/*/agents` prints nothing; the list lives in `base/defaults.yaml`.

### Risks
| Risk | Handling |
|---|---|
| A bad skill name wipes `.claude/agents/` | All checks run before the unlink loop; test (3) |
| Two sources for one skill name | Clash fails both build and validate |
| Company offices in klik-workspace (planned) cannot see this repo's `base/` | Out of scope. T-017/T-024 must decide how the engine supplies `base/` to an office stored elsewhere. Noted for April |
| Context cost: every agent reads one more file every step | Keep the skill to about 25 lines |
| `_fm` parses only flat lines | The `defaults.yaml` header says so; the loader's stricter parse catches anything else |
| Overlap with `CLAUDE.md` "State facts, not guesses" | The skill expands that line, it does not contradict it; `CLAUDE.md` unchanged |
| Schema v0 was approved by Merwyn (T-001) | The change is additive and optional; existing files stay valid. Not a cost or risk choice, so no human gate. Janice may show Merwyn |

**Compliance:** not flagged. Skill text only, no data, no prod.

### Trade-off: where the "every agent" list lives
| Option | Per-agent edit | Per-office edit | Reaches agents without `extends` | Supports opt-in (T-015) |
|---|---|---|---|---|
| **A. `base/defaults.yaml` `base_skills` (chosen)** | no | no | yes | yes, with the agent key |
| B. `base_skills` in each office.yaml | no | yes; a new office can forget | yes | yes |
| C. List in each `base/agents/*.md` | no | no | no; an office override also replaces the list | awkward |
| D. Every folder in `base/skills/` applies to all | no | no | yes | no |
| E. `office_skills` falls back to `base/skills/` | yes | n/a | n/a | yes, but names can shadow |

### Decision record draft (for April)
```
Decision: Shared skills live in base/skills/<name>/SKILL.md; base/defaults.yaml base_skills applies them to every agent of every office, and an agent's optional base_skills key adds more.
Context: T-014 needs one working standard for every agent with no per-agent edits; T-015 needs a shared skill for two agents only.
Options: A repo-wide defaults file (chosen); B per-office list in office.yaml; C list in base agent profiles; D everything in base/skills is universal; E office_skills falls back to base/.
Chosen: A, because it is one place, reaches standalone agents, and cannot be dropped by an office override.
Consequences: build and validate gain base checks and a no-clash rule; all generated agents change once; company offices outside this repo need T-017/T-024 to supply base/.
Links: T-014, T-015, PR <n>
```

### Build order
Build this before T-015, which uses `base_skills`. Independent of T-042, so the two can be built in parallel (WIP 2).

### Open questions
- The original check "Used by PRD and recon skills": those skills are company skills in klik-workspace, and writing there is a human gate (T-002). Recommendation: drop the check from T-014 and open a follow-up once a company office exists. Who: Merwyn via Janice. It does not block the build, but Janice should settle it before review so Cahyani knows whether that box counts.

— Fang (architect)
