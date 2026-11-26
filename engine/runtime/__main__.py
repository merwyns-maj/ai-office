"""CLI: python -m engine.runtime validate|dry-run <office>, or events <office> <log>, or ledger <office> <file>, or chat <action> <office> (stdin only), or usage plan <office> --ledger <file> (stdin only)"""
import argparse
import sys
from pathlib import Path

import json
from datetime import datetime, timezone

from . import budgets as budgets_mod, chat, dryrun, events, ledger, loader, providers as providers_mod, usage_sync


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
    catalogue, _ = providers_mod.load_providers(root)
    header, evs, probs = events.parse_log(text, agents=ids, stages=stages,
                                          forbidden=events.forbidden_terms(office.repo_root), providers=catalogue)
    for p in probs:
        print(p)
    errors = sum(1 for p in probs if p.level == "error")
    print(f"{args.log}: {len(evs)} events kept, {errors} error{'s' if errors != 1 else ''}, "
          f"{len(probs) - errors} warning{'s' if len(probs) - errors != 1 else ''}")
    return 1 if errors else 0


def _ledger(args):
    try:
        root = loader.resolve_office(args.office, Path.cwd())
        office, problems = loader.load_office(root)
        Path(args.file).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2
    if office is None:
        _report(root, problems)
        return 1
    ids = {a.get("id") for a in office.org.get("agents", []) if isinstance(a, dict)}
    catalogue, _ = providers_mod.load_providers(root)
    header, runs, probs = ledger.load_ledger(args.file, agents=ids, office=office.id,
                                             forbidden=events.forbidden_terms(office.repo_root), providers=set(catalogue))
    for p in probs:
        print(p)
    errors = sum(1 for p in probs if p.level == "error")
    unrep = sum(1 for r in runs if r["tokens"] is None)
    tok = sum(r["tokens"] or 0 for r in runs)
    print(f"{args.file}: {len(runs)} runs kept ({unrep} not reported), {tok:,} tokens, {errors} error{'s' if errors != 1 else ''}, "
          f"{len(probs) - errors} warning{'s' if len(probs) - errors != 1 else ''}")
    return 1 if errors else 0


def _chat(args):
    """Office chat helper (T-063). Chat text is company data: it arrives on stdin and leaves on stdout, never a file in the repo.
    Errors name a field or a kind of hit, never the text."""
    try:
        root = loader.resolve_office(args.office, Path.cwd())
        office, problems = loader.load_office(root)
    except (FileNotFoundError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2
    if office is None:
        _report(root, problems)
        return 1
    org = [a for a in office.org.get("agents", []) if isinstance(a, dict)]
    ids = [a["id"] for a in org]
    try:
        now = chat.parse_time(args.now) if args.now else datetime.now(timezone.utc)
        raw = sys.stdin.read()
        data = json.loads(raw) if args.action != "mentions" else raw
    except (ValueError, OSError):
        print("chat: stdin is not valid input for this action", file=sys.stderr)
        return 1
    forbidden = events.forbidden_terms(office.repo_root)
    out = sys.stdout
    if args.action == "mentions":
        m = chat.parse_mentions(data, chat.handles(org))
        print(json.dumps({"ids": m.ids, "all": m.all, "unknown": m.unknown, "route": chat.route(m)}))
        return 0
    if args.action == "rules":
        bad = chat.rules_problem(data)
        print(bad or "rules ok: chat is owner-only for read and write")
        return 1 if bad else 0
    if args.action == "plan":
        if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
            print('chat plan: stdin must be {"rules": [...], "docs": [...]}', file=sys.stderr)
            return 1
        bad = chat.rules_problem(data.get("rules"))
        if bad:
            print(f"chat plan: refusing to route: {bad}", file=sys.stderr)
            return 1
        actions, skipped = chat.plan(data["docs"], now, ids, lease_s=args.lease, forbidden=forbidden)
        for s in skipped:
            print(f"skipped {s}", file=sys.stderr)
        print(json.dumps(actions))
        return 0
    if args.action == "purge":
        if not isinstance(data, list):
            print("chat purge: stdin must be a list of docs", file=sys.stderr)
            return 1
        dels = chat.purge(data, now)
        print(json.dumps(dels))
        return 0
    if not isinstance(data, dict) or not isinstance(data.get("ask"), dict):
        print('chat %s: stdin must be {"ask": {...}, ...}' % args.action, file=sys.stderr)
        return 1
    ask = chat._norm([data["ask"]])[0][0]
    problems = chat.validate(ask, ids)
    if problems or ask.get("kind") != "ask" or not args.agent:
        print("chat %s: ask is not valid (%s)" % (args.action, problems[0] if problems else "need --agent"), file=sys.stderr)
        return 1
    try:
        if args.action == "status":
            path, patch = chat.set_status(ask, args.agent, args.to, now)
            print(json.dumps({"path": path, "patch": patch, "ifVersion": chat._norm([data["ask"]])[0][1]}))
            return 0
        text, question = data.get("text"), data.get("question")
        for field, v in (("text", text), ("question", question)):
            kind = chat.scan(v, forbidden) if isinstance(v, str) else None
            if kind:
                print(f"chat reply: not written, {field} looks like personal data ({kind})", file=sys.stderr)
                return 1
        path, doc, patch = chat.reply(ask, args.agent, text, args.needs_merwyn, question, args.task, now)
    except ValueError as e:
        print(f"chat {args.action}: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"path": path, "doc": doc, "patch": patch, "ifVersion": chat._norm([data["ask"]])[0][1]}))
    return 0


def _usage(args):
    """Usage sync plan (T-069). The db docs arrive on stdin and the plan leaves on stdout, never a file in the repo.
    Exit 1 with no actions when anything is refused; the reason names a doc, a field or a kind, never a value."""
    try:
        root = loader.resolve_office(args.office, Path.cwd())
        office, problems = loader.load_office(root)
        Path(args.ledger).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2
    if office is None:
        _report(root, problems)
        return 1
    try:
        now = args.now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        chat.parse_time(now)
        data = json.loads(sys.stdin.read())
    except (ValueError, OSError):
        print("usage plan: stdin is not valid input", file=sys.stderr)
        return 1
    if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
        print('usage plan: stdin must be {"rules": [...], "docs": [...], "other_docs": <int>}', file=sys.stderr)
        return 1

    def refuse(msg, report=None):
        print(msg, file=sys.stderr)
        print(json.dumps({"actions": [], "error": msg, "report": report or {}}))
        return 1
    ids = {a.get("id") for a in office.org.get("agents", []) if isinstance(a, dict)}
    catalogue, _ = providers_mod.load_providers(root)
    forbidden = events.forbidden_terms(office.repo_root)
    header, runs, main, probs = ledger.load_ledger_full(args.ledger, agents=ids, office=office.id, forbidden=forbidden, providers=set(catalogue))
    errs = [p for p in probs if p.level == "error"]
    if header is None or errs:
        return refuse("usage plan: the ledger has errors, fix them first: " + "; ".join(str(p) for p in errs[:3]))
    budgets, bprobs = budgets_mod.load_budgets(root, agents=ids, providers=set(catalogue))
    if bprobs:
        return refuse("usage plan: budgets.yaml has errors: " + "; ".join(bprobs[:3]))
    try:
        out = usage_sync.plan(header, runs, main, budgets, data["docs"], rules=data.get("rules"), other_docs=data.get("other_docs", 0),
                              forbidden=forbidden, now=now)
    except usage_sync.Refused as e:
        return refuse(f"usage plan: {e}", e.report)
    print(json.dumps(out))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m engine.runtime", description="Load, validate and dry-run an office folder.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, helptext in (("validate", "check an office against the schema"), ("dry-run", "show what the next run would do")):
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp = sub.add_parser("events", help="check an event log (v0 or v1) against an office")
    sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp.add_argument("log", help="path to a .jsonl event log")
    sp = sub.add_parser("ledger", help="check an agent-run ledger (usage/<session>.jsonl) against an office")
    sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp.add_argument("file", help="path to a ledger .jsonl file")
    sp = sub.add_parser("chat", help="office chat helper (T-063): JSON or text on stdin, JSON on stdout")
    sp.add_argument("action", choices=("plan", "reply", "status", "mentions", "purge", "rules"))
    sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp.add_argument("--ask", help="ask id (informational; the ask doc comes on stdin)")
    sp.add_argument("--agent", help="agent id (reply, status)")
    sp.add_argument("--to", choices=("replying",), default="replying", help="status step (status)")
    sp.add_argument("--needs-merwyn", action="store_true")
    sp.add_argument("--task", help="T-nnn the reply opened as a task")
    sp.add_argument("--now", help="ISO UTC time (tests)")
    sp.add_argument("--lease", type=int, default=chat.LEASE_S)
    sp = sub.add_parser("usage", help="sync the ledger and budgets to the artifact db (T-069): plan the db writes; stdin only")
    sp.add_argument("action", choices=("plan",))
    sp.add_argument("office", help="office id (offices/<id>) or path to an office folder")
    sp.add_argument("--ledger", required=True, help="path to the session ledger .jsonl")
    sp.add_argument("--now", help="ISO UTC time (tests)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if args.cmd == "usage":
        return _usage(args)
    if args.cmd == "events":
        return _events(args)
    if args.cmd == "ledger":
        return _ledger(args)
    if args.cmd == "chat":
        return _chat(args)
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
