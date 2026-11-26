---
id: T-060
title: "Usage panel: summary mode (provider vs budget) and detail mode (agent vs budget)"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-059]
pr: null
---

> Merwyn, 26 Nov 2026 14:55 WIB: "let's just create 2 mode. 1. Summary on the high level on the provider level (i.e. Claude Max Plan 20% out of 100% capacity) 2. Detail view Show each agent consumption (no need up to the task level) vs budget for each agents."
> His answers (question card, 26 Nov ~15:00): the 100% is a budget he sets, labelled as his budget (Anthropic publishes no token limit for the Max plan); agent budgets start as a split of the provider budget based on real use so far, adjustable in config.

## Done when
- [x] The usage panel (and phone sheet) has two modes with a clear switch: Summary and Detail; the choice is remembered per viewer (storage in try/catch)
- [x] Summary: one row per provider with used tokens, the budget, and a bar with "N% of your budget" (never "of capacity" or "of the plan"); over budget shows clearly (bar capped, amber/red is not used for this, text says "over by X"); a provider with no budget says "budget not set"
- [x] Detail: one row per agent with used tokens vs that agent's budget, bar and %, no task-level list; agents sorted by % of budget, highest first; "budget not set" handled
- [x] Budgets live in office config (offices/ai-office/budgets.yaml): period, per-provider total, per-agent shares or amounts; each value carries who set it and when; validated (shares add to 100, no negatives); the page never invents a budget
- [x] Starting values set by Janice from this session's real use and marked "starting values, Merwyn to adjust"
- [x] Period: the ledger has no run dates today, so the period is the session until run lines carry a date; the panel says which period it shows. New ledger lines get a `date` field (optional, validated)
- [x] Both pages (synthetic office and recorded usage); tests for budget parsing, shares, % and over-budget maths; all tests, golden and --check pass; headless screenshots of both modes at 1280x800 and 390x844; no console errors

## Spec
Request from Merwyn with his two answers; scope as in Done when. Out of scope: reading Anthropic's own usage limits (not available to the office), alerts or blocking when over budget (T-026). — Janice (pmo)

## Design

Janice (pmo), 26 Nov, starting values (Merwyn to adjust): claude-code budget 5,000,000 tokens per session (this session has used 3,813,702 over 48 recorded runs, so it starts at 76%). Agent shares from real use so far (largest remainder): engineer 43, reviewer 30, architect 13, designer 6, pm 5, curator 2, compliance 1. The PMO (main session) has no share because its tokens are not reported; Detail shows Janice as "not reported". The synthetic demo page gets its own budgets in the fixture header, marked synthetic, not in budgets.yaml.

### UX design
Audience: Merwyn, glancing. Question (playbook 1): "How much of the budget I set has been used, and who is using it?" Order follows playbook 6.

**Layout and hierarchy.** Header: title "USAGE", the existing synthetic or recorded pill, a segmented control "Summary | Detail" (two buttons, 28px high, 44px on the phone sheet), then the existing collapse button. Default is Summary on every first visit; the choice is remembered per viewer (try/catch, as the layout key). The control reuses `.ucol` border and radius; the selected segment is filled with `--text-dim` at low opacity plus bold text, so it is not colour alone (playbook 5). Left out of both modes: input/out/cache figures, models, run lists, task lists, "Show details" links (Merwyn: no task level).

**Summary** (one row per provider, no accordion, not tappable):
1. line 1: provider label (e.g. "Claude Code") left; "3.8M / 5M" right (fmtTok; exact figure in `title`).
2. line 2: bar (existing `.bar`, provider colour) and "76% of your budget" (never "of capacity" or "of the plan").
3. line 3 (dim, 10px): "This session" then "Budget set by Merwyn" or, for Janice's values, "Starting values, Merwyn to adjust". Synthetic page adds the italic "synthetic" tag as now.
Footer: one line, "Budget is yours; Anthropic publishes no limit for the plan."

**Detail** (one row per agent, sorted by % of budget, highest first, ties by name): name left, "1.6M / 2.2M" right; bar; "75%". Row 3 only when needed (below). Janice (PMO) sits last as "Main session: not reported" with no bar. The accordions go in Detail: each would only open to runs and task ids, which Merwyn ruled out, and the rows become plain non-interactive text. `accOff`, `focusBtn` and run lines are no longer used by this panel; focusing an agent stays on the 3D office. A one-line header above the list repeats the provider total ("Claude Code, 76% of your budget") so Detail never loses its anchor.

**States.**
- Over budget (no amber or red, amber is needs-Merwyn only): bar is full at 100% and a hatched segment (diagonal stripes in `--text`, 45deg, 4px pitch) is drawn after a 2px gap to the right of the bar; hatch width = min(overflow/budget, 50%) of bar width, so the bar track extends by that amount. The text turns bold: "over by 210k" replaces "N% of your budget" in Summary (Summary: "over by 210k (104% of your budget)"); Detail: "over by 210k". The row gets a leading "▲" glyph so it reads without colour or hatch. Screen reader: "over budget by 210k".
- Budget not set: no bar, a dashed empty track (still 4px), text "budget not set" in dim italic, used tokens still shown ("3.8M used"). Never a 0% or a guessed budget.
- Agent without budget in Detail: same "budget not set" treatment, sorted after agents with a % ; Janice: "not reported".
- No usage yet: existing "No usage yet" line in both modes.
- Synthetic vs recorded: pill in header stays; synthetic budgets say "synthetic budget" in row 3 and footer; recorded rows say "recorded" nowhere else (the pill does it).
- Percent is capped at 100 in the bar, but the text shows the real figure (104%).

**Collapsed.** One line as today: Summary form "Claude Code 76% of your budget"; with several providers, the highest %. Detail is not summarised separately. The segmented control hides when collapsed so the header stays small; the mode is kept.

**Phone sheet.** Same renderer, same control in the sheet header (44px targets), rows stacked as above, no horizontal scroll at 390px; label and figures wrap to two lines before truncating. Sheet scrolls if Detail has 8 rows.

**Motion.** (1) Mode switch: content cross-fades, 120ms ease-out, to show it is the same panel changing view. Reduced motion (`body.rm` and the media query): instant swap. (2) Bar width on update: 160ms ease-out transition, shows growth. Reduced: none. Hatch and glyph are static. No pulsing, nothing blinks (blinking is reserved for needs-attention, playbook 2).

**Visual spec.** Colours only from theme.yaml and existing vars (`--text`, `--text-dim`, `--panel`, provider colour, `--accent` for focus ring). Bar 4px, radius 2px; hatch same height; fonts as existing (`--ui` labels, `--mono` figures 10-11px). Contrast: dim text over the panel must meet 4.5:1 at 10px, which the Builder checks at the panel's 92% opacity default.

**Accessibility.** Control is `role="radiogroup"` with two `role="radio"` buttons (`aria-checked`), roving tabindex, Left/Right/Home/End move and select, Enter and Space select; visible focus ring. Mode change announces in an `aria-live="polite"` region: "Detail view, 7 agents". Each bar has an `aria-label` row-level sentence ("Claude Code: 3.8 million of 5 million tokens, 76% of your budget, this session, starting values") and the bar itself stays `aria-hidden`. Over, unset and not-reported are all stated in text, never by colour or hatch alone (playbook 5).

**Open questions.** (1) Should Detail show each agent's budget share (43%) as well as its token amount? Default no, amounts only; Merwyn answers. (2) Footer wording on Anthropic's limit: Merwyn or Janice. (3) Hatch width cap 50% is a starting value to judge on screen, Dinda to check at the screenshots.

— Dinda (designer)

Janice (pmo), 26 Nov: Dinda's UX accepted; moved to build. Answers: Detail shows % of each agent's budget only, no extra share column (Merwyn asked for consumption vs budget). Footer wording: "Budgets are yours to set. Anthropic does not publish the Max plan's limit in tokens." Hatch width: builder checks on screen. Technical design: budgets.yaml read by a stdlib loader in engine/runtime (validated, every value with set_by and set_on), injected by office_app; pure budget maths in office-core, node-tested; reuse T-057/T-059 panel code. Janice stands in for Fang. No compliance flag. Engineer: do not set status.

## Build notes

**What changed**
- `engine/runtime/budgets.py` (new): stdlib loader and validator for `offices/ai-office/budgets.yaml`. Period (only `session` for now), per-provider `tokens`, per-agent `share` (add to 100) or `tokens` (all one kind per provider), `set_by` and `set_on` on every value, no negatives, ids checked against providers.yaml and org.yaml. Shares become whole tokens by largest remainder (they add to the provider total). `main_session: pmo` names the agent whose tokens the harness does not report.
- `offices/ai-office/budgets.yaml` (new): Janice's starting values (claude-code 5,000,000; shares engineer 43, reviewer 30, architect 13, designer 6, pm 5, curator 2, compliance 1), noted "Starting values, Merwyn to adjust".
- `scripts/office_app.py`: ledger page reads budgets.yaml; the synthetic page reads `budgets` from its fixture header (`engine/app/fixtures/models-synthetic.jsonl`, marked synthetic, not budgets.yaml) and drops it from the header; both end up in `data.budgets` (null when absent). A bad budget fails the build, nothing written.
- `engine/runtime/ledger.py`, `engine/schema/usage.md`: run lines may carry `date` (YYYY-MM-DD, validated, optional). `engine/schema/events.md`: header `budgets` documented.
- `engine/app/office.template.html`: office-core gets pure `budgetRow`, `sortDetail`, `budgetView`, `parseMode`, `MODE_KEY`. Panel and phone sheet share one renderer. Summary (one row per provider, "N% of your budget", "over by X (N% of your budget)", "budget not set", period and who set it in row 3, footer wording as Janice gave it) and Detail (per provider a header line, then one row per agent sorted by share of budget, unset after, main session "not reported" last). Mode switch is a `radiogroup` (arrow keys, Home/End, Enter/Space), remembered under `office.usage.mode.v1` in try/catch, announced in the live region. Old accordion, run list, in/out/cache and "Show details" panel code is removed. `office.html` regenerated.
- Tests: `tests/test_budgets.py` (new, 18) and 4 new or rewritten in `tests/test_office_app.py` (node tests of the maths and of both views). 336 tests in total.

**How to verify**
```
cp /tmp/three/package/build/three.min.js engine/app/      # gitignored
python scripts/office_app.py ai-office && python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
python -m unittest                                           # Ran 336 tests ... OK
python scripts/golden.py ai-office                           # golden: 13 cases, 75 checks, 0 problems
python scripts/office_app.py ai-office --check               # up to date (166 KB, 84 events)
python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl   # 48 runs kept (1 not reported), 3,813,702 tokens, 0 errors, 0 warnings
python scripts/board.py ai-office                            # 60 tasks, no problems; board.md discarded
```
Open `engine/app/usage-session_...html?t=99999` (recorded) or `engine/app/office.html?t=99999` (synthetic) and use the Summary | Detail switch.

**What the recorded page shows (48 runs, this session)**
- Summary: Claude Code subagents, 3.8M / 5M, 76% of your budget, "This session · Starting values, Merwyn to adjust".
- Detail (highest share first): Emmy 203k / 250k 81%, Fang 514k / 650k 79%, Sebastian 1.6M / 2.2M 77%, Cahyani 1.1M / 1.5M 75%, Dinda 223k / 300k 74%, April 69k / 100k 69%, Wulan 31k / 50k 62%, then Janice "Main session: not reported".

**Screenshots** (headless Chrome, swiftshader, file://, no console errors on any): `/tmp/t060-shots/` `{rec,syn,over,unset}-both-{1280,390}-{summary,detail}.png`. `over` and `unset` are the recorded page built from a temp office copy in `/tmp/t060-cfg` (claude-code budget 3,600,000 and designer without a budget gives "over by 214k (106% of your budget)" and "budget not set"; no budgets.yaml gives "budget not set" for every row). The synthetic page shows an over row (Anthropic API, 70k / 50k, over by 20k), an unset row (DeepSeek) and two normal ones. Also checked in a browser: first visit is Summary; ArrowRight selects Detail and keeps focus; choice survives reload; blocked localStorage does not throw; reduced motion gives no fade; collapsed line reads "Claude Code subagents 76% of your budget" and hides the switch.

**Deviations from the design (small, each for a reason)**
1. The Summary | Detail switch sits on its own full-width row under the header, not inside it. The docked panel is 288px wide and grip, title, pill, switch, options and collapse button do not fit on one line. Hidden when collapsed, as designed.
2. Detail and Summary rows are `role="img"` with one sentence as `aria-label` (so the sentence is read once) rather than a group with a labelled bar.
3. Provider labels are shown without the parenthesis ("Claude Code subagents", catalogue label is "Claude Code subagents (Max plan)"). Dinda's example says "Claude Code".
4. Bar growth (160ms): the panel is redrawn as HTML, so the previous width is carried over by hand in `growBars`; reduced motion skips it. Mode cross-fade 120ms as designed.
5. The hatch is the specified width (overflow / budget of the bar, cap 50%). At 6% over it is only a few pixels wide; the glyph, bold "over by" text and aria sentence carry the state. Dinda to judge on the screenshots (her open question 3).
6. Main session row needs a config fact the design did not name: `main_session: pmo` in budgets.yaml (the page never hardcodes an agent).
7. Without budgets.yaml, the Detail view has no main-session row (it comes from the config).
8. `fmtTok` now rounds millions half-up from the integer (2,150,000 reads 2.2M; `toFixed` gave 2.1M).

**Known limits**
- Period is the session only; `period: day|week|month` is rejected by the validator until run lines carry dates and the page filters by them. `date` is accepted on new lines now.
- Summary lists providers in catalogue order (alphabetical on the synthetic page), not by %.
- The docked panel keeps T-059's default height, so Detail with 8 rows scrolls (Janice's row is the last); the panel can be resized.
- Budgets are never edited from the page; change budgets.yaml.

**Open questions**: none new.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
