---
id: T-002
title: "Give Claude GitHub access to the impact-credit-solutions org"
phase: 0-office
status: todo
priority: P0
owner: human
where: chat
project: ai-office
depends_on: []
pr: null
---

> Blocks every task that touches company repos

## Done when
- [ ] Claude GitHub app installed on the impact-credit-solutions org (org owner)
- [ ] add_repo succeeds for impact-credit-solutions/klik-workspace

## Spec

## Design

## Build notes

## Review log
- 25 Nov 2026: REOPENED. list_repos showed org repos via Merwyn's own GitHub login, but add_repo for klik-workspace failed: the Claude GitHub app is installed only on merwyns-maj. The earlier PASS checked the wrong thing. — Janice (pmo)
- 25 Nov 2026: `list_repos` shows impact-credit-solutions/nimbus, klik-workspace, product-brain, Users-Portal, Document-Generator-Service, nimbus-proto, thirdparty, all with can_push: true. PASS.

## Decision
- Claude GitHub app has access to impact-credit-solutions and merwyns-maj (all repositories). Unblocks T-003, T-017, T-018, T-025.

## Open questions
