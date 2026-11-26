#!/usr/bin/env python3
"""Generate the self-contained 3D office page: theme + org + workflow + event log -> engine/app/office.html.

Usage: python scripts/office_app.py <office> [--fixture PATH | --ledger PATH] [--out PATH] [--check] [--allow-errors]
--ledger replays a recorded agent-run ledger (offices/<office>/usage/<session>.jsonl, T-057); default out engine/app/usage-<session>.html (not committed).
Exit 0 written or up to date; 1 data-rule problems (always), other log errors (unless --allow-errors), missing theme layout or a stale file (--check); 2 usage.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from engine.runtime import events, ledger as ledger_mod, loader, miniyaml, providers  # noqa: E402
import build_agents  # noqa: E402

TEMPLATE = REPO / "engine" / "app" / "office.template.html"
DEFAULT_FIXTURE = REPO / "engine" / "app" / "fixtures" / "models-synthetic.jsonl"
DEFAULT_OUT = REPO / "engine" / "app" / "office.html"
PLACEHOLDER_LINE = '<script type="application/json" id="office-data">__OFFICE_DATA__</script>'


class BuildError(Exception):
    pass


def _planned_model(office, agent):
    """Profile model of an agent: its office file, else its base profile (build_agents.merged), else office default."""
    root = Path(office.repo_root)
    f = root / "offices" / office.id / "agents" / f"{agent['id']}.md"
    if f.exists():
        fm, _ = build_agents.merged(f, root)
        if fm.get("model"):
            return fm["model"]
    return (office.office.get("defaults") or {}).get("model")


def build_data(office_root, fixture, ledger=None):
    """Return (data dict for the page, list of LogProblem). With ledger: the page replays that agent-run ledger instead of fixture."""
    office_root = Path(office_root)
    office, problems = loader.load_office(office_root)
    if office is None:
        raise BuildError("; ".join(str(p) for p in problems) or "office failed to load")
    theme_path = office_root / "theme" / "theme.yaml"
    if not theme_path.exists():
        raise BuildError(f"{theme_path}: theme.yaml is missing")
    theme = miniyaml.loads(theme_path.read_text(encoding="utf-8"), str(theme_path))
    rooms, desks = theme.get("rooms") or [], theme.get("desks") or []
    missing = [f"room {r.get('id')} has no rect" for r in rooms if not isinstance(r.get("rect"), list) or len(r["rect"]) != 4]
    missing += [f"desk {d.get('agent')} has no at" for d in desks if not isinstance(d.get("at"), list) or len(d["at"]) != 2]
    if not isinstance(theme.get("door"), list) or len(theme["door"]) != 2:
        missing.append("theme has no door [x, z]")
    if missing:
        raise BuildError("theme layout incomplete: " + "; ".join(missing))
    org_agents = [a for a in office.org.get("agents", []) if isinstance(a, dict)]
    ids = {a["id"] for a in org_agents}
    stages = list(office.stage_ids) + list(office.terminal)
    catalogue, cat_problems = providers.load_providers(office_root)
    if cat_problems:
        raise BuildError("; ".join(cat_problems))
    forbidden = events.forbidden_terms(office.repo_root)
    lprobs, totals = [], None
    if ledger is not None:
        lh, runs, lprobs = ledger_mod.load_ledger(ledger, agents=ids, office=office.id, forbidden=forbidden, providers=set(catalogue))
        if lh is None:
            return {"log": None, "skipped": [{"line": p.line, "message": p.message} for p in lprobs]}, lprobs
        log_text = ledger_mod.to_event_log(lh, runs)
        totals = ledger_mod.totals(runs)
    else:
        log_text = Path(fixture).read_text(encoding="utf-8")
    header, evs, probs = events.parse_log(log_text, agents=ids, stages=set(stages), forbidden=forbidden, providers=catalogue)
    probs = lprobs + probs
    if totals is not None:
        header = dict(header, not_reported=lh["not_reported"])
    skipped = [{"line": p.line, "message": p.message} for p in probs if p.level == "error"]
    warnings = [{"line": p.line, "message": p.message} for p in probs if p.level == "warning"]
    data = {
        "v": 1,
        "office": {"id": office.id, "name": office.office.get("name", office.id)},
        "theme": {k: theme.get(k) for k in ("style", "palette", "rooms", "desks", "hub", "door")},
        "agents": [dict({k: a.get(k) for k in ("id", "name", "role", "personality")},
                        planned_model=_planned_model(office, a)) for a in org_agents],
        "providers": catalogue,
        "warnings": warnings,
        "stages": stages,
        "log": header,
        "events": evs,
        "skipped": skipped,
    }
    if totals is not None:
        data["ledger"] = totals
    return data, probs


def render(template_text, data):
    if template_text.count(PLACEHOLDER_LINE) != 1:
        raise BuildError(f"template must contain exactly one line: {PLACEHOLDER_LINE}")
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return template_text.replace(PLACEHOLDER_LINE, PLACEHOLDER_LINE.replace("__OFFICE_DATA__", blob), 1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_app.py", description=__doc__.split("\n")[0])
    ap.add_argument("office", help="office id (offices/<id>) or a path to an office folder")
    ap.add_argument("--fixture")
    ap.add_argument("--ledger", help="replay an agent-run ledger instead of an event log")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true", help="fail if --out is not what would be generated")
    ap.add_argument("--allow-errors", action="store_true", help="drop bad log lines instead of failing")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if args.fixture and args.ledger:
        print("office_app: --fixture and --ledger cannot be used together", file=sys.stderr)
        return 2
    try:
        root = loader.resolve_office(args.office, Path.cwd())
        template = TEMPLATE.read_text(encoding="utf-8")
        if args.ledger:
            if not Path(args.ledger).is_file():
                raise FileNotFoundError(f"{args.ledger}: no such ledger file")
            out_default = REPO / "engine" / "app" / f"usage-{Path(args.ledger).stem}.html"
        else:
            out_default = DEFAULT_OUT
        data, probs = build_data(root, Path(args.fixture or DEFAULT_FIXTURE), Path(args.ledger) if args.ledger else None)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except BuildError as e:
        print(f"office_app: {e}", file=sys.stderr)
        return 1
    for p in probs:
        print(p, file=sys.stderr)
    leaks = [p for p in probs if p.level == "error" and events.is_data_problem(p.message)]
    if leaks:
        print(f"office_app: {len(leaks)} data-rule problem(s); nothing written. --allow-errors does not skip these", file=sys.stderr)
        return 1
    if data["log"] is None or (data["skipped"] and not args.allow_errors):
        print(f"office_app: log has {len(data['skipped'])} error(s); fix them or pass --allow-errors", file=sys.stderr)
        return 1
    try:
        html = render(template, data)
    except BuildError as e:
        print(f"office_app: {e}", file=sys.stderr)
        return 1
    out = Path(args.out or out_default)
    if args.check:
        if not out.exists() or out.read_text(encoding="utf-8") != html:
            print(f"office_app: {out} is stale; run: python scripts/office_app.py {args.office}" + (f" --ledger {args.ledger}" if args.ledger else ""), file=sys.stderr)
            return 1
        print(f"{out}: up to date ({len(html.encode('utf-8')) // 1024} KB, {len(data['events'])} events)")
        return 0
    out.write_text(html, encoding="utf-8")
    print(f"{out}: written, {len(html.encode('utf-8')) // 1024} KB, {len(data['agents'])} agents, {len(data['events'])} events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
