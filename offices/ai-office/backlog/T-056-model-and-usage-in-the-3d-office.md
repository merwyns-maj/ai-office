---
id: T-056
title: "Show which model each agent uses, and usage, in the 3D office (multi-provider)"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-048]
pr: 37
---

> Merwyn, 26 Nov 2026 10:35: "in the 3d AI office, can we also track which model is currently being used, the usage as well. Let's say if i have multiple LLM (Claude SDK, Anthropic API, ChatGPT, Deepseek, etc.)". Prototype slice on the recorded log; real numbers arrive with the runtime (T-024) and cost logging (T-026).

## Done when
- [ ] Event log v1 (documented, v0 logs still load) carries, per agent step, a provider (e.g. claude-sdk, anthropic-api, openai, deepseek), a model id, and usage (input, output and cached tokens; cost where the provider prices per token; "plan" where it runs on a subscription)
- [ ] The 3D office shows at a glance which model each agent is on (avatar badge or desk label, colour plus text) and a usage panel: per agent, per provider and total, for the replay so far
- [ ] Providers and prices live in office config (not hard-coded), with a dated source note; unknown provider or model still renders
- [ ] A fixture exercises at least three providers; its usage numbers are marked synthetic in the log header and on screen
- [ ] Tests for the parser, totals and the pricing config; T-026 updated to emit this format

## Spec

**Problem.** Merwyn runs agents on several providers (Claude Agent SDK on his Max plan, Anthropic API, OpenAI/ChatGPT, DeepSeek) but the 3D office shows neither which model an agent is on nor what it has used. The runtime (T-024) and cost logging (T-026) are not built, so this slice works on a recorded log with synthetic numbers.

**In scope**
- Event log v1 (documented; v0 logs still load) carrying per agent step: provider, model id, usage (input, output, cached tokens), and a cost only where the provider bills per token.
- The 3D office shows each agent's model at a glance, and a usage panel per agent, per provider and total, for the replay so far. Dinda consults (UI); Fang owns the log format.
- Provider and model catalogue plus per-token prices in office config, each with a dated source note. An unknown provider or model still renders.
- A fixture with at least three providers, marked synthetic.
- Where model choice comes from: today the agent profile `model:` line (opus or sonnet, as Janice states; Fang to confirm in the profiles). A step's actual model is what its event says; the page shows the event's value, and shows the profile value only as "planned" if they differ.
- T-026 updated to emit this format.

**Out of scope**
- Calling any provider or reading any live usage; live data (T-024, T-026).
- Budgets, caps, alerts (T-026).
- Choosing models for agents or changing any profile.
- Real prices fetched at run time.

**Done when**
- [ ] `engine/schema/events.md` documents v1 fields (provider, model, input, output and cached tokens, cost, billing) and says v0 logs load unchanged; `python -m engine.runtime events ai-office <v0 fixture>` still exits 0 with no errors.
- [ ] Given a step on a subscription plan (Max), the log and page show tokens and the word "plan", and no dollar amount; a test fails if a plan step carries a cost.
- [ ] Given a per-token provider, cost is computed from the config price, and the page shows the config's source date next to it and never says "live" or "current price".
- [ ] The fixture has at least 3 providers, its header says usage is synthetic, and the page shows "synthetic" next to every usage figure (screenshot, Reviewer).
- [ ] Each agent's model shows as colour plus text (not colour alone); a screenshot at a mid-replay time shows models for all 8 agents.
- [ ] Usage panel totals per agent, per provider and overall equal the sum of the fixture's events up to the replay time (unit test with exact numbers; scrubbing back lowers them).
- [ ] An event with an unknown provider or model id renders with its raw id and a neutral colour, and the parser gives a warning, not an error (test).
- [ ] Prices and providers are read from an office config file; a grep of `office.template.html` and `scripts/office_app.py` finds no price number.
- [ ] A step whose event model differs from the profile `model:` shows the event's model (test).
- [ ] `python -m unittest` passes with new parser, totals and pricing-config tests; `python scripts/office_app.py ai-office --check` exits 0; `office.html` still passes the T-048 data scan and size limit.
- [ ] T-026's file lists this format under its Done when or Spec note.

**Open questions**
- Cached-token pricing differs by provider (read vs write): is one "cached" count enough for this slice? Fang; not blocking.
- Where do the config and its price source dates live, `offices/ai-office/` or `engine/`? Fang; not blocking.
- Max plan usage has limits but no per-token bill: show tokens only, or also a share of plan limit? Merwyn; not blocking (default: tokens only).
- Is the `model:` value in the agent profiles exactly opus/sonnet today? Fang to confirm (I did not open the profiles).
- Current price figures and their sources are needed for the config: Fang or Sebastian to fill from provider pages with the date; I have not verified any price.

— Emmy (pm)

## Design

**Facts checked (primary sources, 26 Nov 2026).** Profile models are in `base/agents/<id>.md` frontmatter line 5: architect and reviewer `opus`; pm, pmo, engineer, compliance, curator, designer `sonnet`. Office agent files only say `extends: base/<id>`; `scripts/build_agents.py:merged()` already resolves that; `office.yaml defaults.model: sonnet`. `events.py` accepts only `v == 0` (line 192) and its data rule scans string values only (`_strings`, line 85): keys and numbers are not scanned (the T-027 gap). The page scan test (`tests/test_office_app.py::test_page_passes_the_data_scan`) runs `\d{10,}` over the whole HTML, so a long float in the data blob would fail it. `miniyaml` rejects block maps inside list items, so the config is keyed by id. In office-core `evDur` uses `DUR[ev.type] || 0.4`, so a zero duration needs `in`, not `||`. `office.html` is 104,769 bytes today (limit 200 KB).

### Approach
| file | change |
|---|---|
| `engine/schema/events.md` | v1 section: header `usage_source`, optional `provider`/`model` on `step_started`, new `usage` type, numeric bounds, "v0 loads unchanged" |
| `engine/runtime/events.py` | accept `v` 0 or 1; v1-only fields and type; kinds PROVIDER, MODEL, BILLING, TOKENS, USD; optional catalogue for unknown-id warnings |
| `engine/runtime/providers.py` (new, stdlib) | `load_providers(office_root)` reads and validates the config |
| `engine/runtime/__main__.py` | `events` passes the catalogue; help text "v0 or v1" |
| `offices/ai-office/providers.yaml` (new) | provider and model catalogue, colours, billing, prices "not set" with source and date fields |
| `scripts/office_app.py` | inject `providers`, `agents[].planned_model`, `warnings`; default fixture becomes the v1 synthetic log |
| `engine/app/office.template.html` | office-core: reducer and pure usage functions; office-view: tag line, usage panel, phone sheet (Dinda's design) |
| `engine/app/fixtures/models-synthetic.jsonl` (new) | v1 synthetic fixture, the new default page |
| `tests/fixtures/events-v1-edge.jsonl`, `tests/fixtures/providers-test.yaml` (new) | edge cases; made-up test prices |
| `tests/test_events.py`, `tests/test_office_app.py`, `tests/test_providers.py` (new) | see Tests |
| `offices/ai-office/backlog/T-026-*.md` | one Spec note: emit `usage` events in this format |

No new service, no new dependency. `theme.yaml` is not changed.

### 1. Event log v1
Header: `{"log":"office-events","v":1,"office":"ai-office","clock":"synthetic","usage_source":"synthetic","title":"..."}`. `usage_source` is required in v1, `synthetic` or `recorded`; the page hides the word "synthetic" only when it is `recorded`. A v0 header is checked exactly as today, and in a v0 file the v1 fields keep producing today's warnings ("field not defined", "unknown type kept"). Nothing in v0 behaviour changes.

New kinds:
| kind | rule |
|---|---|
| PROVIDER | `^[a-z0-9][a-z0-9-]{0,31}$` |
| MODEL | `^[A-Za-z0-9][A-Za-z0-9._:/-]{0,63}$` |
| BILLING | `per_token` or `plan` |
| TOKENS | integer, 0 to 999,999,999 (bool rejected). Nine digits at most, so a token count can never carry a 10+ digit run |
| USD | number, 0 to 999,999, at most 6 decimal places |

v1 changes by type:
| type | fields | reducer effect |
|---|---|---|
| `step_started` | + `provider: PROVIDER?`, `model: MODEL?` (both or neither, else error) | as v0; the agent's current model is set when both are present |
| `usage` (new) | agent, task, provider, model, billing: BILLING, input: TOKENS, output: TOKENS, cache_read: TOKENS?, cache_write: TOKENS?, cost_usd: USD? | adds tokens to the agent's bucket; sets the agent's current model. No animation, no ticker line |

Rules (errors unless marked):
- `billing: plan` with `cost_usd` present is an error (the spec's "a plan step carries a cost" test).
- `input` means uncached input tokens. `cache_read` is tokens read from a cache, `cache_write` tokens written to it; both default 0. Providers report these differently (some include cached tokens in their input count); the emitter (T-026) normalises. I have not checked each provider's field names, so T-026 verifies the mapping against each provider's API docs.
- `cost_usd` is the runtime-reported spend (for T-026 budgets). The page does not show it in this slice: on-screen cost is always the config estimate, so there is one cost source on screen.
- Warning, not error: a provider id not in the catalogue, a model id not in that provider's `models`, an event `billing` that differs from the catalogue's (the event wins). One warning per distinct id, not per line. With no catalogue (no `providers.yaml`) no catalogue warnings are given.
- The T-048 data rule still runs first and covers the new strings (provider, model, usage_source). The new numeric fields are bounded by type, which closes the T-027 number gap **for these fields only**. Keys, and numbers in undefined fields, stay unscanned and stay with T-027.

Signature: `parse_log(text, *, agents, stages, forbidden=(), providers=None)`; `SCHEMA_VERSIONS = (0, 1)`; header error text becomes `v=0|1`.

### 2. Provider config: `offices/ai-office/providers.yaml`
In the office folder: prices and plan choices are this office's, and another office may run on other providers. The engine only owns the format (documented in `engine/schema/office.md`). Colours live here, not in `theme.yaml`, so one file says everything about a provider.
```yaml
# Provider catalogue for the 3D office (T-056). Prices are USD per million tokens.
# Prices stay null ("not set") until someone copies them from the provider's pricing page
# and fills prices.source and prices.checked. Never estimate a price.
providers:
  claude-sdk:
    label: Claude Agent SDK (Max plan)
    code: SDK
    colour: "#c084fc"
    billing: plan                      # no prices allowed on a plan provider
    models:
      claude-opus-4-5:   { short: opus,   family: opus }
      claude-sonnet-4-5: { short: sonnet, family: sonnet }
  anthropic-api:
    label: Anthropic API
    code: API
    colour: "#5b8def"
    billing: per_token
    prices: { source: null, checked: null }      # checked: YYYY-MM-DD
    models:
      claude-opus-4-5:   { short: opus,   family: opus,   input: null, output: null, cache_read: null, cache_write: null }
      claude-sonnet-4-5: { short: sonnet, family: sonnet, input: null, output: null, cache_read: null, cache_write: null }
  openai:   { ...same shape, code: OAI, colour: "#f472b6", models: gpt-5 (short gpt-5) }
  deepseek: { ...same shape, code: DSK, colour: "#3fd0e0", models: deepseek-chat (short v3) }
```
Model ids are the fixture's ids. Which ids the office really runs is unknown until T-024/T-026 emit them (Open question). `family` is the profile alias (`opus`, `sonnet`) used for the "planned" comparison.

`load_providers(office_root) -> (dict, list[str] problems)`. No file returns `({}, [])`. office_app raises `BuildError` on a problem (`--check` exits 1):
- `billing` not `plan` or `per_token`; `code` not `^[A-Z0-9]{2,4}$`; `colour` not `#rrggbb`; `short` missing or over 12 characters.
- A plan provider with `prices` or any model price key.
- A price that is not null or a number from 0 to 10,000 with at most 4 decimals (keeps the blob free of long digit runs).
- Any price set while `prices.source` or `prices.checked` (ISO date) is null: no undated price.

### 3. office_app injection
`build_data` adds:
- `data["providers"]` = the validated catalogue, as loaded (keys sorted by `json.dumps`, so the output stays deterministic).
- `data["agents"][i]["planned_model"]` = office agent `model`, else the base profile's `model` via `build_agents.merged()` (reused, not reimplemented), else `office.yaml defaults.model`, else null.
- `data["warnings"]` = `[{line, message}]` for parser warnings (messages name ids that already passed the data rule, never a value that failed it).
- `data["v"]` = 1 (page data format; the log's own version stays in `data["log"]["v"]`).
- `DEFAULT_FIXTURE` = `engine/app/fixtures/models-synthetic.jsonl`. `sprint-03.jsonl` stays unchanged as the v0 compatibility log; `python scripts/office_app.py ai-office --fixture engine/app/fixtures/sprint-03.jsonl --out <path>` still builds the Sprint 3 page.

### 4. office-core (pure, node-testable)
- `DUR.usage = 0`, and `evDur` uses `ev.type in DUR` so a zero duration is not replaced by 0.4.
- `initState`: each agent gets `model: null, switchedAt: null`; `s.usage = {}`.
- `apply`: on `step_started` with provider and model, and on `usage`: if `{provider, model}` differs from the agent's current model and the current model is not null, set `switchedAt = at` and `prevModel`; then set `model`. On `usage`, add to `s.usage[agent + '|' + provider + '|' + model + '|' + billing]` = `{agent, provider, model, billing, input, output, cache_read, cache_write, n}`. `usage` is a known type (not pushed to `s.unknown`).
- `eventCost(bucket, providers) -> {state, micro}`, where state is `plan` | `usd` | `unset` | `none`. `plan` when billing is plan. `none` when the provider or model is unknown. `unset` when any token class with a nonzero count has a null price. Otherwise `usd`, with `micro = Σ Math.round(tokens × usd_per_mtok)` (micro-USD, integers, so sums are exact).
- `usageTotals(s, providers) -> {total, providers: {id: Row}, agents: {id: Row}}`, with Row = `{input, output, cache_read, cache_write, micro, plan, unset, none, dates: [checked...]}`.
- `costText(row) -> string`: `"$1.08 est."`, `"plan"`, `"price not set"`, `"--"`, or combined for mixed rows: `"$1.08 est. + plan runs + 2 unpriced"`. This is the only place a `$` is built, and only from `micro`.
- `modelLabel(providers, provider, model) -> {code, short, colour, known, full}`. Unknown provider: `code` = first 3 letters of the id uppercased, `colour` null (the view uses `palette.wall` and a dashed border). Unknown model: `short` = the raw id cut at 12 characters with an ellipsis.
- `plannedDiffers(planned, providers, provider, model)`: true when planned is set and the model's `family` is missing or not equal to planned.
- Scrubbing back: `stateAt` already rebuilds from `initState`, so totals drop with no extra code.

### 5. Fixture `engine/app/fixtures/models-synthetic.jsonl`
SYNTHETIC v1 log: title says "SYNTHETIC model and usage demo (T-056): invented numbers, not a real run", `usage_source: synthetic`, `clock: synthetic`, `src` = the fixture path, tasks `T-901` to `T-904` through spec, design, build, review and merged, so the workflow animation still has a story. It contains:
- a `step_started` with provider and model for all 8 agents within the first 40 s;
- `claude-sdk` plan runs on each profile's model;
- the engineer switching from `claude-sdk`/sonnet to `openai`/gpt-5 and later to `deepseek`/deepseek-chat (model switch plus a "planned: sonnet" mismatch);
- the reviewer on `anthropic-api`/opus for one step (a different provider with the same family, so no mismatch);
- per-token runs that are unpriced, because the shipped prices are null;
- no unknown ids and no warnings, so `build_data` problems stay `[]`.

It must have 4 providers, at least 12 `usage` events and no `cost_usd`.

`tests/fixtures/events-v1-edge.jsonl` (SYNTHETIC) covers: an unknown provider, an unknown model of a known provider, a billing mismatch (these three are warnings); plan with `cost_usd`, provider without model, tokens 1,000,000,000, `cost_usd` with 7 decimals, `usage_source` missing (errors, the last one rejecting the file, so it is a separate inline case).

### 6. Tests
- **Parser** (`test_events.py`): `sprint-03.jsonl` and `events-all-types.jsonl` give the same events and problems as before (v0 unchanged); the CLI exits 0 on both and on the v1 fixture; v0 file with a `usage` line still warns "unknown type"; each edge case gives the stated level; a data-rule hit in `model` is reported by field name, never value.
- **Config** (`test_providers.py`): the repo file loads with no problems; each validation rule rejects; the repo file has no price set (until someone fills one with source and date); no provider colour has a hue in 0-45 or 345-360 (amber and red) or within 15 degrees of `palette.accent` (Dinda's reserved colours).
- **Totals** (node, `CoreUnderNode`): at t = 0, mid-replay, end and back to mid, `usageTotals` equals a Python sum of the fixture's `usage` events due by that time (passed in as JSON); one hand-written exact case with `providers-test.yaml` (made-up prices, labelled TEST) checks `micro` and `costText`; a plan bucket never yields `$` or `micro > 0`; unknown gives `--` and `none`; switch sets `switchedAt`; `plannedDiffers` is true for the engineer on gpt-5 and false for the reviewer on API opus.
- **No price or provider literals**: `office.template.html` and `scripts/office_app.py` contain none of the test config's price numbers, no `\$\s*\d`, no provider id from `providers.yaml`, and no `current price` or `live (price|cost|usage)` text.
- **Page**: the committed page passes the data scan and the 200 KB limit; `--check` exits 0; the Sprint 3 core checks keep running, on Sprint 3 data passed as JSON (same mechanism as the all-types test), because the default page is now the synthetic log. Update the event-count literal in `test_bad_log_line_exits_1_unless_allowed`.

### Risks
| risk | handling |
|---|---|
| A long float in the blob trips the page scan | integer tokens up to 9 digits; prices with at most 4 decimals; cost computed in the browser in micro-USD, never written to the blob |
| Someone reads a synthetic figure as real | `usage_source` is required; "synthetic" is shown by every figure (Dinda); default fixture title says SYNTHETIC |
| An invented price | the shipped prices are null; a price without a dated source fails the build |
| The default page loses the Sprint 3 story | sprint-03 still builds with `--fixture`; its core tests keep running |
| Provider field semantics differ (cached inside input) | v1 defines `input` as uncached; T-026 normalises and verifies per provider |
| Usage events push out the ticker | usage events have no ticker line; only model switches add one |

### Compliance flag
Not flagged. No production system, no money movement (cost is an estimate of AI spend shown on a local page; nothing pays or moves funds), no personal data (ids, tokens, prices only; the T-048 data rule still applies). No provider is called and no paid resource is created. Filling real prices later is a wording and data change in `providers.yaml`.

### UX design: accepted, with changes
Accepted as written, except:
1. **Ticker**: usage events add no ticker line; only model switches do (`Fang  sonnet -> gpt-5 (SDK -> OAI)`). So the "(synthetic)" ticker suffix applies only to `#tone` when it mentions usage.
2. **Warnings `!` count** reads `data.warnings` (new). In the shipped fixture it is always 0, and it is tested with the edge fixture.
3. **Cost cell** uses `costText` exactly. The source date is shown per provider row (`prices checked YYYY-MM-DD` in dim text) plus the footnote. With today's config every per-token row reads "price not set", so no `$` appears on the committed page.

Answers to Dinda's questions for me:
- `short` label: a config field per model (`short`, at most 12 characters). If a model is missing from the config, the label is derived from the raw id, cut at 12 characters with an ellipsis.
- Colours: only in `providers.yaml`, not `theme.yaml`. Unknown providers use the existing `palette.wall` with a dashed border. A test enforces the amber, red and green exclusions.
- Short laptop heights: yes. The panel starts collapsed when `innerHeight < 520`, and the user's toggle wins for the session.

Answers to Emmy's open questions: two cache counts (`cache_read`, `cache_write`), not one, because providers price reads and writes differently and adding a field later would mean a v2. The config lives in `offices/ai-office/`, with its format in `engine/schema/office.md`. Profile models confirmed above. Plan share of limit: tokens only (Merwyn's default).

### Decision record draft (for April)
```
Decision: Event log v1 adds provider/model to step_started and a new `usage` event; provider catalogue and prices live in offices/<office>/providers.yaml; the page computes an estimated cost from config only.
Context: T-056, multi-provider agents; runtime (T-024) and cost logging (T-026) not built; prices not verified.
Options: A — model and usage on every agent event: simple to read, but repeats data and mixes concerns.
         B — step_started carries the model, a separate usage event carries counts at step end: matches when runtimes know each value.
         C — cost written in the log only: no config needed, but no cost for logs without one, and no dated source.
Chosen: B plus config-priced estimates, because the runtime knows the model at start and the tokens at end, and a dated config price is checkable.
Consequences: Easier: T-026 emits one event type; prices change without code. Harder: two cost notions (log cost_usd for budgets, config estimate on screen) that T-026 must reconcile; default page is synthetic until real logs exist.
Links: T-056, T-048, T-026, T-027, PR (tbd)
```

— Fang (architect)

## UX design

**Question this answers (playbook 1):** "Which model is each agent on, and what has the replay used so far?" **Audience:** Merwyn alone, glancing. The needs-you state from T-048 stays the loudest thing on screen (playbook 2); nothing here may out-shout it. Left out: budgets, charts, per-step token detail, any "live" wording. Reuses T-048 tokens, `.tag`, `.panel`, `.seg`, `#ticker`, `body.rm` (office.template.html). Skills (design-handoff etc.) not called in this session; structure follows playbook 6 by hand. All sizes and durations are starting values to judge on screen (playbook 3).

### 1. Layout and hierarchy
Order of attention: (1) needs-you pill and beacon, unchanged; (2) agent strip; (3) 3D office with model chips; (4) usage panel; (5) controls.

**Model badge = a second line inside the existing `.tag`** (name tag), not a new floating label. One label per agent, so no extra overlap work. The tag stays 11px type; the new line is 10px:
```
+---------------------+
| ■ Fang              |   existing: agent colour square + name
| [SDK] opus          |   new: provider code chip + short model
+---------------------+
```
- Provider chip: 2 to 4 letter code in a 1px border box coloured by provider (SDK, API, OAI, DSK; unknown shows first 3 letters of the raw id, uppercased). The code is the non-colour channel; colour is the border and a 6px swatch only, so the words always use `--text` (contrast stays as T-048's 14:1 on panel).
- Model label: short name (opus, sonnet, gpt-5, v3), from the config's `short` field, else the raw id truncated at 12 chars with an ellipsis; full id in the `title` and the strip tooltip.
- Waiting state: the amber border and beacon stay on the tag and the door, untouched. The provider chip never uses amber, red or green, so a waiting tag still reads as amber first. When an agent is waiting, the model line drops to `--text-dim` so the beacon wins.
- Dim/idle agents: line follows the tag's existing `.dim` opacity.
- "Planned" mismatch (spec: event model differs from profile `model:`): the tag shows the event's model; a small `planned: sonnet` in dim text is added only in the focus card and ticker line for that step, not on the tag. Reason: the tag must stay two lines.
- No step yet for an agent: chip reads `--` dim, no colour.

**Agent strip (desktop):** no change to segments; the provider code is added to each segment's `title` only. The strip is already full at 8 agents.

**Usage panel (desktop, 900px and up):** a collapsible `.panel` docked **above the ticker** in the right column (`--side` 288px), so the ticker keeps its place beside the stage and keeps the latest 8 lines (playbook 2). Height about 40% of the column; ticker takes the rest. Header row shows "Usage" and a `synthetic` pill (see below); it never scrolls away.
```
+- Usage ------------ [synthetic] -+
| TOTAL   in 412k  out 96k  cache 210k |
|         $3.18 est.* + plan runs      |
| BY PROVIDER                          |
| [SDK] claude-sdk   plan   in 180k .. |
| [API] anthropic    $2.10  in 90k ..  |
| [OAI] openai   price not set  ...    |
| [DSK] deepseek     $1.08  ...        |
| BY AGENT  (tap a row to focus agent) |
| Fang   SDK  in 52k out 9k  plan      |
| ... 8 rows                           |
| *prices from config, dated 2026-xx   |
+--------------------------------------+
```
- Three blocks in this order: Total, By provider, By agent. Numbers use `.mono` tabular. Token counts compact (412k), exact value in `title`.
- Columns: in, out, cached (labelled "cache"), then a cost cell. Header labels stay visible; no icons-only.
- **Cost cell, exactly one of four states:** `$1.08` (per-token provider with price set; footnote line shows the config's source date, e.g. "prices from config, source dated 2026-NN-NN"; never "live" or "current"); `plan` (subscription run; no dollar sign anywhere in the row); `price not set` (per-token provider, config price empty; tokens still shown); `--` (no cost info, unknown provider). Total row: sum of priced dollars only, then a dim "+ plan runs" and, if any, "+ N unpriced", so the total is never presented as complete when it is not.
- Rows by provider carry the provider chip (code plus colour), same as the tag, so the panel doubles as the colour legend.
- Panel is collapsible (button, `aria-expanded`); collapsed it shows one line: total tokens + `synthetic`. State remembered for the session only.

**Synthetic label.** While the log header says synthetic: a `synthetic` pill (text `--panel` on `--text-dim` fill, not amber) in the panel header, AND the word `synthetic` in dim text after every usage figure group (total line, each provider row, each agent row) via a trailing `syn` suffix that is visible, not tooltip-only (spec: "next to every usage figure"). Ticker lines that carry tokens add `(synthetic)`. Hidden only when the header says real. The existing bottom-bar clock already says "(synth)"; keep it.

### 2. Provider palette
Must stay out of amber (hue 15-45, reserved), red (#e63946/#ff6b6b/#c1121f) and green (#53BA7E accent). Proposed new tokens for `theme.yaml`/config (Fang or Sebastian apply; I edit this file only):

| provider | code | colour | hue | extra cue |
|---|---|---|---|---|
| claude-sdk | SDK | #c084fc violet | ~270 | text SDK |
| anthropic-api | API | #5b8def blue | ~218 | text API |
| openai | OAI | #f472b6 pink | ~330 | text OAI |
| deepseek | DSK | #3fd0e0 cyan | ~186 | text DSK |
| unknown | first 3 letters of raw id | #8d99ae (existing wall) | n/a | dashed border |

Colours live in the office config next to price and source note, not in the HTML (spec: no hard-coded provider data). A fifth known provider gets its colour from config; if config has none, treat as unknown. Violet and blue are the closest pair (about 50 degrees); the code text separates them for everyone, and the builder should check them side by side on screen. Contrast: provider colour is only ever a border or swatch (non-text, needs 3:1 on panel #1d1e2c); builder to verify each and adjust lightness, not hue, if short. I have not measured them.

### 3. Model switch mid-replay
Purpose: continuity, so Merwyn notices a change without watching (playbook 3).
- Event step carries a different provider/model than the agent's previous one: the tag's model line swaps. Motion: the chip border flashes to `--text` for 400ms then settles to provider colour; line cross-fades 180ms ease-out. Ticker gets a line `Fang  sonnet -> gpt-5 (SDK -> OAI)` in normal weight. No sound, no 3D effect, no beacon (amber stays reserved).
- **Reduced motion (playbook 5):** no flash or cross-fade; line swaps instantly, and the ticker line is the cue. In `body.rm` the existing transition rules already apply; add the new classes to them.
- Scrubbing backward: each agent's badge and every figure recompute for the time; no animation on scrub, so totals never "tick down" slowly. Counts snap, same as the existing ticker rebuild.
- Usage counters increment with a plain number swap (no count-up animation): a count-up would be motion with no purpose.

### 4. States
| state | badge | panel |
|---|---|---|
| Before first event / empty | `--` dim chip on every tag | "No usage yet" one line, `synthetic` pill still shown |
| v0 log (no provider/model) | no model line; tag unchanged (keeps today's look) | panel hidden; one dim line "This log has no model data" in the ticker area, not an error |
| Provider known, price set | normal | `$` cost + source-date footnote |
| Subscription | normal; chip code SDK | `plan`, tokens, no `$` |
| Per-token, price not set | normal | `price not set`; tokens shown; total gains "+ N unpriced" |
| Unknown provider/model | neutral chip, dashed border, raw id uppercased/truncated | row listed under its raw id, `--` cost |
| Parser warning on a step | nothing on tag | dim `!` count in panel footer, title lists warnings; never red |
| Needs Merwyn | unchanged T-048 beacon; model line dim | panel unchanged |

### 5. Phone, under 600px
Question on phone is narrower: "who runs on what, and what total so far?"
- Tag: 3D tags already crowd on a phone, so every tag shows the `[SDK]` code chip only (no model name) beside the name; the model name appears in the focus card and the usage sheet.
- Agent strip (40px segments): add nothing; the initials stay. The provider code goes into each segment's `aria-label`.
- Usage panel does not dock. A `Usage` button joins the existing `#gear` menu area (`#msheet`) and opens a bottom sheet over the stage (same pattern as `#msheet`, `bottom: calc(var(--bar) + 40px)`, max height 60vh, scrolls). Sheet shows Total, By provider, then By agent as stacked two-line rows (name + chip on line 1; in/out/cache and cost on line 2, 12px). Close button 44px; `Esc` and tap outside close.
- A permanent one-line strip is not added: the ticker one-liner (`#tone`) already occupies that slot. Instead `#tone` suffix shows `synthetic` when it says anything about usage; the sheet header carries the pill.
- 600 to 899px: panel appears as the same bottom sheet (the ticker is hidden there too), opened by a `Usage` button in the bar.
- Touch targets 44px min; type 12px min in the sheet.

### 6. Motion summary (playbook 3, 5)
| event | purpose | duration / easing | reduced motion |
|---|---|---|---|
| Model switch | continuity | 400ms chip flash + 180ms cross-fade, ease-out | instant swap, ticker line only |
| Panel collapse/expand | relationship | 160ms height, ease-out | instant |
| Sheet open (phone) | continuity | 180ms slide up, ease-out | instant |
| Counter update | none | no animation | same |
No looping motion is added.

### 7. Accessibility check
- Never colour alone (playbook 5): provider = code text plus colour; unknown = dashed border plus raw id; cost state = words; synthetic = word.
- Provider words use `--text` on `--panel`; colour only on borders/swatches (3:1 non-text, to verify on screen).
- Panel is a `section` with `aria-label="Usage"`; the collapse button has `aria-expanded`; numbers have text units ("412 thousand tokens in" via `title` and `sr` text). Do not put the panel in an `aria-live` region: replay would chatter. The ticker's existing live behaviour carries model-switch lines.
- Order in DOM: panel before ticker. Focus visible via existing `button:focus-visible`.
- Reduced motion read from `matchMedia` and `body.rm` as T-048 does (SCR40, C39).
- Amber reserved rule kept: no provider colour in hue 15-45.

### Open questions
- Is the config's `short` model label a field Fang will add, or derived from the id? Fang.
- Does Merwyn want "plan" rows to show share of plan limit later? Already asked in the Spec; default tokens only. Merwyn.
- Provider colours: ok to add these five to `theme.yaml`, or live only in the usage config? Fang.
- On phone, is the code-only chip on tags enough, or should the focused agent's tag show the full model? Merwyn after seeing a screenshot; default as above.
- Panel-vs-ticker split at short laptop heights (under 520px): suggest panel starts collapsed. Fang to confirm in build.

— Dinda (designer)

## Approvals (PMO)
Spec approved 26 Nov 2026. Answers: profile models today (base/agents): architect and reviewer opus; pm, pmo, engineer, compliance, curator, designer sonnet. Prices: Janice could not verify current per-token prices from this session, so the config ships with prices "not set" and a field for the source and date; a step on a per-token provider with no price shows tokens and "price not set", never an invented number. Merwyn or a later task fills prices from the providers' pricing pages. Dinda consults before Fang finalises Design. — Janice (pmo)

Janice (pmo), 26 Nov: Design accepted (Dinda's UX with Fang's three changes). Build starts when a build slot frees (at most 2 in build). Model ids in the fixture are illustrative and labelled synthetic; prices stay null. Engineer: do not set status.

## Build notes

**What changed**
- Parser `engine/runtime/events.py`: v0 and v1 (`SCHEMA_VERSIONS = (0, 1)`), v1 header needs `usage_source`, `step_started` takes `provider`+`model` (both or neither), new `usage` type, kinds PROVIDER, MODEL, BILLING, TOKENS, USD, plan step with `cost_usd` is an error, catalogue warnings (one per distinct message) via `parse_log(..., providers=)`. v0 behaviour untouched.
- `engine/runtime/providers.py` (new) + `offices/ai-office/providers.yaml` (new): catalogue, colours, codes, `short`, `family`; all prices `null`, `prices.source`/`checked` `null`; a price without a dated source fails the build.
- `scripts/office_app.py`: injects `providers`, `warnings`, `agents[].planned_model` (via `build_agents.merged`), `v: 1`; default fixture is now the v1 synthetic log; Sprint 3 still builds with `--fixture`.
- `engine/app/office.template.html` (office-core): usage reducer, `eventCost`, `usageTotals`, `costText` (the only place a currency sign is built), `modelLabel`, `plannedDiffers`, `tickerItems`/`switchSentence`, `DUR.usage = 0` with `evDur` using `in`. (office-view): second line on each name tag (provider chip + short model; phone shows the chip only), Usage panel (total, by provider, by agent) docked above the ticker, sheet under 900 px (Usage button in the bar at 600-899, in the gear menu on phones), focus card model/planned/usage lines, strip tooltip and aria-label carry the provider code, ticker line on a model switch (usage events add none), "This log has no model data." for v0 logs.
- `engine/app/fixtures/models-synthetic.jsonl` (new, SYNTHETIC): 84 events, 24 `usage`, 4 providers, 8 agents with a model by t=16 s, the engineer switching SDK -> OAI -> DSK -> SDK, the reviewer once on the Anthropic API, a needs-Merwyn moment at +01:45, no `cost_usd`, no warnings.
- Docs: `engine/schema/events.md` (v1 section), `engine/schema/office.md` (providers.yaml), `engine/app/README.md`. T-026 got the Spec note to emit this format.
- Tests: `tests/test_providers.py` (new), `tests/test_events.py` (+V1 class), `tests/test_office_app.py` (node modes `usage` and `pricing`, `NoLiterals`, `Providers`), fixtures `events-v1-edge.jsonl`, `providers-test.yaml` (made-up prices, labelled TEST).

**How to verify** (real output, 26 Nov 2026)
```
$ python -m unittest                      -> Ran 271 tests ... OK   (was 240)
$ python scripts/office_app.py ai-office --check
engine/app/office.html: up to date (128 KB, 84 events)         # 131,275 bytes; limit 204,800
$ python -m engine.runtime events ai-office engine/app/fixtures/sprint-03.jsonl      # v0
engine/app/fixtures/sprint-03.jsonl: 45 events kept, 0 errors, 0 warnings
$ python -m engine.runtime events ai-office engine/app/fixtures/models-synthetic.jsonl   # v1
engine/app/fixtures/models-synthetic.jsonl: 84 events kept, 0 errors, 0 warnings
$ python -m engine.runtime events ai-office tests/fixtures/events-v1-edge.jsonl      # exit 1 by design
... 5 events kept, 8 errors, 3 warnings
$ python scripts/golden.py ai-office      -> golden: 10 cases, 41 checks, 0 problems
$ python -m engine.runtime validate ai-office   -> ai-office: OK - 8 agents, 5 stages, 56 tasks, 17 skills
$ python scripts/build_agents.py ai-office -> built 8 agents;  python scripts/board.py ai-office -> 56 tasks (board.md discarded)
```
Open the page: get three.js as in `engine/app/README.md`, then `engine/app/office.html?t=40` (mid replay, all 8 models), `?t=108` (Janice waiting on Merwyn), `?t=105&play=1` (model switch), `?motion=reduced`, `?usage=open` on a phone width.

**Done-when map**
- v1 documented, v0 loads unchanged: events.md; `V1.test_v0_files_load_unchanged`, CLI exit 0 above.
- Plan step shows tokens and "plan", no dollar; plan + `cost_usd` fails: `V1.test_plan_step_with_cost_is_an_error`, `pricing` node test (`plan` bucket: `micro 0`, text has no currency sign).
- Per-token cost from config with source date, never "live": `pricing` node test (exact micro-USD: 116,088 -> "$0.12 est."), date shown per provider row ("prices checked ..."), footnote; `NoLiterals` bans "current price" and "live price/cost/usage". The shipped config has no price, so the committed page shows "price not set" and no currency sign anywhere (`test_committed_page_data_has_no_dollar_sign...`, `usage` node test asserts the end-of-replay cost text is "plan runs + 3 unpriced").
- Synthetic: header `usage_source: synthetic`, title says SYNTHETIC, pill in the panel header and the word "synthetic" after the total, every provider row and every agent row (screenshots).
- Model as colour plus text for all 8 agents at mid replay: `mid-desktop.png`.
- Totals equal the sum of events due, scrubbing back lowers them: `CoreUnderNode.test_usage_totals_equal_the_sum_of_events_due...` (times 0, 60, end, 60, 120, 0; exact per-agent, per-provider and total).
- Unknown provider/model: warning not error (`V1.test_unknown_ids_warn_once_not_error`, `Providers.test_unknown_provider_still_builds...`); renders raw id (cut at 12 chars with an ellipsis), neutral colour, dashed chip, `--` cost (`pricing` node test on `modelLabel` and `costText`). I did not screenshot an unknown provider on the page; it is covered by the node test only.
- Config not hard-coded: `NoLiterals.test_no_price_numbers_provider_ids_or_live_claims` (no provider id, no test price, no `$\s*\d` in the template or `office_app.py`); `test_dollar_sign_is_built_in_exactly_one_place`.
- Event model differs from profile `model:`: page shows the event's model, "planned: sonnet" only in the focus card (`plannedDiffers` node test; `focus-card.png`: Sebastian on gpt-5, planned sonnet; a same-family model on another provider gives no "planned" line, covered by the node test only).
- T-048 data scan and size limit still pass (`PageRules`).

**Screenshots** (`/tmp/t056-shots/`, headless Chrome, software GL; the only console output is Chrome's "GPU stall due to ReadPixels" driver message, no page errors; fps is red because software GL, not a real frame rate)
`mid-desktop.png` (t=40, 1280x800, all 8 models, synthetic labels), `end-desktop.png` (t=233, four providers, ticker switch line), `needs-merwyn-desktop.png` (t=108, amber still loudest, waiting tag model line dim), `switch-flash.png` (t=105 playing, mid model switch), `reduced-desktop.png` (`?motion=reduced`), `focus-card.png`, `collapsed-desktop.png`, `short-laptop.png` (1280x500, panel collapsed by default), `phone-mid.png` and `phone-needs-merwyn.png` (390x844, chip-only tags), `phone-usage.png` (usage sheet), `tablet-usage.png` (700x800 sheet and bar Usage button), `v0-sprint03.png` (Sprint 3 log: no chips, no panel, "This log has no model data.").
Fixed after looking: wrapping "cache" figure (spans no longer split), focus-card usage lines, the 600-899 px bar overflowing once the Usage button joined it (4x and fps were clipped), a duplicated "gpt-5 gpt-5" in the focus card, smaller chips on phones.

**Deviations from the design**
1. `Row` has an extra `usd` count (priced buckets) next to `plan`, `unset`, `none`: without it a priced bucket of 0 micro-USD cannot be told from "no usage". `costText` uses it.
2. Added `?usage=open|collapsed` URL parameters so the sheet and collapsed state can be screenshotted without a click; documented in the app README. Not in the design.
3. Panel collapse and sheet open are instant, not the 160/180 ms height and slide animations in Dinda's motion table (no loops or flashes were dropped; the model-switch chip flash, 180 ms cross-fade and the reduced-motion fallback are in). Say so if you want them.
4. `tickerItems` (core) builds the ticker list, so the switch line is computed once from the event log and survives scrubbing; the design said the view would detect the switch. Same result, testable under node.
5. Added `engine/schema/office.md` section and `engine/app/README.md` notes (the design named office.md only).

**Known limits**
- Tags are two lines now and the desks are close: Fang's and Dinda's tags overlap by about 8 px at 1280x800 (text stays readable); on phones tags still crowd as they did in T-048, now with a chip.
- Provider rows follow the order of the config keys as written into the page (sorted by `json.dumps`), so the Anthropic API row comes before the SDK row.
- The chip border contrast (3:1 non-text) was judged by eye on screen, not measured.
- Real model ids and prices are unknown: the catalogue holds the fixture's illustrative ids and every price is null (Open questions below).
- T-048 data-rule gap for keys/numbers is T-027's; not widened.

— Sebastian (engineer)

## Review log

## Decision

## Open questions
- Which model ids the office really runs per provider (the catalogue holds the fixture's ids): T-024/T-026 emit them; Merwyn confirms. Not blocking. (Fang)
- How each provider reports cached tokens relative to input (normalised to uncached `input` in v1): T-026 verifies against each provider's API docs. Not blocking. (Fang)
- Real per-token prices with source and date: Merwyn or a later task fills providers.yaml; until then per-token rows show "price not set". Not blocking. (Fang)
