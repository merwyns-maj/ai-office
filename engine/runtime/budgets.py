"""Token budgets for the usage panel (T-060): offices/<office>/budgets.yaml. Stdlib only.

A budget is a number Merwyn (or someone he names) sets; Anthropic publishes no token limit for the Max plan, so the
page never invents one. Every value carries set_by and set_on. Agents inside a provider either all hold a `share`
(whole or fractional percent, adding to 100) of that provider's budget or all hold a `tokens` amount.
The loader returns resolved amounts only (shares become tokens, largest remainder, so they add to the provider total).
"""
import re
from datetime import date
from pathlib import Path

from .miniyaml import loads

FILE = "budgets.yaml"
PERIODS = ("session",)   # day/week/month need a `date` on run lines (ledger.py accepts it since T-060) and a filter: not built yet
MAX_TOKENS = 999_999_999_999
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
TOP_KEYS = ("period", "main_session", "thresholds", "providers")
THRESH_KEYS = ("warn_at", "alert_at", "set_by", "set_on")
DEFAULT_WARN, DEFAULT_ALERT = 70, 90   # T-062: yellow from 70% of a budget, red from 90% (and over)
PROV_KEYS = ("tokens", "set_by", "set_on", "note", "agents")
AGENT_KEYS = ("share", "tokens", "set_by", "set_on")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _iso(v):
    try:
        return isinstance(v, str) and date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def _text(v, hi=120):
    return isinstance(v, str) and 1 <= len(v.strip()) <= hi and "\n" not in v


def _stamp(w, d, out):
    if not _text(d.get("set_by")):
        out.append(f"{w}: set_by is required (who set this value, 1 to 120 characters)")
    if not _iso(d.get("set_on")):
        out.append(f"{w}: set_on is required (YYYY-MM-DD)")


def _split(total, shares):
    """Largest remainder: whole tokens that add up to exactly `total` for the given percentages."""
    raw = [total * s / 100 for s in shares]
    fl = [int(x) for x in raw]
    left = total - sum(fl)
    order = sorted(range(len(shares)), key=lambda i: (-(raw[i] - fl[i]), i))
    for i in order[:left]:
        fl[i] += 1
    return fl


def _thresholds(t, out):
    """T-062: warn_at / alert_at as percent of a budget, 0 < warn_at < alert_at <= 100, with who set them and when.
    Absent gives the defaults (70, 90) marked set_by "default"."""
    if t is None:
        return {"warn_at": DEFAULT_WARN, "alert_at": DEFAULT_ALERT, "set_by": "default", "set_on": None}
    w = "budgets: thresholds"
    if not isinstance(t, dict):
        out.append(f"{w}: must be a map with warn_at, alert_at, set_by and set_on")
        return None
    for k in t:
        if k not in THRESH_KEYS:
            out.append(f"{w}: unknown key {k!r}")
    warn, alert = t.get("warn_at", DEFAULT_WARN), t.get("alert_at", DEFAULT_ALERT)
    if not _num(warn) or not _num(alert) or not 0 < warn < alert <= 100:
        out.append(f"{w}: need 0 < warn_at < alert_at <= 100 (numbers, percent of a budget)")
    _stamp(w, t, out)
    return {"warn_at": warn, "alert_at": alert, "set_by": t.get("set_by"), "set_on": t.get("set_on")}


def resolve(data, *, agents, providers, synthetic=False):
    """Return (resolved dict or None, list of problem strings) for a loaded budgets map.

    agents: org agent ids; providers: ids from providers.yaml (both are checked)."""
    out = []
    if not isinstance(data, dict):
        return None, ["budgets: must be a map with period and providers"]
    for k in data:
        if k not in TOP_KEYS:
            out.append(f"budgets: unknown key {k!r}")
    if data.get("period") not in PERIODS:
        out.append("budgets: period must be one of " + ", ".join(PERIODS) + " (the ledger has no run dates yet)")
    ms = data.get("main_session")
    if ms is not None and (not isinstance(ms, str) or ms not in agents):
        out.append("budgets: main_session must be an agent id from org.yaml")
    th = _thresholds(data.get("thresholds"), out)
    provs = data.get("providers")
    if not isinstance(provs, dict) or not provs:
        out.append("budgets: providers must be a map with at least one provider")
        return None, out
    res = {}
    for pid, p in provs.items():
        w = f"budgets: provider {pid}"
        if not isinstance(pid, str) or not ID_RE.match(pid) or pid not in providers:
            out.append(f"{w}: not an id in providers.yaml")
        if not isinstance(p, dict):
            out.append(f"{w}: must be a map")
            continue
        for k in p:
            if k not in PROV_KEYS:
                out.append(f"{w}: unknown key {k!r}")
        tok = p.get("tokens")
        if "tokens" in p:
            if not _int(tok) or not 1 <= tok <= MAX_TOKENS:
                out.append(f"{w}: tokens must be a whole number from 1 to {MAX_TOKENS} (no negatives)")
                tok = None
            else:
                _stamp(w, p, out)
        if "note" in p and not _text(p["note"], 200):
            out.append(f"{w}: note must be 1 to 200 characters")
        row = {"set_by": p.get("set_by"), "set_on": p.get("set_on")}
        if tok is not None:
            row["tokens"] = tok
        if p.get("note") is not None and _text(p.get("note"), 200):
            row["note"] = p["note"]
        ag = p.get("agents")
        if ag is not None:
            row["agents"] = _agents(w, ag, tok, agents, out)
        res[pid] = row
    if out:
        return None, out
    return {"period": data["period"], "main_session": ms, "synthetic": bool(synthetic), "thresholds": th, "providers": res}, []


def _agents(w, ag, total, agent_ids, out):
    if not isinstance(ag, dict) or not ag:
        out.append(f"{w}: agents must be a map with at least one agent")
        return {}
    shares, amounts, stamps = {}, {}, {}
    for aid, a in ag.items():
        x = f"{w} agent {aid}"
        if aid not in agent_ids:
            out.append(f"{x}: not an agent id in org.yaml")
        if not isinstance(a, dict):
            out.append(f"{x}: must be a map with share or tokens, set_by and set_on")
            continue
        for k in a:
            if k not in AGENT_KEYS:
                out.append(f"{x}: unknown key {k!r}")
        _stamp(x, a, out)
        stamps[aid] = (a.get("set_by"), a.get("set_on"))
        if ("share" in a) == ("tokens" in a):
            out.append(f"{x}: give exactly one of share or tokens")
        elif "share" in a:
            if not _num(a["share"]) or not 0 <= a["share"] <= 100:
                out.append(f"{x}: share must be a number from 0 to 100 (no negatives)")
            else:
                shares[aid] = a["share"]
        elif not _int(a["tokens"]) or not 0 <= a["tokens"] <= MAX_TOKENS:
            out.append(f"{x}: tokens must be a whole number from 0 to {MAX_TOKENS} (no negatives)")
        else:
            amounts[aid] = a["tokens"]
    if shares and amounts:
        out.append(f"{w}: agents are all shares or all amounts, not a mix")
    if shares:
        if total is None:
            out.append(f"{w}: agent shares need the provider tokens budget")
        elif abs(sum(shares.values()) - 100) > 1e-9:
            out.append(f"{w}: agent shares add to {sum(shares.values()):g}, must be 100")
        else:
            amounts = dict(zip(shares, _split(total, list(shares.values()))))
    return {aid: {"tokens": t, "set_by": stamps[aid][0], "set_on": stamps[aid][1]} for aid, t in amounts.items()}


def load_budgets(office_root, *, agents, providers):
    """Return (resolved dict or None, problem strings). No budgets.yaml gives (None, [])."""
    path = Path(office_root) / FILE
    if not path.exists():
        return None, []
    try:
        data = loads(path.read_text(encoding="utf-8"), str(path))
    except (OSError, ValueError) as e:
        return None, [f"{path}: {e}"]
    res, probs = resolve(data, agents=agents, providers=providers)
    return res, [f"{FILE}: {m}" for m in probs]
