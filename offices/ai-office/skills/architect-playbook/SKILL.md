---
name: architect-playbook
description: How Fang designs: smallest viable design, explicit trade-offs, and architecture decision records. Use whenever a task enters design, or a design is questioned.
---
# Architect playbook

Distilled from architecture decision record (ADR) practice (sources at the end). Pairs with `decision-record`.

## 1. Design the problem you have
- Solve today's spec. Do not generalise for futures nobody has asked for; that is the most common design mistake and the one Cahyani is told to watch for.
- Reuse what exists (scripts, schema, base agents) before adding a component. A new service needs a written reason.

## 2. What the Design section contains
- **Approach** — a few bullets naming the files or components touched.
- **Interfaces** — exact file formats, function signatures, CLI arguments, schema keys. Concrete enough that Sebastian builds without guessing.
- **Risks** — what could go wrong and how the build handles it.
- **Flags** — anything touching production, money, credentials or personal data goes to Wulan before build.

## 3. Decision records
Write one when a decision is significant, hard to reverse, or likely to be questioned later. Keep each record to one decision, in the repo next to the work:
- **Title**, **Status** (proposed, accepted, superseded by …), **Context** (the forces at play), **Decision**, **Consequences** (what gets easier, what gets harder).
- Options and pros/cons are fine when they stick to verifiable facts; question assumptions that rest on fashion.
- A decision that replaces an earlier one gets a new record that names it; the old one is marked superseded, never edited away.
- Records are thinking tools, not after-the-fact paperwork: draft the record before building, not after.

## 4. Trade-offs
When two options are close, show them in a short table (cost, risk, effort, reversibility). If the choice is a business call, it is a human gate: hand it to Janice with your recommendation.

## Anti-patterns
- Over-engineering. Designs that only exist in prose. Decision records written after the fact or never. Quietly reversing an earlier decision.

## Sources
- Martin Fowler, Architecture Decision Record — https://www.martinfowler.com/bliki/ArchitectureDecisionRecord.html
- ADR tips (Nygard template, objective pros and cons) — https://github.com/joe-reed/adr-tips
- AWS, ADR best practices from 200+ records — https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/
- Red Hat, ADRs next to the code — https://www.redhat.com/en/blog/architecture-decision-records
- Google eng-practices, over-engineering — https://google.github.io/eng-practices/review/reviewer/looking-for
