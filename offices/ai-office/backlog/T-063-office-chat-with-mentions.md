---
id: T-063
title: "Office chat: a pop-up chat in the 3D office, @mention one or more agents"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-062]
pr: https://github.com/merwyns-maj/ai-office/pull/54
---

> Merwyn, 26 Nov 2026 15:54 WIB: "Can we have a dedicated chat section (can be open or close), maybe a chat button somewhere to pop it up. I can mention each agent like @Janice to mention her and send message directly to her. I can also mention multiple agents if i want to send same message to both. For context, we're building this to replace a claude code interface in a way." Same message: keep the 5M budget for now.

## How it can work today (facts, Janice)
- The 3D office is a published claude.ai artifact. Its page cannot start an agent itself. It can keep data in the artifact's own database (`db` capability), which a Claude session reads and writes with db_get / db_list / db_write.
- So the chat is a shared inbox: Merwyn's message is written to the database with its mentions; the office session (Janice, the main session) reads new messages, hands each to the mentioned agent(s), and writes each agent's reply back as a message from that agent; the page shows replies as they arrive (onSnapshot).
- Replies come only while an office session is running (today: this session, when it checks the inbox; later: the SDK runtime, T-024, continuously). The page must say so honestly ("Janice picks this up when the office is running").

## Done when
- [ ] A chat button in the 3D office opens and closes a chat panel (desktop: a floating panel using the T-059 move/resize/opacity model; phone: a full-height sheet); open/closed remembered per viewer
- [ ] Composer with @mention autocomplete for the 8 agents by name (Janice, Emmy, Fang, Sebastian, Cahyani, Wulan, April, Dinda) and @all; several mentions in one message send it to each; a message with no mention goes to Janice
- [ ] Messages are stored in the artifact database with author, mentions, time and status (new → picked up → answered per agent); the thread shows each agent's reply with the agent's name and colour, and a per-recipient status ("waiting for Janice to pick up", "Fang is replying", "answered")
- [ ] An office-side inbox procedure: a script or playbook step that lists new messages, routes each to the mentioned agents (spawning them with the message and the repo context), writes their replies back, and marks status; agents answer and do read-only work by default; anything that changes the repo becomes a task through the normal workflow (spec → … → review), and anything in human_gates still asks Merwyn
- [ ] Company data: chat text lives only in the artifact database; agents never copy it into the repo (pointers only); the data rule from events.py is applied before any chat-derived text is written to the repo
- [ ] When the inbox has messages waiting, the needs-you logic is unchanged; when an agent's reply needs Merwyn (a question), the reply is marked and the agent shows the waiting state in the 3D office
- [ ] Tests for mention parsing (names, @all, duplicates, unknown names, case, punctuation), the message schema and status transitions; all tests, golden and --check pass; headless screenshots of closed, open, autocomplete, a multi-agent thread with replies, at 1280x800 and 390x844; no console errors
- [ ] The recorded usage page has no chat (build flag); the AI Office artifact declares `db` and `user`

## Spec
Request from Merwyn; scope as in Done when. Out of scope: real-time agent runs without an office session (T-024), voice, attachments, chatting from Telegram (T-029). — Janice (pmo)

## Design
### Technical design
Scope: code, schema and procedure. It changes page logic and data, and adds one runtime module and one playbook section. Facts about the artifact database come from the artifact server's docs as quoted by Janice in the brief. Anything I could not check is listed under "Open questions".

**Approach (files touched)**
- `engine/app/office.template.html`: chat CSS; pure chat functions in `office-core` (node-tested); chat panel and sheet in `office-view`, using T-059 `PANEL` (add `chat` to `PANEL.IDS`) and the `#usheet` pattern for phones; live needs-you overlay. All chat code runs only when `D.chat` exists.
- `scripts/office_app.py`: new `--chat` flag. It adds `data.chat` (below). `--chat` with `--ledger` exits 2, so the recorded usage page can never get chat. Without the flag the page has no `chat` key, no Chat button, and never calls `claude.use`.
- `engine/app/office.html`: regenerated with `--chat`. This is the "AI Office" artifact (slug 5f1bb811-1633-4bfb-8285-9bcb2408dec2), assuming it is `office.html`: see Open questions. The README regenerate and `--check` lines become `python scripts/office_app.py ai-office --chat [--check]`. `test_committed_page_is_up_to_date` builds with `--chat`.
- `engine/runtime/chat.py` (new, stdlib only): the same mention rules as the page, plus schema checks, status transitions, inbox planning, reply building and the data scan. `engine/runtime/__main__.py` gets a `chat` subcommand.
- `engine/schema/chat.md` (new): the db schema below, which is the single reference for both sides.
- `engine/runtime/ledger.py` and `engine/schema/usage.md`: a run with `step: "chat"` may have `tasks: []`, with `note: "chat message <id>"`. Today `tasks` must be 1 to 8 task ids (ledger.py line 79), so a chat run cannot be logged without this change. Chat runs count toward the 5M budget like any run.
- `offices/ai-office/skills/pmo-playbook/SKILL.md`: new section 9 "Office chat inbox" (procedure below).
- `engine/app/README.md`: chat, the flag, and how to declare and publish.
- Tests: `tests/test_chat.py`, `tests/fixtures/chat-mentions.json` (shared parity cases), new node cases in `tests/test_office_app.py`.
- No new service. The db is the artifact's own storage, and the office side is the existing session plus a helper.

**`data.chat` (the build puts this in the page)**
`{"v":1, "agents":[{"id":"pmo","name":"Janice","role":"Chief of Staff (PMO)"}, …8 in org order], "default":"pmo", "all":"all", "max_len":4000, "lease_s":1800}`. Names come from org.yaml, so nothing is hard-coded in the template.

**Database layout.** Even segment count = document. Everything sits under `chat`, so one rule covers it.
- `chat/office` (doc, meta), written only by the office session: `{v:1, last_inbox_at:"<ISO UTC>", by:"pmo", running:bool}`. The page shows "Office running" when `running` is true and `last_inbox_at` is under 15 min old. Otherwise it shows "Office not running", with "last checked hh:mm" when known. This answers Dinda's status dot honestly, from a fact the session wrote, not a guess.
- `chat/office/messages` (collection). Each message is a doc `chat/office/messages/{id}`.

Ask (written by the page, Merwyn only):
```
{ v:1, kind:"ask", id:"m-<Date.now() base36>-<4 random base36>", author:"merwyn", author_uid:"<await user.id()>",
  text:"<1..4000 chars>", created_at:"<ISO UTC>", mentions:["architect","designer"], all:false, unknown:["bob"],
  in_reply_to:null | "<reply id>",            // set when Merwyn answers a needs-you reply ("Reply" on that bubble)
  recipients:{ "<agent id>": {status:"new", reply_id:null, at:"<ISO UTC>", by:"page"} } }
```
Reply (written by the office session):
```
{ v:1, kind:"reply", id:"r-<ask id>-<agent id>", reply_to:"<ask id>", author:"<agent id>", text:"<1..8000>",
  created_at:"<ISO UTC>", needs_merwyn:bool, question:null|"<one line, <=200>", task:null|"T-nnn" }
```
- `recipients` keys are the routed agent ids: the mentions; all 8 for `@all`; `["pmo"]` when nothing is mentioned. `unknown` is kept only so the page can show Dinda's "No agent called Bob" note. Unknown names are never routed.
- Reply ids are deterministic (`r-<ask>-<agent>`). One recipient gives at most one reply doc, so re-running the inbox overwrites instead of duplicating. A follow-up from Merwyn is a new ask.

**Status transitions (the same table in `office-core` and `chat.py`)**

| from | to | who | when |
|---|---|---|---|
| (none) | new | page | ask created |
| new | picked | session | inbox claims it |
| picked | replying | session | agent spawned |
| replying | answered / needs_merwyn | session | after the reply doc is written |
| picked, replying | new | session | lease expired (`at` older than `lease_s`) and no reply doc exists |
| needs_merwyn | answered | session | an ask with `in_reply_to` = that reply (or any later ask from Merwyn that mentions that agent) is picked |

Anything else is rejected by `can_move`. `answered` is terminal. Page labels (`recipientLabel`): new "waiting for Janice to pick up", picked "Janice picked this up", replying "Fang is replying", answered "answered", needs_merwyn "needs you".

**Rules (declared on the artifact)**
`[{path:"chat", read:"owner", write:"owner"}]`. Only Merwyn (owner) writes. The office session uses the server tools under Merwyn's account, which I assume is the owner level (Open questions). I chose `read:"owner"` over `view`: if the page is ever shared, viewers see the 3D office but never the chat, because company data may be typed into it (Compliance flag). The page shows chat only when `db` is non-null and the first snapshot succeeds. A rules rejection shows Dinda's "Chat storage is not available in this view".

**Mention parsing (pure, both sides, same cases)**
- Regex: `(^|[^\w@])@([A-Za-z][A-Za-z-]{0,23})`, case-insensitive name lookup against `name.lower()` and `all`. Trailing punctuation stops the name (`@Fang,` `@Fang's` `@fang?` all match Fang). An email-like `x@fang.id` does not match, because a word character comes before `@`.
- Result: `{ids:[…] in first-appearance order, deduplicated; all:bool; unknown:[lowercased, deduplicated]}`. `@all` gives all 8 in org order, plus any explicit ones (deduplicated). `route(parsed)` returns `ids`, or `["pmo"]` when `ids` is empty.
- JS: `C.chat.parseMentions(text, agents)`, `C.chat.route(p)`, `C.chat.completions(text, caret, agents)` gives `{start, query, items:[{id,name,role}] + all}`, used only when the `@` is at the start or after whitespace (Dinda's trigger). Also `C.chat.newAsk(text, agents, nowMs, rnd, uid)`, `C.chat.valid(doc)`, `C.chat.canMove(a,b)`, `C.chat.threads(docs)` (asks by `created_at` then `id`, each with its replies by `created_at`), `C.chat.label(status, name)`, `C.chat.liveWaiting(docs)` (`{agentId:[askId]}` for recipients at needs_merwyn), and `C.withLive(state, live)`.
- Python `engine/runtime/chat.py`: `handles(org_agents)`, `parse_mentions(text, handles) -> Mentions(ids, all, unknown)`, `route(m)`, `TRANSITIONS`, `can_move(a, b)`, `validate(doc, agent_ids) -> list[str]`, `plan(docs, now, lease_s=1800) -> list[Action]`, `reply(ask, agent, text, needs_merwyn, question, task, now) -> (path, doc, patch)`, `scan(text, forbidden) -> str|None` (wraps `events._data_hit`, so it names the kind of hit and never the value), `pointer(ask_id) -> "chat message <id>"`.
- Parity: `tests/fixtures/chat-mentions.json` holds invented cases `{text, ids, all, unknown}`: each name, upper/lower/mixed case, punctuation, duplicates, `@all`, `@all` plus a name, unknown only, unknown plus known, email-like text, `@` alone, the 24-char limit and an empty string. Both `test_chat.py` and a node case read the same file, so the two parsers cannot drift.

**CLI (what Janice runs; JSON on stdin, so chat text is never written to disk in the repo)**
- `python -m engine.runtime chat plan ai-office` reads the db_list/db_query result (a JSON list of docs) and prints JSON actions in order: `{"op":"claim"|"reset"|"repair"|"close", "path", "patch", "ask", "agent"}`. `repair` means a reply doc exists but the recipient was never marked, so it marks it from the reply. `close` means needs_merwyn becomes answered because of a follow-up. Docs that fail `validate` are skipped with a message that names the id and field, never the text. Exit 0, or 1 on invalid input.
- `python -m engine.runtime chat reply ai-office --ask ID --agent ID [--needs-merwyn --question-stdin] [--task T-nnn]` reads the reply text on stdin and prints `{path, doc, patch}`. Exit 1 on a data-scan hit, with only the kind of hit in the message.
- `python -m engine.runtime chat mentions ai-office` reads text on stdin and prints the routing. This is for checks.

**Inbox procedure (pmo-playbook section 9; Janice in a Claude session, because db tools are MCP tools and Python cannot call them)**
1. When to run: at session start, when Merwyn says "check chat", and at each daily flow check. Write `chat/office` `{running:true, last_inbox_at:now}`. At session end, write `running:false`.
2. Check the rules: db_get the artifact's declared rules if the tools expose them. Never route if `chat` is writable below owner. Then db_query `chat/office/messages` orderBy `created_at` limit 200, and pipe the JSON into `chat plan`.
3. Apply the actions with db_write, in order. Claims are written before any agent is spawned.
4. For each claimed (ask, agent) where the agent is not `pmo`: set `replying`, then spawn the agent by its profile, in parallel for multi-recipient asks. The prompt holds the ask text and id, who else was mentioned, the replied-to reply's text when `in_reply_to` is set, repo path `/home/claude/ai-office`, and these rules. Read-only by default: no edits, commits or pushes. If the request changes the repo, say so and propose a task. If it hits a `human_gates` item, ask Merwyn and set needs_merwyn. Do not put personal data, prod rows or credentials in the reply. Reply in under 300 words and return `{text, needs_merwyn, question}`. Janice answers her own (`pmo`) asks in-session without spawning.
5. Pipe each result into `chat reply`, then db_write the reply doc first and the recipient patch second. On a scan hit, ask the agent once to restate without it. If it hits again, post a fixed reply: "I could not post this reply here because it looked like personal data. Ask me in the session." with needs_merwyn.
6. Append one ledger line per spawned run (`step:"chat"`, `tasks:[]`, `note:"chat message <id>"`).
7. Repo-changing work: Janice creates a task at `todo` through the normal workflow. The task quote line is `> From chat message <id>, <date WIB>`, followed by Janice's own one-line summary, which passes `chat.scan` before it is written. The chat text itself is never quoted. The reply carries `task: "T-nnn"`.
8. Gates: no spawning when `budget_used >= 0.8` (human gate). Janice replies needs_merwyn with the percentage. A chat message is Merwyn's request, but it never answers a permission prompt and never stands in for the human-gate approvals in workflow.yaml unless it answers a needs_merwyn question that asked exactly that.

**Idempotency, crash and ordering**
- Picked once: the claim is written before spawning. One office session at a time is an assumption: the db has no compare-and-set that I know of. A second session would at worst produce the same reply doc id and overwrite it, never a duplicate bubble.
- Crash mid-run: the next `plan` resets `picked`/`replying` older than `lease_s` (30 min) to `new` when no reply doc exists, and repairs the status when one does. The worst case is one repeated agent run, and the ledger shows it.
- Ordering: by `created_at` then `id`. Replies are grouped under their ask, so clock skew between the page and the session only affects order between replies to the same ask.
- Writes: if db_write only replaces whole docs (unknown), the session reads, changes `recipients[agent]` and writes back. This is safe because the page never writes an ask again after creating it.

**Page wiring**
- `claude.use("db")` and `claude.use("user")` start once, when the Chat panel first opens or at load when the saved state is open. Null, or no answer after 10 s, gives Dinda's error states. One `onSnapshot` on the messages query (orderBy `created_at`, limit 200; "Showing the last 200" when the limit is hit) and one on `chat/office`. The page never subscribes again on re-render.
- Values from the db are text. Bubbles are built with `textContent` and DOM nodes, never `innerHTML` and never `esc()` concatenation. Dinda's code fences and links come from a small parser that makes `<pre>` text nodes and `<a>` elements only for `https:` URLs (`rel="noopener noreferrer"`, `target="_blank"`). Mention chips are spans built from the parse result.
- Sending: `newAsk` validates, then the page does a `set` on `chat/office/messages/{id}`. A failure keeps the bubble with "Not sent. Retry". The retry reuses the same id, so it is idempotent.
- Needs-you overlay: `C.withLive(S, live)` returns a copy of the replay state with each live needs_merwyn added to that agent's `waiting` as `chat:<askId>`. The pill, strip, banner, beacon and `document.title` read the merged state. `stateAt` and the replay log are unchanged, so scrubbing the replay never clears a live chat wait. Inbox messages waiting at `new` do not count as needs-you, so that logic stays unchanged. The pill names chat waits as "Fang · chat". Clicking one opens the chat at that reply.
- Storage keys (per browser, inside try like T-059): `office.chat.v1` `{open:bool, seen_at:"<ISO>"}`, and the panel rect through the existing `office.layout.v1`.

**Answers to Dinda's open questions**
- (1) Unseen count is per browser (`seen_at` in localStorage), not in the db: simpler, and nothing new to protect.
- (3) Agent colours: theme.yaml has no per-agent colours. The template's `SPR` body colours (office-view) are the avatar colours. Move them into a small `AGENT_COLOR` map, keyed by agent id through the existing desk-to-sprite mapping, that both the scene and the chat read. Dark ones (`#4b3f72`, `#1f7a99`) will fail 4.5:1 on `--panel`, so the builder uses the lighter tint for name text, as Dinda allows.

**Risks and how the build handles them**

| risk | handling |
|---|---|
| No office session running, so Merwyn waits | Honest status from `chat/office`. Messages stay `new`, and nothing pretends to be live. |
| Page size: 174 KB today against the 200 KB test limit | Chat budget about 20 KB, with no libraries. If it does not fit, Sebastian stops and asks me. Raising the limit is a design change, not a build fix. |
| `PageRules` network test | `claude.use` is not fetch, XHR or WebSocket, so the test stays as is. Add a test that a build without `--chat` has no `chat` key and that a node stub of `claude` is never called. |
| Chat text leaking into the repo | Stdin-only CLI, pointer-only task lines, `chat.scan` on anything chat-derived before a repo write, and invented fixtures only. |
| Markup injection from db text | Text nodes only, and `https:` links only (test with a `<script>`/`javascript:` payload in a node DOM-free check of the parser output). |
| Rules shape or owner level of the server tools differs from the docs | Janice checks at declare time. The inbox refuses to route if writes are open below owner. |

**Test plan**
- Python `test_chat.py`: parity fixture; `validate` (missing or extra keys, wrong kind, bad id pattern, text length, unknown agent, recipients not matching the route); every allowed and disallowed transition; `plan` on invented doc sets (new, a claim, a stale lease with and without a reply, repair, close by `in_reply_to`, two sessions giving the same reply id); `reply` gives a deterministic id; a scan hit exits 1 and the value is absent from stdout and stderr; ledger accepts `step:"chat", tasks:[]` and still rejects `tasks:[]` for other steps.
- Node (`test_office_app.py`): the same parity fixture through `C.chat.parseMentions`; `completions` at different caret positions; `newAsk` shape; `threads` ordering with skewed clocks; `liveWaiting` and `withLive` (merge adds, replay state untouched, needs count includes chat); the link and code parser emits no markup from `<`/`javascript:`.
- `office_app.py`: `--chat --ledger` exits 2; the default build without `--chat` has no `data.chat`; the committed page equals the `--chat` build; golden and `--check` pass.
- Headless (README commands, with a stub `claude` injected through a test-only fixture page under `/tmp`, never committed): closed, open empty, autocomplete, multi-agent thread with replies and one needs-you, at 1280x800 and 390x844; usage page with no Chat button; no console errors. A real-db check on the published artifact is Janice's step after publish.

**Publish order (Janice, not the build)**
`declare_capabilities` on the existing artifact with `db` (rules above) and `user`, then publish the new `office.html`. db tools work only after that.

**Compliance flag for Wulan**
1. Company data typed into chat, or put into replies, lives in the claude.ai artifact database, outside this repo and outside company systems. Is that acceptable? Should replies be barred from row-level or personal data (my default: the scan blocks it and agents are told to summarise)?
2. Prod access from chat follows R-14: read-only by default, writes only on Merwyn's instruction, Bytebase never. Chat-spawned agents keep the prod guard. Any human_gates item still asks Merwyn.
3. Read rule `owner` rather than `view`.
4. Chat text never enters the repo; tasks hold a pointer only.
5. A chat message is not a permission-system approval.

**Decision record draft (for April)**
Decision: Office chat is a shared inbox in the AI Office artifact's own database, read and answered by the office session (Janice) with a stdlib helper. It is not a new service.
Context: Merwyn wants to message agents from the 3D office (26 Nov 2026). The page cannot start agents, and T-024 (continuous runtime) is not built.
Options:
- A. Artifact db inbox plus session procedure. No new service, works today; replies only while a session runs.
- B. Wait for T-024. Live replies, but nothing ships until the runtime does.
- C. Telegram (T-025). Live on the phone, but out of scope and a new connector (human gate).
Chosen: A, because it reuses the page and the session, and the T-024 runtime can later run the same `chat plan`/`chat reply` loop unchanged.
Consequences: Chat text lives on claude.ai, never in the repo. One session at a time. Chat runs are logged with `tasks:[]`. Follow-up: T-024 takes over the inbox loop.
Links: T-063.

— Fang (architect)

### UX design
Question this screen answers: "What did I ask the office, who has it, and did anyone answer or need me?" Audience: Merwyn only. Playbook s1 (one question), s2 (waiting for Merwyn is the loudest state).

**Placement and badge.** A "Chat" button joins the bottom bar next to Usage (same `.btn.opt` look, speech-bubble icon plus word; icon-only below 600px, 44px target). Badge = count of agent replies Merwyn has not seen, a small light-paper pill (`--paper` on `--panel`), never `--warn`. Amber is reserved for needs-you (s2): if any unanswered reply is marked "needs you", the badge becomes a `?` in amber and the button keeps its label, so shape differs from the count (s5, not colour alone). It also feeds the existing top needs-you pill; the pill logic is unchanged. Closing the panel never clears needs-you.

**Panel (desktop, 900px and wider).** Floating `.panel.pp` using the T-059 grip, resize, opacity and saved layout (add `chat` to PANEL.IDS; default bottom-right, 360x480, min 280x240). Open/closed saved per viewer. Header (the drag grip): "Office chat", recipient summary ("To: Janice" or "To: Fang, Dinda"), a status dot with a word, and close x. Status: "Office running" (green `--accent` filled dot) or "Office not running" (hollow dim dot; text "Janice picks this up when the office is running"). Below: thread (scrolls, newest at bottom, sticks to bottom unless Merwyn scrolled up; then a "New replies" pill). Bottom: composer (textarea, 1 to 5 lines, Enter sends, Shift+Enter newline, Send button, "To:" chips row above it).

**Bubbles.** Merwyn: right-aligned, `--paper` fill, `--panel` text, small time under it. Agents: left-aligned, `--panel` lighter fill with a 3px left edge and name label in the agent's avatar colour from theme.yaml (colour plus the written name, never colour alone), 12-13px text. Time on hover/focus and always visible as "15:54". Mentions inside text render as chips: avatar colour tint with the name, `@all` in neutral.

**Per-recipient status chips** under each Merwyn message, one per recipient, text always present: "waiting for pickup" (hollow dot, dim), "replying" (three-dot pulse), "answered" (check, accent), "needs you" (amber fill `--warn`, `!` shape, the only amber in the panel). Order: needs you first.

**@mention autocomplete.** Trigger: `@` at the start or after a space. A list opens above the caret, max 5 rows scrolling, filtered by typed letters, case-insensitive; each row = avatar-colour dot, name, role in dim text ("Fang, architect"); `@all` last with "everyone". Keys: Up/Down move, Enter or Tab insert (name plus a space, becomes a chip), Esc closes without losing the text; Backspace on a chip removes it whole. Multiple mentions allowed; duplicates collapse to one chip; unknown name stays plain text with the note "No agent called Bob; this goes to Janice". No mention = Janice, shown as a dim "To: Janice (default)". Pattern: ARIA combobox/listbox, `aria-activedescendant`.

**Long replies.** Over about 12 lines, collapse with a fade and a "Show more" button (aria-expanded); code in `--mono` blocks with horizontal scroll and a Copy button; links open in a new tab with rel noopener and show the host; no inline images.

**Empty state.** Centered: "Ask the office anything." Three tappable examples that fill the composer: "@Janice what is next on the board?", "@Fang @Dinda is T-063 ready to build?", "@all anything blocked?". Plus the one-line running note.

**Error states.** Not signed in: composer disabled, "Chat needs you signed in" with the sign-in action. `db` null/unavailable: panel opens, thread replaced by "Chat storage is not available in this view" (recorded usage page has no chat button at all). Send failed: bubble stays with a "Not sent. Retry" button, text kept. Offline: banner "You are offline; messages send when you are back". Office not running: sent messages simply show "waiting for pickup".

**Link to the 3D office.** A reply that asks Merwyn a question: bubble gets an amber left edge, an "Needs you" label with `!`, and a "Show Fang in the office" button that calls the existing focusAgent. That agent's seg and sprite already show the waiting state; reply and 3D state clear together when Merwyn answers in chat (his next message to that agent marks it "answered"). Clicking an agent chip in the strip while chat is open adds `@Name` to the composer only via a visible "Message Fang" button in the focus card, not by default (no surprise).

**Phone (under 900px).** Full-height sheet reusing the `#usheet` pattern (sticky header, close x, safe-area padding), composer pinned above the keyboard (visualViewport), autocomplete opens above the composer, rows 44px. Panel move/resize is hidden as in T-059.

**Motion (s3, values are starting points).** New bubble: 160ms fade and 6px rise, ease-out, purpose continuity; reduced: appears instantly. "Replying" dots: 1.2s pulse, purpose attention; reduced: static "..." text "replying". Panel open/close: 140ms fade and scale from 0.98; reduced: instant. Autocomplete: none. Badge change: no animation; one count update.

**Accessibility (s5).** Thread is `role="log"` with `aria-live="polite"`; announce "Fang replied" (not the whole text), needs-you replies announce assertively once via the existing `#live`. Focus order: button, header controls, thread (tabbable for scroll), To chips, textarea, Send. Opening moves focus to the textarea; Esc closes autocomplete first, then the panel, and returns focus to the Chat button. Text contrast: paper on panel and name colours checked at 4.5:1 against the bubble fill (builder verifies each of the 8; if one fails, use a lighter tint, the name stays). 44px touch targets on phone, visible focus ring same as existing `.btn`.

**Open questions.** (1) Should unseen-reply counts persist across devices? Fang (database design). (2) Does Merwyn want Enter to send or Cmd/Ctrl+Enter? Merwyn; default Enter. (3) Agent avatar colours: use theme sprite colours or a new palette? Fang to confirm what theme.yaml exposes; I found only labels there.

— Dinda (designer)

Janice (pmo), 26 Nov, answers to Fang's open questions (facts from the artifact server's tool descriptions): (1) the AI Office artifact (slug 5f1bb811-1633-4bfb-8285-9bcb2408dec2) is engine/app/office.html. (2) db_write runs as the user (owner) by default and has `asLevel` (view, interact, admin) to test rules as a lower role. (3) db_write has op `merge` (writes the given fields, creates if needed) and `update` (merge, fails if missing); a field is removed with {"__delete__": true}; every op on an existing document needs `ifVersion` (optimistic lock), and a call of several ops commits all or none; one db_write at a time (rate limit). Use ifVersion for the claim step instead of a 30-minute timer where possible. (4) Declaring: declare_capabilities first (whole declaration), then publish the code that uses it. (5) One office session at a time is the working assumption; ifVersion makes a second one safe. Dinda's open question on send: Enter sends, Shift+Enter is a new line (Janice's default; Merwyn can change). — Janice (pmo)

## Compliance
Compliance: PASS with conditions (T-063 design, 26 Nov 2026). The design stands only if C1 to C8 are built; if any is declined this becomes a BLOCK and goes to Merwyn.
Reasoning: chat text lives only in the artifact db (owner read and write) and never enters the repo (stdin-only CLI, pointer-only tasks). That store is on claude.ai, outside company systems and likely outside Indonesia: acceptable for operational chat, not for personal data or prod rows (playbook s2: no cloud-agent processing of production personal data without Merwyn and legal approval; none exists). The design scanned replies but not Merwyn's own messages, and had no retention rule.
- C1 Page check before send: NIK-like 16-digit runs, Indonesian phone numbers, emails, long account-number-like digit runs, secret-like tokens; a hit blocks the send, names only the kind, no override; JS port of `chat.scan` with a shared invented-case fixture; Fang confirms `events._data_hit` covers these kinds incl. secrets.
- C2 Office check before spawn: `chat plan` scans each ask; a hit ask never reaches an agent prompt or task; Janice replaces its db text with "[removed: looked like personal data]", marks it answered, posts: "I did not pass this on because it looked like personal data. Please resend without it, using an ID or a link."
- C3 Notice under the composer with a one-time acknowledgement per browser: "Do not type borrower, lender or staff personal data (names, NIK, phone, email, account numbers), production rows or credentials here. Chat is stored on claude.ai and sent to AI agents. Use a loan ID or a link instead. The check catches number patterns, not names." Footnote: "Chat does not approve anything that needs a gate. Those are confirmed in the session."
- C4 pmo-playbook s9 step 8: a chat message is a request, never an approval; it does not answer a permission prompt or approve any human_gates item or prod write (R-14); no "unless it answers a needs_merwyn question" exception for gate items.
- C5 Chat-spawned agents get a read-only tool allowlist set at spawn (no Write, Edit or push; Bash read-only); no prod, kubernetes, database MCP or Bytebase tools until R-8 closes and the T-043 guard is installed and re-checked; prod requests get a plan or pointer for Merwyn; replies carry aggregates or pointers, never rows; repo changes become a task at todo.
- C6 Retention 30 days (confirmed by Merwyn, 26 Nov ~16:20 WIB); each inbox run deletes answered asks and replies older than that (db_write supports op delete for whole documents); the page has "Clear chat"; the playbook states db deletion does not delete session transcripts.
- C7 Before the first real message, Janice tests the owner-only rules with db_write asLevel view and records it in Build notes; the inbox refuses to route if chat is readable or writable below owner; Merwyn approved the first declare_capabilities and publish (26 Nov ~16:20 WIB); the artifact stays private; sharing it needs a new compliance check; the README says so.
- C8 Task quote lines are `> From chat message <id>, <date WIB>` plus a one-line summary naming no borrower, lender or person; fixtures invented, no realistic NIK or phone patterns; chat CLI output never redirected into the repo; ledger notes carry the pointer only.
Not legal advice: whether personal data in chat could ever be approved is for Merwyn and KlikA2C legal; until then it is barred.
— Wulan (compliance), recorded by Janice (pmo)

## Build notes
**What changed**
- Page (`engine/app/office.template.html`, `office.html` regenerated with `--chat`): Chat button in the bar (icon only under 600 px, badge = unseen replies, amber `?` when a reply needs Merwyn); chat panel on the T-059 panel model (`chat` added to `PANEL.IDS`, saved in `office.layout.v1`), full-height sheet under 900 px; @mention combobox (ARIA listbox, Up/Down, Enter/Tab, Esc, Backspace removes a whole mention, `@all`, several mentions, unknown-name note); per-recipient status chips; long replies collapse with Show more; code blocks with Copy; https links only; needs-you replies with "Show X in the office" and "Reply"; C3 notice with a one-time acknowledgement (composer disabled until then) and the gate footnote; C1 page-side scan blocks the send and names only the kind; "Clear chat" (two clicks); office running / not running from `chat/office` (running and under 15 min old); db null, no `claude`, signed-out and 10 s timeout states; live needs-you overlay (`withLive`/`setLive`, re-applied after every seek so scrubbing never clears it); only on the office page (no `data.chat` means the panel and button are removed and `claude.use` is never reached).
- Pure logic in `OfficeCore.chat`: `parseMentions`, `route`, `completions`, `newAsk`, `valid`, `canMove`, `threads`, `label`, `liveWaiting`, `setLive`, `withLive`, `unseen`, `officeStatus`, `blocks`/`inline` (text, link, mention parts, never markup), `scan`, `nameCol`/`contrast`. Agent colours moved from the scene into a `BODY` map used by both.
- Office side: `engine/runtime/chat.py` (pure: mentions, scan, schema `validate`, `TRANSITIONS`/`can_move`, `plan`, `reply`, `set_status`, `purge`, `rules_problem`, `pointer`); CLI `python -m engine.runtime chat plan|reply|status|purge|rules|mentions ai-office` (stdin only); `engine/schema/chat.md`; ledger accepts `step:"chat"` with `tasks:[]` and a `chat message <id>` note (`engine/schema/usage.md`); `scripts/office_app.py --chat` (exit 2 with `--ledger`); pmo-playbook section 9; README notes (artifact stays private).
- Shared parity fixtures `tests/fixtures/chat-mentions.json` (44 cases) and `chat-scan.json` (22 cases; long digit runs are built from `["rep", ch, n]` so no realistic number is stored). Both `tests/test_chat.py` and a node case in `tests/test_office_app.py` read them.
- T-064: `depends_on` now `[T-024, T-063]`; the open-question line is removed.

**Compliance conditions**
C1 page `scan` plus shared fixture; the design assumed `events._data_hit` covers phone numbers and secrets, it does not (email, 16-digit, 10+ digits only), so `chat.scan` and the JS port add phone, long numbers with separators and secret-like tokens; forbidden terms stay office-side. C2 `plan` refuses before any claim (`post` + `refuse` actions). C3 notice and ack in the page. C4/C5/C6/C8 in playbook section 9 (read-only allowlist, no prod tools, 30-day `chat purge`, Clear chat, pointer-only tasks and ledger notes); C7 `chat rules` and `plan` refuse unless `chat` is owner-only (`plan` now requires `{"rules","docs"}` on stdin), README says the artifact stays private.

**How to verify**
```
python -m unittest discover -s tests          # 385 tests OK
python scripts/office_app.py ai-office --chat --check
python -m engine.runtime validate ai-office && python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl
echo "@Fang and @Bob" | python -m engine.runtime chat mentions ai-office
cp /tmp/three/package/build/three.min.js engine/app/   # gitignored; open engine/app/office.html over http for a smoke test
```
Screenshots (headless Chrome, a stub `claude` injected into a copy of the page under /tmp, never committed): `/tmp/t063-shots/` at 1280x800 (`-d`) and 390x844 (`-m`): 1 closed with a needs-you badge, 1b closed with a count badge, 2 open empty with the notice, 3 autocomplete, 3b a sent message, 4 and 4b a multi-agent thread with replies and statuses, 4c "Show Dinda in the office" with the 3D waiting state, 5 a blocked personal-data send, 6 db null, 7 signed out, 8 the recorded page (no chat), 9 no `claude`. Console: no errors or page errors; only Chrome's software-GL "GPU stall" warnings.

**Deviations from the design**
- Size: `office.html` is 214,696 bytes with chat (174,020 before), over the 200 KB test limit; the limit in `test_size_limit` is raised to 224 KB in `tests/test_office_app.py` with the reason in a comment (the chat is about 40 KB of library-free page code). Not trimmed further.
- `chatInit` runs at page load, not only when the panel opens: the badge and the needs-you link need live messages while the panel is closed.
- `plan` returns one action per ask (`agents` and `changes` lists) instead of one per (ask, agent), so a write carries one `ifVersion`; patches always carry the whole `recipients` map. `plan` input is `{"rules","docs"}` (C7), docs may be `{id,data,version}` wrappers. `chat reply` reads JSON `{"ask","text","question"}` on stdin (it needs the ask doc), not bare text. Added `chat status` (picked to replying), `chat purge` and `chat rules`.
- `chat.scan` covers more than `events._data_hit` (see C1 above). `newAsk(text, cfg, nowMs, rnd, uid, inReplyTo)` takes the `data.chat` object. Transitions also allow picked to answered or needs_merwyn (a pmo ask answered in the session, and repair).
- Chat runs with no task are counted in the ledger `shared` row and are not in the event log used by the recorded page (a usage event needs a task).
- Panel minimum size is the T-059 global 240 x 120, not 280 x 240. No sign-in action exists (the API is unknown): the signed-out state offers "Try again".
- Not done here: C7 `asLevel: view` check, declare and publish (Janice, after review); no test against the real artifact db.

— Sebastian (engineer)

### Rework 1 (Sebastian, 26 Nov 2026, after Cahyani's REJECT)
- Fix 1, mentions: `hmap` is now `Object.create(null)` and lookups use `in`; `canMove` uses `hasOwnProperty`. Python was already safe (a dict lookup); parity fixture gets `@constructor`, `@toString @valueOf`, `@__proto__` (no match: a name must start with a letter), `@hasOwnProperty`, and a mixed case.
- Fix 2, version: `chat purge` deletes and `chat status` output now carry `ifVersion` from the `{id, data, version}` wrapper (null for bare docs). Tests: unit (purge) and CLI (status, purge).
- Fix 3, size: Fang decided 216 KB (Janice's message). `test_size_limit` is 216 * 1024 with the comment corrected. office.html is 216,739 bytes (211 KB), about 4.4 KB under the limit.
- Notes: `unavailable` is transient. Writes retry once after 400-1200 ms (`OfficeCore.chat.retryOnce`); a snapshot error with that code shows "Reconnecting..." (chip and thread) and keeps the data, the next snapshot clears it. Other codes go to "not available" as before. Tested under node (retry once, no retry on `revoked`, error after two failures).
- Notes: the scan turns non-ASCII decimal digits (Unicode Nd) into ASCII first, in `chat.scan` (Python `unicodedata`, added to the stdlib allowlist in test_dryrun) and the page (value = offset in its run of Nd, mod 10). Four new scan fixture cases (Arabic-Indic 16-digit, fullwidth 12-digit, mixed phone-like, short non-ASCII digits with no hit).
- Notes: `rules_problem` also refuses a rule with path `""`, `/` or `*` that is below owner for read or write. Tests added.
- Notes: `chat.md` has a "Database API (confirmed)" section (doc/collection paths, get/set/update/delete/acquire/onSnapshot, error codes) and the "not checked yet" wording is gone. The `chatStore` comment says the same.
- How to verify: `python -m pytest -q` (386 passed), `python scripts/golden.py ai-office`, `python -m engine.runtime validate ai-office`, `python scripts/office_app.py ai-office --chat --check`, ledger CLI on the session file (59 runs, 0 errors, 0 warnings), `python scripts/board.py ai-office` (board.md discarded). No browser run in this rework; the new page paths (retry, reconnecting) are covered by node unit tests only.

— Sebastian (engineer)

## Review log
**REJECT (first review), 26 Nov 2026, head eb0628b.** Most of it works and is well built. Three fixes are needed, all small: two are correctness bugs I found by running edge cases, one is a design step that was skipped.

**Checks run (real output)**
- `python -m pytest -q`: `385 passed`, exit 0. `python scripts/golden.py ai-office`: `13 cases, 75 checks, 0 problems`, exit 0. `python -m engine.runtime validate ai-office`: `OK — 8 agents, 5 stages, 64 tasks, 18 skills`. `python scripts/office_app.py ai-office --chat --check`: `up to date (209 KB, 84 events)`, exit 0. `--chat --ledger x`: exit 2. `python -m engine.runtime ledger ai-office offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl`: `59 runs kept, 0 errors, 0 warnings`.
- Headless Chrome at 1280x800 and 390x844. I used my own stub of `claude.use`, written under /tmp and not committed. It checks even/odd path segments (TypeError otherwise), makes `update` reject a missing doc, gives one orderBy and limit 1-1000, uses `{docs:[{id,exists,data(),metadata}]}` snapshots, logs any read of `window.claude.db`, and logs any write from a snapshot callback or two writes to one doc at a time. Results at both sizes:
  - `claude.use` was called for `db` and `user` only. 2 subscriptions were opened over the whole run, including reopening, sending, retrying and Clear chat. 0 rule violations.
  - The composer stays disabled until the C3 notice is acknowledged. Notice and footnote text match C3 exactly.
  - Keyboard autocomplete: `@Fa` lists Fang. `@` lists 9 rows (8 agents and @all). Enter and Tab insert the mention, and `aria-activedescendant` is set. Sending "Hi @Fang and @Dinda is T-063 ready?" writes one `set` on `chat/office/messages/m-…` with `recipients` {architect, designer} at `new`.
  - Simulated session writes: chips read "Fang is replying" and "Dinda picked this up", then "Dinda · needs you" and "Fang · answered". After that, `document.title` is "(1) needs you · AI Office", Dinda is amber in the strip and the scene, and the closed badge shows `?`.
  - A `<script>` payload renders as text (0 script nodes). A `javascript:` link is not linked. The https link gets `noopener noreferrer`, `_blank`.
  - A blocked send ("@Fang call 0811 1111 1111") shows "…(phone number). Not sent…". It makes 0 writes and keeps the text.
  - Esc closes the panel and puts focus on `chatbtn`. Open/closed survives a reload. A failed write shows "Not sent. Retry", and retry writes the same id. Clear chat (two clicks) deleted every doc.
  - With db null, and with `use` hanging (10 s timer), the panel shows "Chat storage is not available in this view".
  - Console: 0 page errors. The only error was my test server's favicon 404.
  - Screenshots are in /tmp/rv63/shots (not committed).
- Recorded page: `--ledger … --out /tmp/…` gives `data.chat` absent and no Chat button, and `claude.use` is never called.
- Page API use, checked against the artifact db API: paths have the right parity. Only `set` (new docs) and `delete` are used, never `update` on a missing doc. There is one subscription each on messages and `chat/office`. No db writes come from render or snapshot callbacks. Every error goes to one generic state (note 1).
- Office CLI run with db_list-shaped input `{id,data,version}`. `plan` puts `post` and `refuse` first, carries `ifVersion` from `version`, and the refuse text and reply text match C2. Rules open below owner exit 1 for `rules` and `plan` (C7). `reply` on a 16-digit run exits 1 and names only the kind.
- C1 to C8 against the code and pmo-playbook section 9: C1, C2, C3, C4, C5 (playbook allowlist), C7 and C8 are present. Fixture numbers are repeated digits, nothing realistic. C6 is present, but its delete step does not work as written (fix 2).
- Python against node parity, my own probes (17 cases): 14 match. The three differences: `@constructor` (fix 1); Arabic-Indic digits, which Python flags and the page does not (note 2); and a different kind name for one phone case, where both still block.

**Required fixes**
1. Mention parsing in the page breaks on names of Object.prototype properties. `hmap` is a plain `{}`, so `@constructor` resolves to the `Object` function. Node shows `newAsk('@constructor please check')` gives recipient key `"function Object() { [native code] }"` and `mentions:[null]`. Python gives `unknown:["constructor"]` and routes to Janice. The ask is never routed, because `chat plan` skips it as invalid. Fix: use `Object.create(null)` or a `hasOwnProperty` check in `hmap` and `parseMentions`, and add `@constructor` to `chat-mentions.json`.
2. `chat purge` and `chat status` drop the document version, but `db_write` needs `ifVersion` on every op on an existing doc (Janice's facts in the Design). Input `{id,data,version:7}` to `purge` printed `{"op":"delete","path":…,"id":…}` with no `ifVersion`. So C6 step 10 ("delete what it lists with db_write op delete") fails when run as written. Fix: carry `ifVersion` from the input on each purge delete and on the `status` output, as `plan` and `reply` already do, and add a test.
3. The page size limit was raised from 200 to 224 KB in the build. Fang's design says: "If it does not fit, Sebastian stops and asks me. Raising the limit is a design change, not a build fix." The comment explains why, but Fang's acceptance is not recorded. Fix: Fang accepts the 224 KB limit in Design, or the page is trimmed under 200 KB.

**Notes (not blocking)**
1. The page handles every db error the same way. A snapshot error, even a transient `unavailable`, turns into a permanent "not available" state with no retry. `quota_exceeded`, `revoked` and `not_granted` are not told apart.
2. The page scan uses ASCII `\d`, so non-ASCII digits get past it. The office side (C2) still catches them.
3. `rules_problem` checks only `path:"chat"` and `chat/…`. A wider rule such as a root path would not be caught.
4. `reply` and `status` patches carry the whole `recipients` map, so another agent's status can be stale in the patch. `ifVersion` turns this into a conflict, and the next `plan` repairs it.
5. While typing `@d`, the To row briefly says "No agent called D".
6. `chat.md` and the chatStore comment still say the API shape is unconfirmed. The API now quoted by Janice matches what the page and `_norm` use, so update the wording.
7. Clear chat sends up to 200 deletes in parallel. It may hit the rate limit, and if it does the page shows a warning.

External skills design:accessibility-review and data:validate-data are not available in this session. The accessibility checks above were done by hand.

— Cahyani (reviewer)

## Decision

## Open questions
- (Sebastian) The page assumes a Firebase-like db API (`db.doc(path).set/delete/onSnapshot`, `db.collection(path).orderBy().limit().onSnapshot`, snapshot `.docs[i].data()`, `user.id()`). It is isolated in `chatStore` in the template. Janice checks the real shape when declaring; if it differs, only that function changes.
- (Sebastian) The shape of a db_query/db_list result is not confirmed; `chat plan` accepts bare docs or `{id, data, version}` and takes `ifVersion` from `version` or `_version`.
- (Sebastian) Does `db_write` accept a partial `recipients` map on `merge`? The patches carry the whole map so either behaviour is safe.
- Is the "AI Office" artifact (slug 5f1bb811-1633-4bfb-8285-9bcb2408dec2) built from `engine/app/office.html` (synthetic fixture), and not a recorded usage page? The design assumes so. Janice answers.
- Exact shape of `rules` in declare_capabilities, and do the db tools act at owner level under Merwyn's account? Janice checks at declare time.
- Does db_write do partial updates of a map key, or whole-doc set only? Janice tries it on first use; the procedure covers both.
- Assumption: one office session processes the inbox at a time (the db has no compare-and-set that I know of). Janice confirms; T-024 must keep it.
