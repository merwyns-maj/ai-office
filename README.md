# AI Office

An office of AI agents that plan, build, review and log work — run on the Claude Agent SDK, managed through files in git.

The **engine** runs any office. Each **office** is a folder of config (org chart, workflow, agents, skills, theme, backlog) that the engine loads. The first office, `offices/ai-office/`, builds AI Office itself.

## Layout

```
ai-office/
  engine/            runtime, app, renderer (planned — see engine/README.md)
    schema/          what an office folder must contain
  base/agents/       shared agent profiles any office can extend
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
- Agents never merge. Merwyn merges.
- Only the PMO changes a task's `status`, except the Reviewer, who moves `review → done` or `review → build`.

## Run the current office in Claude Code

```bash
python scripts/build_agents.py ai-office   # writes .claude/agents/
python scripts/board.py ai-office          # writes offices/ai-office/board.md
claude                                     # then: "PMO, what's next?"
```
