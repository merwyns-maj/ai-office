---
id: T-015
title: "Partner-facing writing skill"
phase: 3-skills
status: design
priority: P2
owner: architect
where: chat
project: ai-office
depends_on: [T-012]
pr: null
---

> Source: research/T-012-chat-mining.md section B (B1-B6). Picked by Merwyn for Sprint 2 (25 Nov 2026). Skill lives in this repo; no company data.

## Done when
- [ ] No overpromising, English banking terms in italics, no em-dashes

## Spec

**Problem.** Agents drafting for people outside the office (partners, banks, leadership, emails) have no written rules, so drafts come back with em-dashes, translated banking terms, unagreed commitments and markdown in emails, and Merwyn has to correct them each time.

**In scope**
- One skill, `partner-writing`, covering B1 to B6: no em-dashes or AI-sounding punctuation (B1); keep banking/fintech terms in English, italicised in Indonesian text, when translation looks odd (B2); partner-facing drafts make no overpromises, add no unneeded detail and commit to no dates or SLAs not yet agreed (B3); concise once the requirement is understood (B4); tone control only on request, soften own-side failures for leadership or push accountability to the partner side when asked, never misstating facts (B5); emails use plain text with no markdown (B6).
- Added to `office_skills` of agents that write for outsiders, then `build_agents.py` run.
- A short list of the Indonesian-text terms kept in English must come only from T-012 or Merwyn, not invented.

**Out of scope**
- Working-standard rules (T-014) and internal-document style.
- Translating or rewriting any existing document.
- Company data or partner names in the skill.

**Done when**
- [ ] Exactly one `SKILL.md` has `name: partner-writing`. Check: `grep -rl "name: partner-writing" offices/ | wc -l` prints 1.
- [ ] It has six rules, each citing B1 to B6. Check: open the file.
- [ ] The skill file contains no em-dash character. Check: `grep -c "—" <path>` prints 0 (rule examples use words, not the character).
- [ ] The B2 rule shows one example with a term italicised in Indonesian text, and the B3 rule lists dates and SLAs as examples of what not to commit to.
- [ ] The skill is in `office_skills` of each agent that writes for outsiders, and `python scripts/build_agents.py ai-office` exits 0. Check: `grep -l partner-writing offices/ai-office/agents/*.md`.
- [ ] The skill contains no borrower, lender, partner name or figures. Check: open the file.

**Open questions**
- Which ai-office agents write for outsiders (Emmy, April, others)? Who: Architect with PMO. Blocking for the `office_skills` check.
- B5 asks the agent to shift blame on request. Confirm the rule is "soften tone only, never state something untrue", consistent with D4. Who: Merwyn.
- Should this live at base level like T-014, or in ai-office only? Who: Architect (Merwyn if cost or risk differs).
- Note: this spec's own check uses the em-dash character in a grep; the Architect may phrase it differently.

— Emmy (pm)
