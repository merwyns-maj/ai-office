import json
import tempfile
import unittest
from pathlib import Path

from engine.runtime import events
from tests._helpers import REPO, run

AGENTS = {"pmo", "pm", "architect", "engineer", "reviewer", "compliance", "curator", "designer"}
STAGES = {"todo", "spec", "design", "build", "review", "done", "parked"}
HDR = '{"log":"office-events","v":0,"office":"ai-office","clock":"synthetic"}'
FIXTURE = REPO / "engine/app/fixtures/sprint-03.jsonl"
ALL_TYPES = REPO / "tests/fixtures/events-all-types.jsonl"


def parse(*lines, header=HDR, forbidden=()):
    text = "\n".join(([header] if header else []) + list(lines))
    return events.parse_log(text, agents=AGENTS, stages=STAGES, forbidden=forbidden)


def ev(**k):
    d = {"t": 1, "type": "step_started", "agent": "engineer", "task": "T-043", "src": "x.md"}
    d.update(k)
    return json.dumps({a: b for a, b in d.items() if b is not None})


def errors(probs):
    return [p for p in probs if p.level == "error"]


class RealFiles(unittest.TestCase):
    def test_fixture_is_clean(self):
        h, evs, probs = parse_file(FIXTURE)
        self.assertEqual(probs, [])
        self.assertEqual(h["v"], 0)
        self.assertEqual(sorted({e["task"] for e in evs if "task" in e}), ["T-002", "T-043", "T-044", "T-045"])

    def test_all_types_fixture_covers_every_type_and_is_clean(self):
        _, evs, probs = parse_file(ALL_TYPES)
        self.assertEqual(probs, [])
        self.assertEqual({e["type"] for e in evs}, set(events.EVENT_TYPES))
        self.assertEqual(len(events.EVENT_TYPES), 11)


def parse_file(path):
    return events.parse_log(Path(path).read_text(encoding="utf-8"), agents=AGENTS, stages=STAGES,
                            forbidden=events.forbidden_terms(REPO))


class BadLines(unittest.TestCase):
    def one_bad(self, bad, *, line=3, text=None):
        h, evs, probs = parse(ev(t=1), bad, ev(t=3))
        self.assertEqual(len(evs), 2, probs)
        errs = errors(probs)
        self.assertEqual(len(errs), 1, probs)
        self.assertEqual(errs[0].line, line)
        if text:
            self.assertIn(text, errs[0].message)

    def test_malformed_json_has_line_number(self):
        self.one_bad('{"t": 2, "type": ', text="malformed")

    def test_non_object(self):
        self.one_bad("[1,2]", text="not a JSON object")

    def test_duplicate_key(self):
        self.one_bad('{"t":2,"t":2,"type":"step_started"}', text="duplicate")

    def test_unknown_agent(self):
        self.one_bad(ev(t=2, agent="nobody"), text="unknown agent")

    def test_missing_and_mistyped_field(self):
        self.one_bad(ev(t=2, task=None), text="missing field")
        self.one_bad(ev(t=2, task="43"), text="bad task id")

    def test_decreasing_t_but_equal_ok(self):
        _, evs, probs = parse(ev(t=5), ev(t=5), ev(t=4))
        self.assertEqual(len(evs), 2)
        self.assertEqual(errors(probs)[0].line, 4)

    def test_wall_bad_and_decreasing(self):
        self.one_bad(ev(t=2, wall="yesterday"), text="wall")
        _, evs, probs = parse(ev(t=1, wall="2026-11-25T22:00:00+07:00"), ev(t=2, wall="2026-11-25T21:00:00+07:00"))
        self.assertEqual(len(evs), 1)
        self.assertIn("wall decreases", errors(probs)[0].message)

    def test_text_too_long_or_newline(self):
        n = ev(type="needs_merwyn", t=2, reason="x" * 121)
        self.one_bad(n, text="text")
        self.one_bad(ev(type="needs_merwyn", t=2, reason="a\nb"), text="text")

    def test_discussion_agent_counts_and_membership(self):
        def d(agents, lines):
            return ev(type="discussion", t=2, agent=None, agents=agents, lines=lines)
        ok = [{"agent": "pm", "text": "hi"}]
        self.one_bad(d(["pm"], ok), text="2 to 4")
        self.one_bad(d(["pm", "pmo", "architect", "engineer", "reviewer"], ok), text="2 to 4")
        self.one_bad(d(["pm", "pmo"], [{"agent": "engineer", "text": "hi"}]), text="line needs")
        _, evs, probs = parse(d(["pm", "pmo"], ok))
        self.assertEqual(probs, [])

    def test_block_without_needs_merwyn_and_reject_without_handoff(self):
        _, evs, probs = parse(ev(type="compliance_result", agent="compliance", verdict="BLOCK"), ev(t=2))
        self.assertEqual([e["type"] for e in evs], ["step_started"])
        self.assertIn("needs_merwyn", errors(probs)[0].message)
        _, evs, probs = parse(ev(type="review_reject", agent="reviewer", reason="no"), ev(t=2))
        self.assertIn("handoff", errors(probs)[0].message)
        _, evs, probs = parse(ev(type="review_reject", agent="reviewer", reason="no"),
                              ev(type="handoff", t=2, agent=None, from_agent="reviewer", to_agent="engineer", to_stage="build"))
        self.assertEqual(probs, [])

    def test_personal_data(self):
        self.one_bad(ev(type="needs_merwyn", t=2, reason="mail a.b@example.com"), text="personal-data")
        self.one_bad(ev(type="needs_merwyn", t=2, reason="id 1234567890123456"), text="personal-data")
        self.one_bad(ev(type="needs_merwyn", t=2, reason="acct 12345678901"), text="personal-data")

    def test_forbidden_term(self):
        _, evs, probs = parse(ev(type="needs_merwyn", reason="see Acme-Corp repo"), forbidden=("acme-corp",))
        self.assertEqual(evs, [])
        self.assertIn("forbidden", errors(probs)[0].message)

    def test_problem_names_field_and_kind_never_the_value(self):
        secrets = ["1234567890123456", "jane.doe@example.com", "98765432109", "Acme-Corp"]
        for sec in secrets:
            _, evs, probs = parse(ev(type="needs_merwyn", t=2, reason=f"x {sec} y"), forbidden=("acme-corp",))
            msg = errors(probs)[0].message
            self.assertNotIn(sec.lower(), msg.lower())
            self.assertIn("field 'reason'", msg)
            self.assertTrue(events.is_data_problem(msg))
        disc = json.dumps({"t": 2, "type": "discussion", "task": "T-043", "agents": ["pmo", "pm"], "src": "x.md",
                           "lines": [{"agent": "pmo", "text": "ok"}, {"agent": "pm", "text": "id 1234567890123456"}]})
        self.assertIn("field 'lines[1].text'", errors(parse(disc)[2])[0].message)
        _, _, probs = parse(header=HDR.replace("ai-office", "a@b.example"))
        self.assertNotIn("a@b.example", " ".join(str(p) for p in probs))

    def test_forbidden_terms_come_from_workspaces(self):
        terms = events.forbidden_terms(REPO)
        self.assertIn("impact-credit-solutions", terms)
        self.assertNotIn("merwyns-maj", terms)


class Warnings(unittest.TestCase):
    def test_unknown_type_and_extra_field_warn_but_keep(self):
        _, evs, probs = parse(ev(type="dance", t=1), ev(t=2, colour="red"))
        self.assertEqual(len(evs), 2)
        self.assertEqual([p.level for p in probs], ["warning", "warning"])


class Header(unittest.TestCase):
    def test_missing_or_wrong_header_rejects_file(self):
        for h in (None, '{"log":"office-events","v":1,"office":"x","clock":"synthetic"}', "not json"):
            hdr, evs, probs = parse(ev(), header=h)
            self.assertIsNone(hdr)
            self.assertEqual(evs, [])
            self.assertTrue(errors(probs))


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        code, out, _ = run("events", "ai-office", str(FIXTURE))
        self.assertEqual(code, 0, out)
        self.assertIn("45 events kept, 0 errors", out)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.jsonl"
            bad.write_text(HDR + "\n" + ev() + "\n{oops\n", encoding="utf-8")
            code, out, _ = run("events", "ai-office", str(bad))
            self.assertEqual(code, 1)
            self.assertIn("3: error: malformed JSON", out)
        code, _, err = run("events", "ai-office", "/nonexistent/x.jsonl")
        self.assertEqual(code, 2)

    def test_cli_never_echoes_personal_data(self):
        secrets = ["1234567890123456", "jane.doe@example.com"]
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "leak.jsonl"
            log.write_text("\n".join([HDR, ev(type="needs_merwyn", t=2, reason=f"id {secrets[0]}"),
                                      ev(type="needs_merwyn", t=3, reason=f"mail {secrets[1]}")]) + "\n", encoding="utf-8")
            code, out, err = run("events", "ai-office", str(log))
        self.assertEqual(code, 1)
        self.assertIn("field 'reason'", out)
        for sec in secrets:
            self.assertNotIn(sec, out + err)


if __name__ == "__main__":
    unittest.main()
