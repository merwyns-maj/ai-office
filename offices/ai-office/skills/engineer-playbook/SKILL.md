---
name: engineer-playbook
description: How Sebastian builds: small short-lived branches, tests with the change, honest build notes. Use whenever a task enters build.
---
# Engineer playbook

Distilled from small-PR and trunk-based development practice (sources at the end). Pairs with `build-conventions` and `pr-workflow`.

## 1. Small batches
- One task, one short-lived branch, merged within the session if possible. Long-lived branches turn into painful merges.
- Keep the PR as small as it can be while still adding value. If the diff is hard to review in one sitting, split it.
- Start every branch from fresh `main`.

## 2. Tests come with the change
- Every "Done when" check that code can verify gets a test or a runnable command in Build notes.
- Tests must fail when the code is broken and pass when it works; a test that cannot fail is noise.
- Run everything before handing off and paste the real output.

## 3. Build to the design
- Follow Fang's interfaces exactly. If the design doesn't survive contact with the code, stop and write why in Build notes; don't redesign silently.
- No speculative features, no "while I'm here" refactors outside the task.

## 4. Build notes (what Cahyani reads after her own check)
- What changed (files), how to verify (commands), what deviates from the design and why, known limits.

## 5. Safety
- Never push to `main`, never merge your own PR, never touch production systems.
- No secrets, tokens or company data in code, tests, fixtures or commit messages.

## Anti-patterns
- Giant PRs. Tests added later. "It works on my machine" without output. Silent design changes.

## Sources
- DORA, trunk-based development — https://dora.dev/capabilities/trunk-based-development/
- Microsoft Engineering Playbook, pull requests — https://playbook.microsoft.com/code-with-engineering/code-reviews/pull-requests/
- Zalando, a plea for small pull requests — https://engineering.zalando.com/posts/2017/10/a-plea-for-small-pull-requests.html
- Swarmia, why small pull requests are better — https://www.swarmia.com/blog/why-small-pull-requests-are-better/
