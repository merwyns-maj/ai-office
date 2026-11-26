---
id: T-058
title: "Usage panel: By provider as an accordion"
phase: 6-office
status: done
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-057]
pr: https://github.com/merwyns-maj/ai-office/pull/43
---

> Merwyn, artifact comment on the 3D office, 26 Nov 2026 13:09 WIB, anchored on "By provider": "accordion here". Same pattern as the T-057 By agent accordion (Dinda's UX, accepted by Fang), so no new UX consult.

## Done when
- [ ] In the usage panel (docked and phone sheet, synthetic and recorded pages), each provider row is an accordion section, expanded by default, using the T-057 pattern: real `<button aria-expanded>`, keyboard Enter/Space, focus kept, no animation under reduced motion
- [ ] Inside each provider: its models (short label, tokens, % of that provider) and the agents that used it (name, tokens, % of that provider); percentages add to 100 within the provider (largest remainder)
- [ ] The provider bar and "N% of session" label stay on the header line; recorded page (one provider) lists the agents with their share
- [ ] Tests for the within-provider shares; all tests, --check and golden pass; headless screenshots at 1280x800 and 390x844 with no console errors

## Spec
Small UI change from Merwyn's artifact comment, spec by Janice: scope as in Done when. Out of scope: other panel sections. — Janice (pmo)

## Design
Reuse accHTML/barLine and `shares()` from T-057 in engine/app/office.template.html; compute per-provider model and agent rows in office-core (pure, node-testable); regenerate office.html. No compliance flag. — Janice (pmo), standing in for Fang on a reuse-only change

## Build notes
What changed (engine/app/office.template.html, regenerated office.html; tests/test_office_app.py):
- New pure `providerBreakdown(s)` in office-core: per provider, models and agents with tokens and whole-number share of that provider via the T-057 `shares()` (largest remainder, ties to earlier item, sorted by tokens desc).
- By provider rows now use `accHTML` (id `prov:<provider>`), expanded by default, same button/aria-expanded/focus/reduced-motion behaviour as By agent. Header keeps chip, name, cost, bar and "N% of session".
- Recorded page: one provider accordion listing the agents with their share of the provider (runs with tokens not reported add 0 and are left out); "Model not reported" note because the ledger records no model.
- Small CSS: `.sub`, `.rr.sh`, `.note`, and the provider name can ellipsize so the cost is not clipped (long recorded label "Claude Code subagents (Max plan)" was clipping at 1280).

How to verify:
- `python3 -m unittest discover -s tests` -> Ran 311 tests, OK (new: test_percentages_within_provider, mode provshares: adds to 100 per provider, tokens match buckets).
- `python3 scripts/golden.py ai-office` -> golden: 13 cases, 75 checks, 0 problems.
- `python3 scripts/office_app.py ai-office --check` and with `--ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --check` -> both up to date.
- Screenshots (headless chrome, usage open, t=99999): /tmp/t058-shots/{office,rec}-{1280x800,390x844}.png (not committed). Only console output is swiftshader "GPU stall due to ReadPixels" driver notices; no page errors.

Deviations / notes: there is no scripts/validate.py in the repo, so no validate run; board.py ran (58 tasks), board.md discarded. Keyboard Enter/Space and reduced motion are inherited from the T-057 button and CSS; I checked them by code reuse, not by a scripted key test. three.min.js copied in for screenshots, gitignored.

## Review log
PASS, 26 Nov 2026, PR #43 head 540545c. Diff limited to template, generated office.html, tests and task file; 311 tests; golden 13/75/0; --check up to date; recorded page built. Within-provider shares match a Python largest-remainder sum of the synthetic fixture and the ledger, every list adds to 100. Headless at 1280x800 and 390x844, both pages, normal and reduced motion: provider headers are buttons, expanded by default; Enter/Space flip aria-expanded and keep focus; 0 console errors.
Notes: recorded provider name truncated at 1280; "Model not reported" needs a scroll on the phone sheet; recorded agent shares tested by hand only.
— Cahyani (reviewer), recorded by Janice (pmo)

## Decision

## Open questions
