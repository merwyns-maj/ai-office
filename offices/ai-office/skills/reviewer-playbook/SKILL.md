---
name: reviewer-playbook
description: How Cahyani reviews: design first, every line, tests that bite, and fair verdicts. Use whenever a task enters review. Pairs with review-checklist.
---
# Reviewer playbook

Distilled from Google's engineering practices on code review and related sources (at the end).

## 1. Order of review
1. **Overview** — read the Spec and the PR description. Does the change make sense at all? If not, say so before reading code.
2. **Main part** — the files that carry the change. Design problems found here stop the review early.
3. **The rest** — in a sensible order, every human-written line. Look at whole files when a snippet isn't enough.

## 2. What to look for
- **Design** — does it fit the system? Is it the simplest thing that meets the spec? Watch hardest for over-engineering.
- **Functionality** — does it do what the spec says, including edge cases and failure paths?
- **Tests** — present with the change, sensible, and they would fail if the code broke.
- **Complexity** — could a future agent understand and change it quickly?
- **Docs** — updated or removed along with the code they describe.
- **Safety** — secrets, company data, edits to generated files, writes outside the repo.

## 3. The standard
- Approve when the change makes the codebase better overall, even if it isn't perfect. Improvement, not perfection.
- Reject only on the spec, correctness, safety or real design problems. Style preferences are notes.
- When the author shows that two approaches are equally valid, accept the author's.
- Don't let a disagreement stall: after the second REJECT, escalate through Janice.

## 4. Evidence
- Run it. Paste commands and output. A PASS without evidence is not a PASS.
- Read Build notes only after forming your own view.

## Sources
- Google eng-practices, code review overview — https://google.github.io/eng-practices/review/
- Google eng-practices, what to look for — https://google.github.io/eng-practices/review/reviewer/looking-for
- Google eng-practices, the standard of code review — https://google.github.io/eng-practices/review/reviewer/standard.html
- freeCodeCamp, three-stage review process — https://www.freecodecamp.org/news/what-google-taught-me-about-code-reviews/
