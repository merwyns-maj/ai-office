---
name: handoff
description: Move a task to the next workflow stage cleanly. Use at the end of every agent's step.
---
# Handoff

At the end of your step, in the task file:
1. Fill your section (Spec, Design, Build notes, Review log or Decision) and sign it "— Name (agent-id)".
2. Tick the "Done when" boxes you verified (Reviewer only ticks on PASS).
3. Set `status` to the next stage and `owner` to that stage's owner from `workflow.yaml`. Only the PMO and the Reviewer write `status` (see `status_writers`); other agents set `owner` and tell the PMO.
4. If anything is unknown, add it to "Open questions" with who can answer. If it blocks, add it to `raid.md` as an Issue or Dependency.
5. Run `python scripts/board.py <office>` and commit with the task id in the message.

Never leave a task with your section half written, an owner who doesn't own that stage, or a status that isn't a workflow stage.
