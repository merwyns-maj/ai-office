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
