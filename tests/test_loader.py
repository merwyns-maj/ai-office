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

    def test_real_repo_no_defaults_warning(self):
        _, _, err = run("validate", "ai-office")
        self.assertNotIn("defaults.yaml is missing", err)

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

    def test_missing_defaults_warns_only(self):
        (self.c.root.parents[1] / "base/defaults.yaml").unlink()
        code, out, err = run("validate", str(self.c.root))
        self.assertEqual(code, 0, out)
        self.assertIn("warning: base/defaults.yaml is missing, so agents will get no base skills\n", err)
        self.assertRegex(out, r"^ai-office: OK")

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

    def test_defaults_names_missing_base_skill(self):
        (self.c.root.parent.parent / "base" / "defaults.yaml").write_text("base_skills: [working-standard, ghost]\n")
        self.check("base/defaults.yaml: base_skills 'ghost' has no base/skills/ghost/SKILL.md")

    def test_agent_base_skill_missing(self):
        f = self.c.root / "agents" / "architect.md"
        f.write_text(f.read_text().replace("name:", "base_skills: [ghost]\nname:", 1))
        self.check("offices/ai-office/agents/architect.md: base_skills 'ghost' has no base/skills/ghost/SKILL.md")

    def test_skill_clash_base_and_office(self):
        d = self.c.root.parent.parent / "base" / "skills" / "handoff"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: handoff\n---\n")
        self.check("offices/ai-office/skills/handoff: skill 'handoff' also exists in base/skills/; keep one")

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


class Consults(unittest.TestCase):
    ENTRY = '  - { agent: designer, stage: design, when: "the Spec or Design has UI, visual or motion work", output_section: UX design, accepted_by: architect }\n'

    def setUp(self):
        self.c = OfficeCopy()
        self.addCleanup(self.c.cleanup)
        self.wf = self.c.root / "workflow.yaml"
        self.text = self.wf.read_text()
        self.assertIn(self.ENTRY, self.text)

    def validate(self, text):
        self.wf.write_text(text)
        return run("validate", str(self.c.root))

    def bad(self, text, needle):
        code, out, _ = self.validate(text)
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)
        self.assertIn("offices/ai-office/workflow.yaml", out)

    def test_real_office_validates_clean(self):
        code, out, _ = run("validate", "ai-office")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.validate(self.text)[0], 0)

    def test_consults_not_a_list(self):
        self.bad(self.text.replace("consults:\n" + self.ENTRY, "consults: x\n"), "'consults' must be a list")

    def test_entry_missing_accepted_by(self):
        self.bad(self.text.replace(", accepted_by: architect", ""), "needs agent, stage, when, output_section and accepted_by")

    def test_unknown_agent(self):
        self.bad(self.text.replace("agent: designer", "agent: desginer"), "consult agent 'desginer' is not an org agent")

    def test_terminal_stage_rejected(self):
        self.bad(self.text.replace("stage: design,", "stage: done,"), "consult stage 'done' is not a workflow stage")

    def test_accepted_by_not_stage_owner(self):
        self.bad(self.text.replace("accepted_by: architect", "accepted_by: pmo"),
                 "consult accepted_by 'pmo' must be the owner of stage 'design' ('architect')")

    def test_output_section_clash(self):
        self.bad(self.text.replace("output_section: UX design", "output_section: Design"),
                 "consult output_section 'Design' is already a stage's output_section")

    def test_no_consults_still_clean(self):
        head = self.text.split("# Consults (T-047)")[0]
        tail = self.text.split(self.ENTRY, 1)[1]
        self.assertNotIn("consults:", head + tail)
        code, out, _ = self.validate(head + tail)
        self.assertEqual(code, 0, out)


class LeanPath(unittest.TestCase):
    """T-068: paths.lean rules in workflow.yaml and the lean entry rule on tasks."""
    NOTE = "> Lean (Janice, pmo, 2026-11-27): the docked chat page; no new data; no compliance flag; no human gate. Reason: small.\n"

    def setUp(self):
        self.c = OfficeCopy()
        self.addCleanup(self.c.cleanup)
        self.wf = self.c.root / "workflow.yaml"
        self.text = self.wf.read_text()
        self.assertIn("paths:\n  lean:", self.text)

    def validate(self):
        return run("validate", str(self.c.root))

    def bad_wf(self, old, new, needle):
        self.assertIn(old, self.text)
        self.wf.write_text(self.text.replace(old, new, 1))
        code, out, _ = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def task(self, note=NOTE, status="design", where="repo", project="ai-office", extra=""):
        self.c.replace_backlog([("T-900", status, "P1", "architect", [])])
        f = next((self.c.root / "backlog").glob("T-900-*.md"))
        f.write_text(f"---\nid: T-900\ntitle: x\nstatus: {status}\npriority: P1\nowner: architect\n"
                     f"where: {where}\nproject: {project}\ndepends_on: []\n---\n{note}## Spec\n{extra}## Open questions\n")
        return f

    def bad_task(self, needle, **kw):
        self.task(**kw)
        code, out, _ = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def test_live_workflow_validates(self):
        self.assertEqual(self.validate()[0], 0)

    def test_skip_review_rejected(self):
        self.bad_wf("skips: [spec] ", "skips: [review] ", "skips 'review' which is in never_skips")

    def test_skip_build_rejected(self):
        self.bad_wf("skips: [spec] ", "skips: [build] ", "skips 'build' which is in never_skips")

    def test_skip_unknown_stage(self):
        self.bad_wf("skips: [spec] ", "skips: [ghost] ", "skips 'ghost' is not a workflow stage")

    def test_no_reviewer_gate(self):
        self.bad_wf("  - { stage: done,   approver: reviewer }", "  - { stage: done,   approver: pmo }", "paths needs a gate {stage: done, approver: reviewer}")

    def test_no_review_stage(self):
        line = [l for l in self.text.splitlines(True) if l.startswith("  - { id: review")][0]
        self.bad_wf(line, "", "paths needs a 'review' stage")

    def test_unknown_entry_id(self):
        self.bad_wf("no_human_gate]", "no_human_gate, extra]", "paths.lean entry must be exactly")

    def test_spec_by_must_own_first_unskipped_stage(self):
        self.bad_wf("spec_by: architect", "spec_by: pm", "spec_by 'pm' must own the first stage not skipped ('architect')")

    def test_spec_approver_must_match_gate(self):
        self.bad_wf("spec_approver: pmo", "spec_approver: human", "spec_approver must equal the spec gate approver")

    def test_other_path_key_rejected(self):
        self.bad_wf("paths:\n  lean:", "paths:\n  fast: {}\n  lean:", "only the key 'lean'")

    def test_qualifying_task_passes(self):
        self.task()
        self.assertEqual(self.validate()[0], 0)

    def test_two_surfaces(self):
        self.bad_task("more than one surface", note=self.NOTE.replace("the docked chat page", "the chat page and the sprint page"))

    def test_missing_no_new_data(self):
        self.bad_task("missing 'no new data'", note=self.NOTE.replace("no new data; ", ""))

    def test_compliance_flagged(self):
        self.bad_task("compliance flagged: full path", extra="Compliance: flagged\n")

    def test_human_gate_question(self):
        f = self.task()
        f.write_text(f.read_text() + "- Needs a human gate: writes to a company repo.\n")
        code, out, _ = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("human gate: full path", out)

    def test_company_work(self):
        self.bad_task("company/chat/office work: full path", where="company")

    def test_lean_task_at_spec_fails(self):
        self.bad_task("lean task is at 'spec'", status="spec")

    def test_escape_to_full_path(self):
        full = "> Full path (Fang, architect, 2026-11-28): two surfaces\n"
        self.task(note=self.NOTE + full + "", status="spec", extra="Compliance: flagged\n")
        code, out, _ = self.validate()
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
