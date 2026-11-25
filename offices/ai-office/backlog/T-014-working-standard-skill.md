---
id: T-014
title: "Working-standard skill"
phase: 3-skills
status: design
priority: P1
owner: architect
where: chat
project: ai-office
depends_on: [T-012]
pr: null
---

> Source: research/T-012-chat-mining.md section A (A1-A10). Picked by Merwyn for Sprint 2 (25 Nov 2026). Skill lives in this repo; no company data.

## Done when
- [ ] Verify vs prod, flag incidental bugs, check external edits, state fact not guesses
- [ ] Used by PRD and recon skills

## Spec

**Problem.** Merwyn's standards for how work is done (T-012 section A) exist only as chat patterns, so each agent works to its own habits: inferred values reported as facts, summaries defended instead of re-verified, incidental bugs left unmentioned, shared files overwritten.

**In scope**
- One skill, `working-standard`, covering A1 to A10: state facts not guesses (A1); verify against primary sources and re-verify when challenged (A2); back recommendations with data (A3); flag incidental bugs with evidence (A4); check for external edits before overwriting shared work (A5); use the team's conventions (A6); scope precisely, wording vs data/logic (A7); stay in the asked lens (A8); start simple, iterate (A9); consistency check before delivery (A10).
- Location: base level, so every office inherits it and no office copies it.
- Every agent in every office receives it automatically, with no per-agent edit.
- No company data in the skill (CLAUDE.md rule).

**Out of scope**
- Editing company PRD or recon skills (they live outside this repo; see Open questions).
- Partner-writing rules (T-015) and Merwyn-interaction rules (T-041).
- Choosing the base-level mechanism (Architect).

**Done when**
- [ ] Exactly one `SKILL.md` has `name: working-standard`. Check: `grep -rl "name: working-standard" offices/ | wc -l` prints 1, at a base-level path every office can reach.
- [ ] The file contains A1 to A10 each as one short rule. Check: open it; ten distinct rules, each citing its A-number.
- [ ] A new agent built for a second office gets the skill without editing its own profile. Check: run the build for any office and `grep -l "working-standard"` on the generated agent files for every agent in it; the count equals the agent count.
- [ ] `python scripts/build_agents.py <office>` exits 0 for every office that exists.
- [ ] `grep -rn "working-standard" offices/*/agents` lists no agent file as the source of truth (the skill is not copy-pasted into agents).
- [ ] The skill contains no borrower, lender, NIK, account numbers or amounts. Check: open the file.

**Open questions**
- Does a base-level skills location exist today, and how do `office_skills` and `build_agents.py` treat it? Not verified. Who: Architect. Blocking for design.
- How many offices exist besides ai-office? I read only that office. Who: Architect.
- Original check "used by PRD and recon skills": those are company skills (klik-workspace), outside this repo, so a repo write is a human gate. Drop it, or open a follow-up task once T-002 lands? Who: Merwyn.

— Emmy (pm)
