---
name: pmo-playbook
description: How Janice runs the office as PMO: planning sprints, limiting work in progress, keeping the RAID log, reporting status and escalating. Use at sprint planning, daily flow checks, status reports, and whenever something is stuck.
---
# PMO playbook

Distilled from PMO, kanban and status-reporting practice (sources at the end), adapted for an office of AI agents.

## 1. Purpose comes first
The office exists to finish the backlog's most valuable work, not to produce process. Every rule below earns its place by preventing a real failure. If a ritual adds paperwork without changing a decision, drop it.
- Tie every sprint to one goal Merwyn would recognise.
- Standardise the steps that repeat (spec, review, merge); stay flexible on everything else.

## 2. Sprint planning
1. Regenerate the board. Read `raid.md`.
2. Candidate tasks: unblocked (`depends_on` all done), not behind a human gate, highest priority first.
3. Pick at most 3. A sprint that finishes 3 beats one that starts 6.
4. Write `sprints/sprint-NN.md`: goal (one sentence), tasks in order with why, exit criteria, "Waiting on Merwyn" (max 3 one-line questions).
5. Move chosen tasks to `spec`, owner `pm`; give the PM exact backlog paths for each task and its parents (pm-playbook §0).
6. Commit the regenerated board.md and the sprint file in a board-refresh PR (pr-workflow, "board.md (generated)").

## 3. Flow, not busyness
- **WIP limits:** at most 2 tasks in `build`, 1 in `design` per Architect. Finish before starting.
- Watch three numbers from the board: **WIP** (items started, not done), **cycle time** (days from `spec` to `done`), **item age** (days an open item has sat in its current stage). They are linked: more WIP means longer cycle time.
- A task whose age in one stage is over 2 days is a flow problem, not a people problem: find the blocker, write it in the RAID log, and either unblock it or escalate.
- Daily flow check (agents: once per working session): look at aging items and blockers first, not at who is busy.

## 4. RAID log (`offices/<office>/raid.md`)
One table, four kinds of entry, each with an owner, date and next action:
- **Risk** — might happen; has a likelihood and a mitigation.
- **Assumption** — believed true but unverified; has a "verify by" date. An assumption found false becomes an Issue.
- **Issue** — happening now; has an owner and a fix date.
- **Dependency** — waiting on someone or something outside the task (often Merwyn, another repo, or an access grant).
Review it at every sprint plan and at every phase change. Close entries explicitly; never delete them.

## 5. Status that asks for help
A status report is a request for support, not a diary.
- Lead with an overall status, and give separate RAG for **scope, schedule, budget** (SDK credit) rather than one colour for everything.
- **Green**: on track, no action needed. **Amber**: at risk, with a plan; every Amber carries a decision request. **Red**: will miss without intervention; say what intervention.
- Red is information, not failure. Never soften a Red into Amber. Report the trend (Red last week, Amber now).
- Format follows `status-report` skill: waiting on Merwyn, done, in progress, blocked.

## 6. Escalation
Escalate early, once, with options:
- Context (one line) → the decision needed → 2–3 options with cost/risk → your recommendation.
- Escalate when: a `human_gates` item, second Reviewer rejection, an item aged over 3 days, budget at 80%, or Compliance BLOCK.
- Never escalate a question an agent in the org can answer.

## 7. Close the loop
- At sprint close, open the board-refresh PR (pr-workflow).
- After each sprint: what finished, cycle times, what got stuck and why. Hand April (Curator) the lessons; she proposes edits to skills and profiles.
- Measure the office by outcomes (tasks done, cycle time, rework rate), not by activity.

## Anti-patterns
- Reporting only Green. Treating RAG as a weapon instead of a signal.
- Starting new tasks to look busy while others sit in review.
- A PMO that only produces templates and reports and never removes a blocker.
- Copying status into chat instead of keeping it in the repo.

## Sources
- PMI, "Unleashing the power of the PMO" — https://www.pmi.org/learning/library/project-management-office-strategic-goals-4122
- CIO, "Why PMO offices fail and 7 ways to help your PMO succeed" — https://www.cio.com/article/4065713/why-pmo-offices-fail-and-7-ways-to-help-your-pmo-succeed.html
- Atlassian, "RAID log" — https://www.atlassian.com/agile/project-management/raid-log
- Scrum.org, flow metrics (WIP, cycle time, work item age, throughput) — https://www.scrum.org/node/16594
- Zoho, kanban metrics and Little's Law — https://www.zoho.com/sprints/track-kanban-metrics.html
- APM, "RAG status: a tool not a weapon" — https://www.apm.org.uk/blog/rag-status-a-tool-not-a-weapon/
- Project Management Compass, "Status Report Survival Guide" — https://projectmanagementcompass.substack.com/p/status-report-survival-guide
- Atlassian, "How to write a project status report" — https://www.atlassian.com/blog/project-management/how-to-write-a-project-status-report
