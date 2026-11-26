"""Adoption metrics for an office, read from this repo's own history (T-032).

Usage: python scripts/metrics.py <office> [--out PATH] [--repo PATH]

How to run monthly (the whole step, no other instructions needed):
  1. git fetch --unshallow origin            # only if `git rev-parse --is-shallow-repository` prints true
  2. git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'
  3. python scripts/metrics.py ai-office     # writes offices/ai-office/metrics/<YYYY-MM>.md
  4. commit the report on a t-xxx branch and open a PR (never commit board.md).
Skip the fetches and the script still exits 0; the report then says which numbers are missing.

The script only reads git (HEAD and refs/remotes/origin/pr/*), never fetches, never writes to git.
Stage times are commit (author) times, not work time. Values that cannot be derived print "not recorded".
"""
import argparse
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from _fm import split  # noqa: E402
from board import stages as board_stages  # noqa: E402
from engine.runtime import events as ev_mod, ledger as ledger_mod, loader, providers as prov_mod  # noqa: E402

NR = "not recorded"
STAGE_COLS = ("spec", "design", "build", "review")


def git(repo, *args):
    """Run git in repo; return stdout, or None on any failure. Never raises."""
    try:
        p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None
    return p.stdout if p.returncode == 0 else None


def history_state(repo):
    shallow = git(repo, "rev-parse", "--is-shallow-repository")
    head = git(repo, "rev-parse", "--short=7", "HEAD")
    refs = git(repo, "for-each-ref", "--format=%(refname)", "refs/remotes/origin/pr/")
    return {
        "shallow": None if shallow is None else shallow.strip() == "true",
        "pr_refs": len(refs.split()) if refs else 0,
        "head": head.strip() if head else None,
    }


def status_events(repo, office):
    """{task_id: [(datetime, status)]} from frontmatter status changes on HEAD and PR head refs."""
    out = git(repo, "log", "--format=%x00%H%x09%aI", "-p", "--unified=0", "--no-renames",
              "HEAD", "--glob=refs/remotes/origin/pr/*", "--", f"offices/{office}/backlog/")
    if out is None:
        out = git(repo, "log", "--format=%x00%H%x09%aI", "-p", "--unified=0", "--no-renames",
                  "HEAD", "--", f"offices/{office}/backlog/") or ""
    events = {}
    for chunk in out.split("\x00")[1:]:
        head, _, diff = chunk.partition("\n")
        try:
            when = datetime.fromisoformat(head.split("\t")[1].strip())
        except (IndexError, ValueError):
            continue
        task, in_front = None, False
        for line in diff.splitlines():
            if line.startswith("+++ "):
                m = re.search(r"/(T-\d{3})-[^/]*\.md$", line)
                task = m.group(1) if m else None
            elif line.startswith("@@"):
                m = re.match(r"@@ -\S+ \+(\d+)", line)
                in_front = bool(m) and int(m.group(1)) <= 12   # frontmatter sits at the top
            elif task and in_front:
                m = re.match(r"\+status:\s*([\w-]+)\s*$", line)
                if m:
                    events.setdefault(task, []).append((when, m.group(1)))
    for t, evs in events.items():
        evs.sort(key=lambda e: e[0])
        dedup = []
        for e in evs:
            if not dedup or dedup[-1][1] != e[1]:
                dedup.append(e)
        events[t] = dedup
    return events


def stage_hours(events, stage_ids):
    """Per stage, total hours over every visit (rework included); None if never left/entered."""
    res = {s: None for s in stage_ids}
    for i, (when, st) in enumerate(events[:-1]):
        if st in res:
            h = (events[i + 1][0] - when).total_seconds() / 3600
            res[st] = (res[st] or 0.0) + h
    return res


def turnaround_hours(events):
    """First non-todo event to first done. Needs a real stage before done, else None."""
    first = next((e for e in events if e[1] != "todo"), None)
    done = next((e for e in events if e[1] == "done"), None)
    if not first or not done or first[1] == "done" or done[0] < first[0]:
        return None
    return (done[0] - first[0]).total_seconds() / 3600


def merges(repo):
    """[(datetime, pr_no, subject)] for main squash commits whose subject ends (#N), oldest first."""
    out = git(repo, "log", "--format=%aI%x09%s", "HEAD")
    res = []
    for line in (out or "").splitlines():
        when, _, subj = line.partition("\t")
        m = re.search(r"\(#(\d+)\)$", subj)
        if m:
            try:
                res.append((datetime.fromisoformat(when), int(m.group(1)), subj))
            except ValueError:
                pass
    return sorted(res, key=lambda m: m[0])


def section(text, heading):
    """Text under '## heading...' up to the next '## ' heading, or None if absent."""
    m = re.search(rf"(?im)^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else None


_REVIEW_PREFIX = r"^(?:- )?(?:(?:Review(?: \d+)?\b[^:\n]*|Verdict): )?"
_REJECT = re.compile(_REVIEW_PREFIX + r"REJECT\b")
_PASS = re.compile(_REVIEW_PREFIX + r"PASS\b")
_COMPLIANCE = re.compile(r"(?i)^-?\s*Compliance:\s*(PASS with conditions|PASS|BLOCK)\b")
_ESCALATED = re.compile(r"(?i)\bescalated to Merwyn\b")


def verdicts(task_text, task_id=None):
    """Counts from the Review log and Compliance sections; each key is None if no source section."""
    review = section(task_text, "Review log")
    compliance = section(task_text, "Compliance")
    res = {"reject": None, "block": None, "escalations": None}
    if review is None and compliance is None:
        return res
    reject = block = esc = 0
    matched_review = False
    for src in (review, compliance):
        for line in (src or "").splitlines():
            s = line.strip()
            if _COMPLIANCE.match(s):
                if _COMPLIANCE.match(s).group(1).upper() == "BLOCK":
                    block += 1
            elif _REJECT.match(s):
                reject += 1
                matched_review = True
            elif _PASS.match(s):
                matched_review = True
            if _ESCALATED.search(s):
                esc += 1
    if review and not matched_review and re.search(r"\b(PASS|REJECT)\b", review) \
            and not _COMPLIANCE.search(review):
        print(f"warning: {task_id or 'task'}: Review log mentions PASS/REJECT but no verdict "
              f"line matched; counts may be low", file=sys.stderr)
    return {"reject": reject, "block": block, "escalations": esc}


def derive_without_review(task_text, tid, evs, close_text):
    """Fallback for a task with no Review log or Compliance section (T-042, T-014, T-015).

    reject: count of review -> build transitions in the status history; if no history is available,
    0 only when the sprint Close says the task finished with Reviewer PASS and it is listed there.
    block: 0 when the Design says 'Compliance: not flagged'.
    escalations: 'escalated to Merwyn' lines in the task, else 0 when the sprint Close says
    'without escalating', else not recorded.
    """
    seq = [st for _, st in evs]
    close = close_text or ""
    if "review" in seq:
        reject = sum(1 for a, b in zip(seq, seq[1:]) if a == "review" and b == "build")
    elif tid in close and re.search(r"(?i)all with Reviewer PASS", close):
        reject = 0
    else:
        reject = None
    block = 0 if re.search(r"(?i)\bCompliance:?\*{0,2}:?\s*not flagged", task_text) else None
    esc = sum(1 for ln in task_text.splitlines() if _ESCALATED.search(ln))
    if not esc:
        esc = 0 if re.search(r"(?i)without escalating", close) else None
    return {"reject": reject, "block": block, "escalations": esc}


def sprint_close_text(office_dir, n):
    f = office_dir / "sprints" / f"sprint-{n:02d}.md"
    if not f.is_file():
        return ""
    text = f.read_text(encoding="utf-8")
    m = re.search(r"(?ms)^## (?:Retro|Close)\b.*", text)
    return m.group(0) if m else ""


def spec_first_time(task_text, evs):
    sec = section(task_text, "Approvals (PMO)")
    if sec is None:
        sec = section(task_text, "Spec approval")
    if sec is None:
        return NR
    if re.search(r"(?i)spec (not approved|sent back|returned)", sec):
        return "no"
    seq = [s for _, s in evs]
    if "spec" in seq:
        i = seq.index("spec")
        if "spec" in seq[i + 1:]:
            return "no"   # re-entered spec after leaving it
    return "yes"


def sprints(office_dir):
    res = []
    for f in sorted((office_dir / "sprints").glob("sprint-*.md")):
        m = re.match(r"sprint-(\d+)\.md$", f.name)
        if not m:
            continue
        text = f.read_text(encoding="utf-8")
        tasks = re.findall(r"^\s*\d+\.\s*\[(T-\d{3})\]", section(text, "Tasks") or "", re.M)
        res.append({"n": int(m.group(1)), "tasks": tasks,
                    "closed": bool(re.search(r"(?m)^## (Retro|Close)\b", text))})
    return res


def sprint_window(mlist, n):
    """(start, end) merge datetimes for sprint n, or None if its plan commit is not in history."""
    plan = re.compile(rf"^Sprint 0?{n} plan")
    close = re.compile(rf"(?i)^Sprint 0?{n} close|close Sprint 0?{n}\b")
    nxt = re.compile(rf"^Sprint 0?{n + 1} plan")
    start = next((m for m in mlist if plan.search(m[2])), None)
    if not start:
        return None
    later = [m for m in mlist if m[0] > start[0]]
    end = next((m for m in later if close.search(m[2])), None) or next((m for m in later if nxt.search(m[2])), None)
    return (start[0], end[0]) if end else None


def window_extras(mlist, window, listed):
    """Merged task PRs (subject T-nnn) inside the window that are not in the sprint list: [(task, pr)]."""
    res = []
    if not window:
        return res
    for when, pr, subj in mlist:
        m = re.match(r"(T-\d{3})\b", subj)
        if m and window[0] < when < window[1] and m.group(1) not in listed:
            res.append((m.group(1), pr))
    return res


def fmt_h(v):
    return NR if v is None else f"{v:.1f}"


def fmt_n(v):
    return NR if v is None else str(v)


def fmt_partial(value, missing):
    """Sprint cell: plain value when all tasks are recorded, NR when none, else marked partial."""
    if value is None:
        return NR
    if missing == 0:
        return str(value)
    return f"{value} (partial, {missing} {NR})"


def _n(v):
    return f"{v:,}"


def _pct(part, whole):
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def _hours(ms):
    return f"{ms / 3_600_000:.2f}"


def usage_section(office_dir, repo):
    """Lines of the '## Token usage' section from every offices/<office>/usage/*.jsonl (T-057). Problems go to stderr."""
    office_dir, repo = Path(office_dir), Path(repo)
    files = sorted((office_dir / "usage").glob("*.jsonl"))
    out = ["## Token usage", ""]
    if not files:
        return out + ["No ledger files under `usage/`: not recorded.", ""]
    office, _ = loader.load_office(office_dir)
    ids = {a.get("id") for a in office.org.get("agents", []) if isinstance(a, dict)} if office else set()
    forbidden = ev_mod.forbidden_terms(repo)
    catalogue = set(prov_mod.load_providers(office_dir)[0])
    for f in files:
        header, runs, probs = ledger_mod.load_ledger(f, agents=ids, office=office_dir.name, forbidden=forbidden, providers=catalogue)
        for p in probs:
            print(f"{f.name}: {p}", file=sys.stderr)
        errors = [p for p in probs if p.level == "error"]
        out += [f"### {f.stem}", ""]
        if header is None:
            out += [f"Ledger rejected ({len(errors)} error{'s' if len(errors) != 1 else ''}); no numbers shown.", ""]
            continue
        if any(ev_mod.is_data_problem(p.message) for p in errors):
            out += ["Tables omitted: a line matched the data rule (details on stderr).", ""]
            continue
        t = ledger_mod.totals(runs)
        S = t["session"]
        out += [f"Covers: {header['covers']}.", "",
                f"Source: {header['source']}. Recorded by {header['recorded_by']}, {header['date']}.", "",
                "Main session's own tokens: not reported here (the harness reports agent runs only; metered readings are in the ledger, T-070).", "",
                "Model used: not reported (profile models are planned, not measured).", "",
                "Share of the Max plan: not shown. The plan has no published fixed token limit, so any percentage of it "
                "would be a guess.", ""]
        if errors:
            out += [f"{len(errors)} lines skipped (errors)", ""]
        out += ["| Runs | Not reported | Tokens | Tool uses | Hours (agent run time) |", "|---|---|---|---|---|",
                f"| {S['runs']} | {S['not_reported']} | {_n(S['tokens'])} | {_n(S['tool_uses'])} | {_hours(S['duration_ms'])} |", ""]

        def table(title, label, rows, keyed):
            lines = [f"**{title}**", "",
                     f"| {label} | Runs | Not reported | Tokens | Share of session | Tasks | Tokens per task |",
                     "|---|---|---|---|---|---|---|"]
            for k, r in rows:
                per = _n(round(r["tokens"] / len(r["tasks"]))) if r["tasks"] else "n/a"
                lines.append(f"| {keyed(k)} | {r['runs']} | {r['not_reported']} | {_n(r['tokens'])} | "
                             f"{_pct(r['tokens'], S['tokens'])} | {len(r['tasks'])} | {per} |")
            return lines + [""]
        out += table("By agent", "Agent", sorted(t["agents"].items(), key=lambda kv: (-kv[1]["tokens"], kv[0])), str)
        out += table("By sprint", "Sprint", sorted(t["sprints"].items()), str)
        sh = t["shared"]
        out += ["**By task**", "", "| Task | Runs | Tokens counted once | Shared runs | Tokens incl. shared runs |", "|---|---|---|---|---|"]
        for tid, r in sorted(t["tasks"].items()):
            out.append(f"| {tid} | {r['runs']} | {_n(r['solo_tokens'])} | {r['shared_runs']} | {_n(r['tokens_with_shared'])} |")
        out += [f"| Shared runs (counted once) | {sh['runs']} | {_n(sh['tokens'])} | {sh['runs']} | - |", "",
                "A run that covered several tasks is never split between them. Task rows show the tokens of runs that "
                "touched only that task; the last row holds the shared runs once. Solo tokens plus the shared row equal "
                "the session total; the 'incl. shared' column adds up to more by design.", ""]
    return out


def build_report(repo, office, run_date):
    repo = Path(repo)
    office_dir = repo / "offices" / office
    state = history_state(repo)
    stage_ids = board_stages(office_dir)
    events = status_events(repo, office) if state["head"] else {}
    mlist = merges(repo) if state["head"] else []
    sprint_list = [s for s in sprints(office_dir) if s["closed"]]

    if not state["head"]:
        notice = ("NO GIT HISTORY. Stage times, windows and turnaround are not recorded; "
                  "counts come from the files only.")
    elif state["shallow"] or state["pr_refs"] == 0:
        why = []
        if state["shallow"]:
            why.append("shallow clone")
        why.append(f"{state['pr_refs']} PR refs")
        notice = (f"PARTIAL HISTORY ({'; '.join(why)}). Stage times need the PR branch commits and "
                  f"sprint windows need the full main history; numbers that depend on them read "
                  f"'{NR}'.")
    else:
        notice = f"full ({state['pr_refs']} PR refs). Stage times are commit times, not work time."

    rows, foot = {}, []
    for sp in sprint_list:
        for t in sp["tasks"]:
            files = list((office_dir / "backlog").glob(f"{t}-*.md"))
            text = files[0].read_text(encoding="utf-8") if files else ""
            evs = events.get(t, [])
            v = verdicts(text, t)
            if text and section(text, "Review log") is None and section(text, "Compliance") is None:
                v = derive_without_review(text, t, evs, sprint_close_text(office_dir, sp["n"]))
            sh = stage_hours(evs, STAGE_COLS)
            rows[t] = {"sprint": sp["n"], "stages": sh, "turn": turnaround_hours(evs), **v,
                       "first": spec_first_time(text, evs) if text else NR}

    def agg(ts, key):
        vals = [rows[t][key] for t in ts if rows[t][key] is not None]
        return (sum(vals) if vals else None), len(ts) - len(vals)

    out = [f"# Office metrics: {office}, run {run_date} at {state['head'] or 'no git'}", "",
           f"> History: {notice}", "", "## Sprints", "",
           "| Sprint | Tasks | Window (UTC) | Reviewer REJECTs | Compliance BLOCKs | Escalations to Merwyn "
           "| Specs approved first time | Median turnaround (h) |",
           "|---|---|---|---|---|---|---|---|"]
    for sp in sprint_list:
        ts = sp["tasks"]
        win = sprint_window(mlist, sp["n"])
        extras = window_extras(mlist, win, set(ts))
        mark = ""
        if extras:
            foot.append(f"[{len(foot) + 1}] Also merged in the Sprint {sp['n']} window, not a sprint task: "
                        + ", ".join(f"{t} (#{p})" for t, p in extras) + ".")
            mark = f" [{len(foot)}]"
        wtxt = (f"{win[0].astimezone(timezone.utc):%Y-%m-%d %H:%M} to "
                f"{win[1].astimezone(timezone.utc):%Y-%m-%d %H:%M}") if win else NR
        firsts = [rows[t]["first"] for t in ts]
        known = [f for f in firsts if f != NR]
        ftxt = f"{known.count('yes')} of {len(ts)}" if known else NR
        if known and len(known) < len(ts):
            ftxt += f" ({len(ts) - len(known)} {NR})"
        turns = [rows[t]["turn"] for t in ts if rows[t]["turn"] is not None]
        med = fmt_partial(fmt_h(statistics.median(turns)) if turns else None, len(ts) - len(turns))
        out.append(f"| {sp['n']} | {len(ts)}{mark} | {wtxt} | {fmt_partial(*agg(ts, 'reject'))} | "
                   f"{fmt_partial(*agg(ts, 'block'))} | {fmt_partial(*agg(ts, 'escalations'))} | {ftxt} | {med} |")

    out += ["", "## Tasks", "",
            "| Task | Sprint | spec h | design h | build h | review h | Turnaround h | Reviewer REJECTs "
            "| Compliance BLOCKs | Escalations | Spec first time |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t, r in rows.items():
        out.append(f"| {t} | {r['sprint']} | " + " | ".join(fmt_h(r["stages"][s]) for s in STAGE_COLS)
                   + f" | {fmt_h(r['turn'])} | {fmt_n(r['reject'])} | {fmt_n(r['block'])} | "
                   f"{fmt_n(r['escalations'])} | {r['first']} |")

    out += ["", "## Hours saved", "",
            "| Hours saved | not set: Merwyn supplies a per-task-type estimate |", "|---|---|", ""]
    out += foot + [""] if foot else []
    out += usage_section(office_dir, repo)
    out += ["## How these are measured", "",
            "- Stage hours: sum over every visit to the stage (rework included), from `status:` changes in task "
            "files on main and on PR head refs; commit author times, not work time.",
            "- Turnaround: first non-todo status to first done; not recorded when no stage before done was seen.",
            f"- A sprint cell 'N (partial, k {NR})' sums, or takes the median of, only the tasks with a "
            "recorded value; k tasks are missing.",
            "- Reviewer REJECTs and Compliance BLOCKs: verdict lines in each task's Review log and Compliance "
            "sections, counted separately.",
            "- Tasks with no Review log: REJECTs are review-to-build transitions in the status history (else "
            "from the sprint Close 'all with Reviewer PASS'); BLOCKs are 0 when the Design says 'Compliance: "
            "not flagged'; escalations come from the sprint Close ('without escalating').",
            "- Escalations to Merwyn: lines saying 'escalated to Merwyn' in those sections.",
            "- Specs approved first time: from the PMO approval heading (from Sprint 2 on); earlier tasks are "
            f"{NR}.",
            "- Sprint window: main squash-commit times from the sprint plan to the sprint close (or the next plan).",
            "- Tasks per sprint: numbered task links in each closed sprint file. Open sprints are left out.",
            "- Token usage: one line per agent run from the harness report, kept in `usage/<session>.jsonl` "
            "(`engine/schema/usage.md`). Only the total per run is reported; the input/output/cache split, the model used "
            "and the main session's own tokens are not. A run with no usage counts as a run and adds 0 tokens, never shown as 0.",
            "- Token shares are of the session's recorded agent tokens. Runs that covered several tasks are counted once "
            "under 'Shared runs', never apportioned.",
            f"- '{NR}' means the source is absent from the history available; it is never blank or 0.", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="metrics.py", description="Write the office adoption-metrics report.")
    ap.add_argument("office")
    ap.add_argument("--out")
    ap.add_argument("--repo")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 2
    repo = Path(a.repo) if a.repo else HERE.parent
    if not (repo / "offices" / a.office / "workflow.yaml").is_file():
        print(f"error: office '{a.office}' not found under {repo}/offices", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    report = build_report(repo, a.office, f"{now:%Y-%m-%d}")
    out = Path(a.out) if a.out else repo / "offices" / a.office / "metrics" / f"{now:%Y-%m}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"metrics: wrote {out} ({report.count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
