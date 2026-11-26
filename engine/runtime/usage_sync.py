"""Usage sync plan (T-069): the repo ledger and budgets.yaml -> the artifact db, one way, re-runnable. Stdlib only, no I/O.

The page (engine/app/office.template.html, usageStore and OfficeCore.usagePick) reads these docs; schema in engine/schema/usage.md.
  usage/office                          meta, written last = the commit point
  usage/office/chunks/<session>-<k:03>  run lines in file order, packed by bytes
  usage/budgets                         the resolved budgets.yaml
plan() returns the db_write actions that make the db equal to the repo, or raises Refused. A doc whose content already matches
gets no action, so a second plan gives 0 writes. Every string of every doc is scanned before anything is planned (U1); messages
name a doc, a field and a kind of hit, never the text. Output is stdin-to-stdout only: it is never written into the repo (U7)."""
import hashlib
import json

from . import chat, events, ledger

V = 1
MAX_DOC = 256 * 1024
MAX_DOCS = 25000
CHUNK_BYTES = 128 * 1024
META, BUDGETS, CHUNKS = "usage/office", "usage/budgets", "usage/office/chunks"
HEADER_KEEP = ("provider", "not_reported", "covers")
OVERHEAD = 256   # room for a chunk doc's own keys around its run lines


class Refused(Exception):
    def __init__(self, message, report=None):
        super().__init__(message)
        self.report = report or {}


def dumps(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def norm(o):
    """What the db hands back after JSON: int keys become strings, tuples lists."""
    return json.loads(dumps(o))


def size(o):
    return len(dumps(o).encode("utf-8"))


def sha(o):
    return hashlib.sha256(dumps(o).encode("utf-8")).hexdigest()


def chunk_path(session, k):
    return f"{CHUNKS}/{session}-{k:03d}"


def _walk(o, where):
    if isinstance(o, str):
        yield where, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{where}.{k}" if where else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{where}[{i}]")


def scan_doc(path, doc, forbidden, session):
    """U1: chat.scan (a superset of events._data_hit) plus the forbidden terms on every string. Returns a message or None.
    The one exempt string is the validated session id itself, in the top-level `session` field of a doc (it is the ledger's file name; ledger.SESSION_RE); it gets the
    events.py data rule and the forbidden terms but not the long-token rule, which a 32-character id would trip."""
    for where, s in _walk(doc, ""):
        if where == "session" and s == session and ledger.SESSION_RE.fullmatch(s):   # U1a: the pattern is checked here, not left to the loader
            kind = next((k for pat, k in zip(events.DATA_PATTERNS, events.PATTERN_KINDS) if pat.search(s)), None)
            if kind is None and any(f and f in s.lower() for f in forbidden):
                kind = "forbidden term"
        else:
            kind = chat.scan(s, forbidden)
        if kind:
            return f"{path}: field '{where}' looks like personal data ({kind}); nothing planned"
    return None


def check_runs(runs):
    """U2: a run keeps only the known fields; one with another field is refused (the loader only warns)."""
    for r in runs:
        extra = [k for k in r if k not in ledger.RUN_KEYS]
        if extra:
            raise Refused(f"run n={r.get('n')}: {len(extra)} field(s) outside the allowlist ({', '.join(sorted(extra)[:3])}); nothing planned")


def pack(session, runs, limit=CHUNK_BYTES):
    """Chunks of run lines in file order. A chunk closes before the next run would take it past `limit` bytes."""
    chunks, cur, used = [], [], OVERHEAD
    for r in runs:
        b = size(r) + 1
        if cur and used + b > limit:
            chunks.append(cur)
            cur, used = [], OVERHEAD
        cur.append(r)
        used += b
    if cur:
        chunks.append(cur)
    return [{"v": V, "session": session, "k": k, "first_n": c[0]["n"], "last_n": c[-1]["n"], "runs": c} for k, c in enumerate(chunks, 1)]


def build(header, runs, main, budgets, chunk_bytes=CHUNK_BYTES):
    """The docs the db should hold, as {path: doc}, plus the meta without synced_at (that is stamped only when something is written)."""
    session = header["session"]
    check_runs(runs)
    docs = {}
    chunks = []
    for c in pack(session, runs, chunk_bytes):
        c = norm(c)
        path = chunk_path(session, c["k"])
        docs[path] = c
        chunks.append({"id": path.rsplit("/", 1)[1], "first_n": c["first_n"], "last_n": c["last_n"], "bytes": size(c), "sha256": sha(c)})
    if budgets is not None:
        docs[BUDGETS] = norm(budgets)
    meta = {"v": V, "by": "pmo", "session": session, "runs": len(runs), "last_n": runs[-1]["n"] if runs else 0, "chunks": chunks,
            "header": {k: header[k] for k in HEADER_KEEP if k in header}, "totals": ledger.totals(runs), "main": ledger.main_totals(main),
            "budgets_sha256": sha(docs[BUDGETS]) if budgets is not None else None}
    docs[META] = norm(meta)
    return docs


def _existing(items):
    out = {}
    for it in items:
        if not isinstance(it, dict):
            raise Refused("docs: each item must be an object with path or id, data and version")
        path = it.get("path", it.get("id"))
        if not isinstance(path, str) or "data" not in it:
            raise Refused("docs: each item needs a path (or id) and data")
        if path.startswith("usage"):
            out[path] = (it["data"], it.get("version"))
    return out


def _act(op, path, version, doc=None):
    a = {"op": op, "path": path}
    if doc is not None:
        a["doc"] = doc
    if version is not None:
        a["ifVersion"] = version
    return a


def plan(header, runs, main, budgets, items, *, rules, other_docs=0, forbidden=(), now, max_doc=MAX_DOC, max_docs=MAX_DOCS, chunk_bytes=CHUNK_BYTES):
    """Return {"actions": [...], "report": {...}} or raise Refused. `items` are the usage docs now in the db: [{path|id, data, version}]."""
    report = {"docs": 0, "largest_doc_bytes": 0, "other_docs": other_docs, "limits": {"docs": max_docs, "doc_bytes": max_doc}}
    try:
        for path in ("usage", "chat"):   # U3, and the chat rule must still be owner-only
            bad = chat.rules_problem(rules, path)
            if bad:
                raise Refused(f"refusing to write: {bad}", report)
        if not isinstance(other_docs, int) or isinstance(other_docs, bool) or other_docs < 0:
            raise Refused("other_docs: must be a whole number (the count of chat docs)", report)
        want = build(header, runs, main, budgets, chunk_bytes)
        report["docs"] = len(want)
        report["largest_doc_bytes"] = max(size(d) for d in want.values())
        session = header["session"]
        for path, doc in want.items():   # U1: every string of every doc; generated hashes and chunk ids are not text from the ledger
            src = {k: v for k, v in doc.items() if k not in ("chunks", "budgets_sha256")} if path == META else doc
            bad = scan_doc(path, src, forbidden, session)
            if bad:
                raise Refused(bad, report)
        if len(want) + other_docs > max_docs:
            raise Refused(f"refusing: {len(want)} usage docs + {other_docs} other docs would pass the {max_docs} doc limit; nothing planned", report)
        old = _existing(items)
        stamped = dict(want[META], synced_at=now)
        report["largest_doc_bytes"] = max(report["largest_doc_bytes"], size(stamped))
        if report["largest_doc_bytes"] > max_doc:
            big = max(list(want) + [META], key=lambda p: size(want[p]))
            raise Refused(f"refusing: {big} is {report['largest_doc_bytes']} bytes, over the {max_doc} byte doc limit; nothing planned", report)
    except Refused as e:
        e.report = e.report or report
        raise
    changed = [p for p in want if p != META and (p not in old or norm(old[p][0]) != want[p])]
    meta_old = norm(old[META][0]) if META in old else None
    meta_same = meta_old is not None and {k: v for k, v in meta_old.items() if k != "synced_at"} == want[META]
    actions = []
    if changed or not meta_same:
        order = sorted((p for p in changed if p.startswith(CHUNKS)), key=lambda p: want[p]["k"]) + [p for p in changed if p == BUDGETS]
        actions = [_act("set", p, old[p][1] if p in old else None, want[p]) for p in order]
        actions.append(_act("set", META, old[META][1] if META in old else None, stamped))
    orphans = sorted(p for p in old if p not in want and (p.startswith(CHUNKS + "/") or p == BUDGETS))
    unknown = sorted(p for p in old if p not in want and p not in orphans)
    actions += [_act("delete", p, old[p][1]) for p in orphans]   # U6: the db mirrors the repo, so what the repo no longer has goes
    report.update({"runs": len(runs), "chunks": sum(1 for p in want if p.startswith(CHUNKS)), "writes": sum(a["op"] == "set" for a in actions),
                   "deletes": len(orphans), "orphans": orphans, "unknown": unknown, "in_sync": not actions, "synced_at": now if any(a["op"] == "set" for a in actions) else (meta_old or {}).get("synced_at")})
    return {"actions": actions, "report": report}
