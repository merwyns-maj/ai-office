---
id: T-039
title: "Engine loader and dry-run (repo-only slice of T-024)"
phase: 6-office
status: design
priority: P1
owner: engineer
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

**Answer to the Spec's architect question.** Python 3.11, stdlib only, under `engine/runtime/`, beside `scripts/` (same language as `board.py` and `build_agents.py`; the Agent SDK has a Python package for the T-024 remainder). No TypeScript.

**Approach**
- New package, no new dependency:
  - `engine/__init__.py`, `engine/runtime/__init__.py` (empty)
  - `engine/runtime/miniyaml.py` — parser for the YAML subset the office files use (stdlib has no YAML)
  - `engine/runtime/loader.py` — load an office folder into dataclasses; validate against `engine/schema/office.md` v0
  - `engine/runtime/dryrun.py` — pick the next eligible task and build the run plan
  - `engine/runtime/__main__.py` — CLI (`python -m engine.runtime ...`)
  - `engine/runtime/README.md` — commands and test command
  - `tests/__init__.py` (empty), `tests/test_miniyaml.py`, `tests/test_loader.py`, `tests/test_dryrun.py`
  - `engine/README.md` — mark the `runtime/` row "loader + dry-run built (T-039); live runs T-024". One-line change; if T-040 merges first, rebase.
- `scripts/_fm.py`, `board.py`, `build_agents.py` are not changed. (Their frontmatter parsing could later move onto `miniyaml`; not in this task.)
- Read-only by construction: the loader opens files with `read_text()` only; no `write`, `mkdir`, `subprocess`, `os.environ` access or network module anywhere in `engine/runtime/`.

**YAML subset (`miniyaml`)**, chosen to cover exactly what `offices/ai-office/*.yaml`, agent and task frontmatter contain today:
- Block mappings nested by indentation (spaces only; tabs are an error); block lists (`- item`), including lists of flow maps and lists of plain scalars containing commas or parentheses.
- Flow lists `[a, b]` and flow maps `{ k: v, k2: [x, y] }`, nested. Inside flow collections a key separator is `: ` (colon + space), so `claude:diagram-design` stays one scalar.
- Scalars: `"double"` and `'single'` quoted strings; `null`/`~` → `None`; `true`/`false` → bool; integers and decimals → int/float; anything else → str (stripped).
- `#` starts a comment only at line start or after whitespace, and never inside quotes.
- Anything else (block scalars `|`/`>`, anchors `&`/`*`, tags `!`, multi-document `---`) raises `YamlError` naming file and line. Fail loudly rather than guess.

**Interfaces**

CLI (run from the repo root):
```
python -m engine.runtime validate <office>     # <office> = office id (→ offices/<id>) or a path to an office folder
python -m engine.runtime dry-run  <office>
```
Exit codes: `0` OK (validate clean; dry-run printed a plan or "nothing to run"). `1` validation problems (dry-run also validates first and exits 1 if there are problems). `2` usage error (argparse) or office folder not found.

Validate output (stdout). Clean:
`ai-office: OK — 7 agents, 5 stages, 40 tasks, 15 skills`
With problems, one line each, then a summary; paths relative to the repo root:
```
offices/ai-office/backlog/T-041-x.md: status 'doing' is not a workflow stage (todo, spec, design, build, review, done, parked)
offices/ai-office/org.yaml: agent 'qa' has no agents/qa.md
ai-office: 2 problems
```

Dry-run output (stdout), fixed key order:
```
ai-office: dry-run (no files changed, no SDK or network calls)
task: T-039 Engine loader and dry-run (repo-only slice of T-024)
file: offices/ai-office/backlog/T-039-engine-loader-and-dry-run-slice-of-t-024.md
stage: design
owner: architect (Fang)
profile: offices/ai-office/agents/architect.md
office_skills: architect-playbook, decision-record, handoff
skill_files: offices/ai-office/skills/architect-playbook/SKILL.md, offices/ai-office/skills/decision-record/SKILL.md, offices/ai-office/skills/handoff/SKILL.md
external_skills: claude:diagram-design
output_section: Design
note: <only when task owner differs from the stage owner, e.g. "task owner compliance differs from stage owner architect">
```
`output_section` is the task's stage `output_section`; for a stage whose section is `null` (todo) it prints `none (exit: PMO picks it)`. `external_skills` prints `none` when empty. With nothing eligible: `ai-office: nothing to run`, exit 0.

Python:
```python
# miniyaml.py
class YamlError(ValueError):
    def __init__(self, source: str, line: int, msg: str): ...
def loads(text: str, source: str = "<string>") -> object
def split_frontmatter(text: str, source: str) -> tuple[dict, str]   # YamlError if no '---' block

# loader.py
@dataclass(frozen=True)
class Problem: file: str; message: str          # file relative to repo root; str() -> "file: message"
@dataclass
class Agent: id: str; path: Path; meta: dict; office_skills: list[str]; external_skills: list[str]; display_name: str | None
@dataclass
class Task: id: str; path: Path; title: str; status: str; priority: str; owner: str; depends_on: list[str]; meta: dict
@dataclass
class Office:
    id: str; root: Path; repo_root: Path          # repo_root = root.parent.parent
    office: dict; org: dict; workflow: dict
    agents: dict[str, Agent]; tasks: dict[str, Task]; skills: set[str]
    @property stage_ids -> list[str]; @property terminal -> list[str]
    def stage(self, sid: str) -> dict | None
def resolve_office(arg: str, cwd: Path) -> Path                  # id or path
def load_office(root: Path) -> tuple[Office | None, list[Problem]]  # None only if a required file is missing/unparseable
def validate(office: Office) -> list[Problem]

# dryrun.py
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
def task_number(task_id: str) -> int                            # "T-039" -> 39 (numeric, so T-100 sorts after T-99)
def eligible(office: Office) -> list[Task]                      # sorted by (rank, number)
def pick_next(office: Office) -> Task | None
def plan(office: Office, task: Task) -> list[tuple[str, str]]   # ordered (key, value) pairs as printed
def format_plan(office: Office, rows: list[tuple[str, str]]) -> str

# __main__.py
def main(argv: list[str] | None = None) -> int
```

**Validation rules** (each yields one `Problem`; all are collected, not first-fail)
1. Required: `office.yaml`, `org.yaml`, `workflow.yaml`, `agents/` with at least one `*.md`, `backlog/` (may be empty). A missing one → `missing required file`; loading stops there (later checks need it).
2. Any YAML or frontmatter parse error → problem with the `YamlError` line.
3. `office.yaml`: keys `id, name, purpose, brain, projects, human, budget, defaults` present; `id` equals the folder name; `brain` in `work|personal`; `human.name` present. (`projects` are not checked against `workspaces.yaml` — out of scope.)
4. `org.yaml`: `agents` is a list; each entry has `id`; ids unique; `agents/<id>.md` exists; `reports_to` is `human` or another org id.
5. `workflow.yaml`: `stages` non-empty list, each with `id` and `owner`; stage `owner` is an org id; `terminal` is a list; each `gates[].stage` is a stage or terminal; each `gates[].approver` is an org id or `human`.
6. `agents/*.md`: frontmatter has `name`; each `office_skills` entry has `skills/<name>/SKILL.md`; each `external_skills` entry has the form `source:name` (sources not checked against `workspaces.yaml`); `extends: base/<x>` → `<repo_root>/base/agents/<x>.md` exists (existence only, per Spec).
7. `backlog/T-*.md`: frontmatter has `id, title, status, priority, owner`; filename starts with `<id>-`; ids unique; `status` in stages + terminal; `priority` in `P0|P1|P2`; `owner` is an org id or `human`; each `depends_on` id exists in this backlog. Cross-office refs (`<office-id>/T-xxx`) are not checked by validate.

**Eligibility (dry-run)** — exactly the approved pick rule, plus one explicit addition:
- Skip tasks whose status is terminal.
- Skip tasks with any `depends_on` not `done` in this backlog. A cross-office dependency cannot be verified offline, so it counts as not done (conservative).
- *Design addition:* skip tasks whose `owner` is `human` (waiting on Merwyn; an agent run cannot act for him). Flagged for Janice below.
- Sort by priority rank, then numeric task id. First wins.

**Tests** (`python -m unittest -v` from the repo root; stated in `engine/runtime/README.md`)
- `test_miniyaml.py`: each construct above parsed from the real `offices/ai-office/workflow.yaml`, `office.yaml`, `org.yaml`; quoted `#` and `: `; nested flow (`{ agent: reviewer, may_set: [done, build], from: review }`); unsupported constructs raise `YamlError` with a line number.
- `test_loader.py`: `validate offices/ai-office` exits 0 and prints counts. Defect tests each `shutil.copytree` `offices/ai-office` and `base/` into a `tempfile.TemporaryDirectory()` as `<tmp>/offices/ai-office` and `<tmp>/base`, apply one defect, run `main(["validate", path])`, assert exit 1 and that the output names the file and the problem: (a) `workflow.yaml` deleted; (b) org agent added with no `agents/` file; (c) a task with `status: doing`; (d) a task with `depends_on: [T-999]`; (e) an agent with `office_skills: [no-such-skill]`.
- `test_dryrun.py`: on the real office exits 0 and prints every key above. Fixture backlog (temp copy, backlog replaced with ~6 small tasks): P1 T-010 vs P0 T-020 → T-020; two P0s T-005/T-012 → T-005; a P0 `done` task and a P0 `parked` task skipped; a P0 task depending on a `todo` task skipped; a P0 task owned by `human` skipped; T-100 vs T-99 sorts numerically; all ineligible → `nothing to run`, exit 0.
- No SDK / network / credential: (1) parse every `engine/runtime/*.py` with `ast` and assert imports are within `argparse, dataclasses, pathlib, re, sys, typing` plus `engine.runtime.*`; (2) run `main(["dry-run", ...])` with `socket.socket` and `socket.create_connection` patched to raise, and with `ANTHROPIC_API_KEY` removed via `unittest.mock.patch.dict(os.environ, ..., clear=False)`; (3) after the run assert no module named `anthropic` or `claude_agent_sdk` is in `sys.modules`.
- Read-only: walk the office folder before and after dry-run and validate, comparing `{relative path: sha256}`; must be equal (catches new files such as stray caches too).

**Risks**

| Risk | Handling |
|---|---|
| Hand-written YAML parser misreads a file | Subset is small and listed; anything outside it is a loud `YamlError`, never a silent guess. Tests run against the real office files. Swapping to PyYAML later is a one-module change behind `loads()`. |
| Two frontmatter parsers (`scripts/_fm.py` and `miniyaml`) drift | Accepted for now; follow-up to point `scripts/` at `miniyaml` once the engine is proven. Noted for April. |
| Validator is stricter than today's files (real office fails validate) | Engineer runs validate on `offices/ai-office` first; a real defect found is reported in Build notes and to Janice, not silently fixed in office files by this task. |
| Pick rule disagrees with how Janice actually picks | Rule is the one approved at spec; the `human` owner skip is flagged below. |
| Validation rules creep into a full schema engine | Rules limited to the seven above; anything else goes to T-024 or a new task. |

**Flags.** None for Compliance: no production system, money, credentials or personal data; reads only this repo's office files. Goes straight to Engineer.

**Decision record (draft for April)**
```
Decision: The engine runtime is Python 3.11 stdlib in engine/runtime/, with a small in-repo YAML-subset parser; loader and dry-run are read-only and import no SDK.
Context: T-039 (slice of T-024). Office folders need schema validation and a preview of a run before live SDK runs spend credit. scripts/ is already stdlib Python.
Options: A — Python stdlib + miniyaml (pro: no dependency, matches scripts/, SDK has Python; con: own parser to maintain).
         B — Python + PyYAML (pro: full YAML; con: first third-party dependency, install step on every machine and CI).
         C — TypeScript (pro: matches a future web app; con: second toolchain, nothing in repo uses it yet).
Chosen: A, because it matches what exists, needs no install, and the office files use a small, stable YAML subset; parser sits behind loads() so B is a cheap swap.
Consequences: Easier: run anywhere with python3; T-024 builds on load_office()/pick_next(). Harder: YAML outside the subset is rejected until miniyaml grows. Follow-up: move scripts/_fm.py onto miniyaml.
Links: T-039, T-024, engine/schema/office.md.
```

**Open questions (design)**
- Janice: confirm the design addition that dry-run skips tasks owned by `human`. Non-blocking: build includes it; removing it is a one-line change.

— Fang (architect)

## Build notes

## Review log

## Decision

## Open questions
- Spec-level questions are in Spec → Open questions; design-level ones in Design → Open questions. (Older duplicate removed by Fang; language question answered in Design: Python stdlib.)
