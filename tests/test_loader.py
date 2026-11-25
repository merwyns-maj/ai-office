import re
import subprocess
import sys
import unittest

from tests._helpers import REPO, OfficeCopy, run


class RealOffice(unittest.TestCase):
    def test_validate_clean(self):
        code, out, _ = run("validate", "ai-office")
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"^ai-office: OK — \d+ agents, \d+ stages, \d+ tasks, \d+ skills$")
        n_tasks = len(list((REPO / "offices/ai-office/backlog").glob("T-*.md")))
        n_agents = len(list((REPO / "offices/ai-office/agents").glob("*.md")))
        self.assertIn(f"{n_agents} agents, 5 stages, {n_tasks} tasks", out)

    def test_validate_by_path(self):
        code, out, _ = run("validate", str(REPO / "offices" / "ai-office"))
        self.assertEqual(code, 0, out)

    def test_module_entry_point(self):
        r = subprocess.run([sys.executable, "-m", "engine.runtime", "validate", "ai-office"],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ai-office: OK", r.stdout)

    def test_unknown_office_exits_2(self):
        code, _, err = run("validate", "no-such-office")
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_usage_error_exits_2(self):
        self.assertEqual(run("bogus", "ai-office")[0], 2)


class Defects(unittest.TestCase):
    def setUp(self):
        self.c = OfficeCopy()
        self.addCleanup(self.c.cleanup)
        self.first_task = sorted((self.c.root / "backlog").glob("T-*.md"))[0]

    def check(self, *needles):
        code, out, _ = run("validate", str(self.c.root))
        self.assertEqual(code, 1, out)
        for n in needles:
            self.assertIn(n, out)
        self.assertRegex(out, r"ai-office: \d+ problems?\n$")
        return out

    def test_clean_copy_passes(self):
        self.assertEqual(run("validate", str(self.c.root))[0], 0)

    def test_missing_required_file(self):
        (self.c.root / "workflow.yaml").unlink()
        self.check("offices/ai-office/workflow.yaml: missing required file")

    def test_org_agent_without_agents_file(self):
        org = self.c.root / "org.yaml"
        org.write_text(org.read_text().rstrip("\n") +
                       "\n  - { id: qa, name: Q, personality: ISTJ, reports_to: pmo, role: QA }\n")
        self.check("offices/ai-office/org.yaml: agent 'qa' has no agents/qa.md")

    def test_task_status_not_in_workflow(self):
        self.first_task.write_text(re.sub(r"(?m)^status: .*$", "status: doing", self.first_task.read_text(), count=1))
        out = self.check(f"offices/ai-office/backlog/{self.first_task.name}: status 'doing' is not a workflow stage")
        self.assertIn("todo, spec, design, build, review, done, parked", out)

    def test_depends_on_missing_task(self):
        self.first_task.write_text(re.sub(r"(?m)^depends_on: .*$", "depends_on: [T-999]", self.first_task.read_text(), count=1))
        self.check(f"offices/ai-office/backlog/{self.first_task.name}: depends_on 'T-999' does not exist")

    def test_agent_skill_without_skill_file(self):
        f = self.c.root / "agents" / "architect.md"
        f.write_text(f.read_text().replace("office_skills: [", "office_skills: [no-such-skill, ", 1))
        self.check("offices/ai-office/agents/architect.md: office_skills 'no-such-skill' has no skills/no-such-skill/SKILL.md")

    def test_yaml_parse_error_names_file_and_line(self):
        f = self.c.root / "workflow.yaml"
        f.write_text("a: |\n  x\n")
        code, out, _ = run("validate", str(self.c.root))
        self.assertEqual(code, 1)
        self.assertIn("offices/ai-office/workflow.yaml: line 1: unsupported YAML construct", out)

    def test_all_problems_collected(self):
        (self.c.root / "skills" / "handoff" / "SKILL.md").unlink()
        self.first_task.write_text(re.sub(r"(?m)^status: .*$", "status: doing", self.first_task.read_text(), count=1))
        out = self.check("status 'doing'", "office_skills 'handoff'")
        self.assertNotIn("1 problem\n", out)


if __name__ == "__main__":
    unittest.main()
