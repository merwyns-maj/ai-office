---
id: T-015
title: "Partner-facing writing skill"
phase: 3-skills
status: review
priority: P2
owner: reviewer
where: chat
project: ai-office
depends_on: [T-012, T-014]
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

## Design

**Basis.** Spec above; `research/T-012-chat-mining.md` §B and §D4; the T-014 Design on branch `t-014-working-standard`; `scripts/build_agents.py`. Janice's brief (25 Nov): this skill is base-level and is attached to `pm` and `curator` in ai-office. `claude:diagram-design` was not available in this session; no diagram needed.

**Depends on T-014.** This design uses the mechanism T-014 builds: `base/skills/<name>/SKILL.md` plus the optional agent key `base_skills: [...]`. Build it only after T-014 is merged: rebase `t-015-partner-writing` on fresh `main` first. I added `T-014` to `depends_on` so the dry-run and the board show the block. Janice, please confirm.

**Answers to the Spec's open questions**
- Which agents? `pm` (Emmy) and `curator` (April), as ruled in the brief. `pmo` status notes go to Merwyn (internal) and stay out. Add others later with a one-line `base_skills` edit.
- Base-level or ai-office only? Base-level. The rules are Merwyn's own writing standard and hold for any office; they contain no company content. Cost and risk are the same either way, so this is an architect call, not a human gate.
- B5: the rule is "tone only, never untrue", consistent with D4. The Design writes it that way; Merwyn may still confirm (below).

### Approach
1. Create `base/skills/partner-writing/SKILL.md`.
2. Add `base_skills: [partner-writing]` to the frontmatter of `offices/ai-office/agents/pm.md` and `offices/ai-office/agents/curator.md`. Do not use `office_skills`: that key resolves only `offices/<o>/skills/`.
3. Run `python scripts/build_agents.py ai-office`. Only `.claude/agents/pm.md` and `curator.md` change, each by one line under `## Skills`.
4. In the T-014 test file `tests/test_build_agents.py`, add one assertion to the real-office test: the generated `pm.md` and `curator.md` list `base/skills/partner-writing/SKILL.md`, and the other five agents do not.
5. No script, engine or schema change.

### Interfaces
**Frontmatter**: `name: partner-writing`, and a `description` like "Rules for anything written for people outside the office: partners, banks, leadership, email. Use when drafting or revising such text."
- The whole file contains **no em-dash (U+2014) or en-dash (U+2013)**, including the description. Examples use words.
- No partner names, company names or figures.

**Body**: six rules, each tagged with its B-number. Wording to start from:
- **B1** No em-dashes or en-dashes as punctuation, and no AI-sounding decoration (arrows, emoji, symbol bullets). Use a comma, a full stop or "to".
- **B2** In Indonesian text, keep a banking or fintech term in English and italicise it when the translation reads oddly. Example: `Dana masuk ke *virtual account* setelah verifikasi.`
  - In plain-text email (B6), keep the English term without asterisks.
  - Use only terms Merwyn has named. Do not build a term list.
- **B3** Partner-facing text makes no overpromises, adds no detail the reader does not need, and commits to nothing not yet agreed. Examples: dates, SLAs, fees, volumes. Write "to be confirmed" and name who confirms.
- **B4** Once the requirement is clear, write the shortest version that carries it. Do not restate the ask.
- **B5** Change tone only when asked. You may soften wording about our own side's failure for leadership readers, or place accountability with the partner when asked. Never state something untrue, drop a material fact or misrepresent a record (see D4). If a request needs that, say so and offer a truthful version.
- **B6** Emails are plain text: no markdown headings, bold, tables or `*` bullets. Use short paragraphs, and "1." lines when a list is needed.

### Spec deltas for the Reviewer (mechanical, same intent)
- Check 1: the skill is at base level, so run `grep -rl "name: partner-writing" base/ offices/ | wc -l`. It prints 1.
- Check 3, without typing the character:
  ```
  python3 -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();print(t.count('—'),t.count('–'))" base/skills/partner-writing/SKILL.md
  ```
  It prints `0 0`. This also answers Emmy's note about the grep.
- Check 5: the key is `base_skills`, not `office_skills`. `grep -l partner-writing offices/ai-office/agents/*.md` lists exactly `curator.md` and `pm.md`. `python scripts/build_agents.py ai-office` exits 0, and so does `python -m engine.runtime validate ai-office`.

### Risks
| Risk | Handling |
|---|---|
| Built before T-014 merges, so `base_skills` is unknown | Hard dependency in `depends_on`; rebase on main first. Without T-014, validate and build would ignore the key silently, so check that the generated `pm.md` lists the path |
| B2 (italics) clashes with B6 (plain-text email) | B2 states the email case explicitly |
| B5 read as permission to shift blame untruthfully | The rule bounds it to tone and cites D4 |
| An invented term list | B2 forbids it; the example term needs Merwyn's confirmation (below) |
| An em-dash slips in through an editor or the description | The Reviewer's python count covers the whole file |

**Compliance:** not flagged. Writing rules only, no data.

### Decision record draft (for April)
```
Decision: partner-writing is a base skill (base/skills/partner-writing), opted into per agent with base_skills; in ai-office, pm and curator use it.
Context: T-015; rules come from Merwyn's own chats (T-012 section B) and apply to any office.
Options: A base skill, opt-in per agent (chosen); B ai-office skill under office_skills (other offices would copy it); C every agent via base/defaults.yaml (adds context to agents that never write for outsiders).
Chosen: A, because one copy serves every office and only writers pay the context cost.
Consequences: depends on T-014's base_skills key; adding a writer later is a one-line edit.
Links: T-015, T-014, PR <n>
```

### Open questions
- B2 example term: the Design uses *virtual account* because T-012 mentions VA work. Is that the right example, and are there other terms Merwyn always keeps in English? Who: Merwyn via Janice. Non-blocking: swapping the example is a one-word edit.
- B5 wording ("tone only, never untrue"). Who: Merwyn, for confirmation. Non-blocking.

— Fang (architect)

## Approvals (PMO)
- Spec approved: B5 = soften tone, never state anything untrue (D4). Outsider-writing agents: pm (Emmy) and curator (April). Base level. — Janice (pmo)
- Design approved; depends_on T-014 confirmed; build after T-014 merges, rebased on main. B2 example term (*virtual account*) accepted. — Janice (pmo)


## Build notes

**What changed**
- `base/skills/partner-writing/SKILL.md` (new): rules B1 to B6, generic, no names or figures. B2 example is `Dana masuk ke *virtual account* setelah verifikasi.`; B2 covers plain-text email; B5 is tone only and cites D4.
- `offices/ai-office/agents/pm.md`, `curator.md`: added `base_skills: [partner-writing]`.
- `.claude/agents/pm.md`, `curator.md`: regenerated, one added line each under `## Skills` (`- base/skills/partner-writing/SKILL.md`). No other generated file changed.
- `tests/test_build_agents.py`: new `test_partner_writing_only_on_pm_and_curator` (pm and curator list the skill, the other five do not).

**How to verify (real output)**
```
$ python3 scripts/build_agents.py ai-office
ai-office: built 7 agents -> .claude/agents/ (architect, compliance, curator, engineer, pm, pmo, reviewer)
$ python3 -m unittest -q
Ran 144 tests in 5.326s
OK
$ python3 -m engine.runtime validate ai-office
ai-office: OK — 7 agents, 5 stages, 42 tasks, 15 skills
$ python3 -c "...count('\u2014'),count('\u2013')..." base/skills/partner-writing/SKILL.md   # design's command
0 0
$ grep -l partner-writing offices/ai-office/agents/*.md
offices/ai-office/agents/curator.md
offices/ai-office/agents/pm.md
```

**Done when to evidence**
| Done when | Evidence |
|---|---|
| Exactly one `name: partner-writing` | `grep -rl "name: partner-writing" base/ offices/` lists the skill and this task file (the task text quotes the string in a sentence below, not as frontmatter). Exactly one SKILL.md carries it: `grep -rl "name: partner-writing" base/ offices/ --include=SKILL.md \| wc -l` prints 1. See deviation 2. |
| Six rules citing B1 to B6 | Open `base/skills/partner-writing/SKILL.md` |
| No em-dash (and no en-dash) | python count prints `0 0` |
| B2 italic example, B3 lists dates and SLAs | In the file: B2 example line, B3 "Examples: dates, SLAs, fees, volumes" |
| In agents that write for outsiders; build exits 0 | grep lists curator.md and pm.md only; build output above; validate OK; new test passes |
| No borrower, lender, partner name or figures | Open the file; none present |

**Deviations**
1. Two existing T-014 tests injected a second `base_skills:` line into the real `pm.md` frontmatter, which now already has one, so they failed (order test, unknown-skill test). I pointed those two tests at `architect.md`, which has no `base_skills`. Intent unchanged. Test-only edit.
2. The Design's check 1 (`grep -rl ... base/ offices/ | wc -l` prints 1) prints 2 because this task file itself contains the string "name: partner-writing". The extra hit is the task file, not a second skill. Use `--include=SKILL.md`.
3. `claude:diagram-design` etc. not used; no diagram needed.

**Known limits:** B2 example term still awaits Merwyn's confirmation (non-blocking). board.md not committed (task branch rule).

— Sebastian (engineer)

