"""Event log v0 parser and validator (engine/schema/events.md). Stdlib only, never raises on bad input."""
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .miniyaml import loads

SCHEMA_VERSION = 0
MAX_LINE = 2000
TASK_RE = re.compile(r"^T-\d{3}$")
VERDICTS = ("PASS", "PASS_WITH_CONDITIONS", "BLOCK")
CLOCKS = ("synthetic", "wall")
OWN_ORG = "merwyns-maj"

# type -> {field: kind}; kinds: AGENT TASK STAGE TEXT INT VERDICT AGENTS LINES; a trailing "?" marks an optional field
EVENT_TYPES = {
    "step_started": {"agent": "AGENT", "task": "TASK"},
    "stage_changed": {"task": "TASK", "from": "STAGE", "to": "STAGE"},
    "handoff": {"task": "TASK", "from_agent": "AGENT", "to_agent": "AGENT", "to_stage": "STAGE"},
    "discussion": {"task": "TASK", "agents": "AGENTS", "lines": "LINES"},
    "needs_merwyn": {"agent": "AGENT", "task": "TASK", "reason": "TEXT"},
    "merwyn_answered": {"agent": "AGENT", "task": "TASK", "answer": "TEXT"},
    "review_pass": {"task": "TASK", "agent": "AGENT", "note": "TEXT?"},
    "review_reject": {"task": "TASK", "agent": "AGENT", "reason": "TEXT"},
    "compliance_result": {"task": "TASK", "agent": "AGENT", "verdict": "VERDICT"},
    "blocked": {"agent": "AGENT", "task": "TASK", "reason": "TEXT"},
    "merged": {"task": "TASK", "pr": "INT"},
}
COMMON = ("t", "type", "src", "wall")

DATA_PATTERNS = (
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),   # email
    re.compile(r"(?<!\d)\d{16}(?!\d)"),        # NIK-like
    re.compile(r"\d{10,}"),                    # account-like
)


@dataclass(frozen=True)
class LogProblem:
    line: int
    level: str   # "error" | "warning"
    message: str

    def __str__(self):
        return f"{self.line}: {self.level}: {self.message}"


class _Dup(ValueError):
    pass


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise _Dup(f"duplicate key {k!r}")
        out[k] = v
    return out


def forbidden_terms(repo_root):
    """Org and repo names from workspaces.yaml that do not belong to the personal org."""
    path = Path(repo_root) / "workspaces.yaml"
    try:
        data = loads(path.read_text(encoding="utf-8"), str(path))
    except (OSError, ValueError):
        return ()
    terms = []
    for group in ("brains", "projects"):
        for entry in (data.get(group) or {}).values():
            repo = entry.get("repo") if isinstance(entry, dict) else None
            if isinstance(repo, str) and "/" in repo:
                org, name = repo.split("/", 1)
                if org != OWN_ORG:
                    terms += [org, name]
    return tuple(sorted({t.lower() for t in terms if t}))


def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def _data_hit(obj, forbidden):
    for s in _strings(obj):
        low = s.lower()
        for p in DATA_PATTERNS:
            if p.search(s):
                return f"personal-data pattern in {s[:40]!r}"
        for f in forbidden:
            if f and f in low:
                return f"forbidden term {f!r}"
    return None


def _text_ok(v):
    return isinstance(v, str) and 1 <= len(v) <= 120 and "\n" not in v and "\r" not in v


def _wall(v):
    if not isinstance(v, str):
        return None
    try:
        d = datetime.fromisoformat(v)
    except ValueError:
        return None
    return d if d.tzinfo is not None else None


def _check_field(kind, v, agents, stages):
    """Return an error string, or None when the value fits the kind."""
    if kind == "AGENT":
        return None if isinstance(v, str) and v in agents else f"unknown agent {v!r}"
    if kind == "TASK":
        return None if isinstance(v, str) and TASK_RE.match(v) else f"bad task id {v!r}"
    if kind == "STAGE":
        return None if isinstance(v, str) and v in stages else f"unknown stage {v!r}"
    if kind == "TEXT":
        return None if _text_ok(v) else "text must be 1-120 characters with no newline"
    if kind == "INT":
        return None if isinstance(v, int) and not isinstance(v, bool) and v >= 1 else "must be an integer >= 1"
    if kind == "VERDICT":
        return None if v in VERDICTS else f"verdict must be one of {', '.join(VERDICTS)}"
    return None


def _check_discussion(ev, agents):
    ag = ev.get("agents")
    if not isinstance(ag, list) or not 2 <= len(ag) <= 4:
        return "agents must be a list of 2 to 4"
    if len(set(map(str, ag))) != len(ag) or any(not isinstance(a, str) or a not in agents for a in ag):
        return "agents must be distinct known agent ids"
    lines = ev.get("lines")
    if not isinstance(lines, list) or not 1 <= len(lines) <= 6:
        return "lines must be a list of 1 to 6"
    for ln in lines:
        if not isinstance(ln, dict) or ln.get("agent") not in ag or not _text_ok(ln.get("text")):
            return "each line needs an agent from agents and text of 1-120 characters"
    return None


def parse_log(text, *, agents, stages, forbidden=()):
    """Return (header, kept events in file order, problems). Events carry their file line as '_line'."""
    problems = []
    header = None
    kept = []
    last_t = 0.0
    last_wall = None
    seen_header = False

    def err(n, msg):
        problems.append(LogProblem(n, "error", msg))

    def warn(n, msg):
        problems.append(LogProblem(n, "warning", msg))

    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        if len(raw) > MAX_LINE:
            err(n, f"line longer than {MAX_LINE} characters")
            if not seen_header:
                break
            continue
        try:
            obj = json.loads(raw, object_pairs_hook=_pairs)
        except _Dup as e:
            err(n, str(e))
            obj = None
        except ValueError as e:
            err(n, f"malformed JSON: {e}")
            obj = None
        if not seen_header:
            seen_header = True
            if (not isinstance(obj, dict) or obj.get("log") != "office-events" or obj.get("v") != SCHEMA_VERSION
                    or isinstance(obj.get("v"), bool) or obj.get("clock") not in CLOCKS):
                err(n, "missing or invalid header (log=office-events, v=0, clock=synthetic|wall): file rejected")
                return None, [], problems
            hit = _data_hit(obj, forbidden)
            if hit:
                err(n, hit)
                return None, [], problems
            header = obj
            continue
        if obj is None:
            continue
        if not isinstance(obj, dict):
            err(n, "line is not a JSON object")
            continue
        typ = obj.get("type")
        t = obj.get("t")
        if not isinstance(typ, str) or not typ:
            err(n, "missing type")
            continue
        if isinstance(t, bool) or not isinstance(t, (int, float)) or t < 0:
            err(n, "t must be a number >= 0")
            continue
        if t < last_t:
            err(n, f"t decreases ({t} after {last_t})")
            continue
        if not isinstance(obj.get("src"), str) or not obj["src"].strip():
            err(n, "src is required")
            continue
        if "wall" in obj:
            w = _wall(obj["wall"])
            if w is None:
                err(n, "wall must be ISO 8601 with an offset")
                continue
            if last_wall is not None and w < last_wall:
                err(n, "wall decreases")
                continue
        else:
            w = None
        hit = _data_hit(obj, forbidden)
        if hit:
            err(n, hit)
            continue
        spec = EVENT_TYPES.get(typ)
        bad = None
        if spec is None:
            warn(n, f"unknown type {typ!r} (kept)")
        else:
            for f, kind in spec.items():
                opt = kind.endswith("?")
                kind = kind.rstrip("?")
                if f not in obj:
                    if not opt:
                        bad = f"missing field {f!r}"
                        break
                    continue
                if kind in ("AGENTS", "LINES"):
                    continue
                bad = _check_field(kind, obj[f], agents, stages)
                if bad:
                    bad = f"{f}: {bad}"
                    break
            if not bad and typ == "discussion":
                bad = _check_discussion(obj, agents)
            if bad:
                err(n, bad)
                continue
            for f in obj:
                if f not in spec and f not in COMMON:
                    warn(n, f"field {f!r} is not defined for {typ} (kept)")
        last_t = t
        if w is not None:
            last_wall = w
        ev = dict(obj)
        ev["_line"] = n
        kept.append(ev)

    # sequence rules: the next event for a task after a reject / BLOCK must be a handoff / needs_merwyn
    drop = set()
    for i, ev in enumerate(kept):
        need = None
        if ev["type"] == "review_reject":
            need = "handoff"
        elif ev["type"] == "compliance_result" and ev.get("verdict") == "BLOCK":
            need = "needs_merwyn"
        if not need:
            continue
        nxt = next((e for e in kept[i + 1:] if e.get("task") == ev.get("task")), None)
        if nxt is None or nxt["type"] != need:
            err(ev["_line"], f"{ev['type']} for {ev.get('task')} must be followed by {need} for that task")
            drop.add(i)
    kept = [e for i, e in enumerate(kept) if i not in drop]
    for e in kept:
        e.pop("_line", None)
    problems.sort(key=lambda p: p.line)
    return header, kept, problems
