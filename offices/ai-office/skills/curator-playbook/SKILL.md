---
name: curator-playbook
description: How April keeps the office's memory: decision logs, lessons, and docs that stay current. Use after every merged task, at sprint close, and when proposing edits to skills or profiles.
---
# Curator playbook

Distilled from knowledge-management and decision-log practice (sources at the end). Pairs with `decision-record` and `status-report`.

## 1. Record what future agents will ask
- Log decisions that are significant, hard to reverse, or likely to be questioned. Each entry: what was decided, why, alternatives considered, who decided, links (task, PR).
- Link the decision from the PR or task that implemented it, so the "why" is one click from the "what".

## 2. Just enough, and current
- Document just enough for a shared understanding; keep it concise and findable. More text is not more knowledge.
- Docs have a lifecycle: create, keep current as reality changes, archive before it misleads. Each doc has an owner.
- When code or a decision changes, the doc changes in the same PR or is marked superseded.

## 3. Lessons become edits
- After each task and each sprint, look for what went wrong or was slow (e.g. a merge failing on a stale mergeable flag).
- Turn each lesson into a concrete proposed edit to a skill or agent profile, as its own small task. A lesson that stays a note is lost.
- Keep the skill set lean: merge overlapping skills instead of adding new ones.

## 4. Where things go
- Task decisions → the task's Decision section.
- Durable office knowledge → the brain (via PR to the office's brain repo, once it exists).
- Company knowledge → company brain only, as pointers.

## 5. Monthly chat-to-office review
Finds work Merwyn repeats in chats and proposes it as skills or workflows. Only the main session can search his chats; April writes up.
1. Who and when: at the month's sprint close the PMO asks the main session to search chats outside Projects for the last 30 days, stated as dates.
2. Hand-off: the main session writes `/tmp/t031-findings.md` (outside the repo, never committed) with columns topic (generic), chats, pointer dates, clear done (Yes, No or Mixed), where it belongs. It states the window and scope. No titles, names, figures, IDs or quotes. Company repo names are written "company repo, behind T-002".
3. Bar: 3 or more chats and a clear done. Check each row's dates add up to its count. Topics already turned into skills go under "Already covered" with the task id; the rest under "Below threshold" with the reason.
4. Output: `offices/ai-office/research/T-031-YYYY-MM.md`, in the format of `T-031-2026-11.md` (Proposals, Already covered, Below threshold, numbered pick-list with a recommendation, Data scan). Pointers are dates only.
5. Data scan: the Engineer runs this over the report (and the findings file as an input check); the Reviewer re-runs it. It prints file, line and kind, never the text. Quoted chat text is not caught by a pattern, so the Reviewer reads for it.
```
python -c "import sys,pathlib; sys.path.insert(0,'.'); from engine.runtime.events import DATA_PATTERNS as P, PATTERN_KINDS as K, forbidden_terms as F; t=F('.'); n=0
for f in sys.argv[1:]:
  for i,l in enumerate(pathlib.Path(f).read_text(encoding='utf-8').splitlines(),1):
    for p,k in zip(P,K):
      if p.search(l): print(f'{f}:{i}: {k}'); n+=1
    if any(x in l.lower() for x in t): print(f'{f}:{i}: forbidden term'); n+=1
print('data scan:', 'clean' if not n else f'{n} hits'); sys.exit(1 if n else 0)" offices/ai-office/research/T-031-YYYY-MM.md
```
6. Merwyn picks from the list; his picks and their time go in the task's Decision section. Picks become backlog only through the PMO.

## Anti-patterns
- Session chatter in the brain. Docs nobody owns. Lessons recorded but never applied. Copying instead of linking.

## Sources
- AWS Well-Architected, knowledge management lifecycle — https://docs.aws.amazon.com/wellarchitected/latest/framework/ops07-bp03.md
- O'Reilly, Building Software Teams, "Document just enough" — https://oreilly.com/library/view/building-software-teams/9781491951781/ch11.html
- Thoughtworks, keeping agile docs current — https://www.thoughtworks.com/en-au/insights/blog/four-goals-agile-documentation-part-two
- DEV, decision logs for engineering teams — https://dev.to/william_geo/decision-logs-for-engineering-teams-building-institutional-memory-that-lasts-ff7
