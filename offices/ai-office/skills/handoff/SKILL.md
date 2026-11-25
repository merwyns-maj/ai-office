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
5. Run `python scripts/board.py <office>` to catch Problems, then discard the regenerated board.md (`git checkout -- offices/<office>/board.md`; see pr-workflow). Commit the task file with the task id in the message.

Never leave a task with your section half written, an owner who doesn't own that stage, or a status that isn't a workflow stage.

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
