import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_agents  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
WS = "base/skills/working-standard/SKILL.md"


class TempRepo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(REPO / "base", self.root / "base")
        shutil.copy(REPO / "workspaces.yaml", self.root / "workspaces.yaml")
        shutil.copytree(REPO / "offices" / "ai-office", self.root / "offices" / "ai-office",
                        ignore=shutil.ignore_patterns("__pycache__", "backlog"))
        self.out = self.root / ".claude" / "agents"

    def build(self, office="ai-office"):
        build_agents.build(office, self.root)

    def fails(self, office="ai-office"):
        with self.assertRaises(SystemExit) as cm:
            self.build(office)
        return str(cm.exception)


class Build(TempRepo):
    def test_every_ai_office_agent_gets_working_standard(self):
        self.build()
        n_agents = len(list((self.root / "offices/ai-office/agents").glob("*.md")))
        hits = [f for f in self.out.glob("*.md") if WS in f.read_text()]
        self.assertEqual(len(hits), n_agents)
        self.assertGreater(n_agents, 0)

    def test_agent_files_do_not_list_the_skill(self):
        for f in (REPO / "offices").glob("*/agents/*.md"):
            self.assertNotIn("working-standard", f.read_text(), f)

    def test_second_office_agent_gets_skill_without_editing_profile(self):
        d = self.root / "offices" / "demo" / "agents"
        d.mkdir(parents=True)
        (d / "solo.md").write_text("---\nname: solo\ndescription: A lone agent.\n---\nBody.\n")
        self.build("demo")
        text = (self.out / "solo.md").read_text()
        self.assertIn(f"- {WS}\n", text)
        self.assertNotIn("working-standard", (d / "solo.md").read_text())

    def test_order_base_then_agent_then_office_deduped(self):
        extra = self.root / "base" / "skills" / "extra"
        extra.mkdir()
        (extra / "SKILL.md").write_text("---\nname: extra\n---\n")
        f = self.root / "offices/ai-office/agents/pm.md"
        f.write_text(f.read_text().replace("name: pm\n", "name: pm\nbase_skills: [extra, working-standard]\n", 1))
        self.build()
        paths = re.findall(r"^- (\S+SKILL\.md)$", (self.out / "pm.md").read_text(), re.M)
        self.assertEqual(paths[:2], [WS, "base/skills/extra/SKILL.md"])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(paths[2].startswith("offices/ai-office/skills/"))
        self.assertNotIn("base_skills", (self.out / "pm.md").read_text().split("<!--")[0])


class Failures(TempRepo):
    def setUp(self):
        super().setUp()
        self.out.mkdir(parents=True)
        self.keep = self.out / "keep.md"
        self.keep.write_text("old")

    def test_unknown_default_skill_exits_and_keeps_output(self):
        (self.root / "base" / "defaults.yaml").write_text("base_skills: [ghost]\n")
        self.assertIn("base/defaults.yaml: base_skills names 'ghost', but base/skills/ghost/SKILL.md is missing", self.fails())
        self.assertTrue(self.keep.exists())

    def test_unknown_agent_base_skill_exits_and_keeps_output(self):
        f = self.root / "offices/ai-office/agents/pm.md"
        f.write_text(f.read_text().replace("name: pm\n", "name: pm\nbase_skills: [ghost]\n", 1))
        self.assertIn("pm.md: base_skills names 'ghost', but base/skills/ghost/SKILL.md is missing", self.fails())
        self.assertTrue(self.keep.exists())

    def test_clash_exits_and_keeps_output(self):
        d = self.root / "base" / "skills" / "handoff"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: handoff\n---\n")
        self.assertIn("skill 'handoff' exists in both base/skills/ and offices/ai-office/skills/; keep one", self.fails())
        self.assertTrue(self.keep.exists())


if __name__ == "__main__":
    unittest.main()
