---
id: T-045
title: "Partner-writing B2 update: keep financial terms in English too"
phase: 3-skills
status: build
priority: P2
owner: engineer
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
**Approach** (wording-only, one file: `base/skills/partner-writing/SKILL.md`, rule B2's first line)
- Replace B2's first line with exactly this line (two spaces of indent and the sub-bullets below it stay as they are):

```
- **B2 English terms in Indonesian text.** In Indonesian text, keep a banking, fintech or financial term in English (for example *tenor* and *outstanding*) and italicise it when the translation reads oddly. Example: `Dana masuk ke *virtual account* setelah verifikasi.`
```

- What changes: "a banking or fintech term" becomes "a banking, fintech or financial term", and the parenthesis "(for example *tenor* and *outstanding*)" is added. The italics condition ("when the translation reads oddly"), the example sentence and both sub-bullets stay word-for-word.
- The three named terms are then `tenor`, `outstanding` (rule text) and `virtual account` (example), so the sub-bullet "Use only terms Merwyn has named. Do not build a term list." still holds without a list.
- Then run `python scripts/build_agents.py ai-office`. The generated `.claude/agents/*.md` files only link the skill path, so expect no diff there; commit any diff it does make.

**Interfaces.** None. The skill file's frontmatter, rule ids and order do not change.

**Grep for other copies of B2** (`grep -rni "B2\b|virtual account|fintech term|banking term|financial term|tenor|outstanding"` over the repo, `.git` excluded):
- No agent file (`base/agents/`, `offices/*/agents/`, `.claude/agents/`) and no other skill restates B2. Agents only list the path `base/skills/partner-writing/SKILL.md`.
- Old wording appears only in records: `offices/ai-office/backlog/T-015-partner-facing-writing-skill.md` (spec, design, build notes), `offices/ai-office/research/T-012-chat-mining.md` (source table) and `offices/ai-office/sprints/sprint-02.md`. These are history; do not edit them. T-015 already points to T-045 (its PMO note).
- `T-007` mentions "outstanding" as a metric name; unrelated.

**Risks**
| Risk | Handling |
|---|---|
| Diff touches more than B2 | Reviewer checks `git diff` shows one changed line, inside B2 |
| A dash slips in | Build notes show `grep -c $'\u2014\|\u2013'` (or a Python check) returns 0 for the file |
| Rule reads as an open-ended list of finance words | "for example" plus the unchanged "Use only terms Merwyn has named" sub-bullet keep it to named terms |

**Flags.** None for Compliance (no prod, money movement or personal data).

**Decision record draft (for Curator)**
```
Decision: Partner-writing B2 keeps banking, fintech and financial terms in English in Indonesian text, naming tenor and outstanding; virtual account stays the example.
Context: Merwyn, 25 Nov 2026 (R-13): financial terms were being translated because B2 named only banking/fintech terms.
Options: A, widen B2's wording and name two examples (one-line edit); B, add a term glossary (B2 forbids building a term list; more to maintain).
Chosen: A, because it applies the decision with a one-line edit and keeps the no-term-list rule.
Consequences: New terms are added only when Merwyn names them, as an edit to B2. No other file restates B2.
Links: T-045, T-015, R-13, PR (tbd)
```

— Fang (architect)

## Approvals (PMO)
- Spec approved. Fang checks with grep whether any other skill or agent file restates B2. — Janice (pmo)

## Build notes

## Review log

## Decision

## Open questions
