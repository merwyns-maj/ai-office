# Office schema (v0, approved 25 Nov 2026 — T-001)

An office is a folder. The engine loads it; nothing about an office is hard-coded in the engine.

```
offices/<office-id>/
  office.yaml      required
  org.yaml         required
  workflow.yaml    required
  agents/*.md      required (at least the agents named in org.yaml)
  skills/          optional
  theme/theme.yaml optional (default theme if missing)
  backlog/T-*.md   required (may be empty)
  board.md         generated
```

## office.yaml

| Key | Type | Meaning |
|---|---|---|
| `id` | string | Folder name, kebab-case |
| `name` | string | Display name |
| `purpose` | string | One sentence |
| `brain` | `work` \| `personal` | Which brain in `workspaces.yaml` agents read and write |
| `projects` | list | Keys from `workspaces.yaml` this office may touch |
| `human` | object | `name`, `approves` (list of gates the human owns) |
| `budget` | object | `monthly_usd_cap`, `max_review_rounds` |
| `defaults` | object | `model`, `branch_prefix` |

## org.yaml

`agents`: list of `{ id, reports_to, role }`. `id` must match a file in `agents/`. The top of the chart reports to `human`.

## workflow.yaml

| Key | Meaning |
|---|---|
| `stages` | Ordered list of `{ id, owner, output_section, exit }`. `id` values are the allowed task `status` values. |
| `terminal` | Stages that end a task (`done`, `parked`). |
| `gates` | `{ stage, approver }`: transitions that need a human or a named agent before moving on. |
| `escalation` | Rules such as `review_rejections >= 2 → human`. |
| `status_writers` | Who may change `status` (default: PMO only, plus listed exceptions). |

## agents/<id>.md

Claude Code subagent format plus two optional keys:

```yaml
---
name: reviewer
extends: base/reviewer        # optional: start from base/agents/reviewer.md
description: ...              # when to use this agent
tools: Read, Grep, Glob, Bash # allowed tools
model: opus                   # opus | sonnet | haiku
office_skills: [...]          # optional: skills from skills/ to load
---
Body: mission, inputs, outputs, rules, hands off to, escalates when.
```

With `extends`, the office file's frontmatter keys override the base's, and its body is appended under "## Office-specific".

## backlog/T-xxx-slug.md

```yaml
---
id: T-001
title: ...
phase: 1-brain
status: todo          # one of workflow.stages ids, or a terminal
priority: P0          # P0 | P1 | P2
owner: pmo            # agent id or human
where: code           # chat | code | office
project: ai-office    # key from workspaces.yaml
depends_on: []
pr: null
---
## Done when
- [ ] ...
## Spec
## Design
## Build notes
## Review log
## Decision
## Open questions
```

## theme/theme.yaml

| Key | Meaning |
|---|---|
| `style` | Free label for the renderer, e.g. `pixel-startup`, `bank-floor` |
| `palette` | Named colors |
| `rooms` | `{ id, label, stage }`: one room per workflow stage; tasks in that stage show there |
| `desks` | `{ agent, room, sprite }`: where each agent sits |
| `hub` | Where handoffs are drawn (agents walk between rooms) |

## Decisions (v0)

- `skills/` follows the Agent Skills folder format: `skills/<name>/SKILL.md`.
- A task belongs to exactly one office. Cross-office links use `depends_on: <office-id>/T-xxx`.
