---
id: T-047
title: "Hire a product designer agent (Dinda) with a researched playbook"
phase: 0-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: []
pr: https://github.com/merwyns-maj/ai-office/pull/24
---

> Merwyn, 25 Nov 2026: "if you need to hire a product designer please do and give her a correct skills to work on". The office has no one who owns how things look and move; T-048 (3D office) needs her.

## Done when
- [ ] A base agent base/agents/designer.md (mission, inputs, outputs, rules, escalation) and an office profile offices/ai-office/agents/designer.md for **Dinda**, Product Designer, ISFP, with persona style, watch-out and sign-off line like the other seven
- [ ] A designer-playbook office skill built from cited sources (motion principles, low-poly three.js performance, ambient status displays, accessibility incl. reduced motion), each rule with a source or "office rule"
- [ ] The designer has a clear place in workflow.yaml (when she is called, which task section she writes, who approves), org.yaml and theme/theme.yaml (desk + sprite)
- [ ] External design skills she uses are valid source:name entries (add any missing source to workspaces.yaml skill_sources)
- [ ] python scripts/build_agents.py ai-office exits 0 and generates .claude/agents/designer.md; all tests pass

## Spec

**Problem.** No agent owns how things look, move and read. T-048 (3D office) needs a visual and motion design before anyone builds, and Fang's Design section is technical, not visual.

**In scope**
- New base agent `base/agents/designer.md` and office profile `offices/ai-office/agents/designer.md` for **Dinda**, Product Designer, ISFP (style, watch-out, sign-off "— Dinda (designer)"), same shape as the other seven.
- Place in the workflow: a **consult in the design stage**. When Fang's Design finds UI or visual work, Janice (or Fang) calls Dinda, who writes a `## UX design` section in the task file. Fang still owns `## Design` and the design stage exit. Dinda is not a new stage and cannot set status.
- Office skill `designer-playbook`, each rule tagged with a source URL or "office rule". Minimum source set: the nine below.
  1. Codrops 2025, efficient Three.js scenes (low poly, Draco): https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/
  2. three.js forum, far characters update less often: https://discourse.threejs.org/t/one-draw-call-massive-crowd-performance-engineering-in-three-js/89928
  3. three.js forum, join geometry / single texture: https://discourse.threejs.org/t/how-do-i-handle-lag-in-my-scene/7883
  4. Codrops Windland, bake lighting: https://tympanus.net/codrops/2022/04/25/case-study-windland-an-immersive-three-js-experience/
  5. IxDF, Disney's 12 principles in UI: https://ixdf.org/literature/article/ui-animation-how-to-apply-disney-s-12-principles-of-animation-to-ui-design
  6. UX in Motion, "Disney is Dead" (easing; UI needs its own principles): https://medium.com/ux-in-motion/ui-animation-principles-disney-is-dead-8bf6c66207f9
  7. ParallelPilot, ambient dashboard, running vs needs_attention: https://arxiv.org/pdf/2609.33113
  8. Agent Status Protocol, lifecycle strip, sort by attention: https://arxiv.org/pdf/2610.21538
  9. ArcGIS, effective dashboards (one audience, drop non-essentials): https://doc.arcgis.com/en/dashboards/reference/author-effective-dashboards.htm
- Skill sources: add `anthropic-skills` to `workspaces.yaml` `skill_sources`. Candidate external skills: `anthropic-skills:design-studio`, `frontend-design`, `ui-ux-pro-max`, `ui-ux-field-rules`, `diagram-design`, plus `design:design-critique`, `design:accessibility-review`, `design:design-handoff`, `design:ux-copy`.
- Entries in `org.yaml` and `theme/theme.yaml` (desk and sprite).

**Out of scope**
- Doing T-048's design (that is Dinda's first job after this lands) or any UI build.
- A new workflow stage, new human gate, or giving Dinda status-writer rights.
- Installing external skills for the SDK engine (R-3, T-024).
- Figma or other connectors (human gate).

**Done when**
- [ ] `base/agents/designer.md` has Mission, Inputs, Outputs (section `UX design`), Rules, Hands off to, Escalates when; `offices/ai-office/agents/designer.md` names Dinda, ISFP, with style, watch-out and sign-off, like `reviewer.md`.
- [ ] `designer-playbook/SKILL.md` exists; every rule line ends with a URL or the words "office rule"; the nine sources above all appear; a section on accessibility incl. reduced motion exists. A reviewer can grep rules with neither.
- [ ] `workflow.yaml` states when Dinda is called (design stage, task has UI or visual work), the section she writes (`UX design`), and who accepts it (Fang folds it into Design; Janice's spec gate unchanged). `org.yaml` lists her with `reports_to`; `theme.yaml` has a `desk` with room and sprite, and no new room unless a stage needs it.
- [ ] Every entry in her `external_skills` is `source:name` with the source present in `skill_sources`; `anthropic-skills` is added with `where` and a note that it is chat-only today (R-3). No skill is listed whose source is missing.
- [ ] `python scripts/build_agents.py ai-office` exits 0 and `.claude/agents/designer.md` exists; the full test suite passes (paste the output).
- [ ] No existing stage, gate or other agent is changed (diff of `workflow.yaml` touches only the new consult entry).

**Risks**
- `workflow.yaml` may not allow a new `consults` key without a script or test change; the tests could fail.
- Playbook rules drift into opinion; the "or office rule" tag keeps it honest.
- Design-skill names exist only in Merwyn's app (R-3); validate cannot prove they exist.

**Open questions**
- Accessibility and reduced-motion: none of the nine sources covers it. Who finds a primary source (e.g. W3C WCAG animation guidance)? Fang or Sebastian at design; blocking only for the "cited" check, otherwise tag "office rule".
- `dataviz` has no source prefix today. Which source does it belong to? Merwyn. Default: leave it out.
- `reports_to` for Dinda: pmo (recommended) or architect? Janice.
- Does `scripts/` (validate, board) accept a consult entry in `workflow.yaml`? Fang.
- Desk location: share the Design wall with Fang or sit in the lobby? Dinda and Fang decide in T-048.

— Emmy (pm)

## Design

**Baseline (25 Nov, this worktree, before any change):** `python -m unittest discover -s tests` ran 158 tests, OK. `python -m engine.runtime validate ai-office` printed "ai-office: OK — 7 agents, 5 stages, 48 tasks, 15 skills". `python scripts/build_agents.py ai-office` exited 0 and built 7 agents.

**Finding behind the loader change.** I added a `consults:` list to a temp copy of workflow.yaml. validate, dry-run and board.py all exited 0, and so did a consult naming `designer` while no such agent was in org.yaml. Unknown workflow keys are ignored without a word, so a typo such as `agent: desginer` would pass. That is the same silent-failure pattern as R-11. So validate learns the key (a small check with tests) and dry-run shows it. The approval puts this in scope.

**Approach** (config, a new agent and one small logic change; files below)
- New: `base/agents/designer.md`, `offices/ai-office/agents/designer.md`, `offices/ai-office/skills/designer-playbook/SKILL.md`.
- Edited, additions only: `offices/ai-office/workflow.yaml` (new `consults:` block), `offices/ai-office/org.yaml` (1 line), `offices/ai-office/theme/theme.yaml` (1 desk line), `workspaces.yaml` (1 `skill_sources` line).
- Logic: `engine/runtime/loader.py` validates `consults`; `engine/runtime/dryrun.py` adds one `consults` row for the task's stage. Doc: one row in `engine/schema/office.md` under workflow.yaml. Tests: `tests/test_loader.py`, `tests/test_dryrun.py`.
- Regenerated: `.claude/agents/` (adds designer.md; the other 7 must stay byte-identical).
- Not changed: any stage, gate, `status_writers`, the other agents' profiles, the handoff skill, build_agents.py. build_agents already accepts any `skill_sources` key matching `[\w-]+`, so `anthropic-skills` works with no code change.

**How a consult runs.** The task stays at `status: design` with `owner: architect` the whole time. Janice (or Fang, from a main session) calls Dinda on the task. She adds `## UX design` directly under `## Design`, signs it and stops. She changes neither `status` nor `owner`. Fang reads it, folds what he accepts into Design (by reference or by summary), and keeps the stage exit. Because the owner never moves, the handoff rule ("never leave a task with an owner who doesn't own that stage") still holds and no skill has to change.

**Interfaces**

1. `offices/ai-office/workflow.yaml`: insert this after the `terminal:` line. Nothing else in the file changes.
```yaml

# Consults (T-047): an agent called inside a stage by the PMO or the stage owner. Not a stage: the consult
# writes only its own section and never sets status or owner. The task stays with the stage owner, who accepts it.
consults:
  - { agent: designer, stage: design, when: "the Spec or Design has UI, visual or motion work", output_section: UX design, accepted_by: architect }
```
I checked that miniyaml parses this line to `{'agent': 'designer', 'stage': 'design', 'when': '...', 'output_section': 'UX design', 'accepted_by': 'architect'}`.

2. `loader.validate`, section 5, after the gates loop. `consults` is optional; when it is missing, validate does nothing new. Exact messages, all reported against workflow.yaml:
   - not a list: `'consults' must be a list`
   - an entry that is not a map, or is missing any of agent, stage, when, output_section, accepted_by (or one is empty): `consult {c!r} needs agent, stage, when, output_section and accepted_by`
   - `agent` not in org_ids: `consult agent '<a>' is not an org agent`
   - `stage` not in `office.stage_ids` (terminal stages are not allowed): `consult stage '<s>' is not a workflow stage`
   - `accepted_by` is not that stage's `owner`: `consult accepted_by '<x>' must be the owner of stage '<s>' ('<owner>')`
   - `output_section` equals any stage's `output_section`: `consult output_section '<o>' is already a stage's output_section`. This stops a consult from overwriting Design.

3. `dryrun.plan`: after the `output_section` row, if any consult has `stage == task.status`, append one row (several consults are joined with "; "):
   `("consults", "designer (Dinda) writes UX design when the Spec or Design has UI, visual or motion work")`. The format is `<agent> (<org name>) writes <output_section> when <when>`, and the name comes from org the same way the `owner` row gets it. Stages with no consult get no row. The existing "note: task owner … differs from stage owner" logic stays as it is.

4. `engine/schema/office.md`, workflow.yaml table, new row:
   `| consults | Optional list of { agent, stage, when, output_section, accepted_by }: an org agent called inside a stage. It writes only its own section and never sets status or owner; accepted_by must be the stage owner; output_section must not be a stage's section. Added in T-047. |`

5. `base/agents/designer.md`, frontmatter `name: designer`, `tools: Read, Grep, Glob, Edit, Write, Bash`, `model: sonnet`. Description: "Product designer. Use in the design stage when a task has UI, visual or motion work: layout, states, motion and accessibility, written as a UX design the Architect folds into Design." Body sections, in this order:
   - **Mission**: make what the office ships readable at a glance, pleasant to watch and usable by everyone, before anyone builds it.
   - **Inputs**: approved Spec, the Architect's Design so far, `theme/theme.yaml`, existing UI in the repo.
   - **Outputs (task section: UX design)**: layout and hierarchy (what is seen first, what is left out); every state and how it looks (e.g. idle, active, needs Merwyn); motion per event (purpose, duration, easing) plus its reduced-motion version; a visual spec (palette from theme.yaml, shapes, sizes) concrete enough to build without guessing; an accessibility check; open questions, each with who can answer.
   - **Rules**: one audience and one question per screen; every motion has a purpose; every animation has a reduced or still alternative; reuse theme.yaml and existing patterns first; you write UX design, the Architect accepts it, and you never set status or owner.
   - **Hands off to**: Architect.
   - **Escalates when**: a taste call that no rule settles, where the Architect disagrees; any need for a new tool, connector or paid asset (human gate).

6. `offices/ai-office/agents/designer.md`, same shape as reviewer.md:
```
---
name: designer
extends: base/designer
display_name: Dinda
personality: ISFP
role_title: Product Designer
office_skills: [designer-playbook, handoff]
external_skills: [anthropic-skills:design-studio, anthropic-skills:frontend-design, anthropic-skills:ui-ux-pro-max, anthropic-skills:ui-ux-field-rules, claude:diagram-design, design:design-critique, design:accessibility-review, design:design-handoff, design:ux-copy]
---
You are **Dinda**, the office's Product Designer. Personality: ISFP.
- Style: Visual and hands-on. Sketches the thing before describing it; cares how it feels to watch and checks that it reads at a glance.
- Watch-out: Can polish what nobody asked for; design the state Merwyn must not miss first, and give every motion a reason.
- Sign your entries in task files as "— Dinda (designer)".
- Office: AI Office — Build Office. Brain: personal. Only project: ai-office.
- Read `offices/ai-office/workflow.yaml` before acting.
```
   `diagram-design` goes under `claude:` because that is the source the architect profile already uses. `dataviz` stays out (approval).

7. `workspaces.yaml`, under `skill_sources`, after `data:`:
   `  anthropic-skills: { where: "Claude app skills from Anthropic's skills library (Skill tool)", note: "chat-only today: not installed for the SDK engine (R-3, T-024)" }`

8. `offices/ai-office/org.yaml`, appended after curator:
   `  - { id: designer,   name: Dinda,    personality: ISFP, reports_to: pmo,       role: Product Designer }`

9. `offices/ai-office/theme/theme.yaml`, appended after the curator desk:
   `  - { agent: designer, label: Dinda,     room: whiteboard, sprite: designer }`. No new room: the consult happens in the design stage, so she sits at the Design wall. Nothing in code reads sprites yet (grep), so the name `designer` is free. T-048 may move the desk.

10. `designer-playbook/SKILL.md`, with frontmatter `name: designer-playbook` and a description ("How Dinda designs UI, motion and the 3D office: glanceable status, purposeful motion, light three.js scenes, reduced motion. Use whenever a task has a UX design section."). Every rule line ends with a URL or "office rule". Sections and the sources behind them:

| § | Section | Rules drawn from |
|---|---|---|
| 1 | Who and what it is for | ArcGIS effective dashboards (one audience, drop non-essentials); office rule: one screen answers one question |
| 2 | Ambient status displays | ParallelPilot arXiv 2609.33113 (running vs needs_attention kept distinct); Agent Status Protocol arXiv 2610.21538 (lifecycle strip, sort by attention); office rule: "waiting for Merwyn" is the most visible state |
| 3 | Motion | IxDF Disney's 12 principles in UI (slow in/out, staging, follow-through); UX in Motion "Disney is Dead" (easing; UI motion serves continuity and relationships, not cartoon); office rule: each motion names its purpose; any duration figure is an office rule unless a source states it |
| 4 | Low-poly three.js scenes | Codrops 2025 (low poly, Draco compression); three.js forum 7883 (merge geometry, one shared texture); three.js forum 89928 (far characters update less often); Codrops Windland (bake lighting); office rule: 8 agents at a smooth frame rate on a laptop (the T-048 target) |
| 5 | Accessibility incl. reduced motion | WCAG 2.3.3 Animation from Interactions; C39 (`prefers-reduced-motion` in CSS); SCR40 (`matchMedia('(prefers-reduced-motion: reduce)')` in script, for three.js); office rule: no state shown by colour or motion alone |
| 6 | Writing the UX design section | office rule: the order of the Outputs in base/agents/designer.md; design:design-handoff for the build handoff |
| — | Sources | the 12 URLs: the 9 in the Spec and the 3 W3C links in the Approvals |

   The Engineer opens each source and writes only what it says (A2). If a source cannot be fetched, its rule is tagged "office rule" and the source is named in Build notes. Nothing is attributed to a paper without reading it. That matters most for the two arXiv IDs, which I could not check from here.

**Tools and model**

| Option | For | Against |
|---|---|---|
| Tools `Read, Grep, Glob, Edit, Write, Bash` (chosen) | She writes her own section; Bash runs handoff step 5 (board.py) and lets her inspect asset sizes or serve a static page for T-048 | Bash is broad; the prod guard and the repo-only project cover it |
| Without Bash, like pm | Narrower | She cannot run board.py or check a prototype; another agent would have to run it for her |
| `model: sonnet` (chosen) | Same as pm, engineer and curator; she runs only on UI tasks; lower cost against the budget gate | Weaker on hard visual judgement |
| `model: opus` | Better judgement on new visual work | Costs more on every consult; this is a one-line change later if her T-048 output is weak |

**Test plan** (paste real output into Build notes)
- New tests in `tests/test_loader.py`, using the existing `OfficeCopy` + `check` pattern: (a) the real office with the consult validates clean; (b) `consults: x` gives "must be a list"; (c) an entry without `accepted_by` gives "needs agent, …"; (d) `agent: desginer` gives "not an org agent"; (e) `stage: done` gives "not a workflow stage"; (f) `accepted_by: pmo` gives "must be the owner of stage 'design' ('architect')"; (g) `output_section: Design` gives "already a stage's output_section"; (h) removing `consults` entirely still validates clean.
- `tests/test_dryrun.py`: the allowed key set on line 22 becomes `KEYS + ["note", "consults"]`; `test_plan_content` (the design-stage task) asserts the `consults: designer (Dinda) writes UX design when …` line; a todo-stage task has no `consults:` row.
- `python -m unittest discover -s tests`: all pass (158 + the new ones).
- `python -m engine.runtime validate ai-office`: "OK — 8 agents, 5 stages, N tasks, 16 skills".
- `python scripts/build_agents.py ai-office` exits 0 and lists 8 agents. `.claude/agents/designer.md` exists with the "Dinda (Product Designer)." description, Skills (working-standard, designer-playbook, handoff) and the 9 external skills. `git diff --stat .claude/agents` shows only designer.md as new.
- Playbook check: `grep -nE '^\s*[-|]' offices/ai-office/skills/designer-playbook/SKILL.md | grep -vE 'https?://|office rule'` returns only table header or separator lines, if any. All 12 URLs are present.
- `git diff offices/ai-office/workflow.yaml` shows only added lines.

**Risks**
- *Unknown keys pass silently.* Handled by the validate check above.
- *External skill names cannot be proven (R-3).* Validate and build check only `source:name` and that the source is listed. I could not confirm that `frontend-design`, `ui-ux-pro-max` and `ui-ux-field-rules` live under `anthropic-skills` rather than `claude`. The Spec lists them after `anthropic-skills:design-studio`, so I default to that; see Open questions.
- *Playbook drifts into opinion, or puts words in a paper's mouth.* Every line is tagged, the Engineer reads each source, and the Reviewer runs the grep above.
- *Consult role creep* (Dinda sets status or redesigns the architecture). Her base Rules and the workflow comment say she writes only UX design; validate stops her section from being a stage's section.
- *Rebuild churn.* build_agents deletes and rewrites `.claude/agents/`; the diff must show the other 7 unchanged.

**Compliance flag: not flagged.** Nothing touches prod, money movement, credentials or personal data. The new agent works only in this repo (project ai-office), and the external skills are chat-side pointers with no connector (Figma stays out: human gate). Hands off to Sebastian (engineer).

**Decision record draft (for April)**
```
Decision: Workflow "consults" are a top-level workflow.yaml list of { agent, stage, when, output_section, accepted_by }, validated by the loader and shown by dry-run.
Context: T-047 adds Dinda inside the design stage, not as a stage. Unknown workflow keys were silently ignored (probe on 25 Nov).
Options: A — top-level consults list + validate check (one place, checked, no stage line edited); B — a consults key inside the design stage map (edits an existing stage line, still unchecked); C — prose comment only (no code, but typos and drift pass silently).
Chosen: A, because it keeps existing stages untouched and turns a silent typo into a validate error for about 20 lines of code.
Consequences: Consult output is accepted by the stage owner and never moves status or owner. The SDK engine (T-024) can schedule consults from this list later. A second consult type (e.g. data viz) is one more list entry.
Links: T-047, T-048
```

— Fang (architect)

## Approvals (PMO)
Spec approved 25 Nov 2026. Answers: Dinda reports_to pmo. Accessibility and reduced-motion rules cite W3C WCAG 2.3.3 Animation from Interactions (https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions), technique C39 (https://www.w3.org/WAI/WCAG22/Techniques/css/C39) and SCR40 (https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR40). dataviz stays out (no source). Consult key in workflow.yaml: Fang decides the shape; if loader or dry-run must change, that is in scope with tests. — Janice (pmo)

Design accepted 25 Nov 2026; moved to build. Fang's open question answered: frontend-design, ui-ux-pro-max and ui-ux-field-rules are listed in this Claude app session as `anthropic-skills:` skills, so `anthropic-skills` is right. — Janice (pmo)

## Build notes
**What changed** (PR #24, commit 0419c6e)
- New: `base/agents/designer.md`, `offices/ai-office/agents/designer.md` (Dinda, ISFP, as in the Design), `offices/ai-office/skills/designer-playbook/SKILL.md`, generated `.claude/agents/designer.md`.
- Additions only: `workflow.yaml` consults block (diff has 0 removed lines), `org.yaml`, `theme/theme.yaml`, `workspaces.yaml` (`anthropic-skills`).
- Logic: `engine/runtime/loader.py` (consults validation, 6 messages as designed), `engine/runtime/dryrun.py` (consults row), `engine/schema/office.md` (row).
- Tests: 8 new in `tests/test_loader.py` (class Consults), dry-run assertions in `tests/test_dryrun.py`.

**How to verify (real output, 25 Nov)**
- `python -m unittest discover -s tests`: `Ran 166 tests ... OK` (158 + 8 new).
- `python -m engine.runtime validate ai-office`: `ai-office: OK — 8 agents, 5 stages, 48 tasks, 16 skills`.
- `python scripts/build_agents.py ai-office`: `built 8 agents -> .claude/agents/ (architect, compliance, curator, designer, engineer, pm, pmo, reviewer)`; git shows only designer.md as new under `.claude/agents`, the other 7 unchanged.
- Playbook grep from the Design: only the two frontmatter `---` lines come back. All 12 URLs are in the Sources list.
- board.py ran; board.md discarded.

**Deviations from the Design**
- `tests/test_miniyaml.py` line 27 asserted 7 org agents; changed to 8. The Design did not list this file.
- Sources: **I fetched none myself.** Every host (tympanus.net, discourse.threejs.org, ixdf.org, medium.com, arxiv.org, doc.arcgis.com, www.w3.org) returned a proxy 403 from this sandbox, so I did not retry. All twelve sources come from Janice's search findings (main session, 25 Nov), not full pages: Codrops 2025, both three.js forum threads (89928, 7883), Windland, IxDF, UX in Motion, ParallelPilot, Agent Status Protocol, ArcGIS, and the three W3C pages (WCAG 2.3.3, C39, SCR40). The playbook's Sources section says so.
- I left out two things the Design table listed because Janice's findings do not state them: IxDF "slow in/out, staging, follow-through" and UX in Motion "not cartoon". I also dropped the "25 skinned characters at 120 fps" finding because it came from a different forum thread with no URL in the source set. Someone with network access should read the two arXiv papers and the Disney pages before T-048 leans on them.
- Duration and easing figures are not given; the playbook tags that as an office rule.

**Known limits**
- External skill names (`anthropic-skills:*`, `design:*`) cannot be proven by validate (R-3).

— Sebastian (engineer)

## Review log

## Decision

## Open questions
- Do `frontend-design`, `ui-ux-pro-max` and `ui-ux-field-rules` live under `anthropic-skills` (the default in Design) or under `claude`? Answer: Merwyn, who can see them in his Claude app. Not blocking: a wrong prefix is a one-word fix and both sources exist. — Fang (architect)
