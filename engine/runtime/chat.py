"""Office chat (T-063): pure parser, scan, status table, inbox plan and reply builder. Stdlib only, no I/O.

The schema is engine/schema/chat.md. The page (engine/app/office.template.html, OfficeCore.chat) holds the same
mention rules and scan; tests/fixtures/chat-mentions.json and chat-scan.json are read by both, so they cannot drift.
Chat text is company data: nothing here writes it anywhere, and every message this module returns names a field or
a kind of hit, never the text."""
import re
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from . import events

V = 1
ALL = "all"
DEFAULT = "pmo"
MAX_LEN = 4000
MAX_REPLY = 8000
MAX_QUESTION = 200
LEASE_S = 1800
RETENTION_DAYS = 30
STATUSES = ("new", "picked", "replying", "answered", "needs_merwyn")
# (from, to): who writes it. The page writes only the first state (an ask is created at "new").
TRANSITIONS = {
    "new": ("picked",),
    "picked": ("replying", "new", "answered", "needs_merwyn"),   # answered/needs_merwyn: a pmo ask answered in-session, or a repair
    "replying": ("answered", "needs_merwyn", "new"),
    "needs_merwyn": ("answered",),
    "answered": (),
}
MENTION_RE = re.compile(r"(^|[^\w@])@([A-Za-z][A-Za-z-]{0,23})", re.ASCII)
ID_RE = re.compile(r"^m-[0-9a-z]{6,12}-[0-9a-z]{4}$")
ISO_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d{1,3})?Z$")
ASK_KEYS = ("v", "kind", "id", "author", "author_uid", "text", "created_at", "mentions", "all", "unknown", "in_reply_to", "recipients")
REPLY_KEYS = ("v", "kind", "id", "reply_to", "author", "text", "created_at", "needs_merwyn", "question", "task")
REC_KEYS = ("status", "reply_id", "at", "by")
REMOVED = "[removed: looked like personal data]"
REFUSAL = ("I did not pass this on because it looked like personal data. "
           "Please resend without it, using an ID or a link.")


class Mentions(NamedTuple):
    ids: list
    all: bool
    unknown: list



# ---------- mentions ----------
def handles(org_agents):
    """{lowercased name: agent id} from org.yaml agents, in org order."""
    return {a["name"].lower(): a["id"] for a in org_agents if isinstance(a, dict) and a.get("id") and a.get("name")}


def parse_mentions(text, hmap):
    """ids in first-appearance order (deduplicated), all flag (ids then holds every agent), unknown names lowercased."""
    ids, unknown, all_ = [], [], False
    for m in MENTION_RE.finditer(text or ""):
        name = m.group(2).rstrip("-").lower()
        if name == ALL:
            all_ = True
        elif name in hmap:
            if hmap[name] not in ids:
                ids.append(hmap[name])
        elif name and name not in unknown:
            unknown.append(name)
    if all_:
        everyone = list(dict.fromkeys(hmap.values()))
        ids = everyone   # @all means every agent, in org order; explicit names are already in it
    return Mentions(ids, all_, unknown)


def route(m, default=DEFAULT):
    return list(m.ids) if m.ids else [default]


# ---------- the personal-data scan ----------
_EXTRA = (
    (re.compile(r"(?<![\w])(?:\+62|62|0)[\s-]?8\d{1,3}[\s.-]?\d{3,4}[\s.-]?\d{2,5}(?!\d)"), "phone number"),
    (re.compile(r"(?<!\d)\d{3,}(?:[ .-]\d{3,}){2,}(?!\d)"), "long number with separators"),
    (re.compile(r"\b(?:sk|pk|ghp|gho|ghs|xox[abp])[-_][A-Za-z0-9_-]{16,}|\bAKIA[0-9A-Z]{12,}|\bAIza[0-9A-Za-z_-]{20,}"), "secret-like token"),
    (re.compile(r"(?i)\b(?:password|passwd|secret|api[_ -]?key|token)\s*[:=]\s*\S{6,}"), "secret-like token"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}"), "secret-like token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY"), "secret-like token"),
)
_LONG_TOKEN = re.compile(r"(?<![\w/+=-])[A-Za-z0-9+/_-]{32,}(?![\w/+=-])")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def _digit_total(s):
    return sum(c.isdigit() for c in s)


def scan(text, forbidden=()):
    """Return the kind of the first hit ("email address", "16-digit run", ...), or None. Never returns the matched text."""
    s = text or ""
    for p, kind in zip(events.DATA_PATTERNS, events.PATTERN_KINDS):
        if p.search(s):
            return kind
    for p, kind in _EXTRA:
        m = p.search(s)
        if m and (kind != "long number with separators" or _digit_total(m.group(0)) >= 10):
            return kind
    for m in _LONG_TOKEN.finditer(s):
        t = m.group(0)
        if any(c.isdigit() for c in t) and any(c.isalpha() for c in t) and not _SHA.match(t):
            return "secret-like token"
    low = s.lower()
    if any(f and f in low for f in forbidden):
        return "forbidden term"
    return None


def pointer(ask_id):
    return f"chat message {ask_id}"


# ---------- schema ----------
def can_move(a, b):
    return b in TRANSITIONS.get(a, ())


def _iso(v):
    return isinstance(v, str) and bool(ISO_RE.match(v))


def parse_time(v):
    return datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reply_id(ask_id, agent):
    return f"r-{ask_id}-{agent}"


def validate(doc, agent_ids, default=DEFAULT):
    """Problems as 'field: what is wrong'. Names fields, never values."""
    if not isinstance(doc, dict):
        return ["doc: not an object"]
    out, ids = [], set(agent_ids)
    kind = doc.get("kind")
    keys = ASK_KEYS if kind == "ask" else REPLY_KEYS if kind == "reply" else None
    if keys is None:
        return ["kind: must be ask or reply"]
    for k in keys:
        if k not in doc:
            out.append(f"{k}: missing")
    for k in doc:
        if k not in keys:
            out.append(f"{k}: not defined for a {kind}")
    if out:
        return out
    if doc["v"] != V:
        out.append("v: must be 1")
    if not isinstance(doc["id"], str):
        out.append("id: must be a string")
    if not isinstance(doc["text"], str) or not (1 <= len(doc["text"]) <= (MAX_LEN if kind == "ask" else MAX_REPLY)):
        out.append("text: length out of range")
    if not _iso(doc["created_at"]):
        out.append("created_at: must be an ISO UTC time")
    if kind == "ask":
        if not (isinstance(doc["id"], str) and ID_RE.match(doc["id"])):
            out.append("id: bad pattern")
        if doc["author"] != "merwyn":
            out.append("author: must be merwyn")
        if not isinstance(doc["author_uid"], str) or not doc["author_uid"]:
            out.append("author_uid: must be a non-empty string")
        m = doc["mentions"]
        if not (isinstance(m, list) and all(isinstance(x, str) and x in ids for x in m) and len(set(m)) == len(m)):
            out.append("mentions: must be distinct agent ids")
        if not isinstance(doc["all"], bool):
            out.append("all: must be a boolean")
        u = doc["unknown"]
        if not (isinstance(u, list) and all(isinstance(x, str) for x in u)):
            out.append("unknown: must be a list of strings")
        if doc["in_reply_to"] is not None and not isinstance(doc["in_reply_to"], str):
            out.append("in_reply_to: must be null or a reply id")
        r = doc["recipients"]
        if not isinstance(r, dict) or not r:
            out.append("recipients: must be a non-empty object")
        elif not out:
            want = set(ids) if doc["all"] else (set(m) or {default})
            if set(r) != want:
                out.append("recipients: do not match the routing of mentions and all")
            for a, rec in r.items():
                if not isinstance(rec, dict) or set(rec) != set(REC_KEYS):
                    out.append(f"recipients.{a}: wrong keys")
                    continue
                if rec["status"] not in STATUSES:
                    out.append(f"recipients.{a}.status: unknown status")
                if rec["reply_id"] is not None and not isinstance(rec["reply_id"], str):
                    out.append(f"recipients.{a}.reply_id: must be null or a string")
                if not _iso(rec["at"]):
                    out.append(f"recipients.{a}.at: must be an ISO UTC time")
                if rec["by"] not in ("page", "session"):
                    out.append(f"recipients.{a}.by: must be page or session")
    else:
        if doc["author"] not in ids:
            out.append("author: unknown agent")
        if not (isinstance(doc["reply_to"], str) and ID_RE.match(doc["reply_to"])):
            out.append("reply_to: must be an ask id")
        elif doc["author"] in ids and doc["id"] != reply_id(doc["reply_to"], doc["author"]):
            out.append("id: must be r-<ask id>-<agent id>")
        if not isinstance(doc["needs_merwyn"], bool):
            out.append("needs_merwyn: must be a boolean")
        q = doc["question"]
        if q is not None and not (isinstance(q, str) and 1 <= len(q) <= MAX_QUESTION and "\n" not in q):
            out.append("question: one line, 1-200 characters, or null")
        if doc["needs_merwyn"] and q is None:
            out.append("question: required when needs_merwyn is true")
        if doc["task"] is not None and not (isinstance(doc["task"], str) and events.TASK_RE.match(doc["task"])):
            out.append("task: must be null or T-nnn")
    return out


def rules_problem(rules):
    """None when the declared rules keep chat readable and writable by the owner only; else a short reason (C7)."""
    if not isinstance(rules, list):
        return "rules: not a list"
    hit = [r for r in rules if isinstance(r, dict) and r.get("path") == "chat"]
    if len(hit) != 1:
        return "rules: need exactly one rule for path chat"
    if hit[0].get("read") != "owner" or hit[0].get("write") != "owner":
        return "rules: chat must be read owner and write owner"
    for r in rules:
        if isinstance(r, dict) and r is not hit[0] and str(r.get("path", "")).startswith("chat/") and \
                (r.get("read") != "owner" or r.get("write") != "owner"):
            return "rules: a path under chat is open below owner"
    return None


# ---------- inbox ----------
Action = dict


def _norm(items):
    """Accept bare docs or {id, data, version} wrappers. Returns [(doc, version)]."""
    out = []
    for it in items:
        if isinstance(it, dict) and isinstance(it.get("data"), dict):
            out.append((it["data"], it.get("version", it.get("_version"))))
        else:
            out.append((it, it.get("_version") if isinstance(it, dict) else None))
    return out


def _clean(doc):
    return {k: v for k, v in doc.items() if k != "_version"}


def ask_path(ask_id):
    return f"chat/office/messages/{ask_id}"


def _sorted_asks(asks):
    return sorted(asks, key=lambda p: (parse_time(p[0]["created_at"]), p[0]["id"]))


def _with(rec, status, now, by="session", reply=None):
    return {"status": status, "reply_id": reply if reply is not None else rec["reply_id"], "at": _fmt(now), "by": by}


def plan(items, now, agent_ids, lease_s=LEASE_S, forbidden=(), default=DEFAULT):
    """Return (actions, skipped). One action per ask, in order. Each action:
    {op: claim|reset|repair|close|mixed|refuse|post, path, patch|doc, ask, agents, changes:[{agent, op, from, to}], ifVersion}.
    Claims come first in the list so no agent is spawned before its claim is written. skipped: 'id: problem' lines."""
    skipped, asks, replies = [], [], {}
    for doc, ver in _norm(items):
        problems = validate(doc, agent_ids, default)
        if problems:
            skipped.append(f"{doc.get('id', '?') if isinstance(doc, dict) else '?'}: {problems[0]}")
            continue
        if doc["kind"] == "reply":
            replies[doc["id"]] = doc
        else:
            asks.append((doc, ver))
    asks = _sorted_asks(asks)
    actions = []
    for idx, (ask, ver) in enumerate(asks):
        rec = ask["recipients"]
        new = [a for a, r in rec.items() if r["status"] == "new"]
        if new and ask["text"] != REMOVED and scan(ask["text"], forbidden):
            now_rec = {a: (_with(r, "answered", now, reply=reply_id(ask["id"], default)) if r["status"] == "new" else r) for a, r in rec.items()}
            rid = reply_id(ask["id"], default)
            doc = {"v": V, "kind": "reply", "id": rid, "reply_to": ask["id"], "author": default, "text": REFUSAL,
                   "created_at": _fmt(now), "needs_merwyn": False, "question": None, "task": None}
            actions.append({"op": "post", "path": f"chat/office/messages/{rid}", "doc": doc, "ask": ask["id"], "agents": [default]})
            actions.append({"op": "refuse", "path": ask_path(ask["id"]), "patch": {"text": REMOVED, "recipients": now_rec},
                            "ask": ask["id"], "agents": new, "ifVersion": ver,
                            "changes": [{"agent": a, "op": "refuse", "from": "new", "to": "answered"} for a in new]})
            continue
        changes, newrec = [], dict(rec)
        for a, r in rec.items():
            st, rep = r["status"], replies.get(reply_id(ask["id"], a))
            to, op = None, None
            if st == "new":
                to, op = "picked", "claim"
            elif st in ("picked", "replying"):
                if rep is not None:
                    to, op = ("needs_merwyn" if rep["needs_merwyn"] else "answered"), "repair"
                elif now - parse_time(r["at"]) > timedelta(seconds=lease_s):
                    to, op = "new", "reset"
            elif st == "needs_merwyn" and _followed(asks[idx + 1:], ask, a):
                to, op = "answered", "close"
            if to and can_move(st, to):
                newrec[a] = _with(r, to, now, reply=reply_id(ask["id"], a) if op == "repair" else None)
                if op == "reset":
                    newrec[a]["by"] = "session"
                changes.append({"agent": a, "op": op, "from": st, "to": to})
        if changes:
            ops = {c["op"] for c in changes}
            actions.append({"op": ops.pop() if len(ops) == 1 else "mixed", "path": ask_path(ask["id"]),
                            "patch": {"recipients": newrec}, "ask": ask["id"], "agents": [c["agent"] for c in changes],
                            "changes": changes, "ifVersion": ver})
    actions.sort(key=lambda x: 0 if x["op"] in ("post", "refuse") else (1 if any(c["op"] == "claim" for c in x.get("changes", ())) else 2))
    return actions, skipped


def _followed(later, ask, agent):
    """True when a later ask from Merwyn is picked for this agent (an in_reply_to match counts too)."""
    rid = ask["recipients"][agent]["reply_id"] or reply_id(ask["id"], agent)
    for doc, _ in later:
        r = doc["recipients"].get(agent)
        picked = any(x["status"] != "new" for x in doc["recipients"].values())
        if (r is not None and r["status"] != "new") or (doc["in_reply_to"] == rid and picked):
            return True
    return False


def set_status(ask, agent, to, now):
    """(path, patch) moving one recipient to replying (the only step the session writes outside plan and reply)."""
    r = ask["recipients"].get(agent)
    if r is None:
        raise ValueError("agent is not a recipient of this ask")
    if not can_move(r["status"], to):
        raise ValueError(f"cannot move {r['status']} to {to}")
    return ask_path(ask["id"]), {"recipients": {**ask["recipients"], agent: _with(r, to, now)}}


def reply(ask, agent, text, needs_merwyn, question, task, now):
    """(path, reply doc, ask patch). The id is r-<ask>-<agent>, so a re-run overwrites and never duplicates."""
    r = ask["recipients"].get(agent)
    if r is None:
        raise ValueError("agent is not a recipient of this ask")
    to = "needs_merwyn" if needs_merwyn else "answered"
    if not can_move(r["status"], to):
        raise ValueError(f"cannot move {r['status']} to {to}")
    if not isinstance(text, str) or not (1 <= len(text) <= MAX_REPLY):
        raise ValueError("text must be 1-8000 characters")
    if needs_merwyn and not question:
        raise ValueError("a needs_merwyn reply needs a question")
    if question is not None and (len(question) > MAX_QUESTION or "\n" in question or not question):
        raise ValueError("question must be one line, 1-200 characters")
    if task is not None and not events.TASK_RE.match(task):
        raise ValueError("task must be T-nnn")
    rid = reply_id(ask["id"], agent)
    doc = {"v": V, "kind": "reply", "id": rid, "reply_to": ask["id"], "author": agent, "text": text, "created_at": _fmt(now),
           "needs_merwyn": bool(needs_merwyn), "question": question if needs_merwyn else None, "task": task}
    patch = {"recipients": {**ask["recipients"], agent: _with(r, to, now, reply=rid)}}
    return f"chat/office/messages/{rid}", doc, patch


def purge(items, now, days=RETENTION_DAYS):
    """Whole-document deletes (C6): asks whose recipients are all answered and older than days, and replies to
    those asks, plus replies whose ask is gone and that are older than days. Returns [{op:'delete', path, id}]."""
    cut = now - timedelta(days=days)
    docs = [d for d, _ in _norm(items) if isinstance(d, dict) and isinstance(d.get("id"), str)
            and d.get("kind") in ("ask", "reply") and _iso(d.get("created_at"))]
    asks = {d["id"]: d for d in docs if d["kind"] == "ask"}
    gone = {i for i, d in asks.items() if isinstance(d.get("recipients"), dict) and d["recipients"]
            and all(isinstance(r, dict) and r.get("status") == "answered" for r in d["recipients"].values())
            and parse_time(d["created_at"]) < cut}
    out = []
    for d in sorted(docs, key=lambda d: (parse_time(d["created_at"]), d["id"])):
        old = parse_time(d["created_at"]) < cut
        if (d["kind"] == "ask" and d["id"] in gone) or \
                (d["kind"] == "reply" and (d.get("reply_to") in gone or (d.get("reply_to") not in asks and old))):
            out.append({"op": "delete", "path": f"chat/office/messages/{d['id']}", "id": d["id"]})
    return out
