# Office event log (v0 and v1; v0 T-048, v1 T-056)

A recorded log of what an office did, replayed by the 3D page (`engine/app/`). v0 is **replay only** (so is v1 in this slice): the live runtime (T-024, T-027) will emit the same events later. Parser: `engine/runtime/events.py`. Check a file with:

```bash
python -m engine.runtime events ai-office engine/app/fixtures/sprint-03.jsonl   # 0 no errors, 1 errors, 2 usage or missing file
```

## File

UTF-8 JSONL: one JSON object per line. Blank lines are ignored. A line is at most 2000 characters. A duplicate key in an object is an error.

Line 1 is the header:

```json
{"log":"office-events","v":0,"office":"ai-office","clock":"synthetic","title":"Sprint 3 replay (T-043, T-044, T-045)"}
```

- `v` must be 0 or 1, otherwise the whole file is rejected. So is a missing or malformed header. **v0 logs load unchanged** (same checks, same warnings) and `python -m engine.runtime events ai-office <v0 file>` still exits 0 on a clean one.
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

## v1: model and usage (T-056)

A v1 header adds one required field and the file may then carry which model an agent ran on and what it used:

```json
{"log":"office-events","v":1,"office":"ai-office","clock":"synthetic","usage_source":"synthetic","title":"SYNTHETIC model and usage demo (T-056): invented numbers, not a real run"}
```

- `usage_source` is required in v1: `synthetic` (invented numbers; the page writes "synthetic" next to every usage figure) or `recorded` (measured by the runtime; T-026 will write this). A v1 header without it is rejected.
- In a v0 file the fields and type below are not defined: a `usage` line gives today's "unknown type" warning and `provider`/`model` give "field not defined". Nothing in v0 behaviour changes.

Field kinds: **PROVIDER** `^[a-z0-9][a-z0-9-]{0,31}$`; **MODEL** `^[A-Za-z0-9][A-Za-z0-9._:/-]{0,63}$`; **BILLING** `per_token` or `plan`; **TOKENS** integer 0 to 999,999,999 (a bool is rejected; nine digits at most, so a token count never looks like an account number); **USD** number 0 to 999,999 with at most 6 decimal places.

| type | fields | reducer effect (the page) |
|---|---|---|
| `step_started` | as v0, plus `provider: PROVIDER?`, `model: MODEL?` (both or neither, else error) | as v0; the agent's current model is set when both are present |
| `usage` (new) | agent, task, provider, model, billing: BILLING, input: TOKENS, output: TOKENS, cache_read: TOKENS?, cache_write: TOKENS?, cost_usd: USD? | adds the tokens to the agent's bucket (agent, provider, model, billing) and sets the agent's current model. No animation, no ticker line |

- `input` means **uncached** input tokens; `cache_read` are tokens read from a cache, `cache_write` tokens written to it (both default 0). Providers report cached tokens differently (some include them in their input count): the emitter (T-026) normalises, and checks each provider's field names against its API docs.
- `billing: plan` (a subscription, e.g. the Max plan) with `cost_usd` present is an **error**. A plan step shows tokens and the word "plan", never a dollar amount.
- `cost_usd` is the runtime-reported spend, for budgets (T-026). The page does not show it: on-screen cost is always `tokens x config price` (see `providers.yaml` in `engine/schema/office.md`), labelled as an estimate with the config's source date, so there is one cost source on screen. A per-token provider with no price in the config shows tokens and "price not set".
- **Warning, not error** (given a catalogue, which `python -m engine.runtime events` and the page generator pass): a provider id not in the catalogue, a model id not in that provider's `models`, an event `billing` that differs from the catalogue's (the event wins). One warning per distinct message, not per line. The event is kept and the page shows the raw id with a neutral colour.
- A model switch (an agent's provider or model differs from its previous one) adds one ticker line; a `usage` event adds none.
- The data rule above runs first and covers the new strings. The new numeric fields are bounded by type. Keys, and numbers in fields a type does not define, are not scanned: that gap belongs to T-027.
- The page shows the event's model; the profile `model:` (opus or sonnet) appears only as "planned: x" when the event's model family differs.

### usage, second shape: total (T-057)

A `usage` event with a `total` field is a recorded agent run from a ledger (`engine/schema/usage.md`): `agent`, `task`, `total: TOKENS|null` (null = not reported, never 0), and optional `tasks: [TASK]` (1-8 distinct), `tool_uses: TOKENS|null`, `run: INT`, `sprint: INT`, `step` (lowercase slug), `note` (1-200 characters). It must not carry `provider`, `model`, `billing`, `input`, `output`, `cache_read`, `cache_write` or `cost_usd` (any of them with `total` is an error): the harness reports totals only. Without `total` the split shape above is checked unchanged. A v1 header written for a ledger also carries `covers`, `ledger` and optionally `provider` (headers are not field-checked). The page shows these per agent with "split not reported" and no "synthetic" label.

## Fixtures

- `engine/app/fixtures/sprint-03.jsonl`: replay of Sprint 3 (T-043, T-044, T-045) from `offices/ai-office/sprints/sprint-03.md` and the task files. Hand-written: git history has five timestamps for that sprint and none inside a stage. Order and wall times: the sprint file, the task files and `git log`. All other times are synthetic.
- `engine/app/fixtures/models-synthetic.jsonl`: **SYNTHETIC v1** log (T-056), the page default: four tasks (T-901 to T-904) through the workflow, 8 agents with a model inside the first 40 s, four providers (claude-sdk, anthropic-api, openai, deepseek), the engineer switching providers twice, 24 `usage` events with invented numbers and no `cost_usd`. Not a real run.
- `tests/fixtures/events-v1-edge.jsonl`: SYNTHETIC v1 edge cases (3 warnings, 8 errors) for the parser tests.
- `tests/fixtures/events-all-types.jsonl`: SYNTHETIC, all 11 types (including reject, blocked, BLOCK), for tests and review. Not a real replay.
