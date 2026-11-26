---
id: T-066
title: "Chat as a docked section below the office; the office resizes"
phase: 6-office
status: build
priority: P1
owner: engineer
where: code
project: ai-office
depends_on: [T-065]
pr: 60
---

> Merwyn, 26 Nov 2026 17:48 WIB: "for chat, i prefer a dedicated section (not in the front) when chat expanded (horizontal below) it will resize the office"

## Facts (Janice)
- Today (T-063) the chat is a floating panel over the 3D office (`#chat`, class `panel pp`, bottom right on desktop; a full-height sheet under 900 px). It is one of the movable panels of T-059 (`PANEL.IDS` has `chat`, layout saved in `office.layout.v1`).
- The Chat button in the bottom bar opens and closes it (`openChat`/`closeChat`; the open state is saved in `office.chat.v1`).
- The published page is the one "AI Office" artifact, built with `office_app.py ai-office --ledger <session ledger> --chat` (T-065).

## Done when
- [ ] Opening chat shows it as a full-width section below the office, not over it; the 3D view shrinks to the space left above it, and no panel or office content sits under the chat
- [ ] Closing chat gives the office its full height back
- [ ] Works on desktop and phone widths; keyboard, focus and screen-reader behaviour from T-063 stay
- [ ] Chat features from T-063 are unchanged (mentions, statuses, needs-you, scan, notice, Clear chat)

## Spec
**Problem.** The chat floats over the 3D office and hides part of it. Merwyn wants chat as its own section: when expanded it sits below the office, full width, and the office shrinks to fit.

**In scope**
- Chat is a docked section below the office view, not a floating panel (it stops being a movable T-059 panel).
- Expanded: the office view takes the height left above the chat. Collapsed: the office has its full height.
- Desktop and phone widths. On phone the chat also docks below (the full-height sheet goes away); it must leave a usable office strip above it.
- The other floating panels (usage, latest events) stay over the office, inside the shrunken office area, and are never covered by the chat. They stay movable within it.
- The bottom bar stays, and stays reachable; the Chat button still opens and closes the section.
- The open or closed state is still saved per viewer (`office.chat.v1`).

**Out of scope.** New chat features; changes to the chat database, inbox or agents; moving or restyling the other panels beyond staying inside the office area; side or top docking; the recorded usage page (still has no chat).

**Done when (refined)**
- [ ] Expanded at 1280x800 and 390x844: the chat spans the full width below the office, its top edge is at or below the office's bottom edge, and no part of the 3D view, usage panel, latest-events panel or bottom bar is under it.
- [ ] Expanding or collapsing resizes the 3D canvas to the space left, with no distorted view and no page scroll; collapsed, the canvas is back to its full height.
- [ ] Usage and latest-events panels remain visible and usable when chat is expanded, and drag positions saved before this change do not push them off screen.
- [ ] The bottom bar stays visible and its buttons work with chat expanded and collapsed.
- [ ] Reload restores the saved open or closed state; first visit uses the same default as today.
- [ ] Keyboard, focus and screen-reader behaviour from T-063 stays (Chat button state, Escape/close, focus return, live replies).
- [ ] Mentions, per-recipient statuses, needs-you, scan, notice and Clear chat behave as in T-063; C1–C8 still pass; all tests, golden and --check pass; headless screenshots of collapsed and expanded at both sizes, no console errors.

**Spec approved** (Janice, 26 Nov 2026 17:52 WIB). C1-C8 are the conditions in T-063's "## Compliance" section. Dinda writes the UX design first, then Fang folds it into Design.

## Design

### UX (Dinda)
**Layout (top to bottom).** top strip (agents, pill) / office stage / bottom bar / chat. The bar sits between the office and the chat, so the Chat button is a tab on the seam of the section it opens, never covered, and on a phone the keyboard hides only the chat. Chat is full width, flush to the screen bottom, same `.panel` look without the 12px radius at the bottom. Collapsed: today's layout exactly (stage bottom = bar). Expanded: `#stage{bottom:calc(var(--bar) + var(--chat-h))}`; the chat is no longer absolutely over it.
**Height.** Adjustable via a handle on the chat's top edge (full width, 8px visible line, 24px hit area, 44px on touch; grab cursor `ns-resize`). Default desktop 38% of viewport height (304px at 800), phone 40% (about 338px at 844). Min 180px (header, 2 thread lines, composer). Max = viewport minus chrome minus minimum office: office stage never under 240px on desktop and 160px on phone. Double click or Enter on the handle resets to default. Saved per viewer as `h` in `office.chat.v1` (px, re-clamped on load and on resize; invalid or absent = default). Answers Emmy: adjustable yes; bar above chat; height saved yes.
**Handle a11y.** `role="separator" aria-orientation="horizontal" tabindex="0" aria-label="Resize chat" aria-valuemin/max/now` (px). Up/Down 16px, Shift 64px, Home/End min/max. Pointer drag with pointer capture; no transition while dragging; canvas resized once per animation frame, never CSS-stretched.
**Office when it shrinks.** The 3D view re-fits (aspect from the new size, same camera target, no distortion). Usage and latest-events stay over the stage and are clamped to the stage rectangle (`pbounds` bottom = stage bottom, not window bottom); when a panel no longer fits it moves up or shrinks to its minimum (240x120), it never goes under the chat. Saved positions are only clamped for display, not overwritten, so closing chat restores where Merwyn put them. Agent strip and bar unchanged; the agent focus card stays inside the stage.
**Phone 390x844.** Under 900px the sheet goes; chat docks under the bar (the bar already holds the 36px tone strip above it). Chrome is about 212px, so default chat 340px leaves a 292px office strip. While the keyboard is up (visualViewport shorter than layout height) the chat takes all room under the top strip and the stage may collapse to 0; the office comes back when the keyboard closes. Composer stays above the keyboard via `--kb`; safe-area padding on the chat bottom.
**Motion.** Open and close: chat height 0 to `--chat-h` over 180ms ease-out (close 140ms ease-in), the stage resizes in step. Purpose: shows the office making room, not jumping. Reduced motion (and body.rm): no transition, instant swap. No motion on drag or on keyboard resize.
**Focus and ARIA.** DOM order: stage, bar, chat; Tab goes bar buttons, then handle, then close, thread, composer. Opening focuses the composer, closing returns focus to the Chat button, Escape closes (all as T-063). Chat button keeps `aria-expanded` and gains `aria-controls="chat"`. The chat stays `role` region "Office chat" with the thread `role="log"` and `aria-live="polite"`; hidden while closed. Handle focus ring uses the existing 2px outline.
**Saved layout.** `chat` leaves `PANEL.IDS`. The `chat` entry in `office.layout.v1` is ignored on load and dropped on the next save; "Reset layout" ignores chat; no move, resize or opacity controls on the chat. Usage and ticker entries are untouched.
**States that must still render** (T-063, now inside a 180px to full height section): empty with notice, autocomplete list (opens upward over the thread, never under the bar), sent and per-recipient chips, needs-you amber edge with "Show X in the office" (the stage is still visible to show it), blocked personal-data send, db null, signed out, offline banner, office not running note, Clear chat, New replies pill. At min height the notice, note and footnote scroll with the thread; composer and header never scroll away.
**Accessibility check.** Handle is operable by keyboard, pointer and touch; 44px targets on phone; contrast uses theme tokens as today; reduced motion covered; no information only by motion. Panels never hidden by chat.
**Open questions.** None for Merwyn. For Fang: confirm renderer resize per frame is cheap enough on the software GL used in screenshots.

### Technical design (Fang)
Dinda's UX accepted as written. Only `engine/app/office.template.html` and `tests/test_office_app.py` change (plus the rebuilt `engine/app/office.html` and golden if it moves). No new files, no Python change.

**Layout: one CSS variable, not a DOM rewrite.** Keep today's absolute layout and media queries; add `--chat-h` (0px when closed). Register it with `@property --chat-h{syntax:'<length>';inherits:true;initial-value:0px}` so the open/close transition animates it (180ms out / 140ms in, `transition:none` under `body.rm`, `prefers-reduced-motion` and `.drag`). Rules: `#chat{left:0;right:0;bottom:0;top:auto;width:auto;height:var(--chat-h);border-radius:12px 12px 0 0;padding-bottom:env(safe-area-inset-bottom)}`, `#bar{bottom:var(--chat-h)}`, `#stage,#side{bottom:calc(var(--bar) + var(--chat-h))}`, and every other rule anchored to `bottom:calc(var(--bar) ...)` gets `+ var(--chat-h)` (grep: `#tone`, `#usheet`, `#msheet` x2, phone `#focus`, `body.tk #ticker`, phone `#stage`). Delete the `<900px` full-screen sheet block and `body.free #chat.placed`. DOM order: move `#chat` after `#bar`; add `<div id="chgrip" role="separator" ...>` as the chat's first child (attributes and keys as Dinda). `#chatbtn` gains `aria-controls="chat"`.
**Height maths (pure, in `C`).** `C.chatDock = {MIN:180, DEF_D:.38, DEF_P:.40, MIN_STAGE_D:240, MIN_STAGE_P:160, STEP:16, STEP_BIG:64}`; `C.chatH(want, vh, chrome, phone, kb)` returns px: invalid/absent `want` = default (round(vh*DEF)); clamp to `[MIN, vh - chrome - minStage]`; if that max is below MIN, MIN wins (tiny landscape: the office strip shrinks, the composer stays usable); if `kb > 0` return `vh - kb - topStrip` (stage may be 0). `chrome` is measured once per layout tick (`#top` + `#bar` + `#tone` heights: 112 desktop, about 212 phone). Page side: `dockLayout()` sets `--chat-h` on `<html>` from `chatOpen() ? C.chatH(CS.st.h, innerHeight, chrome, phone, kb) : 0`, and updates `aria-valuemin/max/now`. Called from openChat, closeChat, handle drag/keys, window resize and the existing visualViewport `kb` listener.
**Renderer and camera (answers Dinda).** The existing `resize()` (W/H from `stage.client*`, `renderer.setSize(W,H,false)`, `fitHome`, `applyCam`) already keeps aspect and camera target; it is already on a ResizeObserver on `#stage`. Change: the RO and window listeners only set a flag, and one `requestAnimationFrame` runs `resize()` once per frame. During a drag or the 180ms transition this is at most one `setSize` per frame (about 11 on open). Software GL measured cost is the risk, so: when the page is in its low-res mode (`lowRes`, pixel ratio 1) or a drag is under way and the last frame took over 50ms, skip intermediate resizes and resize on `pointerup` / `transitionend` only (the canvas keeps its CSS 100% box for those few frames; acceptable, no lasting distortion). `transitionend` on `#chat` also calls `resize()` once, so the final size is always exact.

| Option | Cost | Risk | Pick |
|---|---|---|---|
| Resize every RO callback (today) | up to 2 setSize/frame | jank on swiftshader | no |
| rAF-coalesced, one per frame, end-only fallback when slow | small | none lasting | **yes** |
| Resize only at end of motion | smallest | stretched view for 180ms, visible on drag | fallback only |

**Panels (T-059).** `PANEL.IDS = ['usage','ticker']`; `PNAME.chat`, the chat grip/menu/rz, `PL.r.chat`/`PL.pending.chat` and the openChat clamp line go. `C.panelBounds(winW, winH, barH, dockH)` gets a 4th arg (default 0): `bottom = winH - barH - dockH - MARGIN`; `pbounds()` passes the live `--chat-h` in px. Saved rect vs shown rect: `PL.r[id]` stays the viewer's rect; `paintRect` paints `C.clampRect(PL.r[id], pbounds())`. The window-resize handler stops writing the clamped rect back into `PL.r` (today `settle` replaces it); drag and keys start from the shown rect and only then write `PL.r`. So closing chat restores where Merwyn put them. `dockLayout()` calls the same re-clamp so panels move with the chat, not only on window resize.
**Saved state.** `office.layout.v1`: the loader already iterates `PANEL.IDS`, so a `chat` entry is ignored on load and absent from the next save; Reset layout covers usage and ticker only. `office.chat.v1`: add `h` (finite number, else absent); move parsing into a pure `C.chat.parseSt(json)` returning `{open, seen_at, ack, h}`; `h` is re-clamped on every use, written only by handle actions (Enter/double-click writes absent = default). Default `open` stays false.
**Size budget.** Built page is 216,739 B against a 221,184 B (216 KB) limit, 4.4 KB headroom. Removed: phone sheet CSS, chat panel hooks (about 1 KB). Added: dock CSS, handle, `chatH`, `parseSt`, rAF throttle (about 2.5 KB). Target net +2 KB, limit unchanged at 216 KB. If it does not fit, trim before raising; any raise is stated in Build notes with the number.
**Tests.** Node mode `dock` in `test_office_app.py`: `chatH` (absent, NaN, negative, string, huge, below MIN, default at 800 and 844, phone vs desktop min stage, max<MIN, kb>0); `panelBounds` with dockH and a saved rect below the dock clamps above it while the input rect is unchanged; layout loader drops a `chat` entry and the saver omits it; `parseSt` with corrupt JSON, missing `h`, bad `h`, and T-063-era objects (no `h`). Existing `layout` and `chat` modes updated for the 2-panel IDS. Headless (as T-063, stub under /tmp, never committed) at 1280x800 and 390x844: collapsed, expanded default, expanded at min and max, phone with a simulated `--kb`, panels saved below the dock before opening, handle by keyboard; assert from `getBoundingClientRect` that chat top >= bar bottom >= stage bottom, canvas drawing-buffer size equals stage client size x pixel ratio, `document.scrollingElement.scrollHeight == innerHeight`, no console errors. All tests, golden and `--check` pass.
**Risks.** (1) Missing one `bottom:var(--bar)` rule leaves an element under the chat: grep list above plus the rect assertion in headless. (2) `@property` unsupported: transition is skipped, layout still correct. (3) Phone keyboard: stage at 0 height must not throw; `resize()` already floors W/H at 1. (4) Needs-you "Show X in the office" needs a visible stage: fine at default and min heights; with keyboard up the stage returns when it closes.
**Compliance.** No change to data flow, storage, scan, notice, retention or agents; C1 to C8 are untouched (notice and footnote still render, scroll with the thread at min height). Not flagged; Wulan not needed.
**Decision record draft (for the Curator).** Decision: chat docks below the bar via a `--chat-h` CSS variable on the existing absolute layout; renderer resize coalesced to one per frame. Options: flex column rewrite of the shell (more churn across 3 media queries, no user gain); keep chat as a T-059 panel with a "docked" mode (two code paths); variable on existing layout (chosen, smallest change). Why: reuses the T-059 clamp maths and the existing ResizeObserver; saved state stays backward compatible.
— Fang (architect)

## Build notes
**What changed** (only `engine/app/office.template.html`, `tests/test_office_app.py`, rebuilt `engine/app/office.html`; no Python change, no new files, golden unchanged).
- Chat is a docked section: DOM order stage, bar, chat. `--chat-h` (registered with `@property`, animated 180ms out / 140ms in, none under reduced motion) is set on `<html>` by one function, `dockLayout()`. `--bb` = `--bar` + `--chat-h` replaces `var(--bar)` in every bottom anchor (stage, side, tone, usage sheet, both menu sheets, phone focus card, ticker overlay). Phone sheet and `body.free #chat.placed` removed. Focus card gets a max-height so it stays inside the stage.
- Handle `#chgrip` (role separator, keys Up/Down 16, Shift 64, Home/End min/max, Enter or double click reset, pointer drag with capture). Height saved as `h` in `office.chat.v1` (handle actions only; re-clamped on every use).
- Pure core: `C.chatDock`, `C.chatH(want, vh, chrome, phone, kb)`, `C.chat.parseSt`, `C.panelBounds(..., dockH)`; `PANEL.IDS` is now usage and ticker; chat is no longer a `.pp` panel.
- Panels: saved rects are kept as saved and only painted clamped (`shown(id)`), so closing chat restores where the viewer put them. Window resize no longer writes the clamped rect back.
- Renderer: ResizeObserver and window resize only request one resize per animation frame; if the dock is moving, `lowRes` is on and the last frame took over 50 ms, intermediate sizes are skipped and the exact size is set at drag end / `transitionend` / a 260 ms timer.
- Close: the section is hidden after the 140ms close motion (immediately under reduced motion); focus returns to the Chat button at once; `aria-expanded` flips at once.
- `#cmid` wraps note, thread and notice so at minimum height the note and notice scroll with the thread; header and composer never scroll away.

**Deviations from the Design**
- Size: the Design estimated +2 KB; the build is +4.0 KB (committed page 220,777 B of 221,184 B, 407 B headroom). Limit NOT raised. I trimmed about 1.1 KB of comments to fit, including a few older trailing `//` comments in the T-059/T-063 code. The ledger build used for the published page is 222 KB (it is not covered by `test_size_limit`, as before).
- `chatH` with the keyboard up returns `max(180, vh - kb - chrome)` (the chat minimum wins in a tiny window); `dockLayout` then adds `kb` into `--chat-h` so every anchor stays consistent and the chat sits at `bottom:var(--kb)`.
- Handle hit area is the 12px strip (28px on phone) plus 8px above and below via `::before` (28px desktop, 44px phone), not 24px/44px above only, because the chat clips its overflow during the open motion.
- `dockPx` uses the target height, not the animated computed value, so panels move to their final place at once.

**How to verify**
- `python -m unittest discover -s tests` (388 tests, exit 0; new: `test_chat_dock_maths_under_node` runs node mode `dock`, `test_chat_is_docked_not_a_panel`; `layout` mode updated for two panel ids), `python -m engine.runtime validate ai-office`, `python scripts/office_app.py ai-office --chat --check`, `python scripts/board.py ai-office` (board.md discarded): all exit 0.
- Headless Chrome (CDP over a copy in /tmp with a stub `claude`, software GL), assertions from `getBoundingClientRect`: chat full width and flush to the bottom; chat top >= bar bottom >= stage bottom; usage and ticker bottoms <= stage bottom; canvas buffer = stage client size at pixel ratio 1; `scrollHeight == innerHeight`; no console errors or exceptions. Cases, all passing: 1280x800 closed (stage 688), open default (chat 304, stage 384), max (448/240), min (180/508), window 1280x560 open (208/240), toggle open then closed, keys Up/Up/Down/Home/End/Enter, pointer drag (+100px, saved `h:404`), saved panel rects below the dock (clamped above it when open, back at the saved place when closed, loaded `chat` entry ignored), Escape returns focus to the Chat button; 700x900 tablet; 390x844 closed (stage 632), default (338/294), max (472/160), min (180/452), simulated keyboard 330px (chat fills under the strip, stage 0, office back after). The published build (ledger plus `--chat`) was spot-checked at 1280x800 closed, open and after a key resize, and 390x844 open.
- Not run: a real touch device or real soft keyboard (the keyboard was simulated through a fake `visualViewport`). Software GL here runs about 12 to 60 fps, so the smoothness of the open motion on real GPUs is unmeasured.
- Screenshots (not committed), in /tmp/t066: shot-closed-1280x800.png, shot-open-1280x800.png, shot-open-1280x800-max.png, shot-open-1280x560-resized.png, shot-closed-390x844.png, shot-open-390x844.png, shot-open-390x844-kb.png, shot-pub-closed-1280.png, shot-pub-open-1280.png, shot-pub-open-390.png. The harness prints its result JSON at the top of the page, so it shows in the screenshots only.

**Open questions**: none. C1 to C8 untouched (notice, footnote, scan, storage and agents code not changed; chat state stays in `office.chat.v1`, now with `h` only).
— Sebastian (engineer)

## Review log
**Review 1 (26 Nov 2026): REJECT.** One spec failure, on the C3 notice. Everything else passes.

Commands run on `t-066-chat-dock` at 5d4ae9e:
- `python -m unittest discover -s tests`: `Ran 388 tests ... OK`, exit 0.
- `python -m engine.runtime validate ai-office`: `ai-office: OK — 8 agents, 5 stages, 66 tasks, 18 skills`, exit 0.
- `python scripts/office_app.py ai-office --chat --check`: `engine/app/office.html: up to date (215 KB, 84 events)`, exit 0.
- Size: `git show HEAD:engine/app/office.html | wc -c` gives 220777. `test_size_limit` is still `216 * 1024` (221,184) and the diff does not touch it, so the 407 B headroom is real. Published build (`--ledger ...session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat --out /tmp/...`): exit 0, 228,127 B. No size test covers it, same as before this PR.
- Headless Chromium (Playwright, software GL, dpr 1). I used my own harness and stub `claude` under /tmp, and wrote it before reading the Build notes. Screenshots were not committed. Checks come from `getBoundingClientRect`. Each case checks: chat is full width (l=0, r=vw); chat top >= bar bottom >= stage bottom; usage, ticker and tone bottoms are above the chat top and inside the stage; canvas buffer = stage client size; `scrollHeight == innerHeight`; `scrollY == 0`; no console errors or page exceptions.

Done-when checks:
1. Full width below the office, nothing under it, at 1280x800 and 390x844: **pass**. 1280: closed stage 688; open 304/384; keys +32, Shift -64, End 448/240, Home 180/508, Enter back to 304. Drag +100 gives 404 and saves `h:404`. Dragging to the top clamps at 448. 390: closed 632; open 338/294; End 472/160; Home 180/452; drag gives 438. Every case was OK.
2. Canvas resizes with no distortion and no page scroll; full height again when closed: **pass**. The buffer matched the stage size in every case. Mid-open (60 ms, `--chat-h` 370.9px) `scrollHeight` was 800 = innerHeight. Closing gives back 688 and 632.
3. Panels stay visible and usable; saved positions do not push them off screen: **pass**. With a saved layout of usage (900,500) and ticker (100,560), plus a stale `chat` entry, the panels moved up above the dock when open (bottoms 432 at default, 288 at max). After Escape they were back at exactly (900,500) and (100,560), and the stored `office.layout.v1` was not rewritten. Window 1280x560 open gives 208/240; back at 800 the saved 448 is restored.
4. Bottom bar visible and its buttons work, open and closed: **pass**. An `elementFromPoint` hit test on every visible bar button gave true for all, at both sizes, open and closed.
5. Reload restores open or closed; first visit is closed: **pass**. On first visit `office.chat.v1` is null and the chat is closed. Reload keeps open at 448, or closed.
6. Keyboard, focus and screen reader behaviour from T-063: **pass**. After acknowledgement, opening focuses `ctext`. Before it, focus stays on the Chat button, as on main, because the composer is disabled. Escape and × return focus to `chatbtn`, and `aria-expanded` flips. Escape inside the mentions list closes only the list. Grip `aria-valuemin/max/now` = 180/448/304 (desktop) and 180/472/338 (phone).
7. T-063 features, C1-C8, tests and screenshots: **fail on the notice (C3 surface)**. Mentions list (9 items, inside the chat, never under the bar), per-recipient chips ("needs you", "answered", "is replying", "waiting for ... to pick up"), the needs-you amber edge, the pill and "Show Fang in the office" (focus card 60-292 inside the stage, bottom 296), the blocked 16-digit send ("This looks like personal data or a secret (16-digit run). Not sent."), the empty, nodb and "office not running" states, the footnote and Clear chat all render. The published page and the no-chat page have no errors.
   **The failure: on first visit the notice and its "I understand" button are no longer fully visible.** They now sit inside the `#cmid` scroller, which is not scrolled to them.
   - 390x844 at the default height: `#cmid` shows y 599-735. The notice spans 684-812 and its button 776-803. The text is cut mid-sentence and the button cannot be seen. The composer is disabled until acknowledgement, so a first-time phone user sees a disabled box and no way forward unless they find a thin inner scroll.
   - 1280x800 at the default height: the button spans 686-713 against a visible bottom of 701, so it is half hidden.
   - On main (T-063) at both sizes, the notice and button were fully visible on first open: 1280 button 587-615 above the form at 630; 390 button 691-719 above the form at 734.
   - At min height (180) `#cmid` is 22 px tall on desktop and **0 px on phone**. The thread, note and notice cannot be seen at all, and on the phone they cannot be scrolled to. That also misses Dinda's definition of the minimum: "header, 2 thread lines, composer".
   No C1-C8 logic changed. The scan, the ack gate (composer stays disabled), the notice and footnote text, storage and agents are untouched in the diff. The comments trimmed for size are explanatory only. But the C3 notice is no longer shown as it was in T-063, which the spec's "notice ... behave as in T-063" rules out.

**Fixes needed (back to build):**
1. While the notice still needs acknowledgement (`ack` false), the full notice text and "I understand" must be visible without inner scrolling at the default height at 1280x800 and 390x844. For example, keep the needs-ack notice outside `#cmid` as a `flex:none` block like the composer, or scroll it into view whenever it renders in the `need` state.
2. At minimum height the middle area must show at least two thread lines on both sizes (Dinda's min). The needs-ack notice must stay reachable there too. Options: raise `C.chatDock.MIN`, or derive it from the measured header plus composer, or compact the header and composer at small heights. Update the `dock` node tests if MIN changes.
3. Add a headless or node-level assertion that fails if, on first open, the needs-ack notice button is outside `#chat`'s visible box.

**Non-blocking notes**
- Two lines keep trailing spaces where comments were removed: `function dockEnd() {   ` and `function dockLayout(anim) {   `.
- Some comments removed for size explained real edge cases: `fmtTok` rounding ("2,150,000 reads 2.2M"), the `nameCol` 4.5:1 rule, and the "clamped in memory only: storage is untouched" note in `applySaved`. Consider restoring the `fmtTok` and `applySaved` ones once there is room.
- With 407 B left, the next page change will need either a limit raise or more trimming. Please state the number when that happens.
- Reopening during the 140 ms close motion keeps the `cc` (ease-in) class until `dockEnd`. This is cosmetic.
- External skills `design:accessibility-review` and `data:validate-data` are not available in this session. I did the accessibility checks by hand (above).
— Cahyani (reviewer)

## Decision

## Open questions
- (Answered by Dinda in Design, UX: adjustable, bar above chat, height saved.) Can the chat height be adjusted (drag handle, presets) or is it fixed? Not a stated preference; the Design may choose. Dinda (UX) and Fang (design) to answer. Whatever is chosen must keep a minimum office height on a phone.
- Where does the bottom bar sit relative to the chat: above it or below it? Same owners (Dinda, Fang).
- Should the chat height be saved per viewer if adjustable? Dinda, Fang.
