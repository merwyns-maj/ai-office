---
id: T-062
title: "Budget bars: green, yellow, red as usage nears the budget"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-060]
pr: null
---

> Merwyn, 26 Nov 2026 15:27 WIB: "use color coding like green, yellow, and red if almost reach the capacity". Applies to the Summary and Detail budget bars (T-060) on both pages.

## Done when
- [ ] Each budget bar and its % text are green under the first threshold, yellow from it, red from the second threshold and when over budget; defaults 70% and 90%, set in budgets.yaml (`warn_at`, `alert_at`, validated: 0 < warn_at < alert_at <= 100), with who set them and when
- [ ] Never colour alone: the state also shows as a word or glyph (e.g. "near budget", "over by X") and in the row's aria-label
- [ ] The yellow and red stay clearly distinct from the amber "needs you" beacon and its pill (Dinda picks the colours and checks them side by side); text keeps at least 4.5:1 on the panel at default opacity and with the T-059 backing at low opacity
- [ ] Provider chip colours and the "budget not set" dashed track are unchanged
- [ ] Tests for the thresholds (boundaries 69/70/89/90/100/over), config validation, and the colour state in the aria-label; all tests, golden and --check pass; screenshots of green, yellow and red rows at 1280x800 and 390x844; no console errors

## Spec
Request from Merwyn; scope as in Done when. This replaces T-060's "no amber or red for over budget" rule at Merwyn's request; the needs-you amber keeps its own colour and shape. — Janice (pmo)

## Design

### UX design
Audience: Merwyn, glancing. Question: "Is any agent or provider close to its budget?" (playbook 1). Needs-you amber stays the most visible state (playbook 2); budget colours must never be mistaken for it.

**Colours** (panel #1d1e2c; T-059 backing rgba(12,13,22,.8) over the panel = #0f101a, 0.8*12+0.2*29 = 15, 0.8*13+0.2*30 = 16, 0.8*22+0.2*44 = 26)

| State | Bar fill | Text | Text on panel | Text on backing |
|---|---|---|---|---|
| ok (below `warn_at`) | #53BA7E (theme accent) | #53BA7E | 6.82:1 | 7.84:1 |
| near (from `warn_at`) | #f0e04a | #f0e04a | 12.14:1 | 13.94:1 |
| alert/over (from `alert_at`, or over) | #e63946 (theme bad) | #ff6b6b (theme bad_text) | 5.94:1 | 6.82:1 |

Ratio = (L1+0.05)/(L2+0.05) with WCAG relative luminance: green L=0.385, yellow 0.723, red text 0.328, panel 0.0127 (1.0 against 0.0127+0.05 = 0.0627), backing 0.0053. Bar fills are non-text, need 3:1: red fill #e63946 is 3.95:1 on panel, 4.54:1 on backing; green and yellow are well above.
Why this yellow: needs-you amber #f4a261 is hue 27, L 0.459. Yellow #f0e04a is hue 54, L 0.723: 27 degrees of hue and 0.26 of luminance apart, clearly lemon not orange. The usual #e9c46a was rejected (hue 43, only 16 degrees from amber). Red #ff6b6b is hue 0, 27 degrees the other way. Amber also always carries the diamond and its pill; budget states never use a diamond. The three budget states are also separated from each other by luminance (0.39, 0.72, 0.33), so green vs red does not rely on hue alone.
Bar fill now follows state, not provider. The provider chip colour stays on the chip and the dashed "budget not set" track is unchanged.

**Word or glyph per state** (never colour alone, playbook 5)
- ok: no extra word; the "% of your budget" text.
- near: the word "near budget" after the %, e.g. "70% near budget". Word only, no glyph, so nothing can read as the amber diamond.
- alert, under 100%: "at limit" with the %, e.g. "93% at limit".
- over: keep T-060 text "over by X" and its triangle in the collapsed line; the red colour is added.
- aria-label appends the state: ", near budget" / ", at limit" / existing "over budget by X". No colour names.

**Hatch**: stays for over. It is the non-colour cue for the overflow beyond the bar; keep `var(--text)` colour so it reads on red.

**Where it shows**
- Summary (usage panel rows): bar fill, % text and the word, per provider and per agent.
- Detail: same on every row; sort order unchanged (highest share first), so red rows are already on top.
- Collapsed summary line: the % or "over by X" text takes the state colour and the word ("near budget" / "at limit") follows it; shows the provider with the highest state.
- Phone sheet (390x844): same rows at 12px text; the word wraps below the % rather than truncating.

**Motion**: none added. Bar width keeps its T-060 behaviour; colour changes instantly, so reduced-motion needs no alternative (playbook 3).

**Accessibility check**: all text at least 5.94:1 on both backings; state carried by word and aria-label; hatch for over; builder to verify yellow and amber side by side in the screenshots.

**Open questions**
- Is "near budget" / "at limit" the wording Merwyn wants? Merwyn can answer.

— Dinda (designer)

Janice (pmo), 26 Nov: Dinda's UX accepted; moved to build. Wording as Dinda proposed (Merwyn can change it later). Technical design: thresholds read and validated in engine/runtime/budgets.py, colours as theme.yaml palette tokens (not hard-coded in the template), state maths pure in office-core and node-tested. Janice stands in for Fang. No compliance flag. Engineer: do not set status.

## Build notes
What changed
- `engine/runtime/budgets.py`: optional top-level `thresholds: { warn_at, alert_at, set_by, set_on }`, validated 0 < warn_at < alert_at <= 100 (numbers, bools rejected), set_by and set_on required, unknown keys rejected. Absent gives 70 and 90 marked set_by "default". Resolved data carries `thresholds`.
- `offices/ai-office/budgets.yaml`: thresholds 70 / 90, set by Janice (pmo), 2026-11-26. `theme/theme.yaml`: new palette token `near: "#f0e04a"` (Dinda's yellow); ok uses `accent`, alert uses `bad` (fill) and `bad_text` (text). No hex in the template rules.
- `office.template.html` (office-core): `budgetLevel(pct, over, th)` and `row.level` (unset, ok, near, alert, over), pure and node-tested. The level uses the rounded % the text shows, so a row reading "70%" is always yellow. Bad or missing thresholds fall back to 70/90.
- View: bar fill follows level (not provider; provider chip colours untouched, dashed "budget not set" track untouched); % text coloured; word "near budget" / "at limit" after the % (own span so it wraps below on the phone sheet); over keeps "over by X", triangle and hatch, now red; Detail provider header and collapsed line take the level colour and word; aria-label appends ", near budget" / ", at limit" (over keeps "over budget by X"); no colour names.
- Docs: `engine/schema/usage.md`. `office.html` regenerated.
- Deviation from the design: none. One note: the 100% case below over ("at budget", 99.5 to 100%) reads "at limit". The old T-060 test that bans amber/red on the hatch still passes (hatch uses the text colour).

How to verify
- `python -m unittest discover -s tests -t .` then `python scripts/office_app.py ai-office --check`
- `cp /tmp/three/package/build/three.min.js engine/app/` and open `engine/app/office.html`, or `python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl` for the recorded page.

Output
- Tests: `Ran 346 tests ... OK` (golden: `Ran 29 tests ... OK`); `office.html: up to date (169 KB, 84 events)`; recorded page `up to date (171 KB, 53 events)`; ledger CLI `53 runs kept (1 not reported), 4,198,359 tokens, 0 errors, 0 warnings`; board.py: 62 tasks, no problems (board.md discarded).
- New tests: thresholds boundaries 0/69/70/89/90/100(99.6)/over and custom thresholds (node), config validation (defaults, valid, 10 bad pairs, who/when, unknown key), shipped file 70/90, palette token and no-amber rule, state word and aria-label.
- Recorded page (real, 4,198,359 of 5,000,000 tokens): provider 84% yellow "near budget"; Sebastian 88% yellow, Dinda 87% yellow, Cahyani 83% yellow, Emmy 81% yellow, Fang 79% yellow, April 69% green, Wulan 62% green. No red on the real page.
- Red states: temp budgets copy (not committed, in /tmp/t062-shots/over.html): provider 98% red "at limit", Cahyani 92% red "at limit", Sebastian over by 82k red with triangle and hatch.
- Screenshots in /tmp/t062-shots/, Read and checked: `real-*`, `over-*`, `syn-*` (Summary and Detail, 1280x800 and 390x844) and `needsyou-*` (synthetic copy with a smaller SDK budget at ?t=106: "1 needs you" amber pill with diamond beside a yellow "75% near budget" row; clearly orange vs lemon, different shape and wording). Console and page errors: none across all 24 shots (playwright, chrome headless, swiftshader).
- Note: `?t=2` on the synthetic page has no needs-you yet; the needs-you moment is at ?t=106 (timeline compressed), and the stock synthetic budgets have no yellow row, hence the temp copy.

Open for Reviewer: contrast ratios are from Dinda's table (not re-measured); I checked the colours by eye in the screenshots only.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
