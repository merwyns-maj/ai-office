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

# 5. Merge (PMO only, after Reviewer PASS). Wait until GitHub has computed mergeability:
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
- `mergeable: null` means "still computing", not "conflict": wait and retry. `false` means a conflict: rebase on main and push again.
- Never force-push `main`. Never push to `main`.
- If a push is rejected as too large: `git fetch --depth=50 origin main` and rebase onto `origin/main`.
