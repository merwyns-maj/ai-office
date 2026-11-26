---
id: T-049
title: "Golden examples and evals for the office's own skills (slice of T-016)"
phase: 3-skills
status: review
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: []
pr: 28
---

> T-016 names SLIK, recon and PRD skills; those live in klik-workspace (company repo, behind T-002) and their examples would touch company data. This slice does the same for the skills that live here, so the method is proven before T-016 resumes.

## Done when
- [ ] 3–5 golden cases each for at least three office skills (e.g. partner-writing, spec-writing, review-checklist): input, expected output or must/must-not checks, and why
- [ ] A stdlib runner checks the cases' structure and runs the mechanical checks; it is documented and tested
- [ ] No company data in any case (the T-048 data rule, or the same patterns, passes over them)
- [ ] T-016 updated to point at this method

## Spec

**Problem.** The office's skills are checked only by reading them, so a wording change can silently break a rule (for example partner-writing B1, no em-dashes) and nobody notices. T-016 wants golden examples but its skills sit behind T-002 and would touch company data; this slice proves the method on skills that live here.

**In scope**
- At least 3 office skills, each with 3 to 5 golden cases. Candidates: partner-writing (B1 to B6), spec-writing, review-checklist; working-standard (A1 to A10) if there is room. Each case holds: input, must and must-not checks, a human-judged note, and why the case exists.
- Mechanical checks are script-runnable only (regex or required and forbidden phrases, structure such as required headings). Judgement points sit in the human note and are not scored by the script.
- A stdlib runner that (a) validates every case's structure and (b) runs the mechanical checks against the case's expected output, with a short doc and tests.
- A data-rule pass over all cases, reusing the T-048 rule (`DATA_PATTERNS` and `forbidden_terms` in `engine/runtime/events.py`) or the same patterns.
- T-016 gets a pointer to this method (its Done when is not rewritten).

**Out of scope**
- Running an LLM or the skill-creator eval; this slice checks recorded expected outputs only.
- SLIK, recon and PRD skills, klik-workspace, anything from T-002.
- Extending the data rule to key names and numbers (carried to T-027); this task uses the rule as it stands and says so.
- Rewriting any skill's content.

**Done when**
- [ ] For at least three named skills, a directory of cases exists with 3 to 5 cases each; `ls` shows the count and every case has input, checks, human note and why.
- [ ] Each case has at least one mechanical must or must-not check; for partner-writing, one case fails an expected output containing an em-dash (B1) and passes one without.
- [ ] `python <runner> <office>` exits 0 on the shipped cases; with a case missing "why", an empty check list or an invalid regex it exits 1 and names the file and the problem.
- [ ] A case containing an email, a 16-digit run, a run of 10+ digits or a forbidden term makes the runner exit 1 with a message naming the file and the kind of hit, never echoing the matched text.
- [ ] Runner tests pass and include the failing cases above; usage is documented in a file a new agent can follow in one read.
- [ ] No case contains company data (the same data-rule pass is clean over the cases directory).
- [ ] `offices/ai-office/backlog/T-016-...md` links to this method and states what it still needs (company skills, T-002).
- [ ] `python scripts/build_agents.py ai-office` exits 0 if any agent or skill file was touched.

**Open questions**
- Which three skills: spec-writing, partner-writing, review-checklist as the task suggests? Janice to confirm; I did not open the skill texts for B1 to B6 and A1 to A10, so Fang should check each rule is mechanically checkable. Not blocking.
- Where cases live (next to each skill or one cases directory) and the file format: Fang's choice.
- Can the runner import `engine/runtime/events.py` from `scripts/` cleanly, or should the patterns be copied? Fang to decide; reuse is preferred so one rule changes in one place.

— Emmy (pm)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: the three skills are partner-writing, spec-writing and review-checklist. The runner imports the patterns from engine/runtime/events.py (one source of truth), it does not copy them. — Janice (pmo)

## Design

**Which rules a script can check** (read from the three SKILL.md files, 26 Nov 2026)
| Skill | Rule | Checkable by script? | How |
|---|---|---|---|
| partner-writing | B1 no dash punctuation or decoration | Yes | must_not_match `[—–]` and an arrow or emoji class `[←-⇿☀-➿\U0001F300-\U0001FAFF]` |
| partner-writing | B2 English terms in Indonesian | Per case | must_contain `*virtual account*`, `tenor` or `outstanding`; must_not_contain the Indonesian rendering the case targets |
| partner-writing | B3 no overpromising | Per case only | must_not_contain the promise in the input (a date or "dijamin"/"guaranteed"); must_contain "to be confirmed" |
| partner-writing | B4 concise | Weakly | max_lines; the rest goes in the human note |
| partner-writing | B5 tone, never untrue | No | human note only |
| partner-writing | B6 plain-text email | Yes | must_not_match `(?m)^#`, `\*\*`, `(?m)^\s*[*-] `, `(?m)^\|` |
| spec-writing | five parts present | Yes | must_match `\*\*Problem\.\*\*`, `\*\*In scope\*\*`, `\*\*Out of scope\*\*`, `\*\*Done when\*\*`, `\*\*Open questions\*\*` (the form used in real task files) |
| spec-writing | checks are verifiable, not vague | Partly | must_match `(?m)^- \[ \] `; must_not_match `(?i)\b(works|clean)\b\.?$` for the vague-word case |
| spec-writing | each open question names who answers | Per case | must_match an agent name or "Merwyn" on each question line, as the case requires |
| spec-writing | one screen, no implementation choices, facts only | Partly | max_lines; the rest goes in the human note |
| review-checklist | verdict PASS or REJECT in Review log | Yes | must_match `(?m)^(- )?(PASS|REJECT)\b` |
| review-checklist | REJECT lists each failing check and its fix | Partly | must_contain "Fix" / must_match the failing check's id |
| review-checklist | style comments only under "Notes" | Partly | must_contain `Notes`; whether a note is style is judgement |
| review-checklist | real output pasted, second REJECT goes to Waiting on Merwyn | Partly | must_match `(?m)^Ran \d+ tests` or `OK`; must_contain "Waiting on Merwyn" in the second-REJECT case |

**Approach**
- Cases sit next to their skill, one JSON file per case:
  - `base/skills/partner-writing/golden/*.json` (4 cases: B1 dash, B2 terms, B3 promise, B6 email)
  - `offices/ai-office/skills/spec-writing/golden/*.json` (3 cases)
  - `offices/ai-office/skills/review-checklist/golden/*.json` (3 cases: PASS, REJECT, second REJECT)
- Keeping cases next to the skill means an edit to a skill and its cases lands in the same PR. The loader only reads `skills/<name>/SKILL.md` (`engine/runtime/loader.py:168`), so an extra `golden/` folder changes nothing.
- The format is JSON rather than markdown with front matter. `scripts/_fm.py` reads flat `key: value` pairs only and cannot hold check lists. The spec-writing outputs contain `**Problem.**`-style headings, and review outputs contain `##`, which would confuse a heading-split format. JSON needs only the stdlib `json` module.
- New runner `scripts/golden.py`, alongside `board.py` and the planned `metrics.py`. It inserts the repo root on `sys.path` and runs `from engine.runtime.events import DATA_PATTERNS, PATTERN_KINDS, forbidden_terms`, which loads cleanly because events.py only imports `.miniyaml`. The patterns are imported, not copied.
- Tests in `tests/test_golden.py`. Docs go in a new `## Golden examples` section in the root `README.md`, after "Rules of thumb" (one read: where cases live, the case format, how to run, what a failure looks like).
- T-016 gets one appended note pointing at this method and saying what is still needed (company skills in the company repo, behind T-002). Its Done when stays as it is.

**Case schema** (unknown keys are an error)
```json
{
  "skill": "partner-writing",
  "rules": ["B1"],
  "input": "the ask, as a short brief",
  "expected_output": "the golden text the skill should produce",
  "checks": [
    {"type": "must_not_match", "pattern": "[\\u2014\\u2013]", "rule": "B1"},
    {"type": "must_contain", "text": "to be confirmed", "rule": "B3"}
  ],
  "bad_output": "optional: a text that breaks the rule; the runner requires at least one check to FAIL on it",
  "human_note": "what a person judges and the script cannot (e.g. B5 truthfulness)",
  "why": "the slip this case guards against"
}
```
- Check types: `must_match`, `must_not_match` (regex, `re.MULTILINE`), `must_contain`, `must_not_contain` (literal, case-sensitive), and `max_lines` (int, key `"max": N`). Every check needs a `rule` string. At least one check must be a must or must-not type.
- `bad_output` covers the B1 Done-when. The B1 case's `expected_output` has no dash and passes. Its `bad_output` contains an em-dash, and the runner shows that the check catches it.

**Runner interface**
```
python scripts/golden.py <office> [-v]
  discovers base/skills/*/golden/*.json and offices/<office>/skills/*/golden/*.json
  exit 0: all cases valid, all checks pass on expected_output, every bad_output fails >= 1 check, data scan clean
  exit 1: any problem; one line each: "<repo-relative path>: <problem>"
  exit 2: usage error or office not found
  stdout on success: "<skill>: N cases OK" per skill, then "golden: N cases, M checks, 0 problems"
```
Problems it reports:
- invalid JSON; a missing or empty `why`, `human_note`, `input`, `expected_output` or `rules`; an empty `checks`; an unknown key or check type
- a regex that fails to compile (with the `re.error` message); `skill` not matching its folder; fewer than 3 or more than 5 cases in a `golden/` folder
- a check failing on `expected_output` ("check 2 (must_not_match, B1) failed"); a `bad_output` that passes every check

Data scan: runs over the raw file text and over every decoded string (so `@`-style escapes are caught too). The message is `"<path>: personal-data pattern (<PATTERN_KINDS[i]>)"` or `"<path>: forbidden term (listed in workspaces.yaml)"`. It never prints the matched text or the term, and it works the same way as events.py `_data_hit`.

Functions: `discover(repo, office) -> list[Path]`, `load_case(path) -> (dict|None, list[str])`, `run_check(check, text) -> bool`, `data_hits(raw_text, obj, forbidden) -> list[str]`, `main(argv) -> int`.

**Test plan** (`tests/test_golden.py`; the baseline is 200 tests, all passing on this worktree)
1. The shipped cases give exit 0 with three skills listed.
2. On a temp copy of a golden folder, each of these gives exit 1, with the message naming the file and the problem: `why` removed; `checks: []`; pattern `"(["`; a 6th case; `skill` mismatched.
3. B1: the dash check fails on a text with `—` and passes on the same text without it; a `bad_output` that passes every check is reported.
4. Data rule: temp cases containing an email, a 16-digit run, a 10-digit run, a forbidden term from `forbidden_terms(REPO)`, and an email written as a `@` escape each give exit 1. Each message names the kind, and stdout plus stderr do not contain the planted value.
5. Import check: `scripts.golden.DATA_PATTERNS is engine.runtime.events.DATA_PATTERNS`.
6. Build with `python scripts/build_agents.py ai-office`. No agent or SKILL.md file is touched, but run it anyway since `skills/` gains folders.

**Risks**
| Risk | Handling |
|---|---|
| Cases that pass only because the checks are too loose | `bad_output` is required on B1 and B6 and recommended on others; the reviewer reads the human notes |
| Case text naming company repos, partners or numbers | Generic briefs only (for example "a bank partner", "a lender report"); the data scan runs over the raw text; the rule gap for numbers and keys (T-027) does not apply because the raw-text scan covers them |
| A forbidden term appearing as a substring in ordinary words (for example "data-platform") | Reword the case; never weaken the rule |
| Skill wording changes and its cases go stale | The cases live in the skill's folder, so the reviewer sees both in the same diff |

**Flags.** Compliance: not flagged (no prod, money or personal data; the data rule is enforced). Dinda's UX consult: does not apply (no UI, visual or motion work).

**Decision record draft (for April)**
```
Decision: golden cases are JSON files in <skill>/golden/, checked by scripts/golden.py, which imports the T-048 data patterns.
Context: T-016 needs golden examples; the office's own skills prove the method first; one data rule must live in one place.
Options: A, JSON next to each skill (stdlib, skill and its cases change together); B, markdown with front matter in tests/golden/ (needs a list parser; the headings inside outputs clash); C, a single cases file (merge conflicts, no per-skill count).
Chosen: A, because it is stdlib only and unambiguous, and it keeps a skill and its cases in one diff.
Consequences: T-016 reuses the same runner once company skills are reachable (T-002). The runner scans raw text, so it is stricter than events.py, which scans string values only (T-027).
Links: T-049, T-016, T-048
```

— Fang (architect)

Janice (pmo), 26 Nov: Design accepted, moved to build. Answers: the metrics report states what history shows (Sprint 1 window: T-012 only, footnoted); the retro is not rewritten. W6 (overrides) is April's call on the evidence. Agreed: for T-041 and T-031 the Reviewer records PASS and leaves status at review; Janice sets done after Merwyn acts. Findings file now says "company repo, behind T-002" (no forbidden terms).

## Build notes

**What changed**
- `scripts/golden.py` (new runner, imports `DATA_PATTERNS`, `PATTERN_KINDS`, `forbidden_terms` from `engine/runtime/events.py`; `main(argv, repo=REPO)` takes an optional repo root so tests can use a temp repo).
- Cases: `base/skills/partner-writing/golden/` (b1-no-dash, b2-english-terms, b3-no-overpromise, b6-plain-email), `offices/ai-office/skills/spec-writing/golden/` (five-parts-present, done-when-verifiable, open-question-owner), `offices/ai-office/skills/review-checklist/golden/` (pass, reject-lists-fixes, second-reject). 10 cases, 41 checks. The em-dash in B1 bad_output is a JSON escape, so no case file holds a literal dash.
- `tests/test_golden.py` (24 tests), README "Golden examples" section, note appended to T-016 (Done when unchanged).

**How to verify**
```
$ python scripts/golden.py ai-office
partner-writing: 4 cases OK
review-checklist: 3 cases OK
spec-writing: 3 cases OK
golden: 10 cases, 41 checks, 0 problems
$ python -m unittest
Ran 224 tests in 6.742s
OK
$ python scripts/build_agents.py ai-office
ai-office: built 8 agents -> .claude/agents/ (...)
$ python -m engine.runtime validate ai-office
ai-office: OK - 8 agents, 5 stages, 49 tasks, 16 skills
```
Tests went from 200 to 224 (24 new). board.py ran with no problems; board.md discarded.

**Deviations from the Design**
- Runner exit 1 also covers a `golden/` folder with the wrong case count, as designed. Two small additions: a case whose only checks are `max_lines` is a problem (Spec: at least one must or must-not check), and a data hit in an unparseable JSON file is still reported.
- Message format for the count problem: `<folder>: N cases, expected 3 to 5`.

**Known limits**
- Data scan reuses the T-048 patterns as they stand (T-027 covers key names and numbers); raw-text scan adds coverage of digits and emails anywhere in the file.
- Checks are regex or literal on recorded text; no LLM is run. B5 and part of B4 are human-note only.
- Zero discovered cases exits 0 with "0 cases"; not specified in the Design, left as is.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
