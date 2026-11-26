---
name: pr-workflow
description: Branch, commit, open, check and merge pull requests in this repo from a Claude session. Use whenever you commit, push, open a PR or merge.
---
# PR workflow

```bash
# 1. Branch from fresh main
git checkout main && git pull --depth=5 origin main
git checkout -b t-xxx-short-name

# 2. Commit (author + trailer lines are required)
# Pre-commit check, must print nothing (see "board.md (generated)" below):
git diff --cached --name-only -- 'offices/*/board.md'
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "T-xxx: <what>

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: <your session URL>"

# 3. Push (a "push negotiation failed" warning is harmless)
git -c push.negotiate=true push -u origin t-xxx-short-name

# 4. Open the PR — REST only; `gh pr create` fails (GraphQL is blocked)
gh api repos/merwyns-maj/ai-office/pulls -f title="T-xxx: <title>" \
  -f head=t-xxx-short-name -f base=main -F body=@/tmp/pr-body.md --jq .number
# body ends with:
#   🤖 Generated with [Claude Code](https://claude.com/claude-code)
#   (blank line)
#   <your session URL>

# 5. Merge (PMO only, after Reviewer PASS; planning-only sprint PRs excepted, see below). Wait until GitHub has computed mergeability:
# Check the PR shows YOUR latest commit too: mergeable=true can be stale from before your last push.
head=$(git rev-parse HEAD)
for i in $(seq 1 10); do
  r=$(gh api repos/merwyns-maj/ai-office/pulls/<n> --jq '[.head.sha,.mergeable]|@tsv')
  [ "$r" = "$head	true" ] && break; sleep 5; done
[ "$r" = "$head	true" ] || { echo "PR <n> not ready ($r): stop and check"; exit 1; }
gh api -X PUT repos/merwyns-maj/ai-office/pulls/<n>/merge -f merge_method=squash --jq .message
git checkout main && git pull --depth=5 origin main
```

Rules
- One task, one branch, one PR. Put `pr: <n>` in the task frontmatter.
- `mergeable: null` means "still computing", not "conflict": wait and retry. `false` means a conflict: replay the branch onto fresh main and push again (see Replay, not rebase).
- Never force-push `main`; task branches only as in Replay, not rebase. Never push to `main`.
- If a push is rejected as too large: replay the branch onto `origin/main` (see Replay, not rebase); its first step fetches with `--depth=50`.

## Replay, not rebase (shallow clones)
Our clones are shallow (`--depth=5`). There `git rebase` can report add/add conflicts on files only your branch added, because the shared base commit is missing. Do not resolve those. Replay instead:

```bash
b=t-xxx-short-name
git fetch --depth=50 origin main
git log --oneline --reverse origin/main..$b   # must list only this task's commits; if not: git fetch --deepen=50 origin main, check again
commits=$(git rev-list --reverse origin/main..$b)
old=$(git ls-remote origin refs/heads/$b | cut -f1)
git branch -f $b-backup $b
git checkout -B $b origin/main
git cherry-pick $commits                      # a conflict here is real: resolve it, then git cherry-pick --continue
git -c push.negotiate=true push --force-with-lease=$b:$old origin $b
git branch -D $b-backup                       # once the PR shows the new head
```
- Same branch name, so the open PR and `pr: <n>` stay. `--force-with-lease=$b:$old` refuses the push if someone else pushed to the branch since `$old`.
- Force-push only a `t-xxx` task branch, only this way. Never `main`, never a `sprint-NN-*` branch with someone else's commits.
- If GitHub rejects the force push (branch protection), push as `$b-r2`, open a new PR, close the old one with a link to the new one, and update `pr:`.
- If you resolved a real conflict after a Reviewer PASS, say so in the PR; the Reviewer re-checks the changed files before the PMO merges.

## board.md (generated)
- Task branches never commit `offices/<office>/board.md`. Run `board.py` to see Problems, then discard the file: `git checkout -- offices/<office>/board.md`.
- The PMO commits board.md only in sprint PRs: branch `sprint-NN-plan` at sprint plan and `sprint-NN-close` at sprint close (one PR may do both, as PR #12 did). Regenerate on fresh main, commit it with the sprint file, open a PR. Planning-only sprint PRs need no Reviewer; the PMO merges them. Planning-only is defined once, in the comment on `merge.requires_planning_only` in workflow.yaml: sprints/, board.md, raid.md, usage/ (appended ledger lines; existing lines never edited or deleted; a new session file starts with its header line), new task files at todo or spec, and on existing tasks only status, owner, depends_on (never to done) plus dated PMO decision notes. Any other change needs a Reviewer PASS. Check before merge: `board.py` on the branch leaves `git diff --exit-code` clean, and the full test suite passes on the branch (tests read the ledger and sprint files, so a planning-only change can turn main red; T-055, T-061).
- Between sprint PRs, board.md on main can lag. For the live board, run board.py locally and do not commit it.
