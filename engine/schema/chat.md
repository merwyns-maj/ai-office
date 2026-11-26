# Office chat schema (T-063)

The chat is a shared inbox in the AI Office artifact's own database (`db` capability). The page (Merwyn only) writes asks;
the office session (Janice, the main session) reads them, routes each to the mentioned agents, and writes replies.
Code: `engine/runtime/chat.py` (office side) and `OfficeCore.chat` in `engine/app/office.template.html` (page).
Parity fixtures read by both: `tests/fixtures/chat-mentions.json`, `tests/fixtures/chat-scan.json`.

Chat text is company data. It lives only in the artifact database (claude.ai, owner access). It never enters this repo:
the CLI reads stdin and writes stdout, tasks hold a pointer (`chat message <id>`), fixtures are invented.

## Layout (even segment count = document)
- `chat/office` (doc, meta, written only by the session): `{v:1, last_inbox_at:"<ISO UTC>", by:"pmo", running:bool}`. The page shows "Office running" when `running` is true and `last_inbox_at` is under 15 minutes old.
- `chat/office/messages/{id}` (docs): asks and replies, below.
- Rules (declared with the artifact): `[{path:"chat", read:"owner", write:"owner"}]`. `chat.rules_problem` checks them; the inbox refuses to route otherwise (C7).

## Ask (written by the page)
`{v:1, kind:"ask", id:"m-<Date.now() base36>-<4 base36>", author:"merwyn", author_uid, text (1..4000), created_at, mentions:[agent ids], all:bool, unknown:[lowercased names], in_reply_to:null|<reply id>, recipients:{<agent id>:{status, reply_id, at, by}}}`
- `recipients` keys: the mentioned agents; every agent for `@all`; `["pmo"]` when nothing is mentioned. Unknown names are never routed.
- Mentions: regex `(^|[^\w@])@([A-Za-z][A-Za-z-]{0,23})`, ASCII, name looked up lowercased; a trailing `-` is dropped; `@all` is every agent in org order.

## Reply (written by the session)
`{v:1, kind:"reply", id:"r-<ask id>-<agent id>", reply_to:<ask id>, author:<agent id>, text (1..8000), created_at, needs_merwyn:bool, question:null|<one line, <=200>, task:null|"T-nnn"}`. The id is deterministic, so a re-run overwrites and never duplicates.

## Status per recipient
new, picked, replying, answered, needs_merwyn. Table (`chat.TRANSITIONS`, same in the page): new to picked (claim); picked to replying; picked or replying to answered or needs_merwyn (reply written; a pmo ask is answered from picked); picked or replying back to new (lease older than 1800 s with no reply doc, or `ifVersion` lost); needs_merwyn to answered (a later ask is picked for that agent, or `in_reply_to` matches). `answered` is terminal.

## CLI (stdin only; output is never redirected into the repo)
- `python -m engine.runtime chat plan ai-office`: stdin `{"rules":[...], "docs":[...]}`. Docs are bare docs or `{id, data, version}` wrappers (the db result shape is not checked yet: see the task's open questions). Prints a JSON list of actions in order (`post` and `refuse` for asks that failed the scan, then claims, then the rest): `{op: claim|reset|repair|close|mixed|refuse|post, path, patch|doc, ask, agents, changes, ifVersion}`. One action per ask, so one `ifVersion` per write. The patch always carries the whole `recipients` map. Exit 1 on bad input, bad rules or no rules.
- `chat reply ai-office --agent ID [--needs-merwyn] [--task T-nnn]`: stdin `{"ask": <ask doc>, "text": "...", "question": null|"..."}`. Prints `{path, doc, patch, ifVersion}`. Exit 1 on a scan hit (the kind only) or a bad transition.
- `chat status ai-office --agent ID`: stdin `{"ask": ...}`; prints the picked-to-replying patch.
- `chat purge ai-office`: stdin a list of docs; prints whole-document deletes for answered asks and their replies older than 30 days.
- `chat mentions ai-office`: stdin text; prints the routing. `chat rules ai-office`: stdin the rules list.

## Scan (`chat.scan`, JS `OfficeCore.chat.scan`)
Kinds: email address, 16-digit run, run of 10+ digits (the `events.py` patterns), phone number, long number with separators, secret-like token, and forbidden terms (office side only). A hit returns the kind, never the text. It catches patterns, not names.
