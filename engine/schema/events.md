# Office event log (v0, T-048)

A recorded log of what an office did, replayed by the 3D page (`engine/app/`). v0 is **replay only**: the live runtime (T-024, T-027) will emit the same events later. Parser: `engine/runtime/events.py`. Check a file with:

```bash
python -m engine.runtime events ai-office engine/app/fixtures/sprint-03.jsonl   # 0 no errors, 1 errors, 2 usage or missing file
```

## File

UTF-8 JSONL: one JSON object per line. Blank lines are ignored. A line is at most 2000 characters. A duplicate key in an object is an error.

Line 1 is the header:

```json
{"log":"office-events","v":0,"office":"ai-office","clock":"synthetic","title":"Sprint 3 replay (T-043, T-044, T-045)"}
```

- `v` must be 0, otherwise the whole file is rejected. So is a missing or malformed header.
- `clock` is `synthetic` or `wall`. **`synthetic`: `t` is authored replay time, not real time.** Only a `wall` field on an event is a real timestamp (a git commit time or a time written in a sprint file).

## Fields on every event

| field | rule |
|---|---|
| `t` | number >= 0, seconds from the start of the log. Must not decrease; equal values mean simultaneous |
| `type` | string, one of the types below |
| `src` | required. Repo-relative path the event is taken from, with an optional `#Section`, e.g. `offices/ai-office/backlog/T-043-guard-ask-mode-for-prod-writes.md#Review log` |
| `wall` | optional ISO 8601 with offset. Only where a real time exists. Values present must not decrease |

Field types: **AGENT** an `org.yaml` agent id; **TASK** `^T-\d{3}$`; **STAGE** a `workflow.yaml` stage id or terminal state; **TEXT** 1 to 120 characters, no newline.

## Event types

| type | fields | reducer effect (the page) |
|---|---|---|
| `step_started` | agent, task | agent holds task and is working |
| `stage_changed` | task, from: STAGE, to: STAGE | task.stage = to |
| `handoff` | task, from_agent, to_agent, to_stage: STAGE | task leaves from_agent's hands, enters to_agent's; task.owner = to_agent |
| `discussion` | task, agents: [AGENT] (2 to 4, no repeats), lines: [{agent, text: TEXT}] (1 to 6, each line's agent is in `agents`) | none (transient: agents meet at the table) |
| `needs_merwyn` | agent, task, reason: TEXT | agent waits on the task (at Merwyn's door) and holds it |
| `merwyn_answered` | agent, task, answer: TEXT | wait cleared. A task still in `todo` is released by the agent (nobody holds an unstarted task); any other task stays with the agent |
| `review_pass` | task, agent, note: TEXT (optional) | task marked pass; clears a reject mark |
| `review_reject` | task, agent, reason: TEXT | task marked reject. **Rule:** the next event for that task is a `handoff` |
| `compliance_result` | task, agent, verdict: `PASS` \| `PASS_WITH_CONDITIONS` \| `BLOCK` | task.compliance = verdict. **Rule:** after a BLOCK, the next event for that task is a `needs_merwyn` |
| `blocked` | agent, task, reason: TEXT | agent is blocked on the task; cleared by a later `step_started`, `handoff` or `merwyn_answered` on it |
| `merged` | task, pr: integer >= 1 | task.stage = done; removed from every agent; filed on the archive shelf (pmo stamps, curator files: one animation) |

## Severity

- A field that is not listed for its type: **warning**.
- An unknown `type`: **warning**. The event is kept and the page says "Unknown event skipped".
- Everything else is an **error** and that line is dropped; the rest is kept: malformed JSON, not an object, duplicate key, unknown agent or stage, missing or mistyped field, decreasing `t` or `wall`, TEXT too long or with a newline, a broken discussion, a broken sequence rule above.
- **Data rule:** any string value that looks like an email, a 16-digit run, a run of 10 or more digits, or that contains an organisation or repository name from `workspaces.yaml` that is not the personal one, is an error. Logs carry task ids, agent ids, stages and short text only, never company data.

## Fixtures

- `engine/app/fixtures/sprint-03.jsonl`: replay of Sprint 3 (T-043, T-044, T-045) from `offices/ai-office/sprints/sprint-03.md` and the task files. Hand-written: git history has five timestamps for that sprint and none inside a stage. Order and wall times: the sprint file, the task files and `git log`. All other times are synthetic.
- `tests/fixtures/events-all-types.jsonl`: SYNTHETIC, all 11 types (including reject, blocked, BLOCK), for tests and review. Not a real replay.
