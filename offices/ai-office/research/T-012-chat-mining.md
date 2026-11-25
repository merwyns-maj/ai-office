# T-012 — How Merwyn works: findings from past chats

Pass run 25 Nov 2026 by Claude (acting as April, curator) over chats outside claude.ai Projects (Project chats are only searchable from inside each Project). Patterns only: no company data, names of borrowers/lenders, or figures are recorded here. Each pattern lists where it was seen.

## A. Working standard (how work must be done)
| # | Pattern | Seen in |
|---|---|---|
| A1 | **State facts, no guessing.** Inferred values are not acceptable as data; if a fact isn't in a source, say so and find a way to read the source. | Payor data extraction (Nov) |
| A2 | **Verify against primary sources** (prod/staging DB, full page text, the actual file) before documenting or concluding; re-verify when challenged instead of defending a summary. | TBO PRD (Oct), iFortepay assessment (Nov) |
| A3 | **Data-backed recommendations.** Pull the numbers that test a recommendation before giving it; revise when the data says so. | iFortepay assessment (Nov) |
| A4 | **Flag incidental bugs** found while doing something else, with evidence. | TBO PRD (Oct), onboarding status check (Nov) |
| A5 | **Check for external edits** (other sessions, Confluence comments, repo changes) before overwriting shared work. | TBO PRD (Oct) |
| A6 | **Use the team's conventions** (klik-workspace skills, ticket templates, labels like `ai-drafted`, the right board) rather than inventing a format. | VA funding bug, Pefindo ticket, LC-2270 (Nov) |
| A7 | **Precise scoping**: separate wording-only changes from data/logic changes; say which a change is. | Template Agreement assessment (Nov) |
| A8 | **Stay in the asked lens**: product/engineering view, not legal or risk opinion, unless asked. | Template Agreement assessment (Nov) |
| A9 | **Start simple, iterate.** A complex first version gets rejected; ship the simple shape, then add. | Funding projection (Oct) |
| A10 | **Consistency check before delivery**: page counts, cross-references, leftover placeholders, order of summary matching order of body. | Danamon SOP (Nov), status email (May) |

## B. Writing for others
| # | Pattern | Seen in |
|---|---|---|
| B1 | No em-dashes or AI-sounding punctuation. | Danamon money-flow doc (Nov) |
| B2 | Keep banking/fintech terms in English, italicised in Indonesian text, when translation "looks weird". | Danamon money-flow doc (Nov) |
| B3 | Partner-facing: no overpromising, no unnecessary detail, no commitments (dates, SLAs) not yet agreed. | Danamon money-flow doc (Nov) |
| B4 | Concise and compact once the requirement is understood. | Danamon SOP (Nov), several |
| B5 | Tone control on request: soften wording about own-side failures for leadership audiences; push accountability to the partner side when asked. | Jira patching summary (Oct), steerco rephrase (Apr) |
| B6 | Email-ready formatting (no markdown) for emails. | Status email (May) |

## C. Product design (CaaS 3.0) — company know-how, belongs in the company office
| # | Pattern | Seen in |
|---|---|---|
| C1 | Reuse existing native patterns (e.g. the Risk Assessment drawer) before new layouts. | Committee memo (Oct) |
| C2 | Committee actions (approve, approve with condition, reject, push back) always require a note. | Committee memo (Oct) |
| C3 | Don't show buttons for features that don't exist (Push Back replaced Save Draft). | Committee memo (Oct) |
| C4 | No data-source badges on native screens; placeholders instead of real PII; clickable IDs into the system. | Committee memo (Oct), baseline canvas (Nov) |
| C5 | Fold new items into existing sections rather than adding sections (TBO inside "Conditions & Requirements"). | TBO PRD (Oct) |

## D. How we work together (governance between Merwyn and Claude)
| # | Pattern | Seen in |
|---|---|---|
| D1 | Claude proposes with a recommendation and options; Merwyn answers tersely ("accept", "done", "no"); Claude records the decision where the work lives. | This session; Template Agreement (Nov) |
| D2 | Iteration through artifact comments and short chat instructions; reply in the thread where feedback was given. | TBO PRD (Oct) |
| D3 | Merwyn may override process for speed (e.g. "push directly to main"); Claude complies and records it, unless it breaks a safety rule. | LC-2270 (Nov) |
| D4 | Claude does not misrepresent records (e.g. backdating), even when asked; offers a truthful alternative instead. | Danamon SOP (Nov) |

## Proposed skills (for Merwyn's review — Done when: shortlist reviewed, top 3 saved)
1. **working-standard** (T-014) — section A, for every agent in every office. Lives in this repo (it is about how work is done, not company content).
2. **partner-writing** (T-015) — section B, for any agent writing for people outside the office.
3. **working-with-merwyn** (new) — section D: escalation format, decision recording, terse-reply handling, when to stop and ask. Used by every office's PMO.
4. **caas3-design** (T-013) — section C. Company know-how: belongs in klik-workspace / a company office, so it waits on T-002.
