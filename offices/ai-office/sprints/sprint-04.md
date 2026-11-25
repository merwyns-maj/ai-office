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
