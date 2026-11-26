import io
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from engine.runtime.__main__ import main

REPO = Path(__file__).resolve().parents[1]


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class OfficeCopy:
    """Temp copy of offices/ai-office plus base/ as <tmp>/offices/ai-office and <tmp>/base."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        shutil.copytree(REPO / "offices" / "ai-office", base / "offices" / "ai-office",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(REPO / "base", base / "base")
        self.root = base / "offices" / "ai-office"

    def cleanup(self):
        self.tmp.cleanup()

    def replace_backlog(self, tasks):
        """tasks: list of (id, status, priority, owner, depends_on list)."""
        for f in (self.root / "backlog").glob("*.md"):
            f.unlink()
        for tid, status, prio, owner, deps in tasks:
            (self.root / "backlog" / f"{tid}-x.md").write_text(
                f"---\nid: {tid}\ntitle: Task {tid}\nstatus: {status}\npriority: {prio}\n"
                f"owner: {owner}\ndepends_on: [{', '.join(deps)}]\n---\n## Done when\n", encoding="utf-8")


def appended_copy(src, tmp):
    """T-072: copy a live ledger into tmp (same file name) and append 3 valid lines: a not-reported run, a chat run and a
    main-session reading. Tests that read the live ledger must pass on the result, so an honest append never breaks the suite."""
    import json
    src = Path(src)
    lines = src.read_text(encoding="utf-8").rstrip("\n").splitlines()
    rows = [json.loads(l) for l in lines[1:] if l.strip()]
    last = max(r["n"] for r in rows if "n" in r)
    window = max([r["window"] for r in rows if r.get("kind") == "main_session"] or [0]) + 1
    lines += [
        json.dumps({"n": last + 1, "sprint": 99, "agent": "engineer", "tasks": ["T-901"], "step": "build", "tokens": None,
                    "tool_uses": None, "duration_ms": None, "note": "SYNTHETIC: harness report had no usage figures"}),
        json.dumps({"n": last + 2, "sprint": 99, "agent": "curator", "tasks": [], "step": "chat", "tokens": 1234, "tool_uses": 1,
                    "duration_ms": 5, "note": "chat message m-abcdef12-wxyz"}),
        json.dumps({"kind": "main_session", "window": window, "date": "2026-11-26", "source": "explain-usage skill",
                    "since": "SYNTHETIC test reading", "requests": 3, "input": 10, "cache_write": 20, "cache_read": 30, "output": 40}),
    ]
    out = Path(tmp) / src.name
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
