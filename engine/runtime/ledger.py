"""Agent-run ledger parser, totals and v1 event-log converter (engine/schema/usage.md, T-057).

Stdlib only; never raises on bad input. One ledger file per Claude session: a header line, then one line per agent run.
Reuses the events.py data rule and LogProblem."""
import json
import re
from datetime import date
from pathlib import Path

from . import events
from .events import LogProblem

SESSION_RE = re.compile(r"^session_[A-Za-z0-9]{8,64}$")
STEP_RE = re.compile(r"^[a-z][a-z-]{0,23}$")
NOT_REPORTED = ("split", "model", "main_session")
HEADER_TEXT = ("source", "recorded_by", "covers")
HEADER_KEYS = ("log", "v", "office", "session", "source", "recorded_by", "covers", "date", "not_reported", "provider")
RUN_KEYS = ("n", "sprint", "agent", "tasks", "step", "tokens", "tool_uses", "duration_ms", "note", "date",
            "model", "input", "output", "cache_read", "cache_write")
NUMS = ("tokens", "tool_uses", "duration_ms")
SPLIT = ("input", "output", "cache_read", "cache_write")
MAX_NOTE = 200
CHAT_NOTE = re.compile(r"^chat message m-[0-9a-z]{6,12}-[0-9a-z]{4}$")


def _int(v, lo=0, hi=events.MAX_TOKENS):
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


def _text(v, lo=1, hi=300):
    return isinstance(v, str) and lo <= len(v) <= hi and "\n" not in v and "\r" not in v


def _iso_date(v):
    try:
        return isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) is not None and date.fromisoformat(v) is not None
    except ValueError:
        return False


def _check_header(h, office, providers=None):
    if h.get("log") != "agent-runs":
        return "header: log must be 'agent-runs'"
    if h.get("v") != 1 or isinstance(h.get("v"), bool):
        return "header: v must be 1"
    if not isinstance(h.get("office"), str) or (office is not None and h["office"] != office):
        return "header: office is missing or is not this office"
    if not isinstance(h.get("session"), str) or not SESSION_RE.match(h["session"]):
        return "header: session must look like session_<8-64 letters or digits>"
    for k in HEADER_TEXT:
        if not _text(h.get(k)):
            return f"header: {k} must be 1-300 characters with no newline"
    try:
        ok = isinstance(h.get("date"), str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", h["date"]) and date.fromisoformat(h["date"])
    except ValueError:
        ok = False
    if not ok:
        return "header: date must be YYYY-MM-DD"
    if "provider" in h and not (isinstance(h["provider"], str) and events.PROVIDER_RE.match(h["provider"])):
        return "header: provider must be a provider id"
    if "provider" in h and providers is not None and h["provider"] not in providers:
        return "header: provider is not an id in providers.yaml"
    nr = h.get("not_reported")
    if not isinstance(nr, list) or any(x not in NOT_REPORTED for x in nr) or len(set(nr)) != len(nr):
        return "header: not_reported must be a list drawn from " + ", ".join(NOT_REPORTED)
    return None


def _check_run(r, agents):
    for k in ("n", "sprint", "agent", "tasks", "step") + NUMS:
        if k not in r:
            return f"missing field {k!r}"
    if not _int(r["n"], 1) or not _int(r["sprint"], 1):
        return "n and sprint must be integers >= 1"
    if not isinstance(r["agent"], str) or r["agent"] not in agents:
        return f"unknown agent {r['agent']!r}"
    t = r["tasks"]
    if t == [] and r["step"] == "chat":   # a chat run (T-063) has no task; its note is the pointer to the db message
        if not (isinstance(r.get("note"), str) and CHAT_NOTE.match(r["note"])):
            return "a chat run needs note 'chat message <id>'"
    elif not (isinstance(t, list) and 1 <= len(t) <= 8 and len(set(map(str, t))) == len(t)
            and all(isinstance(x, str) and events.TASK_RE.match(x) for x in t)):
        return "tasks must be 1 to 8 distinct task ids"
    if not isinstance(r["step"], str) or not STEP_RE.match(r["step"]):
        return "step must be a lowercase slug"
    for k in NUMS:
        if r[k] is not None and not _int(r[k]):
            return f"{k} must be an integer from 0 to {events.MAX_TOKENS}, or null for not reported"
    if "note" in r and not _text(r["note"], 1, MAX_NOTE):
        return f"note must be 1-{MAX_NOTE} characters with no newline"
    if "date" in r and not _iso_date(r["date"]):
        return "date must be YYYY-MM-DD"
    if "model" in r and not (isinstance(r["model"], str) and events.MODEL_RE.match(r["model"])):
        return "bad model id"
    present = [k for k in SPLIT if k in r]
    if present:
        for k in present:
            if not _int(r[k]):
                return f"{k} must be an integer from 0 to {events.MAX_TOKENS}"
        if "input" not in r or "output" not in r:
            return "input and output are required when any of input, output, cache_read, cache_write is present"
        if r["tokens"] != sum(r[k] for k in present):
            return "tokens must equal input + output + cache_read + cache_write"
    return None


def parse_ledger(text, *, agents, office=None, forbidden=(), providers=None):
    """Return (header or None, kept runs in file order, problems). A bad header rejects the file.

    providers: optional ids from providers.yaml; with it, a header provider outside them is an error."""
    problems, runs, header = [], [], None
    seen_header, last_n = False, 0
    warned = set()

    def err(n, m):
        problems.append(LogProblem(n, "error", m))

    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        if len(raw) > events.MAX_LINE:
            err(n, f"line longer than {events.MAX_LINE} characters")
            if not seen_header:
                return None, [], problems
            continue
        try:
            obj = json.loads(raw, object_pairs_hook=events._pairs)
        except events._Dup as e:
            err(n, str(e))
            obj = None
        except ValueError as e:
            err(n, f"malformed JSON: {e}")
            obj = None
        if obj is not None and not isinstance(obj, dict):
            err(n, "line is not a JSON object")
            obj = None
        hit = events._data_hit(obj, forbidden) if obj is not None else None   # first, on every line
        if not seen_header:
            seen_header = True
            if obj is None:
                err(n, "missing or invalid header: file rejected")
                return None, [], problems
            if hit:
                err(n, hit)
                return None, [], problems
            bad = _check_header(obj, office, providers)
            if bad:
                err(n, bad + ": file rejected")
                return None, [], problems
            for k in obj:
                if k not in HEADER_KEYS:
                    problems.append(LogProblem(n, "warning", f"header field {k!r} is not defined (kept)"))
            header = obj
            continue
        if obj is None:
            continue
        if hit:
            err(n, hit)
            continue
        bad = _check_run(obj, agents)
        if not bad and obj["n"] <= last_n:
            bad = f"n must increase strictly ({obj['n']} after {last_n})"
        if bad:
            err(n, bad)
            continue
        if last_n and obj["n"] > last_n + 1:
            problems.append(LogProblem(n, "warning", f"gap in n ({last_n} then {obj['n']})"))
        for k in obj:
            if k not in RUN_KEYS and k not in warned:
                warned.add(k)
                problems.append(LogProblem(n, "warning", f"field {k!r} is not defined for a run (kept)"))
        last_n = obj["n"]
        runs.append(obj)
    if not seen_header:
        err(1, "empty file: no header")
    return header, runs, problems


def load_ledger(path, *, agents, office=None, forbidden=(), providers=None):
    """parse_ledger on a file, plus the file-stem = session check. Raises OSError for an unreadable file."""
    path = Path(path)
    header, runs, problems = parse_ledger(path.read_text(encoding="utf-8"), agents=agents, office=office, forbidden=forbidden, providers=providers)
    if header is not None and header["session"] != path.stem:
        problems.append(LogProblem(1, "error", f"file name {path.stem!r} must equal the header session {header['session']!r}"))
        problems.sort(key=lambda p: p.line)
    return header, runs, problems


def _row():
    return {"runs": 0, "not_reported": 0, "tokens": 0, "tool_uses": 0, "duration_ms": 0, "tasks": []}


def _add(row, r):
    row["runs"] += 1
    if r["tokens"] is None:
        row["not_reported"] += 1   # runs whose harness report had no usage
    for k in NUMS:
        row[k] += r[k] or 0
    row["tasks"] = sorted(set(row["tasks"]) | set(r["tasks"]))


def totals(runs):
    """Session, per-agent, per-sprint and per-task totals; null adds 0 and counts once under not_reported.

    A run with one task counts in that task's solo_tokens; a run with 2+ tasks counts once in `shared` and in full in
    tokens_with_shared of every task it touched (never apportioned)."""
    out = {"session": _row(), "agents": {}, "sprints": {}, "tasks": {}, "shared": _row()}
    for r in runs:
        _add(out["session"], r)
        _add(out["agents"].setdefault(r["agent"], _row()), r)
        _add(out["sprints"].setdefault(r["sprint"], _row()), r)
        tok = r["tokens"] or 0
        shared = len(r["tasks"]) != 1   # 2+ tasks, or none (a chat run): counted once, in `shared`, never in a task row
        if shared:
            _add(out["shared"], r)
        for t in r["tasks"]:
            row = out["tasks"].setdefault(t, {"runs": 0, "solo_runs": 0, "solo_tokens": 0, "shared_runs": 0,
                                              "tokens_with_shared": 0, "not_reported": 0})
            row["runs"] += 1
            row["tokens_with_shared"] += tok
            row["not_reported"] += 1 if r["tokens"] is None else 0
            if shared:
                row["shared_runs"] += 1
            else:
                row["solo_runs"] += 1
                row["solo_tokens"] += tok
    return out


def to_event_log(header, runs):
    """Convert a parsed ledger to a v1 event log (text) with usage_source 'recorded' and the total shape of usage."""
    office, name = header["office"], header["session"] + ".jsonl"
    ref = f"offices/{office}/usage/{name}"
    head = {"log": "office-events", "v": 1, "office": office, "clock": "synthetic", "usage_source": "recorded",
            "title": f"Recorded agent runs, {header['session']} (T-057)", "covers": header["covers"], "ledger": ref}
    if "provider" in header:
        head["provider"] = header["provider"]
    lines = [json.dumps(head, ensure_ascii=False, separators=(",", ":"))]
    for r in runs:
        if not r["tasks"]:
            continue   # a chat run has no task for the event shape; its tokens stay in the ledger totals
        ev = {"t": 2 * (r["n"] - 1), "type": "usage", "src": f"{ref}#n={r['n']}", "agent": r["agent"], "task": r["tasks"][0],
              "tasks": r["tasks"], "total": r["tokens"], "tool_uses": r["tool_uses"], "run": r["n"], "sprint": r["sprint"], "step": r["step"]}
        if "note" in r:
            ev["note"] = r["note"]
        lines.append(json.dumps(ev, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(lines) + "\n"
