---
name: compliance-playbook
description: How Wulan checks work for data-protection and safety risk, grounded in Indonesia's PDP Law (UU 27/2022). Use when a design or PR is flagged, or touches personal data, finance data, production or credentials. Not legal advice.
---
# Compliance playbook

An engineering guardrail, not legal advice. Legal questions go to KlikA2C's legal/compliance team through Merwyn. Pairs with `uu-pdp-checklist`.

## 1. The law in brief (what shapes our checks)
- Indonesia's PDP Law (Law No. 27 of 2022) took effect on 17 October 2022 and is the main data-protection law; sector rules (OJK etc.) still apply where they don't conflict.
- It separates the **controller** (decides why and how data is processed) from the **processor** (processes on the controller's instructions). Know which one we are in each flow.
- **Specific personal data** includes biometric and personal financial data. Lending data is in this category, so the bar is higher: it triggers extra duties such as a data protection impact assessment and a data protection officer.
- Processing needs a lawful basis: consent, or another ground such as fulfilling a contract or a legal obligation.
- Transfers outside Indonesia need the destination to offer an equal or higher level of protection.

## 2. What that means for this office
- This repo and the brains hold **pointers, never personal data**: no names, NIK, phone, email, address, bank account numbers, loan rows or exports.
- Company content stays in company-owned repos. Personal repos never receive it.
- No secrets, tokens or connection strings in code, logs or task files.
- Production writes only through the approved path (Bytebase change issues). Read access to prod is still flagged for review.
- Agents running on cloud infrastructure must not be fed personal data from production as context unless Merwyn and legal have approved that flow.

## 3. How to check
1. Read the Design and the diff. List every data source touched and every place data is written.
2. For each: is it personal or specific personal data? Where does it go? Who can see it? Is it copied or only referenced?
3. Verdict in the Review log: `Compliance: PASS`, or `Compliance: BLOCK — <exact item> — <fix>`.
4. Separate real risk from theoretical risk. Block on the first; note the second.
5. Every BLOCK goes to Merwyn via Janice.

## Sources
- Chambers, Data Protection & Privacy 2026: Indonesia — https://chambers.com/practice-guides/guides/data-protection-privacy-2026/indonesia/law-and-practice
- PwC Germany, Indonesia PDP Law overview — https://legal.pwc.de/content/im-fokus/indonesia-global-data-protection-law-overview.pdf
- Norton Rose Fulbright, highlights of Indonesia's PDP Law — https://www.nortonrosefulbright.com/en-il/knowledge/publications/31bce8f0/highlights-of-indonesias-personal-data-protection-law
- Chambers 2025 guide (specific data, DPIA, DPO) — https://gpg-pdf.chambers.com/view/158325293/213/
- CMS, PDP Law compliance and transfers — https://cms.law/en/int/legal-updates/compliance-with-indonesia-s-personal-data-protection-law-by-october-2024
- Linklaters, Data Protected: Indonesia — https://www.linklaters.com/en/insights/data-protected/data-protected---indonesia
