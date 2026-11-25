---
name: spec-writing
description: Write a task's Spec section. Use when a task enters the spec stage.
---
# Spec writing

Write under `## Spec` in the task file:

- **Problem** — 1–2 sentences. Who is affected and what goes wrong today.
- **In scope** — bullets.
- **Out of scope** — bullets. Anything tempting but not needed now.
- **Done when** — rewrite the task's checks so a reviewer can verify each by running a command or opening a file. Replace vague words ("works", "clean") with an observable result.
- **Open questions** — each with who can answer (agent id or Merwyn). If any blocks the build, say so.

Checks: one screen max; no implementation choices (that is the Architect's); facts only, unverified items go to Open questions.
