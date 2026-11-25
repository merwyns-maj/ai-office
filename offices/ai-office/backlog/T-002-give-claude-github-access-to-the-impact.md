---
id: T-002
title: "Give Claude GitHub access to the impact-credit-solutions org"
phase: 0-office
status: done
priority: P0
owner: curator
where: chat
project: ai-office
depends_on: []
pr: null
---

> Blocks every task that touches company repos

## Done when
- [x] Org owner approved the Claude GitHub app
- [x] A session can read klik-workspace and nimbus

## Spec

## Design

## Build notes

## Review log
- 25 Nov 2026: `list_repos` shows impact-credit-solutions/nimbus, klik-workspace, product-brain, Users-Portal, Document-Generator-Service, nimbus-proto, thirdparty, all with can_push: true. PASS.

## Decision
- Claude GitHub app has access to impact-credit-solutions and merwyns-maj (all repositories). Unblocks T-003, T-017, T-018, T-025.

## Open questions
