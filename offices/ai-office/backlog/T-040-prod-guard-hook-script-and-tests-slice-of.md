---
id: T-040
title: "Prod-guard hook script and tests (repo-only slice of T-019)"
phase: 4-code-tooling
status: design
priority: P0
owner: architect
where: code
project: ai-office
depends_on: []
pr: null
---

> Slice of T-019 ("biggest risk reducer"). Builds and tests the guard here, using fixture commands only. Installing it in nimbus or klik-workspace is a write to a company repo and stays a Merwyn gate.

## Done when
- [ ] Given a fixture hook payload (JSON on stdin) whose Bash command writes to the prod target (e.g. INSERT/UPDATE/DELETE/DDL via a SQL client, or a deploy/migrate command), when the hook script runs, then it exits 2 and prints a reason naming the matched rule on stderr
- [ ] Given a fixture payload for a read-only command (e.g. SELECT, `git status`, `ls`), the script exits 0 with no stderr
- [ ] Given a fixture payload for a Bytebase script run that matches an entry in the allowlist file, the script exits 0; given one that matches no entry, it exits 2 (default deny)
- [ ] Given malformed or empty stdin, or a payload with no command, the script exits 2 (fail closed) and says why
- [ ] One test command (stated in the README) runs all fixture cases, exits 0, and the output lists at least 3 blocked, 3 allowed and 1 malformed case
- [ ] A scan of the repo files added by this task finds no real hostname, credential, connection string or data row (fixtures use obvious placeholders such as `prod.example.invalid`); the tests make no network call
- [ ] README (in the guard's folder) gives the settings snippet and steps a company repo would follow to install it, and states that installing is not done here

## Spec
**Problem.** Agents running in company repos could write to nimbus-prod (production lending data) by mistake, and nothing stops them today. This is the repo-only slice of T-019: build and test the guard here so it is proven before any company repo adopts it.

**In scope**
- A Claude Code PreToolUse hook script, in this repo, for the Bash tool.
- Default-deny policy: a command aimed at the prod target is blocked unless it is read-only or matches an explicit allowlist (the allowlist is a file in this repo).
- Fixture-based tests and a README with install steps.

**Out of scope**
- Installing the hook in nimbus, klik-workspace or any other repo (human gate: writes to a company repo).
- Any real connection, hostname, credential or row; any test that reaches a network.
- Guarding non-Bash tools, non-prod environments, or Bytebase itself; approval workflows; logging or alerting.
- Deciding the final Bytebase allowlist contents (see Open questions); the starter allowlist ships with placeholders only.

**Open questions**
- Merwyn: confirm default-deny with an allowlist, and which Bytebase script invocations belong on it. Non-blocking: build proceeds with default-deny and a placeholder allowlist; entries are added when Merwyn answers.
- Fang (architect): how the prod target is identified without real hostnames in this repo (e.g. a pattern file kept outside the repo, supplied at install). Non-blocking for spec; must be settled in Design.
- Fang (architect): confirm the hook's blocking exit code (2) and stdin payload shape against current Claude Code hook docs before design; the checks above assume them.
- Janice: T-019 and T-024 parent files could not be read in this pass (filenames not found); parent-level constraints are unchecked.

— Emmy (pm)

## Spec approval
- Approved for design. Pick rule (priority, then lowest id, dependencies done) confirmed. Parent tasks are T-019 / T-024 in backlog/. — Janice (pmo)

## Design

## Build notes

## Review log

## Decision

## Open questions
- What exactly counts as an allowed "Bytebase script" invocation? Default in the spec is deny unless it matches an explicit allowlist. Owner: Merwyn (answers the allowlist at spec approval if Emmy cannot infer it from the repo).
