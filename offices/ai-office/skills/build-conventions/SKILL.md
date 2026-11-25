---
name: build-conventions
description: Conventions for code built in ai-office. Use whenever writing or changing code or scripts in this repo.
---
# Build conventions

- Python 3.11, standard library first. New dependency only if the Design names it; then add it to `requirements.txt`.
- Scripts take the office id as the first argument and are runnable from the repo root.
- Every script prints a one-line summary of what it did.
- Tests: `tests/test_<module>.py`, runnable with `python -m unittest`. At minimum, one test per "done when" check that code can verify.
- No secrets, tokens or company data in code, fixtures or commit messages.
- Branch `t-xxx-short-name`; commits small; PR body lists what changed and how to verify.
