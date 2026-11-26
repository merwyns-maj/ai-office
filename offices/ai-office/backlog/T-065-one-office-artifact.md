---
id: T-065
title: "One office artifact: the real usage ledger and the chat on one page"
phase: 6-office
status: review
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-063]
pr: 57
---

> Merwyn, 26 Nov 2026 17:14 WIB: "I don't see the chat", then "Keep only 1 artifact, clean up. Have only 1 SSOT".

## Facts (Janice)
- Today there are two artifacts. "AI Office" (5f1bb811-1633-4bfb-8285-9bcb2408dec2) is built with `scripts/office_app.py ai-office --chat`. It replays the synthetic fixture and has the chat with its db (owner-only rule on `chat`). "AI Office token usage" (fdb54f4f-d1f4-4f23-b1d4-2e67b9b0296a) is built with `--ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`. It replays the real ledger and has no chat.
- `office_app.py` refuses `--chat` with `--ledger` (T-063 design: "the recorded usage page never has chat").
- Keep the "AI Office" artifact: its db already holds the chat rules and the `chat/office` meta doc. Deleting "AI Office token usage" is done by Janice after the merge, with Merwyn confirming the delete.

- Merwyn, 26 Nov 2026 17:20 WIB, at 5,201,744 tokens used (104% of 5M): "Raise budget to 8M". `budgets.yaml` claude-code `tokens: 8000000`, `set_by: Merwyn`. Three tests in `tests/test_budgets.py` pin the shipped 5,000,000 and the 76% start, so this change rides with this task's build (not a planning PR).

## Done when
- [ ] `budgets.yaml` claude-code is 8,000,000 set by Merwyn; tests no longer pin the shipped budget value (they check the file is valid and dated, and use their own numbers for maths)
- [ ] One build gives the page that replays the real ledger (usage panel, Summary and Detail, budgets and colours as on the token usage page today) and has the chat, as on the AI Office page today
- [ ] The README and the pmo-playbook say which single command builds the published page, and which artifact it goes to
- [ ] Tests cover the combined build; the existing synthetic and ledger builds still pass
- [ ] After merge: "AI Office" is republished from the combined build, and "AI Office token usage" is deleted once Merwyn confirms

## Spec
**Problem.** Merwyn has two published pages: one with the chat (synthetic replay) and one with the real usage ledger (no chat). He wants one artifact and one source of truth: the real ledger and the chat on the same page.

**In scope**
- One build of the page that replays the real ledger (usage panel, Summary and Detail, budgets and colours as on the token usage page today) and has the chat (as on the AI Office page today).
- That page is published to the existing "AI Office" artifact (5f1bb811-1633-4bfb-8285-9bcb2408dec2), keeping its db, rules (`chat` owner-only) and `chat/office` meta doc.
- The budget change (claude-code 8,000,000, set by Merwyn) and the test changes that go with it.
- README and pmo-playbook name the one command and the one artifact.
- Deleting "AI Office token usage" after merge, only when Merwyn confirms.

**Out of scope**
- New chat or usage features, new panels, visual redesign.
- Changing chat rules, retention, the compliance conditions C1 to C8 (they carry over unchanged), or the T-063 inbox procedure.
- Page size changes beyond what the combined build needs (any new limit is Fang's call).
- Any other artifact, and T-024 or T-064.

**Done when (checks a reviewer can run)**
- [ ] `offices/ai-office/budgets.yaml`: claude-code `tokens: 8000000`, `set_by: Merwyn`; the budget tests pass with the file at any valid value (none asserts 5,000,000 or the 76% start), and still check validity, a date, and their own maths with their own numbers.
- [ ] One command builds a page whose data holds both the ledger replay and `chat`. A node or headless check shows the usage panel (Summary and Detail) with the budget and colours matching the current token usage page, and the Chat button opening the panel.
- [ ] The same page, run with a stub `claude`: `claude.use` is called for `db` and `user` only, and 0 errors in the console, at 1280x800 and 390x844.
- [ ] The ledger numbers on the combined page equal those on a `--ledger`-only build of the same file (same totals and per-run rows); the page never shows the synthetic fixture when a ledger is given.
- [ ] Chat behaviour on the combined page is unchanged from T-063 (mentions, status chips, needs-you, scan, notice); the T-063 chat tests still pass.
- [ ] `--chat` with `--ledger` is accepted and no longer exits 2; its old refusal test is updated. The synthetic-only build and the `--ledger`-only build still work and still pass their tests. The committed page and `--check` agree.
- [ ] README and pmo-playbook name the single publish command and "AI Office" as its artifact, and say the token usage artifact is retired.
- [ ] After merge (Janice): "AI Office" is republished from the combined build and shows the real ledger and the chat; the old artifact is deleted only after Merwyn confirms.

**Spec approved** (Janice, 26 Nov 2026 17:24 WIB). PMO calls on the two Merwyn questions (reversible, no cost or risk difference): the page uses the one session ledger the office runs today (`usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`; there is only one); chat runs are shown the way the token usage page shows them today, with no new behaviour (out of scope).

## Design
**Approach.** Allow `--chat` with `--ledger`. That gives one command for the page we publish. The page code already treats the two as separate: `CFG = D.chat` controls the chat, and `REC` (`log.usage_source === 'recorded'`) controls the recorded usage view. Neither checks the other, so I expect no template change.
- Publish command (the only one): `python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat`. It writes `engine/app/usage-session_01MDGJq3GfaeozLojJo8W5Td.html`. That path is gitignored, keeps the current default and is not committed. Janice publishes this file to "AI Office" (5f1bb811-…) after each ledger append she wants shown. `--check --out <file>` works as it does now.
- `scripts/office_app.py`: remove the exit-2 refusal in `main()` and the `BuildError` in `build_data()`. `data.chat` is built the same way for both sources. Update the docstring and the `--chat` help text. The stale message already prints both flags.
- `offices/ai-office/budgets.yaml`: claude-code `tokens: 8000000`, `set_by: Merwyn`, `set_on: "2026-11-26"`, note `Raised from 5,000,000 by Merwyn, 26 Nov 2026 (T-065)`. Agent shares and thresholds stay the same (Janice's values). 43/30/13/6/5/2/1 of 8M gives whole numbers.

**Committed vs generated (Emmy's question).** `engine/app/office.html` stays committed. It is the synthetic replay with chat, used for the node tests, golden and `--check`, and it is never published. The combined page is generated and not committed.
| Option | Planning PRs | `--check` | Tests |
|---|---|---|---|
| A. Commit the combined page as office.html | Every ledger append makes it stale. A planning PR would need a page rebuild, which is not on the planning-only list | Fails on every session | Pinned to a moving file |
| **B. Keep synthetic office.html, generate the published page** | Unchanged | Same as today | Stable fixture |
B keeps one source of truth: the ledger file is the data, and the published page is built from it. office.html is a dev build, and the README says so.

**Page size.** The 216 KB `test_size_limit` stays on the committed synthetic page, where it guards hand-written page code (now 216,739 B, 4.4 KB headroom). The published page gets no fixed limit, because it grows with data, not code. Measured today: the `--ledger` build is 222,348 B, of which 26 KB is data (67 runs). Events add about 245 B per run, and chat data adds 544 B. 1,000 runs would add about 240 KB. The build prints the size in KB, and Janice records it at publish. The T-064 follow-up (chat code only with `--chat`) is unchanged.

**Page code paths.** None change. Checked: `focusModel` goes to `focusRec` under `REC`, and `renderFocus` still adds "Message <name>" when the chat is open. The needs-you pill, `setLive` after a seek, and the clock "(replay)" label do not depend on the other flag. If the headless check finds an interaction bug, the fix is in scope, is kept to that bug, and goes in Build notes. Any visible change goes to Dinda first.

**Tests.**
- `tests/test_office_app.py`: replace `test_chat_with_ledger_exits_2_and_the_library_refuses` with a combined-build test. It checks that `main([... --ledger L --chat --out tmp])` returns 0. The combined data minus `chat` must equal the `--ledger`-only data exactly (events, ledger totals, budgets, log), and `data.chat` must equal the committed page's `chat`. `--check` must return 0, then 1 after the file is touched. Also run `rec` and `budgets rec` node checks on the combined page. `test_default_build_has_no_chat_key` and the `--ledger`-only test stay as they are.
- `tests/test_budgets.py`: `test_valid_and_marked_as_starting_values` checks that there are no problems, tokens is a positive int, `set_by` is present, `set_on` is a valid date, and the agent tokens add up to the provider total. It no longer checks the literal value, note or author. `test_starting_use_is_76…` keeps the ledger fact 3,813,702 for runs 1 to 48, and checks the percentage with its own number: `round(100*3_813_702/5_000_000) == 76`. `test_recorded_page_carries…` asserts the page value equals `load_budgets(...)`, not 5,000,000.
- Manual check, recorded in Build notes: headless Chrome at 1280x800 and 390x844 on a /tmp copy with the T-063 stub `claude`. The usage panel must show "recorded", with Summary and Detail and budget colours as on the old usage page. The Chat button must open the panel. `claude.use` may be called only for `db` and `user`. The console must show 0 errors. Run the full `python -m unittest discover -s tests`.

**Docs.**
- `engine/app/README.md`: in Files, Regenerate and the chat paragraph, name the one publish command and "AI Office". Say that office.html is the synthetic dev build and is not published. Drop "never has chat / exits 2". Say the token usage artifact is retired.
- `engine/schema/usage.md` line 33: add `--chat`.
- pmo-playbook section 9: add a "Publish" step with the command, the artifact id, `declare_capabilities` (`db`, `user`) before publishing as today, and "republish after a ledger append".

**Risks.** (1) A second session ledger: the command takes one `--ledger`. When a second session starts, combining ledgers is a new task, not built now (Janice's call in the approval note). (2) A stale publish: the page shows the ledger as of its build. That is accepted, because publishing is Janice's step. (3) The artifact host's size limit is unknown. If a publish is refused, that becomes a new task. (4) This reverses a T-063 design line ("the recorded usage page never has chat"). That line was a design choice, not a compliance condition.

**Compliance.** No Wulan check is needed. C1 to C8, the chat rules (`chat` owner-only), retention, the inbox procedure and the private status all carry over unchanged on the same artifact. The ledger data was already on a private artifact and passes `forbidden_terms` at build. No new data class is added.

**Decision record draft.**
Decision: The published AI Office page is one generated build (`--ledger <session> --chat`). The committed office.html stays the synthetic dev build.
Context: Merwyn asked for one artifact and one SSOT. The ledger grows every session, and planning PRs must not rebuild pages.
Options: A, commit the combined page (stale on every append, breaks planning-only PRs). B, generate it and keep the synthetic committed page (stable tests and `--check`).
Chosen: B, because the ledger file is the single source and the page is derived from it.
Consequences: Republishing is a manual step for Janice. Size limits apply only to the synthetic page. Combining several session ledgers is a later task. This supersedes T-063's "the recorded usage page never has chat".
Links: T-065, T-063, T-057.

— Fang (architect)

## Build notes
**What changed.** Built to the Design, no deviations.
- `scripts/office_app.py`: `--chat` with `--ledger` is accepted (exit-2 refusal and the `BuildError` removed; docstring and help text updated). No page template change.
- `offices/ai-office/budgets.yaml`: claude-code `tokens: 8000000`, `set_by: Merwyn`, `set_on: "2026-11-26"`, note "Raised from 5,000,000 at 5,201,744 used (17:20 WIB), before T-065". Shares and thresholds unchanged.
- `tests/test_budgets.py`: the shipped-file test checks validity, a positive int, `set_by`, a valid `set_on`, agent tokens adding to the provider total. The 76% test uses its own 5,000,000. The page test compares to `load_budgets`.
- `tests/test_office_app.py`: the exit-2 test is replaced by `test_chat_with_ledger_builds_the_one_published_page` (exit 0; combined data minus `chat` equals the ledger-only data; `chat` equals the committed page's; `--check` 0 then 1 after touching; `rec` and `budgets rec` node checks on the combined page).
- Docs: `engine/app/README.md`, `engine/schema/usage.md`, pmo-playbook section 9 "Publish".

**Publish command (the only one).** `python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat` writes `engine/app/usage-session_01MDGJq3GfaeozLojJo8W5Td.html` (gitignored). Printed size today: 217 KB, 8 agents, 67 events. `office.html` (synthetic, committed) is unchanged and `--check` passes.

**How to verify.** `python -m unittest discover -s tests` (386 tests, exit 0); `python -m engine.runtime validate ai-office` (OK); `python scripts/office_app.py ai-office --chat --check` (up to date); `python scripts/board.py ai-office` (no problems, board.md discarded). Manual check below.

**Headless Chrome check** (copy of the combined page under /tmp/t065 with a stub `claude` injected, never committed, no screenshots kept), 1280x800 and 390x844, both the same:
- Usage panel: "recorded" pill, Summary and Detail tabs present. At the end of the replay it reads "Claude Code subagents 5.2M / 8M, 65% of your budget" with the new budget note. This equals the ledger total (5,201,744 tokens, 67 runs).
- The Chat button is shown; clicking it opens the panel ("Office chat", "Office not running", the empty-thread hints).
- `claude.use` was called for `db` and `user` only. Console errors, page errors and unhandled rejections: 0.
- Not checked: a real db on the published artifact (Janice's step after publish); colours were not compared pixel by pixel, the page code is unchanged and the recorded budget views pass the node checks.

— Sebastian (engineer)

## Review log
**Verdict: PASS** (26 Nov 2026). Every pre-merge Done-when check passes. Evidence below. I wrote it before reading the Build notes. The post-merge republish and the delete are Janice's.

Commands run on `t-065-one-office-artifact` (head 594ca3f):
```
$ python -m unittest discover -s tests          -> Ran 386 tests ... OK, exit 0
$ python -m engine.runtime validate ai-office   -> ai-office: OK - 8 agents, 5 stages, 65 tasks, 18 skills (exit 0)
$ python scripts/office_app.py ai-office --chat --check
  engine/app/office.html: up to date (211 KB, 84 events) (exit 0)
$ python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat
  engine/app/usage-session_01MDGJq3GfaeozLojJo8W5Td.html: written, 217 KB, 8 agents, 67 events (exit 0; 222,927 B)
$ ... --chat --ledger L --fixture F             -> "--fixture and --ledger cannot be used together", exit 2 (unchanged)
```
1. **Budget: pass.** `budgets.yaml` claude-code has `tokens: 8000000`, `set_by: Merwyn`, `set_on: "2026-11-26"`, and shares and thresholds are unchanged. To test the tests, I set the file to 7,000,000 for a while (then reverted it, and the tree is clean). `tests.test_budgets` (23) and the full suite (386) both passed at that value. So no test pins the value in the file. `grep` finds 5,000,000 only in each test's own maths: `_split` in `test_budgets.py:58`, the 76% check against the literal `5_000_000` at `:187`, and the node `R(...)` and `p(...)` cases in `test_office_app.py`. The shipped-file test still checks no problems, a positive int, `set_by`, a valid `set_on`, and that the agent tokens add up to the total.
2. **One command, ledger plus chat: pass.** I built the command above and a `--ledger`-only page into /tmp, then read `office-data` from both. The combined page has the ledger-only keys plus `chat`. Combined minus `chat` == ledger-only: True. `chat` equals the committed `office.html` chat: True. Values: `log.usage_source` recorded, session 5,201,744 tokens over 67 runs, budget 8,000,000, `budgets.synthetic` false.
3. **Headless page with a stub `claude`: pass.** Playwright drove /usr/bin/google-chrome on a /tmp copy plus `three.min.js`. The script was under /tmp, and no screenshots were kept. At 1280x800 and at 390x844 (with `?usage=open`), the "recorded" label, Summary and Detail all show, with "5.2M / 8M" and "65% of your budget". The Chat button is visible, and clicking it opens "Office chat / Office not running" with the hints. `claude.use` was called with `["db","user"]` only. Console errors and page errors: 0 at both sizes.
4. **Same numbers and colours as the ledger-only page: pass.** I compared every `.bar i` on both pages: key, level class, width and computed colour. They match exactly. The provider row is `lv-ok` 65 rgb(83,186,126). In Detail, compliance is `lv-alert` 96 rgb(230,57,70), and designer 69, engineer 67, reviewer 67, architect 59, pm 51 and curator 43 are all `lv-ok` green. Neither page shows the word "synthetic", and the data has no fixture path.
5. **Chat unchanged from T-063: pass.** `office.template.html`, `engine/schema/chat.md` and `engine/runtime/` are not in the diff. All T-063 chat tests pass in the 386.
6. **`--chat` with `--ledger` accepted: pass.** The exit-2 test is replaced by `test_chat_with_ledger_builds_the_one_published_page`. It checks exit 0, the data equalities, `--check` 0 and then 1 after a touch, and the `rec` and `budgets rec` node checks (node is present, so these ran). `test_default_build_has_no_chat_key` and the ledger-only tests are kept. The committed page and `--check` agree (above).
7. **Docs: pass.** `engine/app/README.md` (Files, Regenerate, artifact and chat paragraphs) and pmo-playbook section 9 "Publish" both name the single command and "AI Office" (5f1bb811-...). Both say the token usage artifact is retired, to be deleted only on Merwyn's confirmation, and that `office.html` is the synthetic dev build and is not published. `engine/schema/usage.md` mentions `--chat`.
8. **C1 to C8 (T-063) not weakened: pass.** There is no change to the page code, the chat schema or the runtime. The playbook diff only adds the Publish paragraph: steps 1 to 11, including C4, C5, C6 and C7, are untouched. The README still says the artifact stays private and that sharing it needs a new compliance check. The ledger still goes through `forbidden_terms` at build (`office_app.py:69-72`). The same artifact and its owner-only rules are kept.

Notes (not blocking):
- With the stub, the combined page called `claude.use('db')` and `('user')` at load, before Chat was opened. The ledger-only page called it 0 times. This is T-063 behaviour (the db is read for the badge and needs-you) and is within C7, but Janice should know the published page reads the db on every load.
- In the 390 px sheet I did not switch the Detail tab, so the per-agent bars were compared at 1280 only.
- Style: `import datetime` sits inside `test_valid_and_dated` and could move to the top of the file.
- The header comment in `budgets.yaml` still says "Starting values by Janice (pmo)". That is still true of the agent shares, so it is fine.
- Risk (1) in the Design still applies: a second session ledger needs a new task.

The Build notes, read after my check, agree with these findings. No deviations.

— Cahyani (reviewer)

## Decision

## Open questions
- Which ledger file does the one published page use: the current session file only, or all sessions as new ones start? Merwyn.
- ~~Should the committed `office.html` (synthetic, used for tests and golden) stay as a separate dev build, or does the combined page replace it? It depends on whether the ledger file counts as repo data for `--check`. Fang.~~ Answered (Fang, Design): it stays as the synthetic dev build and is not published. The combined page is generated (gitignored) and published, so ledger appends never make a committed file stale.
- Chat runs have no task and are not in the event log (T-063 build notes). Should the usage panel show them, given the page is now the usage ledger? Merwyn, then Fang. (PMO call in the approval note: as today. Fang: no page change. Chat runs stay in the ledger totals only.)
- ~~The 216 KB size limit may not fit the combined page. If not, who decides the new limit? Fang (T-063 precedent).~~ Answered (Fang, Design): 216 KB stays on the committed synthetic page. The published page has no fixed limit, because it grows with ledger data (about 245 B per run).

— Emmy (pm)
