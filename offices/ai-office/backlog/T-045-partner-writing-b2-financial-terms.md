---
id: T-045
title: "Partner-writing B2 update: keep financial terms in English too"
phase: 3-skills
status: design
priority: P2
owner: architect
where: chat
project: ai-office
depends_on: [T-015]
pr: null
---

> Merwyn's decision of 25 Nov 2026: keep financial terms in English (e.g. tenor, outstanding), not only banking terms; the *virtual account* example is confirmed.

## Done when
- [ ] Rule B2 in `base/skills/partner-writing/SKILL.md` says that banking, fintech and financial terms stay in English in Indonesian text, and names `tenor` and `outstanding` as examples
- [ ] The existing example sentence `Dana masuk ke *virtual account* setelah verifikasi.` is still in B2, unchanged
- [ ] The sub-bullets "plain-text email keeps the English term without asterisks" and "Use only terms Merwyn has named. Do not build a term list." are kept in B2; `tenor`, `outstanding` and `virtual account` are the named terms
- [ ] The file contains no em dash (U+2014) and no en dash (U+2013); rules B1 and B3 to B6 are word-for-word unchanged (diff touches only B2)
- [ ] `build_agents.py` runs clean, and the full test command exits 0

## Spec
**Problem.** B2 covers only "a banking or fintech term". On 25 Nov 2026 Merwyn decided that financial terms such as tenor and outstanding also stay in English, and agents writing Indonesian text for partners would otherwise translate them.

**In scope**
- Rewording rule B2 in `base/skills/partner-writing/SKILL.md` to cover financial terms and to name tenor and outstanding.

**Out of scope**
- Any term list, glossary or new example sentences; the italics and "translation reads oddly" logic; the B6 email exception; any other rule or skill.
- Memory or personal-preference files outside this repo.

**Open questions**
1. Fang: do agent files or other skills restate B2 and need the same wording? Glob, Grep and Bash were unavailable to me, so I did not check; parent T-015 was also not read (its text is not needed for this wording change). Non-blocking.

— Emmy (pm)

## Design

## Approvals (PMO)
- Spec approved. Fang checks with grep whether any other skill or agent file restates B2. — Janice (pmo)

## Build notes

## Review log

## Decision

## Open questions
