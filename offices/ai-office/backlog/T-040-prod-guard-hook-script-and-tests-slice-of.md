---
id: T-040
title: "Prod-guard hook script and tests (repo-only slice of T-019)"
phase: 4-code-tooling
status: spec
priority: P0
owner: pm
where: code
project: ai-office
depends_on: []
pr: null
---

> Slice of T-019 ("biggest risk reducer"). Builds and tests the guard here, using fixture commands only. Installing it in nimbus or klik-workspace is a write to a company repo and stays a Merwyn gate.

## Done when
- [ ] A PreToolUse hook script in this repo blocks commands that write to nimbus-prod (default deny) and allows read-only commands and Bytebase script runs
- [ ] Tests cover allowed and blocked fixture commands, with no real hostnames, credentials or rows
- [ ] README says how a company repo would install it (install itself is out of scope)

## Spec

## Design

## Build notes

## Review log

## Decision

## Open questions
- What exactly counts as an allowed "Bytebase script" invocation? Default in the spec is deny unless it matches an explicit allowlist. Owner: Merwyn (answers the allowlist at spec approval if Emmy cannot infer it from the repo).
