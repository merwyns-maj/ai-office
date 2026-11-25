import ast
import hashlib
import os
import socket
import sys
import unittest
from unittest import mock

from tests._helpers import REPO, OfficeCopy, run

KEYS = ["task", "file", "stage", "owner", "profile", "base_skills", "office_skills", "skill_files", "external_skills", "output_section"]


class RealOffice(unittest.TestCase):
    def test_prints_every_key(self):
        code, out, _ = run("dry-run", "ai-office")
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertEqual(lines[0], "ai-office: dry-run (no files changed, no SDK or network calls)")
        keys = [ln.split(":", 1)[0] for ln in lines[1:]]
        self.assertEqual(keys[:len(KEYS)], KEYS)
        self.assertTrue(all(k in KEYS + ["note", "consults"] for k in keys))
        self.assertRegex(lines[1], r"^task: T-\d+ ")
        self.assertRegex(lines[5], r"^profile: offices/ai-office/agents/\w+\.md$")


class Pick(unittest.TestCase):
    def setUp(self):
        self.c = OfficeCopy()
        self.addCleanup(self.c.cleanup)

    def picked(self, tasks):
        self.c.replace_backlog(tasks)
        code, out, _ = run("dry-run", str(self.c.root))
        self.assertEqual(code, 0, out)
        return out

    def task_line(self, out):
        return next(ln for ln in out.splitlines() if ln.startswith("task: "))

    def test_priority_first(self):
        out = self.picked([("T-010", "todo", "P1", "pmo", []), ("T-020", "todo", "P0", "pmo", [])])
        self.assertIn("task: T-020 ", self.task_line(out))

    def test_lowest_id_within_priority(self):
        out = self.picked([("T-012", "todo", "P0", "pmo", []), ("T-005", "todo", "P0", "pmo", [])])
        self.assertIn("task: T-005 ", self.task_line(out))

    def test_numeric_id_order(self):
        out = self.picked([("T-100", "todo", "P0", "pmo", []), ("T-99", "todo", "P0", "pmo", [])])
        self.assertIn("task: T-99 ", self.task_line(out))

    def test_skips_terminal(self):
        out = self.picked([("T-001", "done", "P0", "curator", []), ("T-002", "parked", "P0", "pmo", []),
                           ("T-030", "todo", "P2", "pmo", [])])
        self.assertIn("task: T-030 ", self.task_line(out))

    def test_skips_unmet_dependency(self):
        out = self.picked([("T-001", "todo", "P1", "pmo", []), ("T-002", "todo", "P0", "pmo", ["T-001"]),
                           ("T-003", "todo", "P2", "pmo", [])])
        self.assertIn("task: T-001 ", self.task_line(out))
        out = self.picked([("T-001", "done", "P1", "pmo", []), ("T-002", "todo", "P0", "pmo", ["T-001"])])
        self.assertIn("task: T-002 ", self.task_line(out))

    def test_skips_cross_office_dependency(self):
        out = self.picked([("T-001", "todo", "P0", "pmo", ["other-office/T-001"]), ("T-002", "todo", "P2", "pmo", [])])
        self.assertIn("task: T-002 ", self.task_line(out))

    def test_skips_human_owner(self):
        out = self.picked([("T-001", "todo", "P0", "human", []), ("T-002", "todo", "P2", "pmo", [])])
        self.assertIn("task: T-002 ", self.task_line(out))

    def test_nothing_to_run(self):
        out = self.picked([("T-001", "done", "P0", "curator", []), ("T-002", "todo", "P0", "human", []),
                           ("T-003", "todo", "P0", "pmo", ["T-002"])])
        self.assertEqual(out, "ai-office: nothing to run\n")

    def test_plan_content(self):
        out = self.picked([("T-050", "design", "P0", "architect", [])])
        self.assertIn("stage: design\n", out)
        self.assertIn("owner: architect (Fang)\n", out)
        self.assertIn("profile: offices/ai-office/agents/architect.md\n", out)
        self.assertIn("base_skills: working-standard\n", out)
        self.assertIn("office_skills: architect-playbook, decision-record, handoff\n", out)
        self.assertIn("external_skills: claude:diagram-design\n", out)
        self.assertIn("output_section: Design", out)
        self.assertIn("consults: designer (Dinda) writes UX design when the Spec or Design has UI, visual or motion work\n", out)
        self.assertNotIn("note:", out)

    def test_note_when_owner_differs_from_stage_owner(self):
        out = self.picked([("T-050", "design", "P0", "compliance", [])])
        self.assertIn("note: task owner compliance differs from stage owner architect", out)

    def test_todo_stage_has_no_output_section(self):
        out = self.picked([("T-050", "todo", "P0", "pmo", [])])
        self.assertIn("output_section: none (exit: PMO picks it)", out)
        self.assertNotIn("consults:", out)

    def test_invalid_office_exits_1(self):
        (self.c.root / "workflow.yaml").unlink()
        code, out, _ = run("dry-run", str(self.c.root))
        self.assertEqual(code, 1)
        self.assertIn("missing required file", out)


class NoSdkNoNetworkNoWrites(unittest.TestCase):
    ALLOWED = {"argparse", "dataclasses", "pathlib", "re", "sys", "typing"}

    def test_imports_are_stdlib_allowlist(self):
        files = sorted((REPO / "engine" / "runtime").glob("*.py"))
        self.assertGreaterEqual(len(files), 5)
        for f in files:
            for node in ast.walk(ast.parse(f.read_text(), str(f))):
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue  # relative import inside engine.runtime
                    mods = [node.module]
                else:
                    continue
                for m in mods:
                    ok = m.split(".")[0] in self.ALLOWED or m.startswith("engine.runtime")
                    self.assertTrue(ok, f"{f.name} imports {m}")

    def test_dry_run_offline_without_api_key(self):
        def boom(*a, **k):
            raise AssertionError("network access attempted")
        with mock.patch.dict(os.environ):
            for k in [k for k in os.environ if "API_KEY" in k or "ANTHROPIC" in k]:
                os.environ.pop(k)
            with mock.patch.object(socket, "socket", boom), mock.patch.object(socket, "create_connection", boom):
                for cmd in ("dry-run", "validate"):
                    code, out, _ = run(cmd, "ai-office")
                    self.assertEqual(code, 0, out)
        self.assertNotIn("anthropic", sys.modules)
        self.assertNotIn("claude_agent_sdk", sys.modules)

    def test_runtime_source_has_no_env_or_write_calls(self):
        for f in (REPO / "engine" / "runtime").glob("*.py"):
            src = f.read_text()
            for bad in ("os.environ", "subprocess", "write_text", "mkdir", "open(", "urllib", "socket"):
                self.assertNotIn(bad, src, f"{f.name} contains {bad}")

    @staticmethod
    def snapshot(root):
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(root.rglob("*")) if p.is_file()}

    def test_read_only(self):
        root = REPO / "offices" / "ai-office"
        before = self.snapshot(root)
        for cmd in ("validate", "dry-run"):
            self.assertEqual(run(cmd, "ai-office")[0], 0)
        self.assertEqual(self.snapshot(root), before)
        self.assertGreater(len(before), 50)

    def test_snapshot_would_catch_a_write(self):
        c = OfficeCopy()
        self.addCleanup(c.cleanup)
        before = self.snapshot(c.root)
        (c.root / "stray.txt").write_text("x")
        self.assertNotEqual(self.snapshot(c.root), before)


if __name__ == "__main__":
    unittest.main()
