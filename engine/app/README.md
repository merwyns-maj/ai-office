# engine/app: the 3D office page (T-048, model and usage T-056)

One self-contained page, `office.html`, replays a recorded event log (`engine/schema/events.md`) in a three.js (r128) office built from `offices/ai-office/theme/theme.yaml`. No build step, no network calls except loading three.js. v0 is replay only: no live events (T-027 / T-024).

Files
- `office.template.html`: the page source (HTML, CSS, `office-core` pure logic, `office-view` scene and HUD)
- `office.html`: generated, committed. Do not edit by hand. It is the synthetic dev build (with chat) used for tests and `--check`; it is not published
- `fixtures/models-synthetic.jsonl`: SYNTHETIC v1 log (model and usage, four providers), the default page
- The published page (T-065, generated, not committed, goes stale on every ledger append, so republish after one): `python scripts/office_app.py ai-office --ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat` writes `engine/app/usage-session_01MDGJq3GfaeozLojJo8W5Td.html`. It replays the real ledger and has the chat. It is published to the "AI Office" artifact (5f1bb811-1633-4bfb-8285-9bcb2408dec2). The old "AI Office token usage" artifact is retired. Without `--chat` the same command builds a ledger-only page (T-057), for checks
- `fixtures/sprint-03.jsonl`: replay of Sprint 3 (T-043, T-044, T-045), a v0 log: `python scripts/office_app.py ai-office --fixture engine/app/fixtures/sprint-03.jsonl --out /tmp/sprint03.html`
- `offices/<office>/providers.yaml`: provider catalogue and prices the page reads (format in `engine/schema/office.md`)
- `three.min.js`: NOT committed (gitignored). Fetch it as below

## Regenerate

```bash
python scripts/office_app.py ai-office --chat            # writes engine/app/office.html (synthetic dev build, with chat; not published)
python scripts/office_app.py ai-office --chat --check    # exit 1 if the committed file is stale
```

## Run

```bash
cd /tmp && npm pack three@0.128.0 && tar xzf three-0.128.0.tgz        # in an empty dir, e.g. /tmp/three
cp /tmp/three/package/build/three.min.js engine/app/three.min.js        # next to office.html
cd engine/app && python -m http.server 8048                              # open http://localhost:8048/office.html
```

The page loads `./three.min.js` first, then cdnjs r128, unpkg and jsdelivr (0.128.0). If none arrives it shows a "3D view could not load" note and the HUD (Needs-you pill, agent strip, ticker, playback) keeps replaying.

As an artifact: publish the generated page from the command in Files (not `office.html`), together with `three.min.js` as a sibling file, or rely on the CDN fallbacks.

URL parameters: `?t=<seconds>` open paused at that replay time (`&play=1` to play from there), `?motion=reduced`, `?speed=1|2|4`, `?usage=collapsed` (docked usage panel starts collapsed) or `?usage=open` (open the usage sheet on screens under 900 px).

Model and usage (T-056): every name tag shows a provider chip (code plus colour) and a short model name; the right column has a collapsible Usage panel (total, by provider, by agent) above the ticker; under 900 px it is a sheet opened from the Usage button (the gear menu on phones). Every usage figure carries the word "synthetic" while the log header says `usage_source: synthetic`. Cost is `tokens x config price`, an estimate with the config's date; with no price in the config a per-token row says "price not set". A log without model data (v0) shows no chips and no panel.
Movable panels (T-059): at 900 px and wider the Usage and Latest events panels can be moved (drag the header grip) and resized (bottom-right corner), each with its own background opacity (the "..." button, 0 to 100 in steps of 5). Keyboard: Tab to the grip, arrows move 8 px (Shift 32 px), Alt+arrow resizes, Home restores the default position; on the resize handle arrows resize. The layout is kept per browser in `localStorage` key `office.layout.v1` (the page works when storage is blocked) and the gear menu has "Reset layout". Under 900 px the layout is the same as before and a saved layout is ignored, not deleted. The 3D stage runs full width behind the panels. The layout maths is in `OfficeCore` (`clampRect`, `moveRect`, `resizeRect`, `snapRect`, `parseLayout`) and tested under node.
Office chat (T-063): the page is built with `--chat` (the committed synthetic `office.html`, and the published ledger page) and has a Chat button in the bottom bar. At 900 px and wider the chat is a floating panel on the T-059 model (move, resize, opacity, saved in `office.layout.v1`); under 900 px it is a full-height sheet. Type `@Janice`, `@Fang @Dinda` or `@all`; no mention goes to Janice. The page writes each message into the artifact's own database (`db` capability, owner-only rules) and shows each agent's reply and a per-recipient status (waiting for pickup, replying, answered, needs you). Replies come only while an office session runs the inbox (pmo-playbook section 9); the header says "Office running" or "Office not running" from a meta document the session writes. A reply that needs Merwyn shows the agent in the waiting state in the 3D office. Before a message is sent the page checks it for personal data and secrets (number patterns, emails, tokens: a hit blocks the send and names only the kind), and a one-time notice must be acknowledged. "Clear chat" deletes the thread; messages older than 30 days are purged by the inbox run. Chat text is company data: it is stored on claude.ai in the artifact database and never in this repo. **The artifact stays private. Sharing it needs a new compliance check (T-063, C7).** `--chat` with `--ledger` is the one published page; without `--chat` there is no chat. Schema: `engine/schema/chat.md`. Publish order: `declare_capabilities` with `db` and `user` first, then publish the page; the db tools work only after that.
Keys: Space play/pause, Left/Right step one event, 1/2/4 speed, M motion, F follow, Esc close.

## Screenshots (headless Chrome, software GL)

```bash
S="google-chrome --headless=new --no-sandbox --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --hide-scrollbars --enable-logging=stderr --v=0"
mkdir -p /tmp/t048-shots
$S --window-size=1280,800 --virtual-time-budget=6000 --screenshot=/tmp/t048-shots/door.png      "http://localhost:8048/office.html?t=2"
$S --window-size=1280,800 --virtual-time-budget=6000 --screenshot=/tmp/t048-shots/talk.png      "http://localhost:8048/office.html?t=58.5"
$S --window-size=1280,800 --virtual-time-budget=3000 --screenshot=/tmp/t048-shots/walk.png      "http://localhost:8048/office.html?t=29.4&play=1"
$S --window-size=1280,800 --virtual-time-budget=6000 --screenshot=/tmp/t048-shots/end.png       "http://localhost:8048/office.html?t=198"
$S --window-size=1280,800 --virtual-time-budget=6000 --screenshot=/tmp/t048-shots/reduced.png   "http://localhost:8048/office.html?t=2&motion=reduced"
$S --window-size=390,844  --virtual-time-budget=6000 --screenshot=/tmp/t048-shots/phone.png     "http://localhost:8048/office.html?t=2"
```

Console errors: the same commands print `CONSOLE` lines on stderr; pipe through `grep -i "console"` (Chrome's own SODA/socket/GPU noise can be ignored). Software GL gives screenshots, not a real frame rate: read the on-page `fps · calls` readout on a laptop (needs 50 fps with 8 agents for 60 s).

## Tests

```bash
python -m unittest discover -s tests
```
