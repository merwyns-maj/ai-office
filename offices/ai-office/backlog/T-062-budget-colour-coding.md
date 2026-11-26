---
id: T-062
title: "Budget bars: green, yellow, red as usage nears the budget"
phase: 6-office
status: review
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-060]
pr: https://github.com/merwyns-maj/ai-office/pull/50
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
- View: bar fill follows level (not provider; provider chip colours untouched, dashed "budget not set" track untouched); % text coloured; word "near budget" / "at limit" after the % (own span so it wraps below on the phone sheet); over keeps "over by X", triangle and hatch, now red; Detail provider header takes the level colour and word; the collapsed line's % / "over by X" text takes the state colour via `.usum .lv-ok/.lv-near/.lv-alert/.lv-over` (added in rework after Review 1; first version only coloured the trailing word, the % and over text stayed plain); aria-label appends ", near budget" / ", at limit" (over keeps "over budget by X"); no colour names.
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
### Review 1, 26 Nov 2026, PR #50 head 91c6735e087425c89204155793ad5e9836afa63a: REJECT

Checks (run on the PR head, not taken from Build notes):
- Tests, golden, --check, ledger: `python -m unittest discover -s tests` -> `Ran 346 tests ... OK`; `python scripts/golden.py ai-office` -> `golden: 13 cases, 75 checks, 0 problems`; `office_app.py ai-office --check` -> `office.html: up to date (169 KB, 84 events)`; `python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl` -> `53 runs kept (1 not reported), 4,198,359 tokens, 0 errors, 0 warnings`. PASS.
- Thresholds in node: tests cover 0/69/70/89/90/100/over and custom 50/80; bad or missing thresholds fall back to 70/90. On the page (temp copy of the recorded page, agent budgets set from real use): Sebastian 69% green `lv-ok rgb(83,186,126)`, Dinda 70% yellow "near budget" `rgb(240,224,74)`, Cahyani 89% yellow, Emmy 90% red "at limit" (fill `rgb(230,57,70)`, text `rgb(255,107,107)`), Fang 100% red "at limit", April "over by 6.2k" red with triangle and hatch. Same at 1280x800 and 390x844, Summary and Detail. PASS.
- Config validation (temp office copies, built with --ledger): equal 80/80, reversed 90/70, warn 0, alert 101, warn "70" -> exit 1 `budgets: thresholds: need 0 < warn_at < alert_at <= 100`; set_by removed -> exit 1 `thresholds: set_by is required`; 70/100 -> exit 0. Shipped file: 70/90, Janice (pmo), 2026-11-26. PASS.
- Theme tokens: `near: "#f0e04a"` in theme.yaml; template rules use `var(--near)`, `var(--bad)`, `var(--bad-text)`, `var(--accent)`; the `:root` hex is the existing fallback, overwritten at runtime from `D.theme.palette` (same pattern as every other token). PASS.
- Never colour alone: words "near budget" / "at limit" / "over by X" on rows and Detail headers; aria-labels end ", near budget" / ", at limit" / "over budget by X", no colour names. PASS.
- Contrast, measured with getComputedStyle and WCAG luminance: on panel #1d1e2c green 6.82, yellow 12.14, red text 5.94; usage panel at opacity 0 (`tp tpd`, backing `rgba(12,13,22,.8)`) over the panel colour green 7.81, yellow 13.90, red 6.80. All >= 4.5. PASS.
- Amber pill vs yellow: headless render, synthetic page Detail with `#pill.on` ("1 needs you", bg `rgb(244,162,97)`) beside four yellow rows: filled orange pill vs thin lemon bars and lemon text, clearly distinct. PASS. Screenshot /tmp/rv062/shots/pill-vs-yellow-1280.png.
- Provider chips and "budget not set": main vs branch synthetic page, all 8 chips identical (`SDK|rgb(192,132,252)|... /0.22|solid`); unset track identical (`dashed rgb(154,160,180) 1px 4px`, 1 row). PASS.
- Console errors: none across 16 page loads (recorded, temp, synthetic, main; 1280x800 and 390x844). PASS.
- **Collapsed summary line: FAIL.** Dinda's design: "Collapsed summary line: the % or 'over by X' text takes the state colour and the word follows it". Build notes say it does. It does not: `usageSummary()` adds `class="lv-near"` / `class="lv-alert"` / `<b class="lv-over">`, but no CSS rule matches them outside `.bx`, `.dh` and `.bw`. Measured: `<span class="lv-near">84% of your budget</span>` -> `rgb(242,237,228)` (the plain text colour); `<span class="lv-alert">93% ...</span>` -> `rgb(242,237,228)`; `<b class="lv-over">▲ over by 198k</b>` -> `rgb(242,237,228)`. Only the trailing word is coloured, and the over case has no colour at all. Screenshot /tmp/rv062/shots/over-collapsed.png.

Fix needed (one item)
1. Give the collapsed line's state spans their colour from the tokens, e.g. `.usum .lv-ok{color:var(--accent)}.usum .lv-near{color:var(--near)}.usum .lv-alert,.usum .lv-over{color:var(--bad-text)}` (or put `bx` on those spans), and add a test that the collapsed ok/near/alert/over text gets the state colour (a template-rule assertion like the existing palette test is enough). Regenerate office.html.

Notes (not reasons for the reject)
- Contrast against the backing over a light part of the scene (worst case, backing over white) is lower: green 4.44, red 3.87. The spec measures against the panel, so this passes the spec; worth a look if Merwyn runs the panel at 0% over the paper-coloured walls.
- `budgetLevel` accepts any numeric thresholds in the browser (it does not re-check warn < alert); fine because budgets.py validates before build.
- External skills design:accessibility-review and data:validate-data are not available in this session; checks were done by hand as above.

— Cahyani (reviewer)

## Decision

## Open questions

### Rework 1 (Sebastian)
- Added `.usum .lv-ok`, `.lv-near`, `.lv-alert,.lv-over` rules from `--accent`, `--near`, `--bad-text`; new test `test_collapsed_summary_line_text_takes_the_state_colour`; office.html regenerated; recorded page rebuilt.
- Measured on collapsed line at 1280x800 (temp budgets copy): near "84% of your budget" `rgb(240,224,74)` with "near budget" word; over "over by 26k" `rgb(255,107,107)`. Screenshots /tmp/t062-shots/rework-near.png, rework-over.png (3D area blank there: temp copy had no three.js; irrelevant to the line).

— Sebastian (engineer)
