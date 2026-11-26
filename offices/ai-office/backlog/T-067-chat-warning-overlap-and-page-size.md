---
id: T-067
title: "No overlapping parts: panels, chat and bar never cover each other; composer warning; page-size headroom"
phase: 6-office
status: build
priority: P1
owner: reviewer
where: code
project: ai-office
depends_on: [T-066]
pr: 66
---

> From Cahyani's T-066 Review 2 (26 Nov 2026): at minimum chat height, when a composer warning shows (offline, blocked send), the thread runs under the composer; on a phone about 4 px of thread shows and the last message shows through the "Not sent" warning. The warning stays readable and the send stays blocked.

> Merwyn, 26 Nov 2026 18:48 WIB: "if i expand chats, the usage and latest events are overlapped. Can you ensure each components can't overlapped (aside from the office)". At 18:50 he said go past 80% of the 8M budget for this.

## Facts (Janice)
- The committed `office.html` is 221,168 B of the 221,184 B (216 KB) limit after T-066: 16 B of headroom. Any page change needs trimming or an Architect decision on the limit.

## Done when
- [ ] With chat open at any height, and at any window size, the usage panel, latest events, the focus card, menus and sheets never overlap each other, the bar or the chat; only the 3D office may sit behind them. This holds for the default (flow) layout and for moved or resized panels (T-059)
- [ ] With a composer warning shown at minimum height, the thread area is clipped above the composer (or the minimum re-measured) on 1280x800 and 390x844; nothing shows through the warning
- [ ] A size decision by the Architect is recorded (trim, raise the limit with a reason, or split the page), and the page fits it

## Spec
**Problem.** With chat expanded, UI parts can still land on top of each other (Merwyn: usage and latest events overlap). Also, at minimum chat height a composer warning lets the thread run under it. And the page has 16 B of headroom, so any fix needs a size decision.

**In scope**
1. No overlap, first priority. No UI part may overlap another: usage, latest events, focus card, menus and sheets, needs-you pill, agent strip, bottom bar, chat dock. Only the 3D office may sit behind them. This is the default (flow) layout and moved or resized T-059 panels, on desktop, a narrow window and phone widths, with chat closed and at default, min and max height.
2. When there is not room for every panel, no two may overlap. What gives way (hide, stack, collapse, scroll, shrink) is for Dinda and Fang to choose (open question, not Merwyn). Whatever gives way must stay reachable, and the saved layout is not overwritten (as T-066).
3. Composer warning (offline, blocked send): the thread never shows through it, at any height including min, and the warning stays readable. Send stays blocked.
4. Page size: the Architect records a decision (trim, raise the limit with a number and reason, or split), and the page fits it. Merwyn approved spending past 80% of budget for this task (26 Nov, 18:50 WIB).

**Out of scope.** New features; restyling; chat behaviour, notice, scan or storage (T-063/T-066 unchanged, C1-C8 unchanged, min height still measured); recorded usage page; real-device touch testing.

**Done when (refined)**
- [ ] At 1280x800, a narrow window (about 700x900) and 390x844, with chat closed, at default, min (after ack and before) and max: measured rects of usage, latest events, focus card (open on an agent), open menu or sheet, needs-you pill, agent strip, bar and chat do not intersect, and each is inside the window. Only the canvas lies under them.
- [ ] Same with moved and resized panels saved in `office.layout.v1`, including panels saved in the chat's area or on top of each other: shown rects never intersect; the saved values are not rewritten, and closing chat restores them.
- [ ] A window too small for all panels (for example 1280x560 and 390x600) still has no overlap; every panel that is hidden or collapsed can be brought back; the Chat button and bar stay usable.
- [ ] At min height on 1280x800 and 390x844, with the offline warning and with a blocked send (16-digit run): the thread is clipped above the composer, nothing shows through the warning, and the warning is fully visible. Send is still blocked.
- [ ] A size decision is written in Build notes or Design with the numbers; the page fits it; `test_size_limit` matches.
- [ ] A test fails if any pair of listed parts overlaps (headless rect check, plus a pure-maths test for the placement rule). T-063/T-066 checks and C1-C8 still pass; all tests, golden and `--check` pass; screenshots of each case, no console errors.

**Open questions**
- What gives way when panels do not fit (stack, collapse to a chip, hide the lowest priority, scroll)? Dinda (UX) and Fang (design) decide; a small-window rule, not for Merwyn.
- Is the 216 KB limit raised, trimmed or split? Fang. A limit change is stated with the number.
- Does the focus card or a menu count as a layer that may cover a panel while open? Merwyn's ask says no overlap at all; Dinda to confirm how a sheet on a phone stays within this.
— Emmy (pm)

**Spec approved** (Janice, 26 Nov 2026 18:55 WIB). Dinda writes the UX first, then Fang the technical design and the size decision.

## Design

### UX (Dinda)
**Cause (read from code).** In the flow layout `#side` is a flex column with `#usage{min-height:0;overflow:visible}` and `#ticker{min-height:96px}`; when chat shrinks the column below usage + 8 + 96, usage keeps its content height and spills over latest events. The desktop focus card also sits at the same top-right spot as the column (z 5), and on a phone the focus card, `#usheet` and `#msheet` share `bottom:bb+40`. The rule below removes all three.
**Rule.** The free area is the stage rectangle (below the top strip, above the bar, so above the chat). Everything except the 3D office is a part with a priority and takes its own rectangle in that area; no part is painted where a higher one is. Order: bar and chat (fixed) > open sheet or menu > focus card > usage > latest events. Panels and the card never go under the bar, chat, pill or strip. Only the canvas lies under anything.
**What gives way, in this order** (each step only if the last was not enough): (1) latest events shrinks down to its header plus 1 row and scrolls inside (never below 40px: header and one row); (2) usage collapses to its one-line summary (the existing `.col` state, not saved); (3) latest events collapses to its header line; (4) the lowest part that still does not fit becomes a chip in the bar row ("Usage", "Events": 44px target on phone) and opens as the single sheet. Nothing is lost: chips and sheets are the way back, and the Chat button and bar never move.
**Default (flow), desktop.** Column below the focus card when it is open (column top = card bottom + 8; card max-height 45% of the stage so the column keeps room). 1280x800: closed 688px stage, nothing gives way; chat default (stage 384): usage expanded, events about 200px, scrolls; chat min (stage 508 minus warning, about 500): same as default; chat max (stage 240): usage collapses to one line, events shrinks to about 120px; 1280x560 with chat open (stage 240): as max, and with the focus card open, step 3 and 4 apply (events header, then Usage chip). Narrow window 700x900 and phone: panels are not in the stage (as now: `#side` hidden, tone strip, sheets).
**Phone 390x844.** Closed, default, min, max: no panel is shown, only the tone strip, pill and strip. At most ONE transient layer at a time: the usage sheet, the ticker overlay, the menu and the focus card replace each other (opening one closes the others, focus returns to the control that opened it). The layer sits above the tone strip, its max-height is the stage height minus 8px (never into the top strip or the chat) and it scrolls inside. At 390x600 with chat open (stage about 160px) the layer is that small and scrolls; that is the last resort and is allowed.
**Moved or resized panels (T-059).** Saved rects in `office.layout.v1` are never changed by this. The shown rect comes from one pure placement function (Architect names it; input: saved rects in priority order, the focus card rect, bounds): clamp each rect into the bounds (as now), then if it meets a higher part, try in order: (a) slide it up or down the shortest way, (b) slide sideways, (c) shrink height to the free gap (min 120 for usage, 40 for events), (d) collapse (step 2 or 3 above), (e) chip. A part that the viewer places on top of another is accepted and saved, but shown after the rule; during a drag the dragged panel stops at the neighbour's edge (the other panel is never pushed) and shows no overlap. Resizing is stopped at the neighbour's edge the same way. Dock resize, window resize and opening the focus card re-run the placement; when there is room again, every part returns to its saved rect (placement is recomputed from saved values, never from the last shown value). Reset layout is unchanged.
**Focus card and menus.** They are parts, not layers: on desktop the card takes the top of the right column and the panels yield (above); the card keeps `max-height` and scrolls. The gear menu `#msheet` opens above the bar inside the stage; if a panel sits there it yields for as long as the menu is open (menu has priority, panels return on close). Opening the focus card in flow with chat at max: usage collapses and events becomes a header line, the card is never covered.
**Composer warning at min height.** The warning (offline, blocked send) lives in the composer block, above the textarea, on solid `var(--panel)` (no transparency), 12px, wraps up to 2 lines, never truncated, `role="alert"` as today. Its height counts in the minimum (`need` in `dockLayout`), so min height grows by the warning (about 32px; 1280x800 min is 212px with it, phone same). The thread area is `overflow:hidden` clipped at the composer top. If the window is so short that nothing fits, the thread gets 0 lines first; the warning and composer are never clipped. Send stays blocked. Motion: none (the warning appears instantly; the chat height change on appear is not animated). Contrast uses the existing danger and text tokens (at least 4.5:1).
**Motion.** Panels keep their 160ms settle (`.anim`) when placement changes after a dock or window change; purpose: shows where a panel went. Reduced motion and `body.rm`: instant. A collapse to a chip has no animation. No information only by motion: the chip label names the part.
**Accessibility check.** Chips are buttons with names and `aria-expanded`; one sheet at a time keeps focus order simple; Escape closes the open layer and returns focus to its opener; the card, sheets and chips are 44px on touch; the list scrolls by keyboard (tabindex 0 on the scroll area); no colour-only cues.
**Page size (for Fang).** Keep it lean: one placement function (pure, shared by flow and free), `min-height` plus `overflow:hidden` CSS for the shrink steps, and reuse `.col` and the sheet for step 4; no new component. Drop the chip if bytes decide, then the Usage and Events sheets stay reachable from the existing Usage button and the existing events overlay.
**Answers to Emmy.** (1) Order above; small-window rule, not for Merwyn. (2) Size is Fang's. (3) No: the card or a menu never covers a panel; the panel yields, and on a phone one layer at a time stays inside the stage.
**Open questions.** For Fang: is the chip in the bar affordable in bytes (else use the existing Usage button). None for Merwyn.
— Dinda (designer)

### Technical design (Fang)
Dinda's UX accepted, with the chip answer below. Only `engine/app/office.template.html`, `tests/test_office_app.py` and the rebuilt `engine/app/office.html` change. No new files, no Python change.
**Causes, confirmed in code.** (1) Flow: `#usage{min-height:0;overflow:visible}` with `.ubody` not shrinkable, so usage spills over `#ticker{min-height:96px}`. (2) `#focus` (z 5) sits on the same top-right spot as `#side`. (3) Phone/tablet: `#focus`, `#usheet`, `#msheet`, `body.tk #ticker` share `bottom:calc(var(--bb) + 40px)`; `#usheet{max-height:60vh}` can reach the top strip. (4) Composer: `dockLayout()` already counts `#cform.offsetHeight` in `need`, but `showWarn()` never re-runs it, and `.cwrap{min-height:56px}` overflows `#cmid` under the composer; `#cwarn` is 16% transparent.
**Pure placement, in `C`.** `C.place(b, parts)` -> `{id: {x,y,w,h,s}}`. `b` = `panelBounds(...)` (already excludes top strip, bar, chat). `parts` in priority order, each `{id, r:{x,y,w,h}, min, col, axis:'xy'|'y'|'', fixed:bool}`: `r` is the wanted rect (saved rect, or flow slot), `h` the measured natural height, `min` the shrink floor, `col` the measured collapsed height (header, or header plus summary). Higher parts are obstacles for lower ones, gap `PANEL.MARGIN` (8). Per part: clamp (`clampRect`); if it hits an obstacle, slide the shortest free way (along `axis`); else shrink into the largest free gap in its column band (not below `min`) -> `s:'shrunk'`. Ladder for the whole set (Dinda's order): try with no part collapsed; if any part would go below `min`, collapse the collapsible parts in priority order (usage, then events) and retry; if the all-collapsed set still fails, the lowest failing part gets `s:'chip'` (no rect). `s` is `'full'|'shrunk'|'col'|'chip'`. Inputs are never mutated; output depends only on inputs. **Invariant (tested):** every pair of non-chip outputs has `a.x+a.w<=b.x || b.x+b.w<=a.x || a.y+a.h<=b.y || b.y+b.h<=a.y`; each lies in `b`; `h>=min` unless `s` is `col`; with room, output equals `clampRect(saved)` (so parts return to saved places).
**Desktop (>=900), both layouts.** One `fit()` builds the parts and calls `place`: open `#msheet` (fixed), `#focus` (fixed x/y/w, `h` = its scrollHeight, `min` 96, max 45% of the stage), an open `.pm` folds into its panel's `min` (menu bottom), then usage, then events. Run once per animation frame (coalesced like `reqResize`) from `dockLayout`, window resize, focus open/close, `ucol` click, gear open/close, and a ResizeObserver on `#focus`, `#usage`, `#ticker`. Natural heights are measured with the auto class removed (the `measureDefaults` pattern, sync, no paint); same input gives same output, so the RO settles in one pass.
- **Flow: CSS geometry, `place` only for states.** Sound because a flex column whose children shrink cannot overlap itself: `.ubody{flex:1 1 auto;min-height:0}`, `#tlist{flex:1 1 auto;min-height:0;overflow:auto}`, `#ticker{min-height:0}`, and `#side{top:calc(var(--bar) + var(--fh,0px))}` with `--fh` = focus card bottom + 8 (0 when closed). Flow parts are column slots with `axis:'y'`. Applied as classes: usage `.ac` (auto-collapse, joins every `.col` selector, never saved, `usageCol` untouched), events `.hd` (hides `#tlist`), `chip` hides the part. A `ucol` click while `.ac` pins usage expanded until the next layout change (it may still shrink and scroll).
- **Free (T-059):** `shown(id)` returns the last `place` output instead of `clampRect`; `paintRect`/`animPaint` unchanged otherwise. `PL.r` stays the viewer's saved rect; `fit()` always starts from `PL.r`, never from the last shown rect. Drag and resize: new pure `C.sweep(from, to, obst)` moves x then y, each stopped at the first obstacle edge (the neighbour is never pushed); `dragMove`/`keyAct` write the swept rect. Overlapping rects saved before T-067 load unchanged and are shown after placement.
**Phone and tablet (<900): one layer.** No panels there, so no `place`. `layer(name)` opens one of focus card, `#usheet`, `#msheet`, `body.tk` events and closes the rest (focus returns to the opener; Escape as today). Shared rule: `bottom:calc(var(--bb) + 40px);max-height:calc(100% - var(--st) - var(--bb) - 48px);overflow:auto`, `--st` = stage top (112 phone, `var(--bar)` tablet); `60vh` goes.
**Chip (answers Dinda): no new component.** Usage chip = existing `#ubtn`, shown at >=900 by `body.uchip`; it opens the existing `#usheet`, which joins `fit()` as a fixed sheet in the right column. Events chip = existing `#tone` strip, shown at >=900 by `body.echip` (as on phone; it opens the existing events overlay, a layer); it takes the bottom 36px of the stage as a fixed part. Chips appear only when the stage is below about 230px, i.e. windows under about 480px tall; at 1280x560 with chat (stage 240) everything fits collapsed.
**Composer warning.** `showWarn()` calls `dockLayout(false)` when chat is open, so the min is re-measured with the warning; a height below the new min is re-clamped up (saved `h` not rewritten). `#cmid{overflow:hidden}` clips the thread at the composer top; `#cwarn{background:var(--panel)}` (solid, keeps the warn border, `role="alert"`). Send stays blocked: `sendChat` is unchanged.
**Size decision.** Committed page 221,168 B vs limit 221,184 B (216 KB). Estimate for this build: about +3.5 KB (place + sweep 1.5, fit glue 0.8, CSS 0.7, layer 0.3, warn 0.2), so about 224.6 KB. **Raise the limit to 232 KB (237,568 B)**; the comment in `test_size_limit` gives the reason and this number. Reasons: the limit is our creep guard, not a platform limit (the published ledger build at 222 KB loads, T-066 Build notes); trimming comments again (done in T-066) costs reviewability; a split breaks the one-file artifact and adds a loader. The next raise needs a split or minify decision (new record).

| Option | Cost | Risk | Pick |
|---|---|---|---|
| Trim 3.5 KB of comments and CSS | build time | less readable code, Review harder | no |
| Raise to 232 KB, about 7.5 KB headroom after build | none | creep, bounded by the next-raise rule | **yes** |
| Split page (core JS file) | loader, publish change | breaks the single-file artifact | no |
**Tests.** Node mode `place`: grid of W {900, 1024, 1280, 1920} x H {480, 560, 640, 800, 1080} x chat {closed, min, default, max via `C.chatH`} x focus {none, 96, 45%} x menu {none, open} x layouts {default flow, both saved at the same rect, one inside the chat area, half overlap, tiny, huge, off-screen} x natural heights {80, 300, 600}: invariant above, inputs deep-equal before and after, `place(out)` = `out`, returns to `clampRect(saved)` when room; ladder order (events shrinks before usage collapses, usage before events header, chip only when all collapsed fail); `sweep` never ends intersecting and never moves past the target. Headless (as T-066, copy and stub under /tmp, never committed): at 1280x800, 1024x640, 390x844 (plus 700x900, 1280x560, 390x600), chat closed, default, min (before and after ack), max, focus card open and closed, gear menu open, saved overlapping layouts: collect `getBoundingClientRect` of every visible part (`#top`, `#focus`, `#usage`, `#ticker`, `#usheet`, `#msheet`, open `.pm`, `#tone`, `#bar`, `#chat`; skip zero-size, hidden and ancestor/descendant pairs), assert no pair intersects and each is inside the window; `office.layout.v1` text unchanged after each case. Composer at min on 1280x800 and 390x844, offline event and a 16-digit run: `#cthread` bottom <= `#cform` top, `#cwarn` inside `#chat`, `elementFromPoint` at its four inner corners hits `#cwarn`, no write sent. Screenshots per case, no console errors; T-063/T-066 checks, C1-C8, golden, `--check` pass.
**Risks.** (1) RO loop between `fit()` and auto-collapse: rAF coalescing plus idempotent `place`; a test asserts one pass. (2) T-059 regression (saved rects rewritten): `PL.r` written only by drag, keys and Reset; headless compares storage text. (3) An open `.pm` clipped in a short panel: folded into `min` above. (4) The `.rz` hit area (-14px) reaches into the 8px gap: hit area only, not painted; accepted. (5) Golden moves if the flow defaults change at 1280x800 closed: they should not; if it moves, the Engineer explains it in Build notes. (6) The published ledger build will be about 226 KB; if the artifact publish rejects it, stop and tell the PMO.
**Compliance.** No change to data flow, storage, scan, notice or agents; C1-C8 untouched. Not flagged; Wulan not needed.
**Decision record draft (for the Curator).** Decision: HUD parts on desktop are placed by one pure `C.place` in priority order (sheet, focus card, usage, events) with a shrink, collapse, chip ladder; flow keeps CSS geometry and takes only states from it; phone keeps one layer at a time; page limit raised to 232 KB. Options: absolute-paint the flow layout too (one path, but rewrites T-059 defaults and golden); CSS-only (cannot handle the focus card or saved panels); chosen as above. Why: one testable rule with the smallest change to T-059 and T-066; chips reuse `#ubtn` and `#tone`.
— Fang (architect)

**Size note (Fang, 26 Nov 2026).** The 232 KB decision above was made on a +3.5 KB estimate; the build added about 14.6 KB (221,168 B to 235,796 B; Rework 1 ended at 235,833 B). Committed `office.html` is **235,833 B** against the **237,568 B** limit: **1,735 B** headroom. The published ledger page is **250,543 B** (96 events) and grows with every recorded run; the test limit does not cover it.
- **Limit confirmed at 232 KB (237,568 B), no raise.** The page fits it after the three Review 1 fixes. Raising again now would be the "next raise" without the split or minify record, and my estimate was off by 4x, so I do not use another estimate to justify headroom.
- **Next page change.** T-070 (about 0.6 KB) fits: it must land within the 1,735 B and report its real bytes; if it comes in over, it trims in the same PR, no raise. T-069 moves the usage data out of the page: that shrinks the published page (and stops its growth with runs), but the committed page is built from the fixture, so it does not add committed headroom. After T-070, any change that would pass 237,568 B needs the split or minify decision record first (Architect, then Curator), before build.
- `test_size_limit` comment updated to these numbers; the asserted limit is unchanged.
— Fang (architect)

## Build notes
**What changed** (only `engine/app/office.template.html`, the rebuilt `engine/app/office.html` and `tests/test_office_app.py`; no Python, no new files).
- `C.place(b, parts)` and `C.sweep(from, to, obstacles)` in `OfficeCore`, pure, as in the Design. Ladder: slide (vertical first, then sideways) -> shrink into the largest free gap -> collapse (usage, then events) -> chip (lowest failing). A collapsed part never shrinks below its collapsed height. Inputs are never mutated and `place(out) = out`.
- One `fit()` in the view (rAF-coalesced `reqFit`; triggered by dock, window resize, ResizeObserver on `#focus`, `#usage`, `#ticker`, MutationObserver on the card, `#usheet`, `#msheet` and the pm menus, ticker rows, `ucol`, layers). Flow keeps its CSS geometry and takes only states: `.ac` (usage auto-collapse, joins every `.col` selector, never saved, `usageCol` untouched), `.hd` (events header only), `.xc` (chip: hidden), `--fh` (column starts under the card) and `--fb` (column ends above an open menu, sheet or the events chip). Free (T-059) paints `C.place` output instead of `clampRect`; `PL.r` is written only by drag, keys and Reset, and `fit()` always starts from `PL.r`.
- Drag and keyboard move/resize go through `C.sweep`: a panel stops at its neighbour's edge (card, menu, sheet and events chip included), the neighbour is never pushed. Verified in headless: a drag onto the ticker stops with the right edge at the ticker's left edge.
- Chips reuse `#ubtn` (`body.uchip`, opens `#usheet`) and `#tone` (`body.echip`, opens the events layer). They show only when the ladder chips a part (stage under about 230 px).
- One transient layer: `layer(name)` closes the others on phone and tablet (card, `#usheet`, `#msheet`, events list); on desktop `#usheet` and the events list are layers over the card and menu, which sit beside the panels as parts. Escape closes the open layer and returns focus to its opener. Shared CSS rule `bottom: bb+40; max-height: 100% - --st - --bb - 48px; overflow:auto`; `60vh` is gone. Events layer is `position:fixed` (at 900+ its parent `#side` was the containing block and put it at y=-400).
- Composer: `showWarn()` re-runs `dockLayout(false)` when the warning appears, changes or goes (so the min includes it); `#cmid{overflow:hidden}` clips the thread above the composer; `#cwarn{background:var(--panel)}` solid. `sendChat` untouched; a 16-digit run still sends nothing (0 db writes in headless).
- Size: `test_size_limit` raised to 232 KB (237,568 B) with Fang's reason in the comment. Committed page is 235,796 B (was 221,168 B): 1,772 B under the limit, not the 7.5 KB the Design estimated. The code came in at about 14.6 KB, not 3.5 KB (place + sweep about 4.6 KB, fit glue about 5.5 KB, CSS about 1.5 KB, rest layers and notes). I did not trim; the Reviewer or PMO may want a comment trim, and the next raise needs the split or minify decision recorded in the Design.

**Deviations from the Design (small, all in service of "no overlap")**
1. Focus card `min` is 56, not 96, and the card is chippable (`.xc`): at 1280x560 with min chat and the notice (stage 124 px) card 96 + menu 60 cannot fit; the card waits and returns when the menu closes.
2. `body.nost` (stage under 72 px, phone/tablet only): the layers and the tone strip wait, because the chat min covers the whole window (390x600 before ack: stage 0 px). Chat button and bar stay usable.
3. Natural-height measuring also removes `.xc` (a hidden part measured 0 px and flipped on every pass; found by the headless run).
4. `#ticker{min-height:40px}` in flow (was 96px), per the Design's shrink step; `#tlist` scrolls inside.
5. The T-066 test `test_chat_notice_is_pinned_outside_the_scroll_area` asserted that `#cmid` has no `overflow`; it now asserts no `overflow:auto|scroll` (the Design needs `overflow:hidden` as a clip; the notice is outside `#cmid`).
6. Golden did not move (`tests` green, flow defaults at 1280x800 closed are unchanged).

**How to verify**
- `python -m unittest discover -s tests`: exit 0, 393 tests (new class `NoOverlap`: node grid, 10,080 cases of W{900,1024,1280,1920} x H{480,560,640,800,1080} x chat{closed,min,default,max} x focus{none,96,45%} x menu x layouts{flow, same rect, inside chat area, half overlap, tiny, huge, off-screen} x natural heights{80,300,600}; invariants: pairwise non-intersect, inside bounds, h >= min unless collapsed, collapsed never shrinks, inputs unchanged, idempotent, equals `clampRect(saved)` when there is room; ladder order; 3,000 random `sweep` cases).
- `python -m engine.runtime validate ai-office`: OK. `python scripts/office_app.py ai-office --chat --check`: up to date. `board.py`: no problems, board.md discarded.
- Headless (not committed, per the Design; Playwright + Chrome 153, page copy and a stub `claude` under /tmp/t067): sizes 1280x800, 1024x640, 1280x560, 900x700, 700x900, 600x800, 390x844, 390x600; chat closed, default, min after ack, min before ack, max; layouts default, moved, same rect, inside chat area, half overlap (900+ only); states base, focus card, focus card + gear menu, menu, usage sheet (gear on phone, Usage button on tablet), events layer, both panel `...` menus, composer warning (offline), blocked send (16-digit run). Each snapshot waits until the rects stop changing, then asserts: no two visible HUD parts intersect (`#top`, `#pill`, `#banner`, `#strip`, `#usage`, `#ticker`, `#focus`, `#usheet`, `#msheet`, `#tone`, open `.pm`, `#bar`, `#chat`; ancestor pairs skipped; canvas excluded), every part inside the window, no page scroll, no console errors, `office.layout.v1` text unchanged, and for warnings `#cthread` bottom <= `#cform` top, `#cwarn` inside `#chat`, `elementFromPoint` at its four inner corners hits `#cwarn`.
  - Committed page: 867 snapshots, 0 failures. Published ledger page (`--ledger ... --chat`, 245,071 B): 867 snapshots, 0 failures.
  - Control: the same script on main's page (T-066) at 1280x800 chat max reports 22 overlaps (usage/ticker, focus/menu, panels over the menu), so the check does detect the bug.
  - Also: a saved layout in the chat's area is shown moved while chat is open (usage y 520 -> 56) and returns to its saved place when chat closes; storage text unchanged.
- Screenshots: none committed; none needed beyond the rect assertions.

**Not covered / for the Reviewer**
- The headless check is a /tmp script, as the Design says; the committed tests are the node maths plus source assertions. If the Reviewer wants the headless check committed, say so (it needs Chrome and Playwright, which CI may not have).
- Real-device touch is out of scope (Spec). During the 180 ms `--chat-h` dock animation free-mode panels use the final rect with a 160 ms settle, so they can briefly cross the moving bar (as in T-066); final positions never overlap.
- Published ledger page is 245,071 B (239 KB); the 232 KB limit applies to the committed page. Fang's risk 6: if the artifact publish rejects it, stop and tell the PMO.
- Window resize across 900 px with a layer open is not re-evaluated (layers stay as opened).

— Sebastian (engineer)

### Rework 1 (26 Nov 2026, after Review 1 REJECT)
Merged `origin/main` first (clean). Changed only `engine/app/office.template.html`, the rebuilt `engine/app/office.html` and `tests/test_office_app.py`.
- **(a) Collapsed usage with its menu open.** `build()` used `nat.uc` alone for a viewer-collapsed panel. It now uses `uh = max(nat.uc, menu height)` for `h`, `min` and `col`, so `C.place` keeps panel and menu inside the bounds and off the bar. Cahyani's repro (1280x800, usage saved at y=620, collapsed, `...` open) is now clean in her harness.
- **(b) Chip/shown flip.** Cause: `build()` called `pmH()` after the chip class was set, and a hidden (chipped) panel measured a 0 px menu, so it unchipped, then measured the menu and chipped again. The menu heights (`nat.pu`, `nat.pt`) are now taken once in the measuring pass, while no part is chipped. The 1280x520 case (min before ack, moved layout, card open, usage menu open) now ends in a stable state (24 samples at 150 ms, last 12 identical). New node test: a grid (H x dock x menu height x layout x card) asserts `place` is deterministic, `place(own output)` keeps every chip state and every rect (one pass), and a collapsed panel with a menu stays inside the bounds.
- **(c) Short desktop window.** `body.nost` (stage under 72 px) is now set on the desktop path too (`fit()` sets it before the geometry), and the `min-width:900px` CSS hides `#tone`, `#usheet`, `#msheet` and the events layer under it. They wait until there is room; the Chat button and bar are untouched. New test `test_short_desktop_window_has_no_layer_in_the_top_strip` (CSS rule, `nost` set before the float path, `build()` has no `pmH(` and counts the menu).
- Also: stale `PLACE_CHECK` comment about the card (min 56, chippable) fixed; `test_size_limit` comment now says about 15 KB and no longer quotes the 222 KB published figure. Limit unchanged (232 KB). Trimmed six of my own comments in the template.
- **Size.** Committed page **235,833 B** (was 235,796 B in the rejected build; +37 B net after trimming; limit 237,568 B, headroom 1,735 B). Published (`--ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat`): **250,543 B** (244 KB, 96 events; it was 245,071 B with 78 events, the rest is ledger growth on main). Fang writes the dated size note.

**How to verify**
- `python -m unittest discover -s tests`: exit 0, 416 tests. `validate ai-office`: OK. `office_app.py ai-office --chat --check`: up to date. `board.py`: no problems, board.md discarded.
- Cahyani's harness (`/tmp/cah67/h/check.py`, sizes 1280x800, 1024x640, 390x844, 1280x460, 1280x560, 1280x520, 1024x500, 1280x480, 390x600, 900x700, 700x900), 797 snapshots each: committed 16 failures, published 15. **No overlap, outside-window, page-scroll, top-strip, composer or storage failure.** What remains: (1) 14 to 15 "saved place not used/back" with usage h 74 or 90 at windows under 520 px tall: T-056 `usageCol`, Cahyani's non-blocking note, x/y/w match; (2) 1 to 2 `#ubtn` click timeouts at 1280x460: the harness checks `is_visible()`, then the chip goes away one frame later when the panel menu closes (Escape), a one-pass settle, not an oscillation (`flick3`/`flick2` show a single state at rest).
- Control cases: `/tmp/cah67/h/flick.py` (the 1280x520 flip) and `pm.py` (the collapsed menu), no overlap.
- My own earlier run (867 snapshots, 8 sizes) was not re-run; Cahyani's harness covers the three defects.

— Sebastian (engineer)

## Review log
### Review 1 (Cahyani, 26 Nov 2026): REJECT

I wrote my own headless harness and a stub `claude` under /tmp/cah67 before using any part of Sebastian's method. Nothing from it is committed, and there are no screenshots in the repo. Note: I had read the Build notes before my own check because they are in the same file, but every result below comes from my own runs.

**Merge with main.** The branch predates T-068 (#64) and #63. `git merge-tree --write-tree HEAD origin/main` gives exit 0, so the merge is clean. Neither of those PRs touches the four files this PR changes. On a merged copy (/tmp/merged): `unittest` ran 415 tests, OK. `validate ai-office` gave `OK — 8 agents, 5 stages, 71 tasks, 18 skills`, and `--chat --check` said `up to date (230 KB, 84 events)`.

**Runs on the branch (87266e5)**
- `python -m unittest discover -s tests` printed `Ran 393 tests in 16.008s`, `OK`, exit 0.
- `python -m engine.runtime validate ai-office` printed `ai-office: OK — 8 agents, 5 stages, 67 tasks, 18 skills`, exit 0.
- `python scripts/office_app.py ai-office --chat --check` printed `engine/app/office.html: up to date (230 KB, 84 events)`, exit 0.
- Size: the committed page is 235,796 B. Main's page is 221,168 B, so the PR adds 14,628 B. The limit is 237,568 B, which leaves 1,772 B. The published build (`--ledger offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl --chat`) printed `written, 239 KB, 8 agents, 78 events` and is 245,071 B.

**Headless check (own harness).** Playwright with Chrome at dpr 1, served over http from a copy, with a stub `claude` (db and user). Sizes: 1280x800, 1024x640, 390x844 and 1280x460, plus a follow-up run at 1280x560, 1280x520, 1024x500, 1280x480 and 390x600. Chat states: closed, default, min (after ack), min before ack, and max. Layouts: the default flow layout, "moved" (the two panels overlap each other and reach into the chat area), and "roomy" (saved apart, with room). In each case I opened these in turn: the focus card (first strip agent), the gear menu, the usage panel `...` menu, the usage sheet (Usage button, or the gear's Usage on a phone), the events layer (tone strip), the offline warning (`set_offline`), and a blocked send of a 16-digit run.

At every snapshot I checked:
- the rects of `#top`, `#focus`, `#usage`, `#ticker`, `#usheet`, `#msheet`, `#tone`, `#bar`, `#chat` and every open `.pm`, pairwise, skipping ancestor pairs and excluding the canvas;
- that every part is inside the window;
- that there is no page scroll and no console errors or 4xx;
- that the `office.layout.v1` text is unchanged.

For the warnings I also checked that `#cmid` ends at or above the `#cform` top, that `#cwarn` is inside `#chat`, that `elementFromPoint` hits `#cwarn` at points 5 px in from its corners and at its centre, that its background is solid, that its text is not clipped, and that the send made 0 db writes.

Control: on main's page, at 1280x800 alone, the harness reports 48 failing snapshots out of 73 (focus card over usage, panels over each other, ticker over the menu). So the check detects the bug.

| Page | Snapshots | Failures | Where |
|---|---|---|---|
| Committed | 301 | 24 | all at 1280x460 (19 overlaps; 5 are my false positive, see Notes) |
| Published (ledger + chat) | 301 | 24 | the same cases |

At 1280x800, 1024x640 and 390x844 the results are clean for every state and layout:
- no overlap and nothing outside the window;
- no page scroll and no console errors;
- the saved layout text is never rewritten;
- the saved rects are used when there is room, and they come back after the chat closes (25 cases);
- the composer warning passes every check;
- the blocked send writes nothing.

This is a large improvement on main.

**Done when, checked**
1. No overlap at any height and window size, in the flow layout and with moved or resized panels: **FAIL**, three defects.
   - **(a) Main size.** At 1280x800 with chat at default, I saved the usage panel at `{x:300,y:620,w:360,h:300}`, collapsed it with its chevron, and opened its `...` menu. The usage rect became `300,358,360,105` and `pm-usage` became `435,403,216,59`, while the bar is at `0,440`. Both cover the bar by 23 px. This repeats at 1024x500 and 1280x480 (even with chat closed) and at 1280x460. Cause: in `fit()` → `build()`, a viewer-collapsed usage panel gets `min: usageCol ? nat.uc : um` and `h: usageCol ? nat.uc : ur.h`, so `C.place` never sees the open menu's height. `fit()` then sets `style.minHeight` to the menu height, and the panel grows past its placed rect.
   - **(b) Loop that never settles (Fang's risk 1).** At 1280x520, chat at min before ack, with the "moved" layout, the focus card open and the usage `...` menu open, `body.uchip` and the usage panel flip between chip and shown every 100 to 200 ms. I sampled for 3 s and it never stopped. In the shown phase, usage overlaps the ticker (227x50) and the bar (360x23). The Design promised "a test asserts one pass", but none is committed.
   - **(c) Short desktop window.** At 1280x460 and 1280x480 the stage is 40 px or less in two cases: chat at min before ack (chat 324 px), and with the offline warning (chat 360 px). Then the gear menu (`1143,26,125,22`), the usage sheet (`1004,34,264,14`), the events layer (`1004,8,264,40`) and the events chip `#tone` (`1004,18,264,34`) all overlap `#top`. The phone has `body.nost` (deviation 2) for this case; the desktop has no equivalent.
2. Composer warning clipped at min, on 1280x800 and 390x844: **PASS**. At 1280x800 min, `#cwarn` is at `13,686,1254,30` with background `rgb(29, 30, 44)`, which is solid. `#cmid` ends above `#cform` (top 665). All five hit points land on `#cwarn`. The 16-digit run made 0 writes and showed the "personal data" warning. The same holds at 390x844, in the default and max states, and before ack (composer disabled).
3. Size decision recorded and the page fits it: **PASS on the letter, needs a note** (see deviations).

**The deviations**
- **T-066 test relaxed from no `overflow` to no `overflow:auto|scroll` on `#cmid`: accepted.** The T-066 risk was an inner scroll box hiding the notice. `overflow:hidden` cannot scroll, and the same test still asserts that `#cnotice` is outside `#cmid` and is `flex:none`. My headless runs before ack showed the notice and the button inside `#chat`. A clip is what Fang's Design asks for.
- **Size: the numbers are honest, but the decision needs an Architect note.** Sebastian states the overrun plainly: +14.6 KB against an estimate of 3.5 KB, and 1,772 B of headroom against the 7.5 KB the Design expected. My byte counts match. But the 232 KB decision was made on the 3.5 KB estimate, so it was based on the wrong number. The fixes above will add code and may use up the 1,772 B. The decision is Fang's (Done when 3), so it needs a dated Architect note with the real numbers: confirm 232 KB, or trim, or apply the "next raise needs a split or minify" rule now. Two smaller points:
  - The `test_size_limit` comment says "about 13 KB of page code" while the Build notes say 14.6 KB.
  - The comment says "the published ledger page loads at 222 KB", but today's published build is 245,071 B (239 KB). Neither number has been republished or checked.
- **Deviations 1 to 4 and 6** (card `min` 56 and chippable, `nost` on phone and tablet, `.xc` removed while measuring, ticker `min-height:40px`, golden unchanged): reasonable and in the spirit of the Design. Deviation 2 is exactly what the desktop is missing in 1(c).

**C1 to C8 (T-063 Compliance): not weakened.** The diff touches only the four listed files. No changed line in the template mentions `scan`, `cnotice`, the ack, `sendChat`, `newAsk`, purge or `claude.use`. There are no changes in `engine/runtime` or the playbooks. Headless evidence: before ack the composer is disabled (C3); the 16-digit send is blocked, names only the kind, and writes 0 docs (C1); the notice and footnote are unchanged (the T-063 and T-066 tests pass).

**Fixes needed (back to build)**
1. In `fit()` → `build()`, a usage panel collapsed by the viewer (`usageCol`) must still count its open `.pm` menu in `min` and `h`, as the expanded case does with `um`. The panel and menu must then stay inside the bounds and off the bar. Repro: 1280x800, chat default, usage saved at y=620, collapse it, open its `...` menu.
2. Stop the chip/shown loop. The likely fix is to close a panel's `.pm` menu when the panel is chipped, or to leave the menu out of `min` once the panel is chipped. Add the "one pass" test that Fang's risk 1 calls for: running `fit()` twice gives the same classes and rects. Repro: 1280x520, chat min before ack, saved overlapping layout, focus card open, usage `...` menu open.
3. On the desktop, when the stage is below what a layer or the events chip needs (1280x460 or 1280x480 before ack, or with the offline warning), the gear menu, usage sheet, events layer and `#tone` must not enter `#top`. This is the desktop equivalent of `nost`, or clamp them into the stage. The Chat button and bar must stay usable.
4. Fang adds a dated note to the size decision with the real numbers: 221,168 B → 235,796 B (+14.6 KB), 1,772 B headroom, published build 245,071 B. In it, Fang confirms or changes the limit, taking into account the bytes these fixes add. Make the `test_size_limit` comment match.

**Notes (non-blocking)**
- My "saved place" check flagged usage at h 74 in windows under 520 px tall. This is T-056's `usageCol = innerHeight < 520`, a viewer-level collapse that predates this PR, and x, y and w match the saved rect. I do not count it.
- The headless rect check is still /tmp-only. Defects 1(a) to 1(c) suggest the node grid does not model a collapsed panel with an open menu, or a stage under 72 px on the desktop. Adding those two cases to `PLACE_CHECK` would catch fixes 1 and 3 without Chrome.
- The `PLACE_CHECK` comment "a card that cannot fit at all ... has no chip (96px min)" is out of date: the card min is 56 and the card is chippable (deviation 1).
- External skills `design:accessibility-review` and `data:validate-data` were not available in this session; not used.

— Cahyani (reviewer)

## Decision

## Open questions
