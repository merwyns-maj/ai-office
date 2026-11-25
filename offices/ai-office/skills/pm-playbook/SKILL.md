---
name: pm-playbook
description: How Emmy works as PM: framing problems, writing testable acceptance criteria, cutting scope and keeping specs honest. Use whenever a task enters spec, or a spec is challenged.
---
# PM playbook

Distilled from acceptance-criteria and requirements practice (sources at the end). Pairs with `spec-writing`, which gives the section layout.

## 0. Before you start: can you read the backlog?
Sprint 1 lesson: a spec was written without its parent tasks because Glob and Grep were missing from the PM session, though the profile lists them.
1. Read the task file. List its parents: every id in `depends_on`, plus any task named in the title or body ("slice of T-019").
2. Read each parent. Find the path in this order: Glob `offices/<office>/backlog/T-xxx-*.md` if Glob works; else the exact paths in the PMO's brief; else the links in `offices/<office>/board.md` (it can lag main between sprint PRs).
3. If a parent still cannot be read, stop. Write nothing under Spec. Tell the PMO which ids you could not read and ask for the paths or the pasted text.
4. Under Open questions, add one fact line naming any tool that was missing.

## 1. Problem before solution
- Start from who is affected and what goes wrong today. If you can't say it in two sentences, the task is not ready: split it or send it back to Janice.
- Describe the outcome, not the implementation. Leave the how to Fang and Sebastian.

## 2. Acceptance criteria that a reviewer can test
Each "Done when" line must be:
- **Testable** — a yes/no result someone can check by running a command or opening a file.
- **Specific** — replace "works", "fast", "clean", "looks good" with an observable fact: an exit code, a file path, a count, a message.
- **Independent** — each line checkable on its own.
- **Outcome-focused** — what the user or the next agent can do, not which function is called.
Use Given / When / Then when behaviour depends on a situation:
`Given an office whose agent lists a missing skill, when build_agents.py runs, then it exits 1 and names the file and skill.`

## 3. Scope is a decision
- Write **Out of scope** every time. Anything tempting but not needed for this task goes there, or to a new backlog item.
- If the spec needs more than one screen, the task is too big. Split by outcome, not by layer.
- When time is short, cut scope, never the checks.

## 4. Facts and questions
- Anything you haven't verified goes in Open questions, with who can answer (agent id or Merwyn).
- A question that blocks the build is flagged "blocking" and goes to Janice for the RAID log.

## 5. Agreement
- Criteria are only useful if everyone downstream accepts them. Before handing to Fang, read your checks as Cahyani would: could she fail the work on each one?

## Anti-patterns
- Specs that describe code. Vague verbs. No out-of-scope list. Hidden assumptions. Adding "nice to haves" to look thorough.

## Sources
- Atlassian, acceptance criteria — https://www.atlassian.com/work-management/project-management/acceptance-criteria
- Nulab, acceptance criteria (Given/When/Then, outcome vs implementation) — https://nulab.com/learn/software-development/acceptance-criteria/
- ClickUp, testable yes/no criteria — https://clickup.com/blog/how-to-write-acceptance-criteria/
- Lucid, acceptance criteria accepted by all stakeholders — https://lucid.co/blog/acceptance-criteria
