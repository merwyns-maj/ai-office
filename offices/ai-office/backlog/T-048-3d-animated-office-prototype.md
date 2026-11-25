---
id: T-048
title: "3D animated office: design and three.js prototype (slice of T-027)"
phase: 6-office
status: build
priority: P1
owner: pmo
where: code
project: ai-office
depends_on: [T-047]
pr: 25
---

> Merwyn, 25 Nov 2026: "start designing my 3d animated office". A first slice of T-027 that does not wait on the SDK runtime (T-024): it plays a recorded event log instead of live events.

## Done when
- [ ] Dinda's design: scene layout (rooms = workflow stages from theme.yaml), avatar look per agent, animation for each event type, idle/active/needs-Merwyn states, camera, palette, reduced-motion behaviour
- [ ] An event log format v0 (documented) and a fixture that replays a real sprint from this repo's history, no company data
- [ ] engine/app/ holds a single self-contained three.js page that renders the office from theme.yaml data and animates the fixture: agents walk between rooms on handoff, show what they hold, and a "waiting for Merwyn" state is visible at a glance
- [ ] Runs from a static file server with no build step; works with reduced motion; holds a smooth frame rate with 8 agents on a laptop
- [ ] Tests cover the event-log parser or generator; all tests pass
- [ ] Merwyn can open it as an artifact

## Spec

**Problem.** Merwyn cannot see the office working: no event exists yet (`engine/runtime/dryrun.py` only prints the next step) and no visual. He wants a 3D animated office; the live runtime (T-024) is not ready.

**In scope**
- A prototype slice of T-027: replay a **recorded** event log, no live events.
- Dinda writes `## UX design` (needs T-047); Fang writes the technical `## Design`.
- Event log format v0, documented, plus a fixture from this repo's own history: Sprint 3 tasks T-043, T-044, T-045 moving through stages (`offices/ai-office/sprints/sprint-03.md`). Task ids, agent names and stages only.
- One self-contained HTML page in `engine/app/`, three.js from a CDN, no build step, reading office layout (rooms=stages, desks, palette, hub, Merwyn's door) from `theme.yaml` data.
- Parser or generator for the log, with tests.

**Out of scope**
- Live events, the SDK runtime (T-024), multi-office views, other offices: all stay in T-027, which remains open.
- Sound, multiplayer, editing the office, controlling agents from the page, auth, hosting.
- Company data of any kind; real-time reads from this repo.
- Custom-built or paid 3D assets; building a bundler.

**Done when**
- [ ] `## UX design` (Dinda) covers: scene layout per room, avatar look per agent, one animation per event type, idle / active / needs-Merwyn states, camera, palette from `theme.yaml`, and reduced-motion behaviour. Each event type in the log format has an animation entry.
- [ ] Event log format v0 is documented in a file in the repo (fields and event types listed). Fixture exists, is a replay of T-043/T-044/T-045, and a grep for personal data (names beyond office agents, NIK, emails, account numbers) finds none.
- [ ] Given the fixture, when the page loads from `python -m http.server` (no install, no build), then 8 agents are drawn at their desks and each handoff event shows the agent walking to the target room carrying a visible label of the task id.
- [ ] Given a `needs_merwyn` state in the fixture, the waiting agent appears at Merwyn's door and is distinguishable from idle and active without reading text (colour from `warn`, plus a shape or icon), checked in a screenshot.
- [ ] Given `prefers-reduced-motion: reduce` (or a toggle), agents move between rooms without walking animation and the status is still readable; Reviewer shows both modes.
- [ ] Frame rate: 8 agents, measured with `renderer.info` or an on-page fps counter on a laptop, stays at or above 50 fps for 60 seconds (Cahyani records the device and the numbers).
- [ ] Tests for the log parser or generator pass; one case for a malformed line. Full test suite output pasted.
- [ ] The same HTML file opens as an artifact for Merwyn; Janice or Merwyn confirms it renders, and the artifact link is in Build notes.

**Risks**
- The CDN may be blocked in the artifact sandbox or offline; the page then shows nothing.
- Sprint 3 history may lack timestamps; the fixture may need a synthesised clock.
- Scope creep towards the live view; T-027 holds that.
- Unknown whether T-047 lands before design starts (dependency).

**Open questions**
- Can the artifact environment load three.js from a CDN? Merwyn / Janice test with a stub page. Blocking for the last check.
- Is the fixture to be hand-written from `sprint-03.md` and git history, or generated? Fang. Not blocking.
- "Smooth" threshold: 50 fps at 8 agents is my proposal. Merwyn to confirm or change.
- Do all 8 agents include Dinda? Assumed yes (7 today plus her, once T-047 lands).

— Emmy (pm)

## Design

**Skills.** claude:diagram-design was not called (sub-agent session, no Skill tool); the layout diagram in Dinda's section 3 serves.

### Approach
One stdlib Python path turns repo data into one self-contained HTML file. The browser does no fetching apart from three.js, and only ever reads the data embedded in the page.

```
theme.yaml + org.yaml + workflow.yaml + fixture.jsonl
   └─ scripts/office_app.py (uses engine/runtime/events.py, miniyaml, loader)
        └─ fills engine/app/office.template.html → engine/app/office.html (committed)
```

| file | new / changed | what |
|---|---|---|
| `engine/schema/events.md` | new | event log v0: header, common fields, the 11 types, rules, synthetic clock |
| `engine/runtime/events.py` | new | parser and validator, stdlib only |
| `engine/runtime/__main__.py` | changed | adds subcommand `events <office> <log>` (same exit codes as `validate`) |
| `engine/app/fixtures/sprint-03.jsonl` | new | hand-written replay of Sprint 3 (see Fixture) |
| `engine/app/office.template.html` | new | HTML, CSS and JS with one data placeholder |
| `engine/app/office.html` | new, generated | the page for both `python -m http.server` and the artifact |
| `engine/app/README.md` | new | how to regenerate, serve, publish and screenshot |
| `scripts/office_app.py` | new | generator, with `--check` |
| `offices/ai-office/theme/theme.yaml` | changed | Dinda's palette tokens, layout coordinates, meeting room |
| `engine/schema/office.md` | changed | documents the optional theme keys `rect`, `at`, `door` |
| `tests/test_events.py`, `tests/test_office_app.py` | new | see Test plan |
| `tests/fixtures/events-all-types.jsonl` | new | synthetic log with all 11 types, labelled synthetic, for tests and the Reviewer |

The fixture is **hand-written, not generated** (Spec open question 2). Git history has only 5 timestamps for Sprint 3 and none of the in-stage moments. A generator from task-file prose would be more code than the 50 lines it writes, and it could not be honest about order.

### three.js: classic r128 from cdnjs
`<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js" crossorigin="anonymous">`. If the cdnjs script fails to load, a small loader tries `https://unpkg.com/three@0.128.0/build/three.min.js`, then `https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js`. If `window.THREE` is still missing after 8s, Dinda's "3D failed" state shows and the HUD keeps replaying.

| option | works in file / served / artifact | cost |
|---|---|---|
| **A. r128 UMD global (chosen)** | classic script, no module loading, so all three behave the same | no `CapsuleGeometry` (added in r139); legacy light units; no addons needed |
| B. importmap to `cdn.jsdelivr.net/npm/three@0.16x` ES module | needs module support and CORS in the artifact sandbox, which nobody has tested | newer API; one more unknown in the one place the Spec calls a risk |

Reason: r128 is the last widely used UMD build on cdnjs, and the UMD build was dropped from later releases. A plain global script removes the module/CORS question from the artifact sandbox. Nothing in Dinda's design needs anything newer than r128:
- capsules become a shared `LatheGeometry` with a capsule profile;
- furniture uses core `InstancedMesh` (r109 and later);
- labels are HTML.

Not verified from here: the agent proxy returns 403 for cdnjs, unpkg and jsdelivr, so I could not check that the URL resolves. The npm registry is reachable, and `three@0.128.0` exists there. Janice checks the cdnjs URL from the main session before build ends (Open questions). No SRI hash: I could not fetch the exact cdnjs bytes, and an npm-built hash may not match them. The version is pinned in the path.

### Interfaces

**1. Event log v0** (`engine/schema/events.md`). The file is UTF-8 JSONL with one JSON object per line. Blank lines are ignored. Lines are at most 2000 characters, and a duplicate key in an object is an error.

Line 1 is the header:
`{"log":"office-events","v":0,"office":"ai-office","clock":"synthetic","title":"Sprint 3 replay (T-043, T-044, T-045)"}`
- `v` must be 0, otherwise the whole file is rejected.
- `clock` is `synthetic` or `wall`.

Common fields on every event line:
- `t`: number ≥ 0, in seconds from the start of the log. It must not decrease; equal values mean simultaneous.
- `type`: string.
- `src`: required. The repo-relative path the event is taken from, with an optional `#Section`, e.g. `offices/ai-office/backlog/T-043-guard-ask-mode-for-prod-writes.md#Review log`.
- `wall`: optional ISO 8601 with offset. Only use it when a real time exists (git commit time or the sprint file). Values present must not decrease.

Field types:
- AGENT: an `org.yaml` agent id (`pmo`, `pm`, `architect`, `engineer`, `reviewer`, `compliance`, `curator`, `designer`).
- TASK: matches `^T-\d{3}$`.
- STAGE: a `workflow.yaml` stage id or terminal state.
- TEXT: a string of 1 to 120 characters with no newline.

| type | fields | reducer effect |
|---|---|---|
| `step_started` | agent, task | agent holds task; working |
| `stage_changed` | task, from: STAGE, to: STAGE | task.stage = to |
| `handoff` | task, from_agent, to_agent, to_stage: STAGE | task moves from from_agent's hands to to_agent's; task.owner = to_agent |
| `discussion` | task, agents: [AGENT] (2 to 4, no repeats), lines: [{agent, text: TEXT}] (1 to 6, each line's agent in `agents`) | none (transient) |
| `needs_merwyn` | agent, task, reason: TEXT | agent.waiting adds task; agent holds it |
| `merwyn_answered` | agent, task, answer: TEXT | agent.waiting removes task |
| `review_pass` | task, agent, note: TEXT (optional) | task.mark = pass; clears reject |
| `review_reject` | task, agent, reason: TEXT | task.mark = reject. **Rule:** the next event for that task must be a `handoff` |
| `compliance_result` | task, agent, verdict: `PASS` \| `PASS_WITH_CONDITIONS` \| `BLOCK` | task.compliance = verdict. **Rule:** a BLOCK must be followed by a `needs_merwyn` for that task, as the next event for that task |
| `blocked` | agent, task, reason: TEXT | agent.blocked[task] = reason. Cleared by a later `step_started`, `handoff` or `merwyn_answered` on that task |
| `merged` | task, pr: integer ≥ 1 | task.stage = done; removed from every agent; filed on the archive shelf (pmo stamps, curator files, all inside one animation) |

Severity:
- A field not listed for its type is a **warning**.
- An unknown `type` is a **warning**: the event is kept, and the page shows Dinda's "Unknown event skipped".
- Everything else is an **error**: that line is dropped and the rest is kept.

**2. `engine/runtime/events.py`**
```python
SCHEMA_VERSION = 0
EVENT_TYPES: dict[str, dict[str, str]]        # type -> {field: kind}, kind in AGENT TASK STAGE TEXT INT VERDICT AGENTS LINES; optional fields suffixed "?"
@dataclass(frozen=True)
class LogProblem: line: int; level: str; message: str   # level "error" | "warning"; str() -> "<line>: <level>: <message>"
def parse_log(text: str, *, agents: set[str], stages: set[str], forbidden: tuple[str, ...] = ()) -> tuple[dict | None, list[dict], list[LogProblem]]
    # returns (header, kept events in file order, problems). Never raises on bad input.
def forbidden_terms(repo_root: Path) -> tuple[str, ...]
    # org and repo names from workspaces.yaml whose owner is not merwyns-maj (e.g. the company org and its repos)
DATA_PATTERNS: tuple[re.Pattern, ...]          # email, 16-digit run (NIK-like), any run of 10+ digits (account-like)
```
- Data rule: every string value is checked against `DATA_PATTERNS` and `forbidden` (case-insensitive). A hit is an error.
- CLI: `python -m engine.runtime events ai-office engine/app/fixtures/sprint-03.jsonl` prints problems. Exit codes: 0 when there are no errors (warnings are printed), 1 on errors, 2 on usage or a missing file.

**3. `scripts/office_app.py`**
```
python scripts/office_app.py <office> [--fixture PATH] [--out PATH] [--check] [--allow-errors]
  defaults: --fixture engine/app/fixtures/sprint-03.jsonl, --out engine/app/office.html
  exit 0 written / up to date; 1 log errors (unless --allow-errors), theme layout missing, or --check finds a stale file; 2 usage
def build_data(office_root: Path, fixture: Path) -> tuple[dict, list[LogProblem]]
def render(template_text: str, data: dict) -> str
```
- The template must contain the line `<script type="application/json" id="office-data">__OFFICE_DATA__</script>` exactly once; otherwise the generator exits 1.
- `render` uses `json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`, then replaces `</` with `<\/` and escapes U+2028 and U+2029. The output is deterministic: no timestamp and no absolute paths, so `--check` can compare bytes.
- Data block keys: `v`, `office {id, name}`, `theme {style, palette, rooms, desks, hub, door}`, `agents [{id, name, role, personality}]` (org order), `stages [...]`, `log` (header), `events [...]`, `skipped [{line, message}]`.
  - `skipped` is empty for the committed file.
  - With `--allow-errors` it carries the dropped lines, so Dinda's "malformed lines" state can be shown.
- The page never parses JSONL, so the Python parser is the only parser.

**4. theme.yaml additions** (wording and data, no logic). Dinda's numbers are used unchanged. The schema already allows free palette names, and nothing else reads theme.yaml today (grep).
- `palette`: add `bad_text`, `bad_tag`, `panel`, `text`, `text_dim`, `rug`, `wood`, `paper`, `skin_light #e0b48f`, `skin_mid #c68e65`, `skin_dark #8d5a3c`.
- `rooms`: each room gets `rect: [x0, z0, x1, z1]` from section 3, for example `lobby [0, 9, 9, 16]` and `corner [10, 0, 14, 7]`. Add `- { id: meeting, label: Meeting table, stage: null, rect: [9, 9, 15, 16] }`.
- `desks`: each desk gets `at: [x, z]` from Dinda's desk table.
- Add the top-level key `door: [12, 0]`.
- The generator exits 1 if any room lacks `rect` or any desk lacks `at`.
- In the page, avatar shapes and colours live in a JS table keyed by `sprite`: they are art, not office data.

**5. Page structure** (one template; 1000 to 1400 lines in total; `office.html` at most 200 KB)
- `<style>`: Dinda's tokens become CSS variables, which the page sets from `theme.palette` at boot.
- `<script id="office-data" type="application/json">`: the data block.
- `<script id="office-core">`: pure JS with no DOM and no THREE. It exposes `globalThis.OfficeCore` and runs under node.
  - `timeline(events)`: playback times. Gaps over 3s compress to 1.5s.
  - `DUR`: Dinda's durations.
  - `initState(data)`, `apply(state, ev)`: the reducer from the table above. Unknown types are recorded in `state.unknown`.
  - `stateAt(data, t)`: replays from 0, used for scrubbing and stepping.
  - `agentStatus(state, id)`: one of waiting, blocked, discussing, working, idle. The scene adds walking.
  - `stripOrder(state)`: Dinda's priority order, ties broken by time in state.
  - `sentence(ev, names)`: ticker text.
- `<script id="office-view">` holds the rest, as plain function sections in one IIFE:
  - **boot**: loads three.js, shows the failed state if it never arrives, reads the URL params.
  - **scene**: floor, rooms, instanced furniture, door and lights; shared geometries; materials cached by hex (at most 30).
  - **avatars**: built per sprite; card, ring and beacon meshes per agent.
  - **anim**: one queue per agent so each agent's events play in series; tweens and easings. A queue longer than 2 skips its oldest animation to the end state, so 4x never drifts.
  - **labels**: HTML tags placed with `translate3d`.
  - **hud**: Needs-you pill, strip, ticker, aria-live region.
  - **playback**: play, pause, speed, scrub, step.
  - **camera**: ortho camera, follow, focus, pan and zoom.
  - **motion**: reduced or full mode.
  - **governor**: fps and quality.
  - **loop**: one `requestAnimationFrame`.
- URL params, for screenshots and review:
  - `?t=<seconds>` opens paused at `stateAt(t)`;
  - `?motion=reduced`;
  - `?speed=1|2|4`.
- Motion: `matchMedia('(prefers-reduced-motion: reduce)')`, re-checked on change, always wins (Janice answer 4). The toggle is then disabled and labelled "Reduced (system)". Otherwise the choice is stored in localStorage inside try/catch.
- Governor: the fps value is averaged over 0.5s. The readout shows `<fps> fps · <renderer.info.render.calls> calls`. If fps stays under 45 for 3s, the pixel ratio drops from min(devicePixelRatio, 1.5) to 1.0. The readout is always on.
- Banned in the page:
  - `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource` and `import()`;
  - external `<link>` and `<img>`;
  - any script host except the three listed above.
  The test checks this.

### Fixture (`engine/app/fixtures/sprint-03.jsonl`)
- It uses task ids, agent ids, stages and short TEXT only. Each event's `src` points at its sprint file or task file section.
- Order follows Janice's answer 1, then the documented flow:
  1. pmo `needs_merwyn` ×3: T-045, T-043 and T-002, with the questions from sprint-03.md "Decisions recorded". The card label reads "T-045 +2".
  2. `merwyn_answered` ×3, `wall` 2026-11-25T22:44:00+07:00.
  3. Plan: `stage_changed` todo→spec and `handoff` pmo→pm for each task, with `wall` 22:48:55 (PR #17).
  4. T-043 and T-044 Spec questions: a `discussion` pm/pmo for each.
  5. Design by the architect. T-043 has a `discussion` architect/compliance, then `compliance_result PASS_WITH_CONDITIONS`.
  6. T-044 runs beside T-043 while T-043 waits on compliance.
  7. Build, then review: `review_pass` with the real test counts (144, 148, 154).
  8. `merged` for PR 18, 19 and 20 with `wall` 23:02:24, 23:03:06 and 23:07:32 (git log).
- The fixture has no `review_reject`, `blocked` or BLOCK events, because Sprint 3 had none. Those types are shown with `tests/fixtures/events-all-types.jsonl`.
- `t` is authored at replay pace, about 150 to 220s in total. `events.md` states that the clock is synthetic and that only `wall` values are real.
- Speech lines are short quotes or condensations of the cited sentence, at most 48 characters. Dinda's candidates are acceptable, with one correction: the T-043 Review log says 154 tests, and her "148" belongs to T-044. Janice confirms the replay is fair at review.

### Accepting Dinda's UX design: accepted, with these changes
1. Avatars use a `LatheGeometry` capsule, not `CapsuleGeometry` (r128). Furniture uses `InstancedMesh`, not BufferGeometryUtils.
2. One animation per event. The carry-back after `review_reject` is its own `handoff` event, and a BLOCK is followed by `needs_merwyn`. The validator enforces both. `merged` contains the pmo→curator hand-over itself; no extra events are emitted for it.
3. Clock label: `+mm:ss (synth)`. The ticker adds the real time only when an event has `wall`. Nothing shows "Day 1 14:20".
4. Malformed lines: the page never sees raw lines. The state is kept and is driven by `skipped`, which is empty in the committed build.
5. Layout coordinates move into theme.yaml (`rect`, `at`, `door`, a meeting room). The numbers are hers. Skin tones become three named tokens.
6. Lights use r128 legacy intensities; Sebastian tunes them on screen. `style` stays `pixel-startup` (Janice answer 3).
7. OS reduced motion always wins (Janice answer 4).

— consult accepted_by architect

### Risks
| risk | handling |
|---|---|
| CDN blocked or URL wrong (Spec risk 1) | Three hosts are tried in turn, then the 3D failed state shows. The HUD still answers "does anyone need me". Janice checks the URL from the main session. |
| Committed `office.html` drifts from its sources | `--check` and the up-to-date test |
| Company or personal data in the fixture or page | parser data rule plus a scan of the whole `office.html`; `forbidden_terms` comes from workspaces.yaml |
| `</script>` in TEXT breaks the page | escaped in `render`; tested |
| Logic bugs are hidden behind WebGL | the core is pure and tested under node |
| fps cannot be measured in this sandbox (software GL) | Headless gives screenshots only. The 50 fps for 60s check is measured on Merwyn's laptop from the main session or the artifact, and Cahyani records it. |
| Scope creep to live events (T-027) | The page reads only the embedded data and has no polling. |

### Test plan
`python -m unittest -v` must pass in full; paste its output in Build notes.

**`tests/test_events.py`**
- The committed fixture has 0 errors and 0 warnings against the real office.
- Each of these gives an error, and the other lines are kept:
  - a malformed JSON line, with its line number;
  - a non-object line;
  - a duplicate key;
  - an unknown agent;
  - a missing or mistyped field;
  - decreasing `t` (equal `t` is OK);
  - a bad or decreasing `wall`;
  - TEXT over 120 characters or with a newline;
  - a discussion with 1 or 5 agents, or a line whose agent is not in `agents`;
  - a BLOCK without `needs_merwyn`, and a reject without `handoff`;
  - an email, a 16-digit run, a 10+ digit run, or a forbidden term.
- An unknown event type and an extra field each give a warning, and the event is kept.
- A missing header or `v` ≠ 0 rejects the file.
- The CLI exits 0, 1 and 2 in the right cases.
- `events-all-types.jsonl` has all 11 types and parses clean.

**`tests/test_office_app.py`**
- The committed `office.html` equals the generator output.
- A template without the placeholder, or with it twice, exits 1.
- The data block round-trips as JSON, and a TEXT containing `</script>` stays inside it.
- The data has 8 agents, every room has `rect`, and every desk has `at`.
- Script `src` values come only from the three hosts, with version 0.128.0 or r128. None of the banned APIs appear.
- The whole file passes the data scan.
- File size is at most 200 KB.
- **Headless core check**, run with `skipUnless(shutil.which("node"))` (node 22 is present here). It extracts `office-data` and `office-core` from `office.html` and runs them in `node -e`. It asserts:
  - after the first 3 events, pmo is waiting with 3 tasks;
  - after the answers, the needs count is 0;
  - at the end, all three tasks are done and nobody holds a card;
  - `state.unknown` is empty;
  - `stateAt(t)` equals sequential `apply` at 5 sample times;
  - the all-types build runs with no exception and shows blocked and rejected states.

**Reviewer, rendered check** (commands go in `engine/app/README.md`, nothing is committed):
1. Download the three.js 0.128.0 package from npm into `/tmp`.
2. Copy `office.html` to `/tmp` with the script URL rewritten to the local `three.min.js`.
3. Run `python -m http.server` there.
4. Take screenshots with `google-chrome --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --window-size=1280,800 --virtual-time-budget=15000 --screenshot` at three points: `?t=2` (Janice at the door, amber ◆), a handoff time, and `?t=2&motion=reduced`.
- The artifact render and the fps number come from Janice or Merwyn (Spec Done-when 6 and 8).

### Compliance flag: not flagged
The work touches no prod system, no money movement, no credentials and no personal data. It reads only this repo's office files and history, and the page makes no network calls except loading three.js. The data rule and the full-page scan keep it that way. The artifact is published by Merwyn or Janice, which is already their step. The design goes straight to the Engineer.

### Decision record draft (for April)
```
Decision: The office view is one generated, self-contained HTML page (classic three.js r128 from cdnjs) that replays a JSONL event log v0 embedded at build time.
Context: T-048 needs a 3D office that runs from a static server and as a claude.ai artifact (CDN scripts only, no fetch) before the live runtime (T-024) exists.
Options: A — r128 UMD + stdlib generator injecting data: same file everywhere, no module/CORS question; older API (no CapsuleGeometry).
         B — ES-module three 0.16x via importmap: newer API; module loading in the artifact sandbox is untested.
         C — page fetches theme/log at runtime: no generator; breaks as an artifact (fetch blocked) and from file://.
Chosen: A, because the artifact constraint is the riskiest one, and A has the fewest unknowns there.
Consequences: Easier: one parser (Python), byte-for-byte up-to-date test, core logic testable in node. Harder: data changes need a regenerate; moving to a newer three.js means swapping the loader and geometry helpers. T-027 live view replaces the embedded log with a stream using the same v0 events.
Links: T-048, T-027, T-024, PR (tbd)
```

— Fang (architect)

## UX design

**Question this screen answers (playbook 1):** "Does anyone need me, and what is moving?" **Audience:** Merwyn alone, on a laptop beside his work (sometimes his phone), glancing at it rather than watching. Every choice below serves that glance. Anything that does not is left out: no sound, no minimap, no settings panel, no per-agent statistics.

**Skills.** design:design-handoff and the other external skills in my profile were not called in this session (sub-agent, no Skill call made). This section follows the design-handoff structure by hand (playbook 6). All durations, easings and sizes below are starting values to judge on screen, not sourced numbers (playbook 3, office rule).

### 1. Layout and hierarchy

What the eye should find, in order:
1. **Needs you.** An amber pill at top left with a count, an amber beacon at Merwyn's door in the 3D scene, and the agent standing there. It is designed first and is the loudest thing on screen (playbook 2: "Waiting for Merwyn is the most visible state").
2. **Agent strip.** One segment per agent, sorted attention-first (playbook 2, arxiv 2610.21538).
3. **What is moving.** The 3D office (walkers and the meeting table) and the event ticker beside it (playbook 2: live event stream beside the list).
4. **Controls and fps.** Quiet, at the bottom.

**Desktop, 900px wide or more**
```
+------------------------------------------------------------------------+
| [◆ 1 needs you] | ◆Fang  ⬣Seb  💬Emmy 💬Wulan →Janice ●Cahyani ○April ○Dinda |  56px strip
+--------------------------------------------------------+---------------+
|                                                        | Ticker (280px)|
|                3D office (canvas, full bleed           | 14:20 ◆ Fang  |
|                behind the HUD)                         |  waits for you|
|                                                        | 14:18 → ...   |
|                                                        | (last 8)      |
+--------------------------------------------------------+---------------+
| ▶ ❚❚  [1x|2x|4x]  ──●──────◆────◆────  Day 1 14:20 (synth)  Motion: Full |  56px bar
|                                                         58 fps · 74 calls|
+------------------------------------------------------------------------+
```
- **600 to 899px:** the ticker collapses into a single line under the strip that shows the latest event. Tapping it opens the full list as an overlay.
- **Under 600px (phone, portrait):** see section 9.

### 2. Art direction

**Concept.** A warm studio after hours, seen like a dollhouse from above. The rooms are laid out in workflow order, so the office reads as the pipeline, left to right. The look is low-poly, flat-shaded, matte and toy-like. There are no textures; colour comes from vertex or material colour only.

**Style key.** theme.yaml says `style: pixel-startup`. I propose `style: lowpoly-studio`, because pixel art does not fit a 3D scene. Fang decides.

**Palette.** I keep theme.yaml's five tokens and add the ones the scene and HUD need. These are proposed additions to `theme.yaml`, for Fang or Sebastian to apply (I edit only this task file):

| token | hex | used for | contrast (WCAG) |
|---|---|---|---|
| floor (existing) | #2b2d42 | floor slab, dark base | n/a |
| wall (existing) | #8d99ae | low walls, idle icon in HUD | 4.69 on floor |
| accent (existing) | #53BA7E | working ring, PASS check, done | 6.82 on panel |
| warn (existing) | #f4a261 | **waiting on Merwyn only**: beacon, door light, Needs-you pill | 7.99 on panel; 6.54 on floor |
| bad (existing) | #e63946 | blocked or rejected tag fill in 3D (non-text) | 3.95 on panel: passes 3:1 for non-text, fails for small text |
| bad_text (new) | #ff6b6b | red words in the HUD and ticker | 5.94 on panel |
| bad_tag (new) | #c1121f | HTML red tag background, white text on it | white on it: 6.22 |
| panel (new) | #1d1e2c | HUD panels, name tags (at 92% opacity) | n/a |
| text (new) | #f2ede4 | HUD text (warm off-white) | 14.13 on panel |
| text_dim (new) | #9aa0b4 | secondary HUD text, timestamps | 6.33 on panel |
| rug (new) | #353850 | room floor zones, one step up from floor | n/a |
| wood (new) | #7d6650 | desks, door, shelves (low saturation) | n/a |
| paper (new) | #efe6d2 | task cards, speech bubbles (text on it: panel colour, 14:1) | n/a |
| skin (new) | #e0b48f, #c68e65, #8d5a3c | heads, assigned per agent below | n/a |

**Amber is reserved.** No other surface may sit in hue 15 to 45° above 40% saturation. This is why desks are wood #7d6650 rather than a warm orange, and Emmy's sticky notes are pastel rather than orange. If amber turns up anywhere except the door and waiting agents, the glance breaks.

**Lighting.** Use cheap lighting with no shadow maps:
- `HemisphereLight(sky #fff1e0, ground #2b2d42)` for warm fill from above and cool from below.
- One `DirectionalLight(#ffe2c4)` from front-left-high, position (−8, 14, 10) relative to the office centre, as a late-afternoon key.
- Use `MeshLambertMaterial({flatShading: true})` everywhere for the faceted look and low cost.
- A soft dark disc under each agent (blob shadow, #000 at 25% opacity, radius 0.4) grounds the avatars without a shadow map (playbook 4: baked or fake shadows instead of a dynamic map).
- Intensities depend on the three.js version's light units, so Sebastian tunes them on screen.

**Type (HTML overlay only).** There is no web font, because only scripts are allowed from the CDNs (Approvals 1).
- UI: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
- Numbers, times, fps and task ids: `ui-monospace, "SF Mono", Menlo, Consolas, monospace` with `font-variant-numeric: tabular-nums`.

| role | size / weight |
|---|---|
| Needs-you pill | 16px / 700 |
| HUD strip names, controls | 13px / 600 |
| Ticker lines | 12px / 400; time in text_dim |
| Name tags in 3D | 11px / 600, panel bg, 1px border in the agent's body colour, radius 4px |
| Card labels (T-043) | 11px mono / 700, panel colour on paper |
| Speech bubbles | 12px / 500, panel colour on paper, max 2 lines, max width 180px |

### 3. Floor plan

The grid is 1 unit = 1 m. The office runs x 0 to 24 (left to right) and z 0 to 16 (back wall to open front), with the slab at y = 0. Back-row rooms have low cut-away walls (1.2 high) so the camera sees in. The back wall is 2.4 high and holds Merwyn's door. The front row has no walls; its rooms are rug zones with a floor label.

```
 z=0  ████████████████████ back wall (2.4 high) ███[DOOR]████████████████████
      | Product room | Design wall   | Merwyn's | Workshop     | QA lab      |
      | (spec)       | (design)      | door     | (build)      | (review)    |
      |  Emmy        |  Fang  Dinda  | ◆◆◆ slots|  Sebastian   |  Cahyani    |
      |              |               |   Wulan  |              |             |
 z=7  +----D---------+------D--------+----D-----+------D-------+------D------+   D = doorway 1.6 wide
      ============== corridor, walk line z = 8 ==================================
 z=9  +-------D-----------------+---------D------------+----------D-----------+
      | Lobby / Backlog (todo)  |   Meeting table      |  Archive (done)      |
      |  Janice   card board    |   (round, 4 seats)   |  April   shelves     |
 z=16 +------------- open front, nearest the camera -------------------------+
      x=0                       x=9                    x=15                   x=24
```

| room (theme id) | x range | z range | doorway node (on corridor) | notes |
|---|---|---|---|---|
| Product room (product) | 0–5 | 0–7 | (2.5, 8) | Emmy's desk, a board of pastel sticky notes on the back wall |
| Design wall (whiteboard) | 5–10 | 0–7 | (7.5, 8) | a whiteboard along the back wall at z 0.3; two desks |
| Merwyn's door (corner) | 10–14 | 0–7 | (12, 8) | a wood door centred in the back wall at (12, 0); amber light strip above it; three waiting slots |
| Workshop (workshop) | 14–19 | 0–7 | (16.5, 8) | Sebastian's desk, workbench |
| QA lab (lab) | 19–24 | 0–7 | (21.5, 8) | Cahyani's desk, small test bench |
| Lobby / Backlog (lobby, hub) | 0–9 | 9–16 | (4.5, 8) | Janice's desk, a card board of todo cards |
| Meeting table | 9–15 | 9–16 | (12, 8) | round table r 0.9 at (12, 12.5) |
| Archive (archive) | 15–24 | 9–16 | (19.5, 8) | April's desk, shelves along x = 23.7 |

Merwyn's door sits at the top centre of the frame. It is the middle of the pipeline and the one spot the camera never crops (section 7).

**Desks** (desk centre; the agent sits on the corridor side, facing the back wall):

| agent | desk (x, z) | room |
|---|---|---|
| Janice (pmo) | (3, 12) | lobby |
| Emmy (pm) | (2.5, 3.5) | product |
| Fang (architect) | (6.5, 3.5) | whiteboard |
| **Dinda (designer)** | (8.8, 3.5) | whiteboard |
| Wulan (compliance) | (13.2, 4.8) | corner, side-on beside the door, as compliance reports to Merwyn |
| Sebastian (engineer) | (16.5, 3.5) | workshop |
| Cahyani (reviewer) | (21.5, 3.5) | lab |
| April (curator) | (20, 12.5) | archive |

- **Waiting slots** at Merwyn's door: (11, 1.3), (12, 1.3), (12.9, 1.3), facing the door. A fourth waiting agent queues at (11, 2.3).
- **Meeting seats:** (12, 11.3), (13.2, 12.5), (12, 13.7), (10.8, 12.5). If more than 4 agents join, extra agents stand on a ring of radius 1.8.
- **theme.yaml needs a Dinda desk.** It lists 7 desks and has none for Dinda. Proposed line: `- { agent: designer, label: Dinda, room: whiteboard, sprite: designer }`.

**Paths.** Agents walk on a waypoint graph, not with pathfinding: desk → own doorway node → along the corridor line z = 8 → target doorway node → target spot. Front-row doorways connect at z = 9 and back-row doorways at z = 7. Agents turn to face their heading over 0.15s. If two walkers would overlap on the corridor, the later one offsets to z = 8.5, which is enough at 8 agents.

### 4. Avatars

Each avatar is built from primitives only and stands about 1.1 high. The body is a `CapsuleGeometry(0.28, 0.45)` and the head an `IcosahedronGeometry(0.22, 1)`, which gives the low-poly look. Both geometries are shared by all agents. The silhouette comes from one hair or hat shape plus one accessory, so each agent reads even as a dark shape. Body colours mark **identity only** and avoid the status hues (no greens near accent, no orange or red). State is never shown on the body colour.

| agent | body | skin | hair / hat (silhouette) | accessory (primitives) | height |
|---|---|---|---|---|---|
| Janice (pmo, chief) | #4361ee blue blazer | #c68e65 | short bob: half-sphere over head | **clipboard**: box 0.28×0.36×0.03 in wood + small clip box, held at chest | 1.15 |
| Emmy (pm) | #c77dd9 orchid | #e0b48f | ponytail: small sphere behind head | **sticky notes**: 3 squares 0.1 (#fdf0a6, #a8dadc, #f7cad0) on her hand; more on her wall board | 1.10 |
| Fang (architect) | #1f7a99 deep cerulean | #e0b48f | flat-top: short box on head | **marker**: cylinder 0.03×0.2, #22304a with a cerulean cap; plus glasses as two thin boxes | 1.18 |
| Sebastian (engineer) | #4b3f72 indigo + light apron (#d9d4c7 box on front) | #8d5a3c | cap: half-sphere + brim box, brim backwards | **wrench** in hand (two boxes + a short cylinder); an open laptop on his desk | 1.12 |
| Cahyani (reviewer, qa) | #eceae4 lab-coat white | #c68e65 | short hair: half-sphere | **magnifier**: torus ring r 0.08 (#22304a) + cylinder handle | 1.08 |
| Wulan (compliance, officer) | #8f9a62 muted olive uniform | #e0b48f | officer cap: flat cylinder + brim, white top | **shield badge** on chest (6-sided flat cylinder, #d9d4c7) + a **stamp** on her desk (cylinder + knob) | 1.12 |
| April (curator, librarian) | #7b5e57 cardigan brown | #8d5a3c | bun: small sphere on top | **book**: box 0.22×0.28×0.06, cover #3d2f2b with a paper-colour page edge | 1.06 |
| Dinda (designer) | #e7a3c4 pastel pink | #c68e65 | **beret**: flattened sphere tilted 15° | **palette**: flat cylinder 0.18 in wood with 3 dots (#4361ee, #c77dd9, #efe6d2) + pen | 1.04 |

**Name tags** are HTML, projected to the head top plus 0.45. They show the full name on desktop and initials on phones, except for the focused agent and waiting agents, which always show the full name. Tags fade to 50% opacity behind a focused agent's card.

**Task card.** A shared `BoxGeometry(0.34, 0.02, 0.24)` in paper colour with an HTML label `T-043`, 11px mono. It lies flat on the desk when working and is held at chest height when walking. Each agent carries at most one card. If an agent holds more, the label reads `T-043 +1`.

### 5. States and their visuals

Every state has colour **plus** a shape or position (playbook 5: never colour or motion alone). The shapes are the same in 3D and in the HUD icon.

| state | HUD icon (shape) | 3D look | ambient motion (full) | reduced motion |
|---|---|---|---|---|
| **waiting on Merwyn** (designed first) | ◆ amber diamond | The agent stands at a door slot, facing the door. An amber emissive **octahedron** (r 0.2) floats 0.5 above the head with an amber **floor ring** (r 0.5) under the feet. The door's light strip glows amber. A card with the task id is held up. The name tag gets an amber border and a ◆. | beacon: scale 1 → 1.15 → 1 over 1.2s, easeInOutSine, plus a 6s slow spin; ring opacity 0.9 ↔ 0.45 on the same beat. That is 0.8 pulses per second, under the WCAG 2.3.1 limit of 3 per second. Purpose: attention. | beacon, ring and door strip are static at full brightness; nothing else changes |
| **blocked / rejected** | ⬣ red octagon | A red octagon tag (bad #e63946, 6-sided flat cylinder r 0.16) is pinned on the agent's card and floats over the desk. An HTML word on bad_tag: "Blocked" or "Rejected". | the tag shakes once, ±0.05 over 0.3s, when the state starts, then stays still. Purpose: attention without nagging. | no shake |
| **discussing** | 💬 speech bubble (an SVG rounded rectangle with a tail, not an emoji) | Agents sit at the meeting table, turned to each other. Paper speech bubbles (HTML) alternate above the speaker. | speaker leans 5° forward; listener nods (head ±4°, 0.6s) once per line. Purpose: who is speaking. | no lean or nod; the bubble just appears and the speaker's tag gets a 2px underline |
| **walking** | → arrow | Agent on a path, holding a card labelled T-xxx. | walk cycle: body bob 0.04 at 2 steps per second, arm (accessory) swing ±10°. Purpose: continuity (where the work goes). | teleport (see section 8) |
| **working** | ● filled circle | Agent at the desk, card flat on the desk with its label, laptop or tool open. A green **accent ring** (r 0.45, 60% opacity) on the floor. | typing loop: hands or accessory dip 0.02 at 4 per second; head tilts ±3° every 3s. Purpose: shows it is alive and busy. | ring and card static, no loop |
| **idle** | ○ hollow circle (wall grey) | Agent at the desk, no card, no ring. | breathing: body scale-y 1 ↔ 1.015 over 4s, plus a small look-around every 8 to 12s at a random offset. Purpose: it is a living office, kept below notice. | none |
| **done** (task-level, a short beat on the curator) | ✓ check | The card is filed in an Archive shelf slot and stays there as a spine labelled with the task id (the archive fills up across the replay). | see `merged` in section 6 | static ✓ badge on the shelf for 3s |

**State priority** when one agent has two at once: waiting > blocked > discussing > walking > working > idle. The highest one is shown and the strip sorts by the same order. Ties sort by time in state, longest first.

**Speech-bubble lines** must come from the fixture's `lines`, not be invented. Real candidates from Sprint 3, for Fang's fixture:
- T-043: Fang: "Please check the ask/block split." Wulan: "PASS, with conditions." (both from T-043 Design and Review log)
- T-043 Q1: Emmy: "Which blocks become ask?" Janice: "Only clear write rules." (T-043 Spec and Approvals)
- T-045: Janice: "Does any other file restate B2?" Fang: "No other file restates B2." (T-045 Approvals and Design)
- T-044: Cahyani: "PASS — 148 tests OK." (T-044 Review log)

Bubbles have a maximum of 48 characters and end in "…" if longer. Each bubble shows for max(1.6s, 0.05s × characters), capped at 3.5s at 1x, and lines are not shown at the same time.

### 6. Events v0 and their animations

Fang owns the log format. These are the event types I need an animation for; each one maps to one entry. If Fang renames any, keep one row per type. Durations are at 1x and scale with playback speed. Walks move at 2.2 units/s, and any single walk is capped at 4s by raising the speed, so long trips do not stall the replay. Easing: walks use easeInOutSine over the first and last 0.25s and run linear between.

| event (fields I need) | animation (full motion) | duration / easing | purpose | reduced motion |
|---|---|---|---|---|
| `step_started` {agent, task} | agent sits; card placed on desk; working ring fades in | 0.3s, easeOutCubic | attention: what is active | ring and card appear instantly |
| `stage_changed` {task, from, to} | the card's icon on the room board moves to the new room's board; the target room's rug brightens 15% | 0.4s easeOutCubic; rug 0.6s in and out | relationship: the task is in a new stage | the rug highlight shows for 1s, no glow animation |
| `handoff` {task, from_agent, to_agent, to_stage} | from_agent stands, picks up the card (0.25s), **walks to to_agent's desk** carrying the card, hands it over in a small arc (0.4s, easeOutBack), then walks back. to_agent starts working. | walk at 2.2 u/s, ≤ 4s each way | continuity: where the work went (the Spec's must-have) | from_agent and card teleport to the to_agent's desk; the card sits there with its label; from_agent teleports back. Destination tile outline for 1s. |
| `discussion` {agents[2–4], task, lines[]} | agents walk to the meeting seats; bubbles play the lines in order; agents walk back to their desks (or to the next event's place) | walks as above; bubbles per section 5 | relationship: who talks to whom about what | teleport to seats, bubbles appear one at a time with no scale-in, teleport back |
| `needs_merwyn` {agent, task, reason} | agent walks to the next free door slot holding the card; when they arrive, the beacon drops in from 0.6 higher (0.35s, easeOutBack), the floor ring and door light turn on, the Needs-you count increments, and the tab title becomes "(1) needs you · AI Office". An aria-live announcement fires. | walk ≤ 4s, then 0.35s | attention: the one thing Merwyn must not miss | teleport to the slot, beacon static (no drop), everything else identical |
| `merwyn_answered` {agent, task, answer} | beacon shrinks and fades (0.3s, easeInCubic); agent walks back to the desk and resumes | 0.3s + walk | continuity: the wait cleared | beacon removed, agent teleports |
| `review_pass` {task, agent} | Cahyani raises her magnifier, a green ✓ stamps onto the card (scale 1.3 → 1, 0.25s, easeOutBack) | 0.6s total | closure for the stage | ✓ appears static |
| `review_reject` {task, agent, reason} | a red octagon tag snaps onto the card with one shake; the card is carried back to the Workshop (a handoff to the engineer) | 0.3s, then handoff timings | attention: work went backwards | tag static; teleport |
| `compliance_result` {task, verdict: PASS \| PASS_WITH_CONDITIONS \| BLOCK} | Wulan stamps the card: green ✓ for PASS, ✓ with a small amber dot for conditions (the dot is not the diamond, so it does not read as waiting), red octagon for BLOCK. A BLOCK is a human gate, so the log must also emit `needs_merwyn`. | stamp down 0.2s, up 0.2s | closure / attention | stamp result appears static |
| `blocked` {agent, task, reason} | red octagon tag on the agent's card plus the shake; agent stays put | 0.3s | attention | static tag |
| `merged` {task, pr} | Janice stamps the card "#20" (0.4s), hands it to April (handoff), April files it into a shelf slot (0.5s arc), does a 0.15 hop (0.3s, easeOutQuad), and 12 paper or accent confetti quads burst from the shelf (0.8s, gravity, fade) | about 2.5s plus the walk | closure: something finished (the one celebration) | card appears on the shelf; static ✓ badge for 3s; no hop or confetti |
| unknown type | nothing in 3D; the ticker shows "Unknown event ‹type› skipped" in text_dim | – | – | same |

**Playback clock.** The Sprint 3 log has no real timestamps (Approvals 4), so the clock is synthesised.
- Events for one agent run in series. Events for different agents may overlap.
- At 1x, gaps longer than 3s are compressed to 1.5s, so the replay never sits still.
- The full Sprint 3 replay should last 2 to 4 minutes at 1x.
- At 2x and 4x, all durations divide by the speed, except that the waiting-beacon pulse stays at its 1.2s period. Attention cues are not sped up.

### 7. HUD overlay (HTML, not 3D)

- **Needs-you pill** (top left). With waiting agents: amber fill, panel-colour text (7.99:1), a ◆ icon and "1 needs you"; clicking it focuses the first waiting agent. With none: a panel fill and text_dim "Nobody needs you". The count is never hidden.
- **Agent strip.** 8 segments, each a `<button>`.
  - Each shows a 4px left bar in the state colour (wall grey for idle and walking, accent, warn, bad, white for discussing), the state icon (section 5 shapes), the name and the task id held, e.g. "◆ Fang · T-043".
  - Segments are sorted attention-first. When the order changes, a segment slides to its new place over 200ms easeOutCubic (FLIP); with reduced motion it jumps.
  - Re-sorting happens at most once every 2s, so the strip does not twitch during busy stretches.
  - Clicking a segment does the same as clicking the agent.
- **Ticker.** The last 8 events, newest on top, each with time (mono, text_dim), icon and a sentence such as "Fang → Sebastian · T-043 to build". needs_merwyn lines carry an amber 2px left rule; reject and block lines are in bad_text. New lines slide in over 150ms (reduced: appear).
- **Playback bar.**
  - Play / pause.
  - Speed as a segmented 1x / 2x / 4x control.
  - A scrub slider with event markers: amber ◆ ticks for needs_merwyn, red for reject or block, green for merged. Dragging the scrub rebuilds the state at that time instantly, with no animation.
  - The synthesised clock is labelled "(synth)".
  - Motion: Full / Reduced. It defaults from `prefers-reduced-motion` and the choice is kept in localStorage if the artifact allows it; otherwise it lasts for the session only.
  - "Follow action" on / off (section 8).
- **fps readout** (bottom right). Mono, 11px, text_dim: "58 fps · 74 calls". It updates twice per second and turns bad_text below 50. It is always on, for Cahyani's 60-second test; Fang may hide it behind a `?debug` flag later.

### 8. Camera and interaction

- **Projection.** `OrthographicCamera`, fixed angle, azimuth 30° from the front, elevation 40°: offset from target = R·(−0.383, 0.643, 0.663). The pipeline reads left to right almost level and the back wall with Merwyn's door sits at the top. I chose this over true 45° iso because at 45° the pipeline runs diagonally and room labels collide. The frustum fits the 24×16 slab plus 1 unit margin and refits on resize.
- **Auto-framing ("Follow action").** On by default.
  - On a new active event, the camera eases its target toward the event's centroid by at most 25% of the view and zooms by at most 1.3x, over 0.8s easeInOutCubic.
  - It returns home 4s after the last event.
  - **Merwyn's door and every waiting agent stay in frame at all times.** If the framing would crop them, it zooms out instead.
  - It is suspended for 10s after any user pan or zoom, and while an agent is focused.
  - Reduced motion: no auto-framing; the camera stays home (camera motion is the most likely to bother people with vestibular sensitivity).
- **Focus.**
  - Clicking or tapping an agent raycasts against a shared invisible hit capsule (r 0.5, larger than the body, for touch). The camera eases to centre the agent at 1.6x over 0.6s (reduced: cut).
  - A side card opens with the name, role and personality from org.yaml, the current state with its icon, the task held and how long it has been held, and the agent's last 3 events.
  - The card closes with Esc, × or a click on empty floor; the camera then returns home.
  - Desktop: the card overlays the ticker column. Phone: it is a bottom sheet.
- **Touch.** Tap focuses. One-finger drag pans, clamped to the slab. Pinch zooms between 1x and 2.5x. Double-tap goes home.
- **Keyboard.**
  - Tab order: pill → strip → playback bar.
  - Space toggles play / pause; ← and → step one event; 1, 2 and 4 set the speed; M toggles motion; F toggles follow; Esc closes the card.
  - The canvas is `role="img"` with an `aria-label` that updates on state change, e.g. "AI office. 1 agent waiting for you: Fang, T-043."

### 9. Mobile layout, under 600px

```
+------------------------------+
| ◆ Fang is waiting · T-043  > |  amber banner, full width; only when the count is above 0
+------------------------------+
| ◆F ⬣S 💬E 💬W →J ●C ○A ○D     |  8 chips, 40×44px each, icon + initial
+------------------------------+
|                              |
|   3D office, fitted to width |
|   (Follow action on)         |
|                              |
+------------------------------+
| 14:20 → Fang to Merwyn's door|  latest event, tap opens ticker sheet
| ▶  1x  ───●────◆───   ⚙      |  64px bar; ⚙ holds Motion, Follow, fps
+------------------------------+
```
Touch targets are at least 44px. That is above WCAG 2.2 SC 2.5.8's 24px minimum; this source is not in my playbook yet, so April may want to add it. Name tags show initials (section 4). The pixel ratio cap stays at 1.5.

### 10. Empty, loading and error states

| state | what shows |
|---|---|
| **Loading** (three.js not yet ready) | The HUD renders at once from inline data: pill "Nobody needs you", 8 strip segments in idle grey, and centred text "Opening the office…". No spinner, so no motion. |
| **Empty** (fixture has 0 events) | The office is drawn with all 8 agents idle at their desks. The ticker reads "No events to replay. The office is quiet." and play and scrub are disabled. |
| **3D failed** (CDN blocked, the Spec's first risk; WebGL missing; or three.js not loaded within 8s) | The canvas area shows "The 3D view could not load. The status below still works." and the reason in text_dim ("three.js from cdnjs did not arrive" or "WebGL is not available"). **The HUD keeps replaying the fixture**: strip, pill and ticker, so Merwyn's question is still answered without 3D. |
| **Malformed log lines** | Bad lines are skipped and the rest plays. The ticker's first line becomes a bad_text ⬣ "2 lines skipped (line 14, line 31)", with details in the console. If every line is bad, the Empty state shows with that message. |

### 11. Performance budget (8 agents, laptop, at least 50 fps for 60s)

| item | budget / rule |
|---|---|
| draw calls (`renderer.info.render.calls`) | **≤ 120** in a busy frame; aim for about 80 |
| triangles | ≤ 60k (playbook 4: minimise polygons) |
| static office | Merge geometry by material into **≤ 12 meshes** (playbook 4: join geometry to cut draw calls). For repeated furniture (8 desks, chairs, shelves, 4 meeting seats), use core `InstancedMesh` if Fang prefers to avoid the BufferGeometryUtils addon. |
| avatars | Shared geometries (body, head, hair shapes, ring, beacon, card, blob shadow). One `MeshLambertMaterial` per colour, cached by hex: **≤ 30 materials** in the whole scene. About 6 meshes per agent comes to about 48 calls, which is within budget, so no avatar instancing (A9). Playbook 4's "update far characters less" is not needed at 8 agents. |
| shadows | **No shadow maps.** Blob shadows go in one `InstancedMesh` (1 call). |
| confetti | One `InstancedMesh` of 12 quads, created once and reused. |
| renderer | `antialias: true` (edges matter at low poly; playbook 4 says decide per scene). `setPixelRatio(Math.min(devicePixelRatio, 1.5))`. If fps stays under 45 for 3s, drop to 1.0 and show "· low res" after the fps figure. |
| HTML labels | At most 8 tags, 4 bubbles and 8 card labels. Move them with `transform: translate3d` only, with no layout reads in the loop. Hide labels outside the view. |
| loop | Use `requestAnimationFrame`, which pauses itself in a background tab. When paused with reduced motion on, render only on change. |
| lights | 2 (hemisphere + directional), no others. Beacons use emissive material, not point lights. |

### 12. Accessibility check

- **Contrast** (computed with the WCAG formula, values in section 2):
  - Text on panel ranges from 5.94:1 to 14.13:1.
  - Amber pill text is 7.99:1.
  - `bad` #e63946 is 3.95:1 on panel. That passes for non-text (3:1) but fails for small text, so red words use bad_text #ff6b6b (5.94) and red tags use white on #c1121f (6.22).
- **Not colour alone** (playbook 5). Each state has its own shape in 3D and in the HUD: ◆ waiting, ⬣ blocked, 💬 discussing, → walking, ● working, ○ idle, ✓ done. Waiting also has its own **position** (at the door). Amber vs green, and amber vs red, are weak pairs for red-green colour blindness. The diamond, octagon and circle shapes carry that difference.
- **Reduced motion** (playbook 5; WCAG 2.3.3; techniques C39 for the CSS and SCR40 for the render loop via `matchMedia('(prefers-reduced-motion: reduce)')`, re-checked on change, plus the in-page toggle). Every animation in sections 5 and 6 has its reduced version next to it. The sum of the reduced mode:
  - teleport instead of walk;
  - no bob, breathing, typing, nods or shake;
  - beacons, rings and the door strip static but fully visible;
  - no camera easing or auto-framing;
  - no confetti or hop, a static ✓ instead;
  - HUD reorders and ticker lines jump into place.
  Status stays fully readable (Spec Done-when 5).
- **Flashing.** The only pulsing element is the beacon, at 0.8 pulses per second, under 3 per second (WCAG 2.3.1).
- **Keyboard and screen reader.** Everything the canvas shows is also in the HUD buttons and ticker. The canvas has a live `aria-label`. One `aria-live="polite"` region announces **only** needs_merwyn and merwyn_answered, so it is not too chatty.
- **Touch.** Targets are at least 44px (section 9).

### Open questions
1. Event type names and fields: does Fang's log v0 use the names in section 6? If he renames them, keep one animation row per type. Fang.
2. The Sprint 3 history has no real `needs_merwyn` moment. Sprint 3 says none of its tasks were behind a human gate; T-043 Q1 was answered by Janice for Merwyn. To show the waiting state, the fixture needs one. Candidates: T-043 Q1 shown as a wait for Merwyn "(via Janice)", or a waiting event for T-002, which sprint-03 lists under "Waiting on Merwyn". The fixture must be labelled honestly either way. Fang to choose, Janice to confirm it is a fair replay.
3. Adding a Dinda desk, the new palette tokens and `style: lowpoly-studio` to theme.yaml (section 2 and 3 proposals): Fang accepts or changes; Sebastian applies.
4. Can the artifact keep the Motion choice in localStorage? If not, it lasts for the session only. Janice, from the artifact pages guide.
5. Is auto-framing on by default the right call for a glance view? I chose on, with the door always in frame. Merwyn can say if any camera motion distracts him; it is one toggle.

— Dinda (designer)

## Approvals (PMO)
Spec approved 25 Nov 2026. Answers: (1) CDN: the artifact page rules (checked by Janice in the artifact server's pages guide) allow scripts from cdnjs.cloudflare.com, cdn.jsdelivr.net/npm and unpkg.com; fetch to other hosts is blocked. Use a pinned three.js from cdnjs. The page must carry its theme and fixture data inline (or as relative files of the same artifact) — no fetch to other hosts. (2) 50 fps with 8 agents accepted, measured by an in-page fps readout. (3) Fixture hand-written vs generated: Fang's call. (4) A synthesised clock is fine if documented. (5) 8 agents = the seven plus Dinda. Dinda writes "## UX design" before Fang finalises Design. — Janice (pmo)

Janice (pmo), 25 Nov, answers to Dinda's open questions: (1) The fair "waiting on Merwyn" moment in Sprint 3 is real: before the sprint, Janice asked Merwyn three questions (financial terms in partner-writing, how agents touch prod, T-002) and he answered on 25 Nov 22:44 (sprint-03.md "Decisions recorded"). Open the fixture with Janice at Merwyn's door (needs_merwyn) and merwyn_answered, then T-045/T-043 flow from those answers. (2) Event names: Fang's call. (3) Dinda's desk is already on main from T-047 (branch rebased); a style rename is out of scope. (4) Motion setting may be remembered in localStorage inside try/catch; the OS prefers-reduced-motion always wins. (5) Follow-action on by default, off under reduced motion. Section order: keep as written.

Janice (pmo), 25 Nov: Design accepted, moved to build. Answers to Fang's open questions: (1) CDN reachability can't be tested from here, so remove the risk: the page loads `./three.min.js` first (a sibling file, not committed; fetched from npm three@0.128.0 per engine/app/README.md and published beside the page as an artifact file), then falls back to cdnjs r128, unpkg, jsdelivr at 0.128.0. npm confirms three@0.128.0 exists. (2) 50 fps: Cahyani records a software-GL smoke result (frames render, governor works); the real laptop fps reading is taken by Merwyn from the in-page readout and recorded at sprint close, not a blocker for review.

## Build notes
Artifact (Done-when 8): published by Janice 26 Nov from 042190b as a private artifact, index.html only; three.js loads from cdnjs r128 (the ./three.min.js sibling is not published). https://claude.ai/artifact/CkB5c3hEKfaK61kUuUjMku — render not yet confirmed by Merwyn.

PR #25, branch `t-048-3d-office`.

**What changed**
- `engine/schema/events.md` (log v0), `engine/runtime/events.py` (parser, data rule, sequence rules), `events <office> <log>` in `engine/runtime/__main__.py`.
- `scripts/office_app.py` (generator, `--check`); `engine/app/office.template.html` (1396 lines, 93 KB) -> `office.html` (104 KB, limit 200 KB); `engine/app/fixtures/sprint-03.jsonl` (45 events, 0 errors, 0 warnings); `engine/app/README.md`.
- `theme.yaml`: Dinda's palette tokens, `rect` per room, `at` per desk, `door`, meeting room; `engine/schema/office.md` documents them.
- Tests: `tests/test_events.py` (18), `tests/test_office_app.py` (13, includes the pure core run under node), `tests/fixtures/events-all-types.jsonl` (synthetic, all 11 types).
- The page: warm low-poly studio (one baked vertex-coloured mesh for the office, 8 distinct avatars with hair/hat, accessory, name tag), eased waypoint walking with a T-xxx card, hand-over arc, discussion at the meeting table with speech bubbles, amber beacon + beam + floor ring + door light + diamond for "needs Merwyn", red hexagon tag for blocked/rejected, confetti on merge. HUD: Needs-you pill, agent strip sorted attention-first (FLIP, 2 s throttle), ticker (last 8), play/pause, 1x/2x/4x, scrub with markers, fps and calls readout, Motion and Follow toggles, focus card, keyboard, aria-live. Phone (<600px): amber banner, 8 chips, one-line ticker, settings sheet.

**How to verify**
```
python -m unittest discover -s tests            # Ran 197 tests in 5.7s ... OK
python scripts/office_app.py ai-office --check  # office.html: up to date (101 KB, 45 events)
python -m engine.runtime events ai-office engine/app/fixtures/sprint-03.jsonl   # 45 events kept, 0 errors, 0 warnings
python -m engine.runtime validate ai-office     # ai-office: OK - 8 agents, 5 stages, 48 tasks, 16 skills
```
Rendered: commands in `engine/app/README.md` (three@0.128.0 from npm, `python -m http.server`, headless Chrome with SwiftShader). Screenshots (not committed) in `/tmp/t048-shots/`: `door.png` (t=2, Janice at Merwyn's door, beacon, 1280x800), `reduced.png` (same, `motion=reduced`), `talk.png` (t=58.5, discussion with bubble), `walk.png` (t=29.4 playing, Janice walking with T-043), `end.png` (t=198, three tasks archived), `phone.png` (390x844), `phone360-talk.png` (360x740). Console: no JS errors in any run; the only CONSOLE lines are Chrome's software-GL "GPU stall due to ReadPixels" messages. Playback length at 1x: 198.6 s.

**Deviations from the design**
1. `MeshLambertMaterial` has no `flatShading` in r128 (console warning on the first run). Facets come from non-indexed geometry with recomputed face normals instead.
2. Avatars are drawn 1.3x the sizes in Dinda's table (readability at 1280 px); relative proportions are unchanged.
3. Agents sit behind their desk facing the camera (not on the corridor side facing the back wall), otherwise the viewer sees only backs.
4. Phone portrait (aspect < 0.8) turns the camera azimuth from 30 to 62 degrees so the office fills the width; Dinda's design had no rule for this.
5. The stage (3D area) sits between the HUD bars and the ticker instead of full bleed behind them, so nothing covers the office.
6. `merwyn_answered` releases a task still in `todo` (no one holds an unstarted task); documented in events.md. Needed so Janice does not hold T-002 for the rest of the replay.
7. Timeline: an event's start is also pushed back by the DUR estimate of earlier events of the same agents, and a `stage_changed` is shown together with the handoff that follows it.
8. `tests/test_dryrun.py` import allowlist for `engine/runtime` gains `json` and `datetime` (events.py parses JSON and ISO times; still no network or SDK).
9. Blob shadows are one InstancedMesh, one speech bubble at a time (lines never overlap), the beacon is drawn about 2x Dinda's radius so it reads at a glance.
10. The fixture was written by a throwaway script (not committed) to get the JSON quoting right; the content is hand-authored from sprint-03.md and the task files.

**Known limits and not verified**
- fps: only software GL here (13-33 fps in headless, meaningless for the 50 fps goal). Draw calls are 46-50, well under the 120 budget. The 60 s laptop reading comes from the in-page readout (Merwyn or Janice, Cahyani records it).
- Artifact render and CDN reachability not tested (CDNs are blocked here); `./three.min.js` must sit beside the page, or the CDN fallbacks must work.
- Reduced mode was checked in a still (`reduced.png`) and the logic, not as a screen recording. Light/dark surroundings: the page paints its own dark background, so both look the same.
- Archive spines are small green blocks on top of the shelf; the walk path to the meeting table's far seat uses a fixed detour.

— Sebastian (engineer)

### Rework 1 (after Review 1 REJECT)
**Safety fix**
- `engine/runtime/events.py`: `_data_hit` now returns the field path and the kind, never the text: `personal-data pattern (16-digit run) in field 'reason'`, `personal-data pattern (email address) in field 'lines[1].text'`, `forbidden term (listed in workspaces.yaml) in field 'reason'`. The data check now runs first on every line (before the `t`/`wall` checks), so a leaky line is always reported as a data-rule problem and never as some other error. New `is_data_problem(message)`.
- `scripts/office_app.py`: any data-rule problem exits 1 and writes nothing, also with `--allow-errors`. Other errors can still be skipped with `--allow-errors`. The page's `console.warn` prints `skipped[].message`, which is now always the sanitised text.
- Tests (200 now, was 197): `test_problem_names_field_and_kind_never_the_value`, `test_cli_never_echoes_personal_data` (events CLI: 16-digit number and email absent from stdout+stderr, exit 1), `test_data_rule_problem_always_exits_1_and_never_echoes_the_value` (office_app by subprocess, with and without `--allow-errors`, plus a malformed line: exit 1, no HTML file, neither string in stdout/stderr or in the built data), and a node assertion that `merged` starts after every earlier event of its task has ended.

**Polish (template)**
- Waiting agent's name tag sits above the beacon (world position head + 1.3), not 46 px below the feet.
- Reduced-motion handoff: the sending agent's tag is moved 62 px down (under the avatar) while the handoff runs, so it no longer overlaps the receiver's tag.
- Follow camera: the active agents' heads (and waiting agents' beacons) must stay inside a margin of 70 px from the screen edge, so tags are not cropped at the left.
- `merged` waits for all earlier events of its task (so it starts after the `review_pass` beat). Replay length changes slightly; nothing else moved.

**Evidence**
```
python -m unittest discover -s tests           # Ran 200 tests in 5.8s ... OK
python scripts/office_app.py ai-office --check # office.html: up to date (102 KB, 45 events)
python -m engine.runtime events ai-office engine/app/fixtures/sprint-03.jsonl   # 45 events kept, 0 errors, 0 warnings
python -m engine.runtime validate ai-office    # ai-office: OK - 8 agents, 5 stages, 48 tasks, 16 skills
python scripts/build_agents.py ai-office       # built 8 agents (no tracked change); board.py ran, board.md discarded
# a log with a 16-digit number and an email:
python -m engine.runtime events ai-office /tmp/leak.jsonl
2: error: personal-data pattern (email address) in field 'reason'
/tmp/leak.jsonl: 0 events kept, 1 error, 0 warnings          (exit 1)
python scripts/office_app.py ai-office --fixture /tmp/leak.jsonl --out /tmp/leak.html --allow-errors
office_app: 1 data-rule problem(s); nothing written. --allow-errors does not skip these   (exit 1, no file)
```
Screenshots re-taken headless from `file://` (not committed), `/tmp/t048-shots2/`: `door.png` (Janice's tag above the beacon at the door), `handoff1842.png` (reduced motion, Janice -> Emmy: two tags apart), `follow.png` (follow on, Emmy's tag at the left edge intact). No JS errors seen.

**Not changed / still open**: phone layout label collisions and separator phone-number patterns (`+62 812-...`) are left for T-027 (see Open questions). The `merged`-after-`review_pass` beat and the follow-camera margin were checked by the node assertion and a still, not on a screen recording.

— Sebastian (engineer)

## Review log
Review 1 of PR #25 (head 46e06e7), 26 Nov 2026: REJECT (one safety fix). Done-when 1–5 and 7 pass with evidence (197 tests OK, parser broken 16 ways with the expected errors, hosts limited to ./three.min.js + cdnjs/unpkg/jsdelivr, 8 s fallback works, fixture wall times match git, needs-Merwyn readable by colour + shape + position, both reduced-motion modes). Done-when 6 fps waived for review (software GL 22–40 fps, 44–50 draw calls; laptop reading owed by Merwyn). Done-when 8 artifact is Janice's step.
Reason: the data rule echoes the value it caught. events.py `_data_hit` returns "personal-data pattern in '<value>'", which reaches the CLI output, office.html's skipped block under --allow-errors (generator exits 0), and the page's console.warn. Fixes: (1) name the field and pattern kind, never the value; (2) office_app must not write a page that fails its own data scan, even with --allow-errors; (3) test that a 16-digit number and an email never appear in stdout, stderr or output HTML.
Notes: waiting agent's tag lands on Dinda's desk; tags overlap in reduced-motion handoff; phone view labels collide; follow camera crops left edge; merged and review_pass start together; separator phone numbers not caught (T-027).
— Cahyani (reviewer), recorded by Janice (pmo)

Review 2 of PR #25 (head 042190b), 26 Nov 2026: REJECT (second; escalated to Merwyn). Fixed: values in string fields (16-digit, email, both, forbidden term, 10-digit) give exit 1 from the events CLI and office_app with and without --allow-errors, nothing written, messages name field and kind only; console.warn only gets value-free messages. 200 tests OK; --check up to date; fixture 45/0/0; all-types 15/0/0; validate and build_agents OK; waiting tag above beacon; reduced-motion handoff tags apart.
Still failing fix (2): the data rule checks string values only, not key names or numbers, and unknown fields are only warnings. "nik": 3171234567890123 (no --allow-errors) exits 0 and the number lands in office.html; an email or 16-digit key is written and echoed in the warning. Fix: scan keys and numbers, or scan the rendered data blob in office_app and refuse to write on a hit; never echo a hit key; tests for both.
— Cahyani (reviewer), recorded by Janice (pmo)

Janice (pmo), 26 Nov: second rejection, so per workflow.yaml escalation (review_rejections >= 2 → human) this waits for Merwyn: (a) back to build for the ~15-line fix and a third review (Cahyani's and Janice's recommendation), or (b) accept with the gap sent to T-027. Not merged. The published artifact (built from 042190b) was read in full by Janice and holds only the Sprint 3 fixture: no company data.

## Decision

## Open questions
- Does https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js resolve and load in the artifact sandbox? Agent proxy returns 403 for all three CDNs, so it is unchecked. Janice, from the main session (curl or stub artifact). Blocking for the artifact Done-when only; build can proceed.
- fps on a real laptop: headless here is software GL. Merwyn or Janice runs the 60 s check on the laptop and reports device + numbers for Cahyani to record. Not blocking for build.
- T-027: phone layout (<600px) label collisions, and a data-rule pattern for separator phone numbers (e.g. `+62 812-3456-7890`), which the 10+ digit-run pattern does not catch. Deliberately left out of T-048 (Cahyani's notes).
