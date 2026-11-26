---
name: document-assessment
description: Turn a partner or vendor API doc, tech doc or template agreement into a gaps-and-risks assessment with a fixed structure. Use when a partner document arrives for review. Flags risks for a human; not legal advice or approval.
---
# Document assessment

A partner or vendor sends an API doc, a tech doc or a template agreement. Read it and write one assessment in the fixed structure below, so gaps and risks have the same shape every time. Architect uses it for API and tech docs; compliance uses it for agreements.

## Rules
- **Document**: say what the document is, its version or date if stated, and what it covers. 1 to 3 lines.
- **Gaps**: list what is missing or unclear, each with an ID (G1, G2) and where in the document you looked.
- **Risks**: each risk has an ID (R1, R2), a severity and a reason that cites a gap or clause. Severity is fixed:
  - **high**: can cause money loss or mis-routed funds, personal data exposure, a regulatory breach, or blocks go-live.
  - **medium**: needs a written answer or a fix before signing or building, and a workaround exists.
  - **low**: clarity or consistency issue with no direct impact.
  When unsure between two levels, pick the higher one and say why.
- **Questions**: each question names the gap or risk ID it closes. When the questions are sent to the partner as written, also apply `base/skills/partner-writing` (B1, B3, B4).
- **Not reviewed**: always say what was not read (a part, annex, linked doc or aspect), or "Nothing left out: all N pages read". Never leave it empty.
- **No approval**: never write that a document is approved, safe to sign, legally compliant or free of legal risk. For legal and regulatory points, name who answers: KlikA2C legal or compliance, through Merwyn.
- **Data**: the assessment lives where the document lives (the company repo or Drive), and the task file links to it. Never paste a real partner document, name, figure or credential into this repo. Golden cases use invented documents only.
- Language: English by default. If Merwyn asks for Indonesian, partner-writing B2 applies.

## Output template
Exact headings, in this order:

```
## Document
<what it is, version or date if stated, what it covers; 1 to 3 lines>
## Gaps
- G1 <what is missing or unclear, and where in the document>
## Risks
- R1 [high|medium|low] <risk>. Why: <reason, citing the gap or clause>.
## Questions for the partner
1. <question> (G1)
## Not reviewed
- <part, annex, linked doc or aspect not read, or "Nothing left out: all N pages read">
This assessment flags risks for a human decision. It is not legal review or approval.
```
