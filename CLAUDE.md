# Working in this repo

You are part of an AI office. Read `offices/<office>/workflow.yaml` before acting on any task.

- A task is a file in `offices/<office>/backlog/`. Its frontmatter `status` is the workflow state; `owner` is the agent holding it.
- Stay in your lane: do only the step your agent profile owns, then hand off by updating the task file and `owner`.
- Write your output into the task file's section for your role (Spec, Design, Build notes, Review log, Decision).
- Never push to `main`. Work on a branch named `t-xxx-short-name` and open a PR. Only the PMO merges, and only after a Reviewer PASS (except planning-only `sprint-NN-*` PRs, see pr-workflow).
- Stop and ask Merwyn for anything in `human_gates` in the office's workflow.yaml.
- Never copy company data (borrower, lender, NIK, account numbers, prod rows) into this repo. Link to where it lives.
- After editing any office's `agents/`, run `python scripts/build_agents.py <office>`.
- After changing any task's frontmatter, run `python scripts/board.py <office>` to check for problems, then discard board.md: only the PMO's sprint PRs commit it (see the office's pr-workflow skill).
- State facts, not guesses. When something is unknown, write it under "Open questions" in the task.
