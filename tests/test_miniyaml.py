import unittest

from engine.runtime.miniyaml import YamlError, loads, split_frontmatter
from tests._helpers import REPO

O = REPO / "offices" / "ai-office"


class RealFiles(unittest.TestCase):
    def test_workflow(self):
        wf = loads((O / "workflow.yaml").read_text(), "workflow.yaml")
        self.assertEqual([s["id"] for s in wf["stages"]], ["todo", "spec", "design", "build", "review"])
        self.assertIsNone(wf["stages"][0]["output_section"])
        self.assertEqual(wf["stages"][0]["exit"], "PMO picks it")
        self.assertEqual(wf["terminal"], ["done", "parked"])
        self.assertEqual(wf["status_writers"]["exceptions"][0],
                         {"agent": "reviewer", "may_set": ["done", "build"], "from": "review"})
        self.assertIn("budget_used >= 0.8", wf["human_gates"])
        self.assertTrue(any("(company repos, brains)" in g for g in wf["human_gates"]))

    def test_office_and_org(self):
        o = loads((O / "office.yaml").read_text(), "office.yaml")
        self.assertEqual(o["id"], "ai-office")
        self.assertEqual(o["budget"]["monthly_usd_cap"], 60)   # int, comment dropped
        self.assertEqual(o["human"]["approves"][0], "spec")
        org = loads((O / "org.yaml").read_text(), "org.yaml")
        self.assertEqual(len(org["agents"]), 8)
        self.assertEqual(org["agents"][0]["role"], "Chief of Staff (PMO)")

    def test_frontmatter_agent_and_task(self):
        meta, body = split_frontmatter((O / "agents" / "architect.md").read_text(), "a.md")
        self.assertEqual(meta["external_skills"], ["claude:diagram-design"])
        self.assertEqual(meta["office_skills"], ["architect-playbook", "decision-record", "document-assessment", "handoff"])
        self.assertIn("Fang", body)
        t001 = sorted((O / "backlog").glob("T-001-*.md"))[0]
        meta, _ = split_frontmatter(t001.read_text(), str(t001))
        self.assertEqual(meta["depends_on"], [])
        self.assertEqual(meta["status"], "done")


class Constructs(unittest.TestCase):
    def test_scalars(self):
        d = loads("a: null\nb: ~\nc: true\nd: false\ne: 3\nf: 0.8\ng: hello world\nh: 'it''s'\ni: \"q\\\"x\"\nj:\n")
        self.assertEqual(d, {"a": None, "b": None, "c": True, "d": False, "e": 3, "f": 0.8,
                             "g": "hello world", "h": "it's", "i": 'q"x', "j": None})

    def test_comments(self):
        d = loads("# top\na: 1   # trailing\nb: \"x # y\"\nc: 'p: q # r'\nd: don't # c\ne: a#b\n")
        self.assertEqual(d, {"a": 1, "b": "x # y", "c": "p: q # r", "d": "don't", "e": "a#b"})

    def test_flow_nested(self):
        d = loads("x: { agent: reviewer, may_set: [done, build], from: review }\ny: [a, 'b, c', { k: v }]\nz: []\nw: {}\n")
        self.assertEqual(d["x"], {"agent": "reviewer", "may_set": ["done", "build"], "from": "review"})
        self.assertEqual(d["y"], ["a", "b, c", {"k": "v"}])
        self.assertEqual((d["z"], d["w"]), ([], {}))

    def test_colon_without_space_is_one_scalar(self):
        d = loads("e: [claude:diagram-design, claude:dataviz]\nf: claude:x\n")
        self.assertEqual(d["e"], ["claude:diagram-design", "claude:dataviz"])
        self.assertEqual(d["f"], "claude:x")

    def test_block_nesting_and_lists(self):
        d = loads("a:\n  b:\n    c: 1\n  d:\n    - x (y, z)\n    - 'q: r'\ne:\n- one\n- two\n")
        self.assertEqual(d, {"a": {"b": {"c": 1}, "d": ["x (y, z)", "q: r"]}, "e": ["one", "two"]})


class Unsupported(unittest.TestCase):
    def assertErr(self, text, line):
        with self.assertRaises(YamlError) as cm:
            loads(text, "f.yaml")
        self.assertEqual(cm.exception.line, line)
        self.assertIn("f.yaml:%d" % line, str(cm.exception))

    def test_block_scalar(self):
        self.assertErr("a: 1\nb: |\n  text\n", 2)

    def test_anchor_alias_tag(self):
        self.assertErr("a: &x 1\n", 1)
        self.assertErr("a: 1\nb: *x\n", 2)
        self.assertErr("a: !!str 1\n", 1)

    def test_multi_document(self):
        self.assertErr("a: 1\n---\nb: 2\n", 2)

    def test_tab_indent(self):
        self.assertErr("a:\n\tb: 1\n", 2)

    def test_block_map_in_list(self):
        self.assertErr("a:\n  - k: v\n", 2)

    def test_bad_flow_and_missing_frontmatter(self):
        self.assertErr("a: [1, 2\n", 1)
        with self.assertRaises(YamlError):
            split_frontmatter("no frontmatter", "x.md")
        with self.assertRaises(YamlError):
            split_frontmatter("---\na: 1\n", "x.md")

    def test_frontmatter_line_numbers(self):
        with self.assertRaises(YamlError) as cm:
            split_frontmatter("---\na: 1\nb: |\n---\nbody", "x.md")
        self.assertEqual(cm.exception.line, 3)


if __name__ == "__main__":
    unittest.main()
