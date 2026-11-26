# AI Office

An office of AI agents that plan, build, review and log work — run on the Claude Agent SDK, managed through files in git.

The **engine** runs any office. Each **office** is a folder of config (org chart, workflow, agents, skills, theme, backlog) that the engine loads. The first office, `offices/ai-office/`, builds AI Office itself.

## Layout

```
ai-office/
  engine/            runtime, app, renderer (planned — see engine/README.md)
    schema/          what an office folder must contain
  base/agents/       shared agent profiles any office can extend
  base/skills/       shared skills; base/defaults.yaml base_skills applies them to every agent of every office
  offices/
    ai-office/       the office that builds AI Office
      office.yaml    name, brain, repos, budget
      org.yaml       agents and reporting lines
      workflow.yaml  stages, handoffs, approvals, escalation
      agents/        this office's agents (extend base/ or stand alone)
      skills/        office-specific skills
      theme/         floor plan, rooms, sprites for the visualization
      backlog/       one file per task (T-xxx-*.md)
      board.md       generated kanban
  workspaces.yaml    brains and project repos the offices may touch
  scripts/
    build_agents.py  resolves `extends` and writes .claude/agents/ for an office
    board.py         generates an office's board.md from its backlog
  .claude/agents/    generated — do not edit by hand
```

## Rules of thumb

- Code that runs lives here. Knowledge lives in a brain repo. Deliverables live in the project repo.
- This repo holds **no company data** — only pointers in `workspaces.yaml`.
- Self-managed inside this repo: PMO approves specs and merges after a Reviewer PASS. Anything in `human_gates` waits for Merwyn.
- Only the PMO changes a task's `status`, except the Reviewer, who moves `review → done` or `review → build`.

## Golden examples

Golden cases check that a skill's rules still hold after someone edits its wording. They check recorded outputs only; no LLM runs.

- **Where:** `<skill folder>/golden/*.json`, one case per file, 3 to 5 per skill. Today: `base/skills/partner-writing`, `base/skills/consultant-slides`, `offices/ai-office/skills/spec-writing`, `offices/ai-office/skills/review-checklist`.
- **Case format:** `skill` (must equal the folder name), `rules` (rule ids), `input` (the brief), `expected_output` (the golden text), `checks` (list), optional `bad_output` (a text that breaks the rule; at least one check must fail on it), `human_note` (what a person judges and the script cannot), `why` (the slip the case guards against). Unknown keys are errors.
- **Checks:** each has a `rule` and a `type`: `must_match` / `must_not_match` (`pattern`, a regex, multiline), `must_contain` / `must_not_contain` (`text`, literal, case-sensitive), `max_lines` (`max`). At least one must or must-not check per case. Judgement (tone, truthfulness) goes in `human_note`, not in checks.
- **Run:** `python scripts/golden.py ai-office` (add `-v` for one line per case). Exit 0 prints `<skill>: N cases OK` then `golden: N cases, M checks, 0 problems`. Exit 1 prints one `<path>: <problem>` line per problem. Exit 2 is a usage error.
- **Data rule:** every case file is scanned with the patterns and forbidden terms from `engine/runtime/events.py`. A hit names the file and the kind, never the matched text. Cases use invented, generic text only. The rule does not yet cover key names or numbers (T-027), but the raw-text scan catches the digit and email patterns.
- **Add a case:** copy a case from the same folder, change it, run the command above. Keep the skill and its cases in the same PR.

## Run the current office in Claude Code

```bash
python scripts/build_agents.py ai-office   # writes .claude/agents/
python scripts/board.py ai-office          # writes offices/ai-office/board.md
claude                                     # then: "PMO, what's next?"
```
