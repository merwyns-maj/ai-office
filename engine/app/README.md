# engine/app: the 3D office page (T-048)

One self-contained page, `office.html`, replays a recorded event log (`engine/schema/events.md`) in a three.js (r128) office built from `offices/ai-office/theme/theme.yaml`. No build step, no network calls except loading three.js. v0 is replay only: no live events (T-027 / T-024).

Files
- `office.template.html`: the page source (HTML, CSS, `office-core` pure logic, `office-view` scene and HUD)
- `office.html`: generated, committed. Do not edit by hand
- `fixtures/sprint-03.jsonl`: replay of Sprint 3 (T-043, T-044, T-045)
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

URL parameters: `?t=<seconds>` open paused at that replay time (`&play=1` to play from there), `?motion=reduced`, `?speed=1|2|4`.
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
