"""Generate offices/<office>/board.md (kanban by status) from the backlog.

Usage: python scripts/board.py <office-id>
"""
import re, sys, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _fm import split, as_list

ROOT = pathlib.Path(__file__).resolve().parent.parent

def stages(office_dir):
    wf = (office_dir / "workflow.yaml").read_text()
    ids = re.findall(r"-\s*\{\s*id:\s*([\w-]+)", wf.split("terminal:")[0])
    term = re.search(r"terminal:\s*\[([^\]]*)\]", wf)
    return ids + (as_list(term.group(1)) if term else ["done", "parked"])

def main(office):
    d = ROOT / "offices" / office
    cols = stages(d)
    tasks, problems = [], []
    for f in sorted((d / "backlog").glob("T-*.md")):
        fm, _ = split(f.read_text())
        if fm.get("status") not in cols:
            problems.append(f"{f.name}: status '{fm.get('status')}' is not a workflow stage")
        fm["_file"] = f.name
        tasks.append(fm)
    done_ids = {t["id"] for t in tasks if t.get("status") == "done"}
    order = {"P0": 0, "P1": 1, "P2": 2}
    lines = [f"# Board — {office}", "",
             f"_Generated {datetime.date.today().isoformat()} by scripts/board.py. Do not edit._", ""]
    counts = " · ".join(f"{c}: {sum(t.get('status') == c for t in tasks)}" for c in cols)
    lines += [f"**{len(tasks)} tasks** — {counts}", ""]
    waiting = [t for t in tasks if t.get("owner") == "human" and t.get("status") not in ("done", "parked")]
    if waiting:
        lines += ["## Waiting on you", ""] + [f"- [{t['id']}](backlog/{t['_file']}) {t.get('title','')}" for t in waiting] + [""]
    for c in cols:
        col = sorted([t for t in tasks if t.get("status") == c], key=lambda t: (order.get(t.get("priority"), 9), t["id"]))
        lines += [f"## {c} ({len(col)})", ""]
        if not col:
            lines += ["_empty_", ""]
            continue
        lines += ["| ID | P | Task | Owner | Blocked by |", "|---|---|---|---|---|"]
        for t in col:
            blockers = [x for x in as_list(t.get("depends_on")) if x not in done_ids]
            lines.append(f"| [{t['id']}](backlog/{t['_file']}) | {t.get('priority','')} | {t.get('title','')} | {t.get('owner','')} | {', '.join(blockers) or '—'} |")
        lines.append("")
    if problems:
        lines += ["## Problems", ""] + [f"- {p}" for p in problems] + [""]
    (d / "board.md").write_text("\n".join(lines))
    print(f"{office}: {len(tasks)} tasks -> offices/{office}/board.md" + (f" ({len(problems)} problems)" if problems else ""))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
