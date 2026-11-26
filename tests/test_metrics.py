import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
import metrics  # noqa: E402
from engine.runtime.events import DATA_PATTERNS, forbidden_terms  # noqa: E402

HAVE_GIT = shutil.which("git") is not None
OFFICE = "ai-office"


def _git(cwd, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", "-C", str(cwd), *args], env=env, check=True, capture_output=True)


def task_text(tid, status, extra=""):
    return f"---\nid: {tid}\nstatus: {status}\nowner: x\n---\n\n## Spec\nx\n{extra}"


def make_fixture(root):
    """Mini repo: Sprint 1 (T-901, T-902), T-903 merged in the window; PR ref holds the stages of T-901."""
    root = Path(root)
    od = root / "offices" / OFFICE
    (od / "backlog").mkdir(parents=True)
    (od / "sprints").mkdir()
    shutil.copy(REPO / "offices" / OFFICE / "workflow.yaml", od / "workflow.yaml")
    (od / "sprints" / "sprint-01.md").write_text(
        "# Sprint 1\n\n## Tasks (in order)\n1. [T-901](../backlog/T-901-a.md) (P1): x\n"
        "2. [T-902](../backlog/T-902-b.md) (P1): y\n\n## Retro\nok\n")
    _git(root, "init", "-q", "-b", "main")
    final_extra = ("\n## Approvals (PMO)\nSpec approved.\n\n## Review log\n- REJECT — a\n"
                   "- PASS — b\nCompliance: BLOCK item\nescalated to Merwyn\n")
    f901, f902, f903 = (od / "backlog" / n for n in ("T-901-a.md", "T-902-b.md", "T-903-c.md"))
    f901.write_text(task_text("T-901", "todo")); f902.write_text(task_text("T-902", "todo"))
    _git(root, "add", "."); _git(root, "commit", "-q", "-m", "init", date="2026-01-01T09:00:00+00:00")
    _git(root, "commit", "-q", "--allow-empty", "-m", "Sprint 1 plan (#2)", date="2026-01-02T08:00:00+00:00")
    base = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    # PR branch with stages: design 09:00, build 11:00, review 11:30 (rework: build 12:00, review 12:30), done 13:00
    _git(root, "checkout", "-q", "-b", "pr1")
    for st, when in (("design", "09:00"), ("build", "11:00"), ("review", "11:30"), ("build", "12:00"),
                     ("review", "12:30"), ("done", "13:00")):
        extra = ""
        if st == "done":
            extra = final_extra
        f901.write_text(task_text("T-901", st, extra))
        _git(root, "commit", "-q", "-am", st, date=f"2026-01-03T{when}:00+00:00")
    _git(root, "update-ref", "refs/remotes/origin/pr/1", "HEAD")
    _git(root, "checkout", "-q", "main")
    _git(root, "branch", "-q", "-D", "pr1")
    f901.write_text(task_text("T-901", "done", final_extra)); f902.write_text(task_text("T-902", "done"))
    f903.write_text(task_text("T-903", "done"))
    _git(root, "add", "."); _git(root, "commit", "-q", "-m", "T-901: x (#1)", date="2026-01-03T13:05:00+00:00")
    _git(root, "commit", "-q", "--allow-empty", "-m", "T-903: z (#3)", date="2026-01-03T13:30:00+00:00")
    _git(root, "commit", "-q", "--allow-empty", "-m", "Sprint 2 plan; close Sprint 1 (#4)",
         date="2026-01-03T14:00:00+00:00")
    return root


class Parsers(unittest.TestCase):
    def test_reject_variants(self):
        for line in ("- REJECT — x", "Review 1 of PR #25 (a, b): REJECT (why)", "Verdict: REJECT", "REJECT"):
            t = f"## Review log\n{line}\n"
            self.assertEqual(metrics.verdicts(t)["reject"], 1, line)

    def test_compliance_pass_with_block_word_is_not_block(self):
        t = "## Review log\n- PASS — fine\nCompliance: PASS with conditions BLOCK item noted\n"
        v = metrics.verdicts(t)
        self.assertEqual((v["reject"], v["block"]), (0, 0))
        self.assertEqual(metrics.verdicts("## Compliance\nCompliance: BLOCK\n")["block"], 1)
        self.assertEqual(metrics.verdicts("## Review log\nCompliance: REJECT\n")["reject"], 0)

    def test_escalation_and_missing_sections(self):
        self.assertEqual(metrics.verdicts("## Review log\n- PASS\nEscalated to Merwyn at 10\n")["escalations"], 1)
        self.assertEqual(metrics.verdicts("## Spec\nx\n"), {"reject": None, "block": None, "escalations": None})

    def test_approval_headings(self):
        self.assertEqual(metrics.spec_first_time("## Spec approval\nok\n", []), "yes")
        self.assertEqual(metrics.spec_first_time("## Approvals (PMO)\nok\n", []), "yes")
        self.assertEqual(metrics.spec_first_time("## Approvals (PMO)\nspec sent back once\n", []), "no")
        self.assertEqual(metrics.spec_first_time("## Spec\nx\n", []), "not recorded")
        t = datetime.fromisoformat
        evs = [(t("2026-01-01T01:00:00+00:00"), "spec"), (t("2026-01-01T02:00:00+00:00"), "todo"),
               (t("2026-01-01T03:00:00+00:00"), "spec")]
        self.assertEqual(metrics.spec_first_time("## Spec approval\nok\n", evs), "no")

    def test_turnaround_needs_a_real_stage(self):
        t = datetime.fromisoformat
        self.assertIsNone(metrics.turnaround_hours([(t("2026-01-01T01:00:00+00:00"), "done")]))
        self.assertIsNone(metrics.stage_hours([(t("2026-01-01T01:00:00+00:00"), "done")], ("build",))["build"])


@unittest.skipUnless(HAVE_GIT, "git not available")
class FixtureHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = make_fixture(Path(cls.tmp.name) / "full")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_stage_hours_and_turnaround(self):
        ev = metrics.status_events(self.root, OFFICE)["T-901"]
        sh = metrics.stage_hours(ev, ("design", "build", "review"))
        self.assertAlmostEqual(sh["design"], 2.0)
        self.assertAlmostEqual(sh["build"], 0.5 + 0.5)   # 11:00-11:30 and 12:00-12:30
        self.assertAlmostEqual(sh["review"], 0.5 + 0.5)
        self.assertAlmostEqual(metrics.turnaround_hours(ev), 4.0)

    def test_window_and_footnote(self):
        ml = metrics.merges(self.root)
        win = metrics.sprint_window(ml, 1)
        self.assertEqual((win[0].hour, win[1].hour), (8, 14))
        self.assertEqual(metrics.window_extras(ml, win, {"T-901", "T-902"}), [("T-903", 3)])

    def test_fmt_partial(self):
        self.assertEqual(metrics.fmt_partial(2, 0), "2")
        self.assertEqual(metrics.fmt_partial("0.3", 0), "0.3")
        self.assertEqual(metrics.fmt_partial(None, 3), "not recorded")
        self.assertEqual(metrics.fmt_partial(1, 1), "1 (partial, 1 not recorded)")
        self.assertEqual(metrics.fmt_partial("0.3", 2), "0.3 (partial, 2 not recorded)")

    def test_report(self):
        rep = metrics.build_report(self.root, OFFICE, "2026-01-31")
        self.assertIn("History: full (1 PR refs)", rep)
        part = "(partial, 1 not recorded)"
        self.assertIn(f"| 1 | 2 [1] | 2026-01-02 08:00 to 2026-01-03 14:00 | 1 {part} | 1 {part} | 1 {part} "
                      f"| 1 of 2 (1 not recorded) | 4.0 {part} |", rep)
        self.assertIn("T-903 (#3)", rep)
        self.assertIn("| T-901 | 1 | not recorded | 2.0 | 1.0 | 1.0 | 4.0 | 1 | 1 | 1 | yes |", rep)
        self.assertIn("| T-902 | 1 | not recorded | not recorded | not recorded | not recorded | "
                      "not recorded | not recorded | not recorded | not recorded | not recorded |", rep)
        self.assertIn("not set: Merwyn supplies", rep)
        self.assertNotIn("| T-903 |", rep)

    def test_cli_exit_codes_and_data_rules(self):
        out = Path(self.tmp.name) / "r.md"
        self.assertEqual(metrics.main([OFFICE, "--repo", str(self.root), "--out", str(out)]), 0)
        text = out.read_text()
        for p in DATA_PATTERNS:
            self.assertIsNone(p.search(text))
        for term in forbidden_terms(REPO):
            self.assertNotIn(term.lower(), text.lower())
        self.assertEqual(metrics.main(["no-such-office", "--repo", str(self.root)]), 2)
        self.assertEqual(metrics.main([]), 2)


@unittest.skipUnless(HAVE_GIT, "git not available")
class MissingHistory(unittest.TestCase):
    def test_shallow_clone(self):
        with tempfile.TemporaryDirectory() as d:
            full = make_fixture(Path(d) / "full")
            shallow = Path(d) / "shallow"
            subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{full}", str(shallow)],
                           check=True, capture_output=True)
            out = Path(d) / "r.md"
            self.assertEqual(metrics.main([OFFICE, "--repo", str(shallow), "--out", str(out)]), 0)
            rep = out.read_text()
            self.assertIn("PARTIAL HISTORY", rep)
            self.assertIn("| T-901 | 1 | not recorded | not recorded | not recorded | not recorded | not recorded |", rep)

    def test_no_git(self):
        with tempfile.TemporaryDirectory() as d:
            plain = Path(d) / "plain"
            shutil.copytree(make_fixture(Path(d) / "full"), plain, ignore=shutil.ignore_patterns(".git"))
            out = Path(d) / "r.md"
            self.assertEqual(metrics.main([OFFICE, "--repo", str(plain), "--out", str(out)]), 0)
            self.assertIn("NO GIT HISTORY", out.read_text())


class RealFiles(unittest.TestCase):
    def _v(self, prefix):
        f = next((REPO / "offices" / OFFICE / "backlog").glob(f"{prefix}-*.md"))
        return metrics.verdicts(f.read_text(encoding="utf-8"), prefix)

    def test_spot_checks(self):
        v = self._v("T-040")
        self.assertEqual((v["reject"], v["block"], v["escalations"]), (0, 1, 1))
        v = self._v("T-048")
        self.assertEqual((v["reject"], v["escalations"]), (2, 1))

    def test_sprint2_row_is_zero_not_unrecorded(self):
        """T-042/T-014/T-015 have no Review log; their counts derive from Design and sprint Close."""
        od = REPO / "offices" / OFFICE
        sp = next(s for s in metrics.sprints(od) if s["n"] == 2)
        close = metrics.sprint_close_text(od, 2)
        tot = {"reject": 0, "block": 0, "escalations": 0}
        for t in sp["tasks"]:
            f = next((od / "backlog").glob(f"{t}-*.md"))
            v = metrics.derive_without_review(f.read_text(encoding="utf-8"), t, [], close)
            for k in tot:
                self.assertIsNotNone(v[k], (t, k))
                tot[k] += v[k]
        self.assertEqual((tot["reject"], tot["block"], tot["escalations"]), (0, 0, 0))

    def test_review_to_build_transitions(self):
        t = datetime.fromisoformat
        evs = [(t(f"2026-01-01T0{i}:00:00+00:00"), s) for i, s in
               enumerate(["design", "build", "review", "build", "review", "build", "review", "done"])]
        v = metrics.derive_without_review("## Design\n**Compliance:** not flagged\n", "T-1", evs, "")
        self.assertEqual((v["reject"], v["block"]), (2, 0))

    def test_sprint_task_counts(self):
        counts = {s["n"]: len(s["tasks"]) for s in metrics.sprints(REPO / "offices" / OFFICE) if s["closed"]}
        # Sprints 1-4 are history; later sprints are added as they close (T-055).
        self.assertEqual({k: v for k, v in counts.items() if k <= 4}, {1: 2, 2: 3, 3: 3, 4: 3})

    def test_committed_report_clean(self):
        for rep in (REPO / "offices" / OFFICE / "metrics").glob("*.md"):
            text = rep.read_text(encoding="utf-8")
            for p in DATA_PATTERNS:
                self.assertIsNone(p.search(text), rep.name)
            for term in forbidden_terms(REPO):
                self.assertNotIn(term.lower(), text.lower())


if __name__ == "__main__":
    unittest.main()
