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
Claude-Session: https://claude.ai/code/session_01MDGJq3GfaeozLojJo8W5Td"

# 3. Push (a "push negotiation failed" warning is harmless)
git -c push.negotiate=true push -u origin t-xxx-short-name

# 4. Open the PR — REST only; `gh pr create` fails (GraphQL is blocked)
gh api repos/merwyns-maj/ai-office/pulls -f title="T-xxx: <title>" \
  -f head=t-xxx-short-name -f base=main -F body=@/tmp/pr-body.md --jq .number
# body ends with:
#   🤖 Generated with [Claude Code](https://claude.com/claude-code)
#   (blank line)
#   https://claude.ai/code/session_01MDGJq3GfaeozLojJo8W5Td

# 5. Merge (PMO only, after Reviewer PASS). Wait until GitHub has computed mergeability:
for i in 1 2 3 4 5; do
  m=$(gh api repos/merwyns-maj/ai-office/pulls/<n> --jq .mergeable); [ "$m" = true ] && break; sleep 5; done
gh api -X PUT repos/merwyns-maj/ai-office/pulls/<n>/merge -f merge_method=squash --jq .message
git checkout main && git pull --depth=5 origin main
```

Rules
- One task, one branch, one PR. Put `pr: <n>` in the task frontmatter.
- `mergeable: null` means "still computing", not "conflict": wait and retry. `false` means a conflict: rebase on main and push again.
- Never force-push `main`. Never push to `main`.
- If a push is rejected as too large: `git fetch --depth=50 origin main` and rebase onto `origin/main`.
