---
name: review-checklist
description: Independent review of a task's PR against its spec. Use when a task enters the review stage.
---
# Review checklist

1. Read only the Spec first. Write down how you will verify each "done when" check.
2. Check out the PR branch. Run every check: tests, scripts, file existence. Paste real output.
3. Then read Build notes and the diff. Look for: untested paths, deviations from the Design, secrets or company data, files edited that are marked "generated — do not edit".
4. Verdict in `## Review log`:
   - `PASS` — every check passes with evidence.
   - `REJECT` — list each failing check and the fix. Style comments go under "Notes", never cause a reject.
5. On PASS set status `done`; on REJECT set status `build` and owner `engineer`. Second REJECT: add the task to "Waiting on Merwyn".
