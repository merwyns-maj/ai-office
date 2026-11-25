"""CLI: python -m engine.runtime validate|dry-run <office>, or events <office> <log>"""
import argparse
import sys
from pathlib import Path

from . import dryrun, events, loader


def _load_and_validate(arg):
    root = loader.resolve_office(arg, Path.cwd())
    office, problems = loader.load_office(root)
    if office is not None:
        problems = problems + loader.validate(office)
    return root, office, problems


def _report(root, problems):
    for p in problems:
        print(p)
    n = len(problems)
    print(f"{root.name}: {n} problem{'s' if n != 1 else ''}")


def _events(args):
    try:
        root = loader.resolve_office(args.office, Path.cwd())
        office, problems = loader.load_office(root)
        text = Path(args.log).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2
    if office is None:
        _report(root, problems)
        return 1
    ids = {a.get("id") for a in office.org.get("agents", []) if isinstance(a, dict)}
    stages = set(office.stage_ids) | set(office.terminal)
    header, evs, probs = events.parse_log(text, agents=ids, stages=stages,
                                          forbidden=events.forbidden_terms(office.repo_root))
    for p in probs:
        print(p)
    errors = sum(1 for p in probs if p.level == "error")
    print(f"{args.log}: {len(evs)} events kept, {errors} error{'s' if errors != 1 else ''}, "
          f"{len(probs) - errors} warning{'s' if len(probs) - errors != 1 else ''}")
    return 1 if errors else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m engine.runtime", description="Load, validate and dry-run an office folder.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, helptext in (("validate", "check an office against the schema"), ("dry-run", "show what the next run would do")):
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp = sub.add_parser("events", help="check an event log (v0) against an office")
    sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp.add_argument("log", help="path to a .jsonl event log")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if args.cmd == "events":
        return _events(args)
    try:
        root, office, problems = _load_and_validate(args.office)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    if office is not None:
        for w in office.warnings:
            print(f"warning: {w.file} {w.message}", file=sys.stderr)
    if problems:
        _report(root, problems)
        return 1
    if args.cmd == "validate":
        print(f"{office.id}: OK — {len(office.agents)} agents, {len(office.stage_ids)} stages, "
              f"{len(office.tasks)} tasks, {len(office.skills)} skills")
        return 0
    task = dryrun.pick_next(office)
    if task is None:
        print(f"{office.id}: nothing to run")
        return 0
    print(dryrun.format_plan(office, dryrun.plan(office, task)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
