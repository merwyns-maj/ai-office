---
name: consultant-slides
description: Make consulting-grade slide decks (Big 4 and MBB style): answer-first storyline, action titles, one message per slide, sourced charts, a clean grid. Use when asked for a deck, slides, board pack, steering-committee update or executive summary.
---
# Consultant slides

How to make a deck that reads like a Big 4 or MBB deliverable. The rules are tagged C1 to C40. Each rule ends with a source URL or the words "office rule". The research behind them is in `offices/ai-office/research/consultant-slides-2026-11.md`.

Text on slides leaves the office, so `partner-writing` (B1 to B6) applies as well: no dash punctuation, no overpromising, concise.

The reference template is `template/deck.html`. It is an 11-slide sample deck with every layout in section 5, and every design token in section 7 is defined there. Copy it, keep the CSS, and replace the content.

## 0. Pick the output
- **C1** No file format named: build an HTML deck from `template/deck.html` (16:9, 1280 x 720 px per slide; it prints to PDF one slide per page). A `.pptx` was asked for: use the `pptx` skill and apply the same grid at 13.333 x 7.5 in. Google Slides was asked for: use the `google-workspace` skill. office rule
- **C2** Never use a real firm's logo, wordmark, name or exact brand colours on a deck that is not that firm's. The style is borrowed, the brand is not. Use the client's brand or the neutral tokens in section 7. office rule

## 1. Storyline before slides
- **C3** Write the governing question and its one-sentence answer before any slide. The deck opens with the answer, not with the build-up. https://slidemodel.com/mckinsey-presentation-structure/
- **C4** Structure the argument as a pyramid: the answer on top, 2 to 4 supporting points, evidence under each. Apply it to the deck and again inside each slide. https://www.think-cell.com/en/resources/content-hub/using-the-pyramid-principle-to-build-better-powerpoint-presentations
- **C5** Frame the opening with SCR (Situation, Complication, Resolution) or SCQA (adds the Question). https://umbrex.com/resources/the-consulting-career-guide/storylining-and-deck-structure/
- **C6** Draft a ghost deck first: titles only, in order, no bodies. Read the titles top to bottom. If they do not tell the whole story on their own, fix the titles before building any body. office rule
- **C7** Slide 2 is the executive summary. A senior reader should get the conclusion, evidence, recommendation, risks and the decision needed from it without reading the other slides. https://deckary.com/blog/consulting-slide-standards
- **C8** End the main deck with decisions required and next steps (owner, date). Put detail that supports but does not drive the story in an appendix. office rule

## 2. Action titles
- **C9** Every content slide has an action title: a full sentence stating the conclusion, not a topic label. "Logistics cost grew twice as fast as revenue since 2023", not "Logistics costs". https://piktochart.com/blog/mckinsey-style-presentation/
- **C10** One message per title. If the title needs "and" or a semicolon to hold two claims, split the slide. https://piktochart.com/blog/mckinsey-style-presentation/
- **C11** Put the number in the title when there is one ("Five levers close the 4.1-point margin gap"). Big 4 report headlines lead with the figure; PwC's 2026 CEO Survey release leads with "only three-in-ten (30%) of CEOs" confident on revenue. https://pwc.com/gx/en/news-room/press-releases/2026/pwc-2026-global-ceo-survey.html
- **C12** Titles fit in two lines at the title size, about 15 words at most. Sentence case, no full stop at the end. office rule
- **C13** The body proves the title and nothing else. Any chart, row or bullet that does not support the title moves to another slide or the appendix. https://umbrex.com/resources/the-consulting-career-guide/building-strong-consulting-slides/
- **C14** Topic labels are allowed only on the title slide, section dividers, the agenda and appendix slides. office rule

## 3. Slide anatomy
Every content slide, top to bottom:

| Zone | Content | Template class |
|---|---|---|
| Tracker | Section name, small caps, top left. Shows where the reader is | `.tracker` |
| Action title | C9 to C12 | `.title` |
| Lead line (optional) | One line of context or unit, muted | `.lead` |
| Body | Chart, table, framework. 2 to 4 supporting points | `.body` |
| Takeaway (optional) | The "so what", right third or bottom band | `.takeaway` |
| Footer | Notes and source bottom left, page number bottom right | `.footer` |

- **C15** The source line sits bottom left in small type. No number appears without a source. https://deckary.com/blog/consulting-slide-standards
- **C16** Source format: `Source: <publisher>, <title> (<year>); <team> analysis`. Survey data adds the base: `Note: n = 1,204 respondents; multiple answers allowed`. Notes come before the source. office rule
- **C17** A takeaway box answers "so what?" for the reader: what the data means and what to do about it. Use it on chart slides, either in the right third or as a bottom band. https://deckary.com/blog/consulting-slide-standards
- **C18** One base layout serves most slides. Keep the title, tracker and footer in the same place on every slide so the eye never hunts. https://deckary.com/blog/consulting-slide-standards

## 4. Grid and spacing (1280 x 720 px; pptx values in brackets)
- **C19** Margins 56 px left and right, 40 px top, 32 px bottom (0.58 in, 0.42 in, 0.33 in). 12-column grid, 24 px gutters. Chart plus takeaway is 8 + 4 columns. office rule
- **C20** Align every element to the grid edges. Equal gaps between equal things. Nothing within 8 px of another element unless they are grouped. office rule
- **C21** Leave white space. When a slide feels full, cut content rather than shrink the type. office rule

## 5. Layout library (all in `template/deck.html`)
| # | Layout | Use when |
|---|---|---|
| 1 | Title | Opening; client, project, date, "Draft for discussion" |
| 2 | Executive summary | SCR in three bands, or 3 to 5 numbered messages with a bold lead-in |
| 3 | Section divider | Large number and section name; shows the next part of the storyline |
| 4 | Chart + takeaway | One chart (8 col) proving the title, takeaway (4 col) |
| 5 | Waterfall | Bridge from a start value to an end value (gap, margin, budget) |
| 6 | KPI row | 3 or 4 big numbers, each with a label and a delta |
| 7 | 2 x 2 matrix | Prioritising options on two axes (impact vs ease) |
| 8 | Options table + Harvey balls | Comparing 3 to 5 options on 4 to 6 criteria; recommended row highlighted |
| 9 | Roadmap (Gantt) | Phases and workstreams over time, with milestones |
| 10 | Next steps | Decisions required and actions with owner and date |
| 11 | Appendix | Method, definitions, data sources; topic title allowed (C14) |

- **C22** Pick the layout from the message, not the other way round. When none fits, use the chart + takeaway layout. office rule

## 6. Charts
- **C23** Choose the chart from the comparison the title makes: share of a whole (stacked bar or a single bar, rarely a pie), ranking (sorted horizontal bar), change over time (column or line), distribution (histogram), relationship (scatter). office rule (after Zelazny, *Say It With Charts*)
- **C24** One highlight colour carries the message; everything else is grey. The highlighted bar or line is the one the title talks about. office rule
- **C25** Label data directly on the bars or line ends. Drop the legend, gridlines and y-axis when the labels carry the values. No 3D, shadows or gradients. office rule
- **C26** Bars and columns start at zero. Sort bars by value unless the categories have a natural order (time, size bands). office rule
- **C27** Units go in the lead line or axis label, once ("Index, 2023 = 100"; "EBITDA margin, % of revenue"). Not repeated on every label. office rule
- **C28** In a waterfall, show the start and end bars in the ink colour, the steps in the accent (red for negative), with thin connector lines and a value on every bar. office rule
- **C29** Make charts with SVG or a charting library in HTML, or native charts in pptx, so they stay sharp and editable. No screenshots of charts. office rule

## 7. Visual system (tokens in `template/deck.html` `:root`)
- **C30** Colour: ink navy `#0B1F33` for titles and key bars, one accent teal `#00857C`, greys `#4A5560 / #8A949E / #C9D0D6 / #EEF1F4`, negative `#B4442E`. Add a second accent only when two series must both stand out. office rule
- **C31** Type: one sans family for everything (Inter, falling back to Arial). A serif (Source Serif 4, falling back to Georgia) only for the title slide, dividers and KPI numbers. office rule
- **C32** Type scale: title 26 px semibold; body 15 to 16 px; table and chart labels 12 to 13 px; tracker and footer 10 to 11 px. Never below 10 px. In pptx: title 20 pt, body 12 to 14 pt, source 8 pt. office rule
- **C33** Emphasis by weight or colour, not by underline, italics, caps or exclamation marks. At most one bold phrase per bullet (the lead-in). office rule
- **C34** No clip-art, stock photos, icons as decoration or emoji (B1). An icon is allowed only when it labels something the reader must tell apart. office rule

## 8. Words and numbers
- **C35** Bullets: at most 4 per box, each at most 2 lines, parallel grammar. Start with the point, not with "We believe". office rule
- **C36** Numbers: same precision across a slide; thousands separators; `%` for shares and `pts` for percentage-point changes; currency and period stated once (`IDR bn, FY2026`). Round to what the decision needs. office rule
- **C37** Status labels in the top right corner: `Draft for discussion` until the client has seen the deck, then `Final`. Add `Confidential` when the content is not public. office rule

## 9. Before you deliver
- **C38** Read the titles alone, in order (C6). They must tell the full story, and each must match its body (C13). office rule
- **C39** Check every number against its source, every slide has a source line (C15), totals add up, and the executive summary matches the body (A10 in `working-standard`). office rule
- **C40** Render the deck and look at every slide: nothing overflows its box, nothing overlaps, the grid lines up, and the type is readable at 50% zoom. For HTML, take a Playwright screenshot of each slide at 1280 x 720. office rule

## Example action titles
| Weak (topic) | Strong (action) |
|---|---|
| Market overview | Mid-market demand grows 9% a year, twice the enterprise segment |
| Cost analysis | Logistics cost grew twice as fast as revenue since 2023 |
| Options | A phased rollout delivers 80% of the value at half the risk |
| Next steps | Three decisions this month keep the 2027 launch on track |
