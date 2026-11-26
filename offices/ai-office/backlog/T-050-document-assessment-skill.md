---
id: T-050
title: "Partner or vendor document assessment skill"
phase: 3-skills
status: done
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: []
pr: 35
---

> From T-031 (Nov 2026 chat review), picked by Merwyn on 26 Nov 2026. 3 chats (research/T-031-2026-11.md, topic 4). Generic method only; any real partner document stays where it lives.

## Done when
- [ ] A skill that turns a partner's API, tech doc or template agreement into a gaps-and-risks assessment with a fixed structure
- [ ] 3 golden cases with invented documents (scripts/golden.py passes)
- [ ] Loaded by the agents that will use it

## Spec

**Problem.** When a partner or vendor sends an API doc, tech doc or template agreement, each assessment is written from scratch and its gaps and risks vary in shape and depth. Merwyn's chat review (T-031) found this repeated in 3 chats, and nothing in the office guides it.

**In scope**
- One skill, under `base/skills/` or `offices/ai-office/skills/` (Fang chooses), that takes a partner document (API or tech doc, template agreement) and produces a gaps-and-risks assessment in a fixed structure.
- The fixed structure: what the document is and covers; gaps (what is missing or unclear); risks (each with severity and why); questions to send back to the partner; a clear line for what was not reviewed. Fang may refine headings.
- 3 golden cases using invented documents (for example one API doc, one tech doc, one template agreement), run by `scripts/golden.py`.
- Skill loaded by the agents that use it. Proposal: architect for API and tech docs, compliance for agreements. Fang and Janice decide.

**Out of scope**
- Any real partner or company document, name or figure; real documents stay where they live.
- Legal advice or sign-off: the skill flags risks for a human, it does not approve a contract.
- Running an LLM on the cases (golden checks recorded text only).
- Skills for T-051 to T-053.

**Done when**
- [ ] A `SKILL.md` exists with valid frontmatter, and its output structure lists each required heading by name.
- [ ] `ls <skill>/golden/` shows 3 cases, each with input, expected output, checks, human note and why; `python scripts/golden.py ai-office` exits 0 and lists the skill with 3 cases.
- [ ] Each case has a `bad_output` (for example a missing risks section or no "not reviewed" line) that fails at least one check.
- [ ] The three invented documents cover an API doc, a tech doc and a template agreement; the golden data scan reports no hit, and a reviewer reading the cases finds no real partner, product or figure.
- [ ] Each assessment in the cases states what was not reviewed, and does not claim legal approval (a must_not_match check).
- [ ] The skill is named in the `skills:` list of each chosen agent; `python scripts/build_agents.py ai-office` and `python -m engine.runtime validate ai-office` exit 0.
- [ ] `python -m unittest` passes.

**Open questions**
- Which agents load it: architect and compliance as proposed, or also the PM? Fang and Janice; not blocking.
- Base or office skill: base if other offices could use it. Fang; not blocking.
- Should risk severity use fixed levels (high, medium, low) and a rule for each? Fang; not blocking.
- Does Merwyn want Indonesian-language assessments (partner-writing B2 rules)? Merwyn; not blocking, default English.

— Emmy (pm)

## Design

Baseline (26 Nov, this worktree at 95cc937): `python -m unittest` OK; `python scripts/golden.py ai-office` exit 0, "10 cases, 41 checks, 0 problems"; `build_agents.py ai-office` built 8 agents; `python -m engine.runtime validate ai-office` OK, 17 skills.

**Approach**
- New office skill `offices/ai-office/skills/document-assessment/SKILL.md` (not base). This office is the only one, and only two of its agents use the skill. Moving it to `base/skills/` later means a `git mv` plus changing `office_skills` to `base_skills` in two agent files, which is cheap and reversible.
- Golden cases in `offices/ai-office/skills/document-assessment/golden/`, run by the existing `scripts/golden.py`. No runner change.
- Wiring: add `document-assessment` to `office_skills` in `offices/ai-office/agents/architect.md` (API and tech docs) and `offices/ai-office/agents/compliance.md` (template agreements), as Janice approved. The PM does not load it. Then run `python scripts/build_agents.py ai-office` and commit the regenerated `.claude/agents/architect.md` and `compliance.md`.
  - architect: `office_skills: [architect-playbook, decision-record, document-assessment, handoff]`
  - compliance: `office_skills: [compliance-playbook, uu-pdp-checklist, document-assessment, handoff]`

**SKILL.md interface**
- Frontmatter: `name: document-assessment`; `description: Turn a partner or vendor API doc, tech doc or template agreement into a gaps-and-risks assessment with a fixed structure. Use when a partner document arrives for review. Flags risks for a human; not legal advice or approval.`
- Body: a short purpose paragraph, then the rules, then the output template. Rules use these names, which are also the golden `rules` values: `Document`, `Gaps`, `Risks`, `Questions`, `Not reviewed`, `No approval`, `Data`.
- Output template. Exact headings, in this order:
  ```
  ## Document
  <what it is, version or date if stated, what it covers; 1 to 3 lines>
  ## Gaps
  - G1 <what is missing or unclear, and where in the document>
  ## Risks
  - R1 [high|medium|low] <risk>. Why: <reason, citing the gap or clause>.
  ## Questions for the partner
  1. <question> (G1)
  ## Not reviewed
  - <part, annex, linked doc or aspect not read, or "Nothing left out: all N pages read">
  This assessment flags risks for a human decision. It is not legal review or approval.
  ```
- Severity, fixed levels (answers Emmy's open question):
  - **high**: can cause money loss or mis-routed funds, personal data exposure, a regulatory breach, or blocks go-live.
  - **medium**: needs a written answer or a fix before signing or building, and a workaround exists.
  - **low**: clarity or consistency issue with no direct impact.
  When unsure between two levels, pick the higher one and say why.
- Rule `Questions`: each question names the gap or risk ID it closes. When the questions are sent to the partner as written, also apply `base/skills/partner-writing` (B1, B3, B4).
- Rule `No approval`: never write that a document is approved, safe to sign, legally compliant or free of legal risk. For legal and regulatory points, name who answers: KlikA2C legal or compliance, through Merwyn. This matches the compliance-playbook line.
- Rule `Data`: the assessment lives where the document lives (the company repo or Drive), and the task file links to it. Never paste a real partner document, name, figure or credential into this repo. Golden cases use invented documents only.
- Language: English by default. If Merwyn asks for Indonesian, partner-writing B2 applies. His answer stays an open question; not blocking.

**Golden cases** (existing format; each file has `skill`, `rules`, `input`, `expected_output`, `checks`, `bad_output`, `human_note`, `why`)

| File | Invented input (about 10 to 15 lines in `input`) | `bad_output` fails because |
|---|---|---|
| `api-doc.json` | A fictional payment-status REST API ("Partner A"): two endpoints, no error codes, no idempotency key, a vague rate limit | the `## Risks` section is missing |
| `tech-doc.json` | A fictional vendor's batch file-transfer spec: SFTP, a daily file, no retry or checksum, encryption "per agreement" | the `## Not reviewed` heading is missing, or has no bullet under it |
| `template-agreement.json` | A fictional services template: auto-renewal, unlimited liability cap blank, data-processing annex "to follow" | it says the agreement is "safe to sign" (fails the no-approval check) |

Checks in every case (same set, so each is checked three times):
1. `must_match` for each of the 5 headings, one check each: `^## Document$`, `^## Gaps$`, `^## Risks$`, `^## Questions for the partner$`, `^## Not reviewed$`.
2. `must_match` `^- R\d+ \[(?:high|medium|low)\] .+Why: ` (rule `Risks`): at least one well-formed risk.
3. `must_not_match` `^- R\d+(?! \[(?:high|medium|low)\] )` (rule `Risks`): no risk line without a severity. This is the per-line lookahead form chosen in T-054.
4. `must_match` `^## Not reviewed\n- \S` (rule `Not reviewed`).
5. `must_not_match` `(?i)\b(?:legally (?:approved|compliant|sound)|approved for sign(?:ing|ature)|safe to sign|no legal risk)\b` (rule `No approval`).
6. `must_contain` `It is not legal review or approval.` (rule `No approval`).
7. `max_lines` 40.

Invented content: use "Partner A", "Vendor B" and round figures (for example 100 requests per minute). No 10+ digit runs, emails, real company or product names, or any term in `workspaces.yaml`. The golden data scan enforces this, and the Reviewer reads for real names.

**Test plan**
- `python scripts/golden.py ai-office` exits 0 and lists `document-assessment: 3 cases OK` (total 13 cases).
- Mutation check by hand, recorded in Build notes: drop a severity tag from one risk line in an `expected_output`, confirm exit 1, then revert.
- `tests/test_golden.py` `Shipped`: add `document-assessment` to the skill list in `test_exit_0_with_three_skills` and its folder in `test_case_counts_3_to_5_per_skill`. Do not hard-code the total case count (T-054 runs in parallel).
- `python scripts/build_agents.py ai-office`, `python -m engine.runtime validate ai-office` (expect 18 skills), `python -m unittest`, all exit 0.

**Risks**
- Over-strict checks make real assessments rigid. The headings are the contract; content under them is free. The `human_note` in each case says what a human judges: the severity fits the rule, and the questions close the gaps.
- A real partner document leaking into a case. Handled by the Data rule, the golden scan and the Reviewer read.
- The skill used as legal sign-off. Handled by the `No approval` rule, the fixed closing line and checks 5 and 6.
- Merge order with T-054: if T-054 merges first, its zero-case exit and its per-line form do not affect these cases. Either order works.

**Flags.** Compliance: not flagged. The skill writes text only, and the cases are invented with no prod, money movement or personal data. Real use on partner documents happens in company locations under the Data rule. UX consult: not needed (no UI).

**Decision record draft (for Curator)**
```
Decision: document-assessment is an office skill loaded by architect and compliance, with a fixed five-heading output and three severity levels.
Context: T-050 from T-031; partner-document assessments varied in shape across 3 chats.
Options: A office skill, two agents load it; B base skill, available to every office, but no second office exists yet.
Chosen: A because only this office uses it; moving to base later is a git mv and a frontmatter change.
Consequences: Assessments share headings that golden checks can test; severity follows fixed rules. Move to base when a company office needs it.
Links: T-050, T-031
```

— Fang (architect)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: loaded by architect (API and tech docs) and compliance (agreements), as Emmy proposed; Fang confirms. — Janice (pmo)

Janice (pmo), 26 Nov: Design accepted, moved to build. Indonesian-language assessments: write in English by default; when asked in Indonesian, follow partner-writing (financial terms stay English). Not blocking. Engineer: do not set status.

## Build notes

**What changed**
- New `offices/ai-office/skills/document-assessment/SKILL.md` (office skill, per Design): rules Document, Gaps, Risks, Questions, Not reviewed, No approval, Data; fixed severity levels; output template with the five headings.
- 3 golden cases in `offices/ai-office/skills/document-assessment/golden/`: `api-doc.json`, `tech-doc.json`, `template-agreement.json`. Invented documents (Partner A, Vendor B, round figures). Same 11 checks each, as in the Design table; each has a `bad_output` (no Risks section; no Not reviewed section; "safe to sign").
- `document-assessment` added to `office_skills` of architect and compliance; `build_agents.py` regenerated `.claude/agents/architect.md` and `compliance.md`.
- Tests: `tests/test_golden.py` Shipped now includes document-assessment (no total hard-coded). `tests/test_dryrun.py` and `tests/test_miniyaml.py` asserted architect's exact skill list; updated to include `document-assessment`.

**How to verify** (all run on this branch)
```
python scripts/golden.py ai-office
  document-assessment: 3 cases OK
  partner-writing: 4 cases OK
  review-checklist: 3 cases OK
  spec-writing: 3 cases OK
  golden: 13 cases, 74 checks, 0 problems
python scripts/build_agents.py ai-office   -> built 8 agents
python -m engine.runtime validate ai-office -> OK — 8 agents, 5 stages, 56 tasks, 18 skills
python -m unittest                          -> Ran 240 tests ... OK
python scripts/board.py ai-office           -> 56 tasks (board.md discarded)
```
Mutation check: removed the `[medium]` tag from R2 in `api-doc.json` expected_output; golden exited 1 with `check 7 (must_not_match, Risks) failed on expected_output`; reverted, exit 0.

**Deviations from the Design**
- The Design's check 7 `max_lines 40` uses the key `max` in the golden schema (not `n`); I used `max: 40`.
- Two extra test files updated (test_dryrun, test_miniyaml) because they hard-code architect's skill list; not named in the Design.
- The task file was already at status build / owner engineer (uncommitted in the worktree, from the PMO); committed as is, with owner set to reviewer and pr set. Status not touched by me.

**Known limits**: golden checks only recorded text; no LLM run. Real-name check is by Reviewer read plus the golden data scan (0 hits).

— Sebastian (engineer)

## Review log
PR #35 at e7c21e4, 26 Nov 2026: PASS. Five headings and severity rules; golden 3 cases OK (13 total, 74 checks); each bad_output fails; expected_output weakened 10 ways, every one caught; invented data only, data scan 0 hits; no-approval checks in all cases; loaded only by architect and compliance; build_agents no diff; 240 tests OK; combined with T-054: 13 cases, 0 problems.
Notes: template-agreement R5 [low] fits the medium rule; the Questions-cite-ID rule has no golden check.
— Cahyani (reviewer), recorded by Janice (pmo)

## Decision

## Open questions
