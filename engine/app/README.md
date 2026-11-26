# engine/app: the 3D office page (T-048, model and usage T-056)

One self-contained page, `office.html`, replays a recorded event log (`engine/schema/events.md`) in a three.js (r128) office built from `offices/ai-office/theme/theme.yaml`. No build step, no network calls except loading three.js. v0 is replay only: no live events (T-027 / T-024).

Files
- `office.template.html`: the page source (HTML, CSS, `office-core` pure logic, `office-view` scene and HUD)
- `office.html`: generated, committed. Do not edit by hand
- `fixtures/models-synthetic.jsonl`: SYNTHETIC v1 log (model and usage, four providers), the default page
- Recorded ledger page (T-057, not committed, goes stale on every ledger append): `python scripts/office_app.py ai-office --ledger offices/ai-office/usage/<session>.jsonl` writes `engine/app/usage-<session>.html`
- `fixtures/sprint-03.jsonl`: replay of Sprint 3 (T-043, T-044, T-045), a v0 log: `python scripts/office_app.py ai-office --fixture engine/app/fixtures/sprint-03.jsonl --out /tmp/sprint03.html`
- `offices/<office>/providers.yaml`: provider catalogue and prices the page reads (format in `engine/schema/office.md`)
- `three.min.js`: NOT committed (gitignored). Fetch it as below

## Regenerate

```bash
python scripts/office_app.py ai-office            # writes engine/app/office.html
python scripts/office_app.py ai-office --check    # exit 1 if the committed file is stale
```

## Run

```bash
cd /tmp && npm pack three@0.128.0 && tar xzf three-0.128.0.tgz        # in an empty dir, e.g. /tmp/three
cp /tmp/three/package/build/three.min.js engine/app/three.min.js        # next to office.html
cd engine/app && python -m http.server 8048                              # open http://localhost:8048/office.html
```

The page loads `./three.min.js` first, then cdnjs r128, unpkg and jsdelivr (0.128.0). If none arrives it shows a "3D view could not load" note and the HUD (Needs-you pill, agent strip, ticker, playback) keeps replaying.

As an artifact: publish `office.html` together with `three.min.js` as a sibling file, or rely on the CDN fallbacks.

URL parameters: `?t=<seconds>` open paused at that replay time (`&play=1` to play from there), `?motion=reduced`, `?speed=1|2|4`, `?usage=collapsed` (docked usage panel starts collapsed) or `?usage=open` (open the usage sheet on screens under 900 px).

Model and usage (T-056): every name tag shows a provider chip (code plus colour) and a short model name; the right column has a collapsible Usage panel (total, by provider, by agent) above the ticker; under 900 px it is a sheet opened from the Usage button (the gear menu on phones). Every usage figure carries the word "synthetic" while the log header says `usage_source: synthetic`. Cost is `tokens x config price`, an estimate with the config's date; with no price in the config a per-token row says "price not set". A log without model data (v0) shows no chips and no panel.
Movable panels (T-059): at 900 px and wider the Usage and Latest events panels can be moved (drag the header grip) and resized (bottom-right corner), each with its own background opacity (the "..." button, 0 to 100 in steps of 5). Keyboard: Tab to the grip, arrows move 8 px (Shift 32 px), Alt+arrow resizes, Home restores the default position; on the resize handle arrows resize. The layout is kept per browser in `localStorage` key `office.layout.v1` (the page works when storage is blocked) and the gear menu has "Reset layout". Under 900 px the layout is the same as before and a saved layout is ignored, not deleted. The 3D stage runs full width behind the panels. The layout maths is in `OfficeCore` (`clampRect`, `moveRect`, `resizeRect`, `snapRect`, `parseLayout`) and tested under node.
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
