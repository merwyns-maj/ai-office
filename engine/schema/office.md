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

## Base (shared by every office)

```
base/
  agents/<name>.md             profiles an office agent can `extends`
  skills/<name>/SKILL.md       shared skills, Agent Skills format
  defaults.yaml                repo-wide defaults, flat `key: [list]` lines only
```

`defaults.yaml` `base_skills` lists base skills that every agent of every office follows, with no per-agent edit. An agent may add more with its own `base_skills` key. The effective list is, in order and de-duplicated: `defaults.yaml` `base_skills`, the agent's `base_skills`, its `office_skills`. A skill name lives in `base/skills/` or in one office's `skills/`, never both; build and validate fail on a clash. Every name must resolve to a `SKILL.md`. Added in T-014; optional, so existing offices stay valid.

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

`agents`: list of `{ id, name, personality, reports_to, role }`. `id` must match a file in `agents/`. The top of the chart reports to `human`.

## workflow.yaml

| Key | Meaning |
|---|---|
| `stages` | Ordered list of `{ id, owner, output_section, exit }`. `id` values are the allowed task `status` values. |
| `terminal` | Stages that end a task (`done`, `parked`). |
| `gates` | `{ stage, approver }`: transitions that need a human or a named agent before moving on. |
| `consults` | Optional list of { agent, stage, when, output_section, accepted_by }: an org agent called inside a stage. It writes only its own section and never sets status or owner; accepted_by must be the stage owner; output_section must not be a stage's section. Added in T-047. |
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
base_skills: [...]            # optional: extra skills from base/skills/<name>/SKILL.md, on top of base/defaults.yaml
office_skills: [...]          # optional: skills from skills/<name>/SKILL.md to follow
external_skills: [claude:skill-creator]  # optional: skills outside the repo, source from workspaces.yaml skill_sources
display_name: Emmy            # optional persona: shown in the app and in task signatures
personality: ENFJ             # optional persona: communication style (MBTI-style label)
role_title: Product Manager   # optional persona
---
Body: mission, inputs, outputs, rules, hands off to, escalates when.
```

With `extends`, the office file's frontmatter keys override the base's, and its body is appended under "## Office-specific". Persona keys are an office choice, so the same base Reviewer can be Cahyani in one office and someone else in another. The personality label sets tone and working style only; competence comes from the profile and skills.

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
