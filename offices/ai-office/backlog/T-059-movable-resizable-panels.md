---
id: T-059
title: "3D office: rearrange, resize and set opacity of the panels"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-058]
pr: 45
---

> Merwyn, 26 Nov 2026 13:49 WIB: "can the widget easily be rearranged and managed the height and width? also have the opacity so i want transparent background". Applies to the 3D office page and the recorded usage page (same template).

## Done when
- [x] Each HUD panel (usage panel, latest events; the agent strip and needs-you pill if Dinda judges it useful) can be moved by dragging its header and resized by width and height from a corner handle, on desktop (mouse and touch); panels stay inside the window and cannot be lost off-screen
- [ ] A background opacity control per panel (or one for all, Dinda decides) from fully transparent to solid; text stays readable at every setting (text shadow or a minimum contrast rule), so the 3D office shows through
- [x] Layout and opacity are remembered per viewer in browser storage (wrapped in try/catch; the page works without it) and a "Reset layout" control restores the default
- [x] Keyboard: panels can be moved and resized without a mouse (e.g. arrow keys on a focused handle); reduced motion has no animated snapping
- [x] Phone (under 600px) keeps today's sheet layout; dragging is off there
- [x] Tests for the pure layout maths (clamping to the window, size limits, saved-state parsing including corrupt storage); all tests, golden and --check pass; headless screenshots at 1280x800 and 390x844 with a moved, resized, half-transparent panel; no console errors

## Spec
UI request from Merwyn, spec by Janice: scope as in Done when. Out of scope: moving 3D objects, sharing a layout between viewers or devices, new panels. — Janice (pmo)

## Design

### UX design
**Question this answers (playbook s1):** "Can I put the panels where they do not hide the office, and see through them?" Audience: Merwyn, desktop. The needs-you state stays first (s2): its pill and strip never move.

**Scope.** Movable and resizable: `#usage` and `#ticker` only. Not movable: needs-you pill, agent strip, bottom bar, gear menu (the pill is the state Merwyn must not miss, and a fixed place is what makes it findable; s2). Panels float only at 900px and wider, because below 900px `#side` is `display:contents` and `#usage`/`#ticker` are already hidden in favour of `#usheet`/`#tone`. So 600-899px and phone keep today's layout, no grips, no handles. (Open question 1.)

**Default = today.** Default positions are today's right column: x = window width - 288 + 8, ticker below usage, as now. Defaults: opacity 92% (today's .92 fill), blur on. Nothing changes until a viewer acts. The stage stays `right:var(--side)` until a panel is moved or set below 100% opacity; then body gets `.free` and the stage goes `right:0` so the office shows under panels. Engineer: check camera framing does not jump on that switch; if it does, make `.free` the permanent state at 900px+ and say so in Build notes.

**Handles.**
- Move: the panel header (`.uh` / the h2 row) gets a 6-dot grip icon at the left, `cursor:grab`, `touch-action:none`, pointer events (mouse and touch). Buttons in the header (collapse) still click normally. It is a focusable `role="button"` with `aria-label="Move Usage panel"`.
- Resize: bottom-right corner, 16px visible mark (two diagonal lines, `--text-dim`), 44x44px transparent hit area centred on the corner, `cursor:nwse-resize`, `touch-action:none`, `aria-label="Resize Usage panel"`, focusable.
- Opacity and reset: a small "..." button in each header opens a tiny menu (see below). Gear stays for the global "Reset layout".

**Sizes (px) min / default / max.** Usage: 240x120 / 272xauto-as-today / 520 x (window height - 16). Ticker: 240x120 / 272xfill-as-today / 520 x (window height - 16). Max never exceeds window minus 16px. Content scrolls inside (`overflow:auto`) when smaller than its body; collapse button on usage keeps working and remembers the expanded height.

**Clamping, snapping, window resize.** Panel always stays fully inside the window with an 8px margin; clamp on every move and resize. Top limit is the top of the window, but never under the bottom bar (bottom limit = window height - bar height - 8). Snap: within 12px of an edge margin, the position snaps to 8px; no snapping to other panels. On window resize, re-clamp (shrink size first down to its min, then move). If the window is too small for even the min size, show the panel at min at 8,8-ish and let it overflow; never hide it. Below 900px, floating is off and saved layout is ignored, not deleted. Keep positions as pure numbers (x, y, w, h) so the clamp is testable.

**Opacity: one control per panel** (the two panels sit over different parts of the scene; one slider for all would be wrong for one of them). Range 0-100% in 5% steps, `<input type="range">` in the panel's "..." menu, labelled "Background opacity", showing the value. Default 92. Only the background fill changes: text, border, grip, handle and focus rings stay solid.
Readability (s5 office rule: no state by one cue): below 100% opacity add `text-shadow:0 1px 2px rgba(0,0,0,.85), 0 0 6px rgba(0,0,0,.6)` on panel text; backdrop blur stays at 8px down to 30% (it is what keeps text legible over a moving scene) and fades to 0 below 30%, where the shadow takes over. At 0% keep a 1px `rgba(255,255,255,.18)` border so the panel edge and handles are still findable. Dim text (`--text-dim`) rises to `--text` colour under 60% opacity to hold contrast. Engineer: verify 4.5:1 on the lightest scene area in the screenshot at 0%, 30%, 60%.

**Reset layout.** In the gear menu (button already in the bar; on desktop it is the place for global actions), one item "Reset layout" that clears storage and restores default positions, sizes and opacity; confirm-free (cheap and reversible by redoing), and announce "Layout reset" via `#live`. It lives only in the gear menu.

**Storage.** Key `office.layout.v1`, JSON `{usage:{x,y,w,h,o},ticker:{...}}`, in try/catch on read and write. Parse validates every number (finite, within limits) and falls back per panel, then to default. Corrupt, missing, or storage blocked: use default, no error shown, page works. Saved layout bigger than the window: clamp on load, do not overwrite storage until the viewer next moves something.

**Keyboard (s5).** Tab order: panel header grip, resize handle, "..." menu, then panel content. On a focused grip: arrows move 8px, Shift+arrow 32px. On a focused resize handle: arrows resize 8px (Shift 32px); Alt/Option+arrow on the grip also resizes (same as handle). Home on grip: snap to default position. Esc: nothing. Focus ring is the existing 2px `--text` outline, and handles show a 2px ring plus a visible grip on focus even at 0% opacity. `#live` announces only on key end (debounced 600ms): "Usage panel at 120, 80, size 300 by 240." Never during drag or per keypress. No announcement for pointer drags.

**Focus and z-order.** Pointer-down or focus inside a panel brings it to front (z-index counter, max 2 panels, panels stay under dialogs `#usheet`, `#focus`, `#msheet`, which keep their z-index). Overlapping panels are allowed. While dragging: panel gets a stronger shadow and `opacity` is unchanged (do not make the thing you are aiming at harder to see).

**Motion (s3, purpose named).**
| Event | Motion | Purpose | Reduced motion |
|---|---|---|---|
| Drag / resize | none, panel follows pointer 1:1 | direct manipulation | same |
| Snap to edge | 120ms ease-out position settle | continuity: shows where it landed | instant jump |
| Window-resize re-clamp, Reset layout | 160ms ease-out | continuity: shows the panel moved by itself | instant |
| Drag lift shadow | 100ms | feedback: you hold it | instant |
Check `prefers-reduced-motion` in CSS (C39) and in the script (SCR40) before adding any transition class.

**States.** Default / hover (grip and handle brighten to `--text`) / focus (ring) / dragging (lift shadow, cursor grabbing) / resizing / at limit (no feedback needed; it stops) / transparent (shadow, blur fade) / storage unavailable (silent default) / collapsed usage (header only, height = header).

**Accessibility check.** Pointer-only is not required: every move and resize has a keyboard path. Hit area 44px on handle; grip header height at least 36px (today's header height, check). Name, role and value on all controls; slider has a visible label and value. No state by colour alone. Contrast to verify per Build notes. Touch drag only on 900px+ touch screens (tablet landscape); `touch-action:none` on the grip and handle only, so scrolling inside panels still works.

**Open questions.**
1. 600-899px has no side panels today (`#usheet`/`#tone` only). Done when says phone sheet only; I propose floating only at 900px+. Who can answer: Janice (pmo) or Merwyn.
2. Stage switching to full width on first move may shift the camera framing. Who can answer: Fang (architect).

— Dinda (designer)

Janice (pmo), 26 Nov: Dinda's UX accepted; moved to build. Answers: (1) floating panels only at 900px and wider, as Dinda proposed; under 900px today's layout stays. (2) The 3D stage runs full width behind the panels at 900px+ (so transparency shows the office); the camera frames the office for the full width once at load and on window resize, never on each drag. Technical design is reuse-only within the page (pure layout maths in office-core, node-tested), so Janice stands in for Fang. No compliance flag. Engineer: do not set status.

## Build notes

**What changed**
- `engine/app/office.template.html` (and generated `engine/app/office.html`): layout maths added to `office-core` as `OfficeCore.PANEL`, `panelBounds`, `clampRect`, `moveRect`, `resizeRect`, `snapRect`, `keyDelta`, `opacityStep`, `blurFor`, `textMode`, `rectSentence`, `parseLayout`, `serializeLayout` (pure, numbers only). View code (`movable panels` block in `office-view`) adds the grip, resize handle, "..." opacity menu, pointer and keyboard handling, storage and reset. Same template, so the recorded usage page gets it too.
- `tests/test_office_app.py`: three tests (layout maths under node, every `localStorage` touch inside try, control names and full-width stage).
- `engine/app/README.md`: one paragraph on the feature.

**How it behaves**
- Usage and Latest events only; floating at 900px and wider. The first action (move, resize, opacity) freezes both panels at their current rectangles (so nothing jumps) and adds `body.free`; stage is `right:0` at all widths (Janice's answer 2), framed once at load and on window resize by the existing code, not on drag.
- Pointer events (mouse and touch); keyboard: grip arrows 8px / Shift 32px, Alt+arrow on the grip or arrows on the resize handle resize, Home restores the default position; one `#live` announcement and one save 600 ms after the last key. Snap (within 12px, 120ms settle) on pointer release only; Reset layout settles 160ms; reduced motion (OS or the page toggle) = instant.
- Opacity per panel, 0 to 100 in steps of 5, default 92 (today's fill). Below 100 a text shadow, blur 8px down to 30% then fading to 0, dim text promoted to text colour under 60%, 1px `rgba(255,255,255,.18)` border at 0%. Text, border, grip and handles stay solid.
- Storage key `office.layout.v1` `{usage:{x,y,w,h,o},ticker:{...}}`; read, write and remove are each in try/catch. A saved layout is clamped in memory on load and storage is not rewritten until the viewer acts. "Reset layout" is in the gear menu, which now also shows at 900px and wider (see deviations).
- Phone and 600-899px: nothing floats; all floating rules sit in `@media (min-width:900px)` and use CSS variables, so a saved layout is ignored (not deleted) below 900px and the phone ticker sheet is untouched.

**Deviations from the design (please check)**
1. Top limit is the bottom edge of the top bar (56px, or 48px on short windows), not the top of the window, so a panel can never cover the needs-you pill or the agent strip (Dinda's own principle, s2). Left, right and bottom limits are the 8px margin as designed.
2. The gear button is `display:none` above 600px today (phones only), so Dinda's "gear already in the bar" was not true on desktop. It now shows at 900px and wider and its menu holds only "Reset layout"; phones keep the old gear menu.
3. Default width is 264px (today's `--side` minus 24px), not 272px; defaults are read from today's flow layout, not recomputed. Today's ticker is 96px tall, below the 120px minimum, so a move keeps it at 96 and only a resize or window-resize re-clamp raises it to 120. On first freeze the bottom panel can shift up to 4px (today's 4px bottom gap vs the 8px margin).
4. Opacity default is 92 but a 5%-step slider shows 90 at that value; the label says "92%" until the viewer touches the slider.
5. The ticker header is now a grip row (grip, title, "..." button), about 30px taller than today's bare title, and `overflow:visible` replaces `overflow:hidden` on both panels so the 44px resize hit area can reach 14px outside the corner. These two are visible at the default layout.
6. With the stage full width at all widths the default office is framed for the whole window, so the Archive shelf on the right now sits under the default usage column at 1280px (move the panel to see it). Janice decided this; recorded here because the default picture changed.

**How to verify**
```
python -m unittest discover -s tests          # Ran 314 tests ... OK
python scripts/office_app.py ai-office --check   # up to date (162 KB, 84 events)
python scripts/golden.py ai-office            # golden: 13 cases, 75 checks, 0 problems
python scripts/board.py ai-office             # 59 tasks (board.md discarded)
```
Mutation check: changing `SNAP: 12` to 14 in the page makes `test_panel_layout_maths` and `test_committed_page_is_up_to_date` fail.
Headless Chromium (playwright, swiftshader), 1280x800 on the recorded page, scripts in `/tmp/t059-scripts`, shots in `/tmp/t059-shots/`:
- `01-default-1280.png` default (identical in `04-after-reset-1280.png` after Reset layout; `store None`, live text "Layout reset")
- `02-mouse-moved-resized-40pct-1280.png` real mouse: grip dragged from (1004,60) to (384,160), corner dragged +60 wide, slider via keyboard to 40; storage `{"usage":{"x":384,"y":160,"w":324,"h":576,"o":40},...}`; `03-after-reload-1280.png` same layout after reload
- `05-keyboard-1280.png` keyboard only (Shift+arrows, Alt+arrows, handle arrows, Home on ticker); live: "Usage panel at 684, 92, size 464 by 644."
- `06-phone-390.png` 390x844 unchanged (grip display none, no `.free`); `09-800px.png` 800px unchanged
- `07` storage throwing (drag still works), corrupt storage -> default, touch drag on a 1024x768 touch context (ticker moved 300,204), window shrink to 900x500 re-clamps, snap to x=8 from x=14, off-screen drag stops at 8,56. Console errors: none (all runs).
- Contrast (Dinda asked for 4.5:1 at 0, 30, 60%), `08-contrast-lightest-NN.png`, panel on the lightest part of the scene, measured on the pixels hugging the glyphs with the shadow included: typical text run 8.5:1 (0%), 9.8:1 (30%), 8.9:1 (60%), 13.2:1 (92%); the worst runs, where text sits over a whiteboard or paper object, are 1.28:1 (0%), 3.17:1 (30%), 2.84:1 (60%), 5.52:1 (92%). So 4.5:1 is NOT met in the worst case at 0, 30 and 60%; it is met over dark floor and wall. Not fixed here: a stronger fix (a minimum scrim) is a design call between "see-through" and "always legible". See Open questions.

**Known limits**
- Touch drag was driven with CDP touch events, not on a real tablet. No test runs the view code in CI (only the pure maths is node-tested); the browser runs above are by hand.
- On window resize, panels are clamped in memory only; after shrinking and growing the window again they stay at the shrunken position until reload.

— Sebastian (engineer)

Decision (Merwyn, 26 Nov 2026 ~14:20 WIB, recorded by Janice): below 60% opacity, each text line keeps a soft dark backing so it stays readable; the panel itself stays see-through as set. Rework to add it, then review.

## Review log

## Decision

## Open questions
- Worst-case contrast over light scene objects is below 4.5:1 at 0%, 30% and 60% opacity (numbers in Build notes). Add a minimum scrim, a stronger shadow, or accept? Who can answer: Dinda (designer), Merwyn for the see-through versus legibility trade-off.
- Deviation 1 (top limit is under the top bar) and 2 (gear shown at 900px and wider): accept? Who can answer: Dinda (designer) or Janice (pmo).
