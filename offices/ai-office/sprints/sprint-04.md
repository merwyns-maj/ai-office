# Sprint 4

**Goal:** Close the last prod-access wording gap, hire the office's product designer with a researched playbook, and put a first 3D animated office in front of Merwyn, all inside merwyns-maj/ai-office.

## Tasks (in order)
1. [T-046](../backlog/T-046-compliance-files-match-prod-access-decision.md) (P0): compliance files still name Bytebase change issues as the write path; must match the 25 Nov decision before any guard install. Small, runs first and in parallel.
2. [T-047](../backlog/T-047-hire-product-designer-agent.md) (P1): hire Dinda (Product Designer, ISFP) with a designer-playbook built from sources. Merwyn asked for it on 25 Nov.
3. [T-048](../backlog/T-048-3d-animated-office-prototype.md) (P1): 3D animated office prototype (three.js, replays a recorded event log). Depends on T-047 so Dinda designs it.

3 tasks, all repo-only, none behind a human gate. Not chosen: T-019 guard install (human gate), T-024 SDK runs, T-041, everything behind T-002.

## Exit criteria
- T-046, T-047, T-048 `done`: Reviewer PASS, PR merged by Janice.
- Specs approved by Janice before design; at most 2 tasks in `build`.
- build_agents.py clean; all tests pass; Merwyn has a link to the office prototype.

## Decisions recorded (Merwyn, 25 Nov 2026)
- "Proceed ahead without waiting for me. Goes all the way end!" The office runs Sprint 4 end to end and stops only for human_gates.
- Hire a product designer if needed and give her the right skills. The name Dinda and ISFP are Janice's choice; Merwyn can rename.

## Waiting on Merwyn (not blocking)
- T-002 (no chasing), R-8 read-only roles, R-7 SQL key names, T-019 guard install.

## Close (26 Nov 2026) — Janice (pmo)
Status: scope Green, schedule Green, budget Green.

**Finished:**
- T-046 compliance files match the 25 Nov prod access decision — PR #23 (Compliance PASS with conditions C1, C2; Reviewer PASS)
- T-047 Dinda (Product Designer, ISFP) hired, designer-playbook, `consults:` key validated — PR #24 (Reviewer PASS)
- T-048 3D animated office prototype — PR #25. Two Reviewer REJECTs (value echo, then keys and numbers not scanned); Merwyn chose on 26 Nov 09:01 to accept as is and move the remaining gap to T-027. Published as a private artifact: https://claude.ai/artifact/CkB5c3hEKfaK61kUuUjMku

**What went well:** Dinda's first consult (UX design) fed Fang's design directly; Cahyani's reviews caught a real data-rule leak twice; the page replays a real sprint with real merge times.

**What got stuck:** agent sandboxes cannot reach CDNs or most source sites (npm works); approval prompts unanswered while Merwyn was away blocked a CDN check, so the page loads a sibling three.js first and falls back to cdnjs.

**Carry forward:**
- T-027: the data rule must also scan key names and numbers (or the rendered data blob) and never echo a hit key; phone numbers with separators; phone layout.
- Merwyn: open the artifact, confirm it renders, and read the fps readout on a laptop for 60 s.
- T-002 (no chasing), R-8 read-only roles, R-7, T-019 guard install: unchanged.
