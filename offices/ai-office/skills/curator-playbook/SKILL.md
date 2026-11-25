---
name: curator-playbook
description: How April keeps the office's memory: decision logs, lessons, and docs that stay current. Use after every merged task, at sprint close, and when proposing edits to skills or profiles.
---
# Curator playbook

Distilled from knowledge-management and decision-log practice (sources at the end). Pairs with `decision-record` and `status-report`.

## 1. Record what future agents will ask
- Log decisions that are significant, hard to reverse, or likely to be questioned. Each entry: what was decided, why, alternatives considered, who decided, links (task, PR).
- Link the decision from the PR or task that implemented it, so the "why" is one click from the "what".

## 2. Just enough, and current
- Document just enough for a shared understanding; keep it concise and findable. More text is not more knowledge.
- Docs have a lifecycle: create, keep current as reality changes, archive before it misleads. Each doc has an owner.
- When code or a decision changes, the doc changes in the same PR or is marked superseded.

## 3. Lessons become edits
- After each task and each sprint, look for what went wrong or was slow (e.g. a merge failing on a stale mergeable flag).
- Turn each lesson into a concrete proposed edit to a skill or agent profile, as its own small task. A lesson that stays a note is lost.
- Keep the skill set lean: merge overlapping skills instead of adding new ones.

## 4. Where things go
- Task decisions → the task's Decision section.
- Durable office knowledge → the brain (via PR to the office's brain repo, once it exists).
- Company knowledge → company brain only, as pointers.

## Anti-patterns
- Session chatter in the brain. Docs nobody owns. Lessons recorded but never applied. Copying instead of linking.

## Sources
- AWS Well-Architected, knowledge management lifecycle — https://docs.aws.amazon.com/wellarchitected/latest/framework/ops07-bp03.md
- O'Reilly, Building Software Teams, "Document just enough" — https://oreilly.com/library/view/building-software-teams/9781491951781/ch11.html
- Thoughtworks, keeping agile docs current — https://www.thoughtworks.com/en-au/insights/blog/four-goals-agile-documentation-part-two
- DEV, decision logs for engineering teams — https://dev.to/william_geo/decision-logs-for-engineering-teams-building-institutional-memory-that-lasts-ff7
