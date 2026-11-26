import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import golden  # noqa: E402
from engine.runtime import events  # noqa: E402

SKILL = "partner-writing"


def run(argv, repo):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = golden.main(argv, repo=repo)
    return code, out.getvalue() + err.getvalue()


class Shipped(unittest.TestCase):
    def test_exit_0_with_three_skills(self):
        code, out = run(["ai-office"], REPO)
        self.assertEqual(code, 0, out)
        for s in ("partner-writing", "spec-writing", "review-checklist", "document-assessment"):
            self.assertIn(f"{s}: ", out)
        self.assertIn("0 problems", out)

    def test_case_counts_3_to_5_per_skill(self):
        for folder in (REPO / "base/skills/partner-writing/golden",
                       REPO / "offices/ai-office/skills/spec-writing/golden",
                       REPO / "offices/ai-office/skills/review-checklist/golden",
                       REPO / "offices/ai-office/skills/document-assessment/golden"):
            self.assertTrue(3 <= len(list(folder.glob("*.json"))) <= 5, folder)

    def test_patterns_are_imported_not_copied(self):
        self.assertIs(golden.DATA_PATTERNS, events.DATA_PATTERNS)
        self.assertIs(golden.PATTERN_KINDS, events.PATTERN_KINDS)

    def test_usage_and_unknown_office(self):
        self.assertEqual(run([], REPO)[0], 2)
        self.assertEqual(run(["no-such-office"], REPO)[0], 2)


class TempRepo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copy(REPO / "workspaces.yaml", self.root / "workspaces.yaml")
        (self.root / "offices" / "ai-office").mkdir(parents=True)
        shutil.copytree(REPO / "base/skills/partner-writing/golden",
                        self.root / "base/skills/partner-writing/golden")
        self.dir = self.root / "base/skills/partner-writing/golden"
        self.assertEqual(run(["ai-office"], self.root)[0], 0)

    def case(self, name="b1-no-dash"):
        p = self.dir / f"{name}.json"
        return p, json.loads(p.read_text())

    def edit(self, name="b1-no-dash", **changes):
        p, c = self.case(name)
        for k, v in changes.items():
            if v is None:
                c.pop(k, None)
            else:
                c[k] = v
        p.write_text(json.dumps(c, indent=2))

    def assert_problem(self, text, name="b1-no-dash"):
        code, out = run(["ai-office"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn(f"{name}.json", out)
        self.assertIn(text, out)
        return out


class Structure(TempRepo):
    def test_missing_why(self):
        self.edit(why=None)
        self.assert_problem("missing or empty 'why'")

    def test_empty_checks(self):
        self.edit(checks=[])
        self.assert_problem("empty 'checks'")

    def test_invalid_regex(self):
        _, c = self.case()
        c["checks"][0]["pattern"] = "(["
        self.edit(checks=c["checks"])
        self.assert_problem("invalid regex")

    def test_sixth_case(self):
        for n in ("extra1", "extra2"):
            shutil.copy(self.dir / "b1-no-dash.json", self.dir / f"{n}.json")
        code, out = run(["ai-office"], self.root)
        self.assertEqual(code, 1)
        self.assertIn("6 cases, expected 3 to 5", out)

    def test_too_few_cases(self):
        (self.dir / "b6-plain-email.json").unlink()
        (self.dir / "b3-no-overpromise.json").unlink()
        code, out = run(["ai-office"], self.root)
        self.assertEqual(code, 1)
        self.assertIn("2 cases, expected 3 to 5", out)

    def test_skill_mismatch(self):
        self.edit(skill="spec-writing")
        self.assert_problem("does not match folder")

    def test_unknown_key_and_type_and_bad_json(self):
        self.edit(colour="red")
        self.assert_problem("unknown key 'colour'")
        self.edit(colour=None)
        (self.dir / "b2-english-terms.json").write_text("{not json")
        self.assert_problem("invalid JSON", name="b2-english-terms")

    def test_unknown_check_type(self):
        self.edit(checks=[{"type": "vibes", "rule": "B1"}])
        self.assert_problem("unknown check type")

    def test_only_max_lines_is_not_enough(self):
        self.edit(checks=[{"type": "max_lines", "max": 9, "rule": "B4"}])
        self.assert_problem("no must or must-not check")


class Checks(TempRepo):
    def test_b1_dash_check_fails_with_dash_passes_without(self):
        _, c = self.case()
        dash = c["checks"][0]
        self.assertEqual(dash["type"], "must_not_match")
        self.assertFalse(golden.run_check(dash, "Late — sorry"))
        self.assertFalse(golden.run_check(dash, "Pages 1–3"))
        self.assertTrue(golden.run_check(dash, "Late, sorry"))

    def test_expected_output_with_dash_fails_runner(self):
        _, c = self.case()
        self.edit(expected_output=c["expected_output"] + " Late — sorry.")
        self.assert_problem("(must_not_match, B1) failed on expected_output")

    def test_bad_output_that_passes_is_reported(self):
        _, c = self.case()
        self.edit(bad_output=c["expected_output"])
        self.assert_problem("bad_output passes every check")

    def test_each_check_type(self):
        t = "a\nb\nc"
        self.assertTrue(golden.run_check({"type": "must_match", "pattern": "^b$"}, t))
        self.assertTrue(golden.run_check({"type": "must_contain", "text": "b"}, t))
        self.assertFalse(golden.run_check({"type": "must_contain", "text": "B"}, t))
        self.assertTrue(golden.run_check({"type": "must_not_contain", "text": "z"}, t))
        self.assertTrue(golden.run_check({"type": "max_lines", "max": 3}, t))
        self.assertFalse(golden.run_check({"type": "max_lines", "max": 2}, t))

    def test_shipped_bad_outputs_exist_for_b1_and_b6(self):
        for n in ("b1-no-dash", "b6-plain-email"):
            _, c = self.case(n)
            self.assertTrue(c.get("bad_output"), n)


class DataRule(TempRepo):
    def plant(self, value, kind):
        self.edit(input=f"brief {value} end")
        code, out = run(["ai-office"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("b1-no-dash.json", out)
        self.assertIn(kind, out)
        self.assertNotIn(value, out)

    def test_email(self):
        self.plant("someone" + "@" + "example.com", "email address")

    def test_16_digits(self):
        self.plant("1234" * 4, "16-digit run")

    def test_10_digits(self):
        self.plant("1234567890", "run of 10+ digits")

    def test_forbidden_term(self):
        term = events.forbidden_terms(REPO)[0]
        self.plant(f"see {term} here", "forbidden term")

    def test_email_written_as_escape(self):
        p, c = self.case()
        c["input"] = "someone\\u0040example.com"  # JSON decodes to a real at-sign
        raw = json.dumps(c, indent=2).replace("someone\\\\u0040", "someone\\u0040")
        p.write_text(raw)
        code, out = run(["ai-office"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("email address", out)
        self.assertNotIn("someone", out)

    def test_data_hit_in_unparseable_file_is_still_found(self):
        (self.dir / "b2-english-terms.json").write_text("{" + "9" * 12)
        code, out = run(["ai-office"], self.root)
        self.assertEqual(code, 1)
        self.assertIn("run of 10+ digits", out)
        self.assertNotIn("9" * 12, out)


if __name__ == "__main__":
    unittest.main()
