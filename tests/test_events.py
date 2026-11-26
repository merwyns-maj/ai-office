import json
import tempfile
import unittest
from pathlib import Path

from engine.runtime import events, providers
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


HDR1 = '{"log":"office-events","v":1,"office":"ai-office","clock":"synthetic","usage_source":"synthetic"}'
V1_FIXTURE = REPO / "engine/app/fixtures/models-synthetic.jsonl"
V1_EDGE = REPO / "tests/fixtures/events-v1-edge.jsonl"
CATALOGUE = {
    "claude-sdk": {"billing": "plan", "models": {"claude-opus-4-5": {}}},
    "openai": {"billing": "per_token", "models": {"gpt-5": {}}},
    "deepseek": {"billing": "per_token", "models": {"deepseek-chat": {}}},
    "anthropic-api": {"billing": "per_token", "models": {"claude-opus-4-5": {}}},
}


def use(**k):
    d = {"type": "usage", "provider": "anthropic-api", "model": "claude-opus-4-5", "billing": "per_token", "input": 10, "output": 5}
    d.update(k)
    return ev(**d)


def parse1(*lines, providers=None, forbidden=()):
    text = "\n".join([HDR1] + list(lines))
    return events.parse_log(text, agents=AGENTS, stages=STAGES, forbidden=forbidden, providers=providers)


class V1(unittest.TestCase):
    def test_v0_files_load_unchanged(self):
        for path, n in ((FIXTURE, 45), (ALL_TYPES, 15)):
            h, evs, probs = parse_file(path)
            self.assertEqual((h["v"], len(evs), probs), (0, n, []), path)
        code, out, _ = run("events", "ai-office", str(FIXTURE))
        self.assertEqual(code, 0)
        code, out, _ = run("events", "ai-office", str(ALL_TYPES))
        self.assertEqual(code, 0, out)

    def test_v1_fields_in_a_v0_file_keep_todays_warnings(self):
        _, evs, probs = parse(use(t=1), ev(t=2, provider="openai", model="gpt-5"))
        self.assertEqual(len(evs), 2)
        self.assertEqual([p.level for p in probs], ["warning"] * 3)
        self.assertIn("unknown type", probs[0].message)
        self.assertTrue(all("not defined" in p.message for p in probs[1:]))

    def test_v1_header_needs_usage_source(self):
        hdr = '{"log":"office-events","v":1,"office":"x","clock":"synthetic","usage_source":"%s"}'
        self.assertEqual(parse(ev(), header=hdr % "made-up")[0], None)
        for ok in ("synthetic", "recorded"):
            self.assertEqual(parse(ev(), header=hdr % ok)[0]["usage_source"], ok)
        self.assertIsNone(parse(ev(), header='{"log":"office-events","v":1,"office":"x","clock":"synthetic"}')[0])
        self.assertIsNone(parse(ev(), header='{"log":"office-events","v":2,"office":"x","clock":"synthetic","usage_source":"synthetic"}')[0])

    def test_synthetic_fixture_is_clean_with_four_providers(self):
        h, evs, probs = parse_file(V1_FIXTURE)
        self.assertEqual(probs, [])
        self.assertEqual(h["usage_source"], "synthetic")
        self.assertIn("SYNTHETIC", h["title"])
        us = [e for e in evs if e["type"] == "usage"]
        self.assertGreaterEqual(len(us), 12)
        self.assertEqual(len({e["provider"] for e in us}), 4)
        self.assertTrue(all("cost_usd" not in e for e in us))
        first40 = {e["agent"] for e in evs if e["type"] == "step_started" and e["t"] <= 40 and "model" in e}
        self.assertEqual(first40, AGENTS)

    def test_plan_step_with_cost_is_an_error(self):
        _, evs, probs = parse1(use(billing="plan", provider="claude-sdk", cost_usd=0.5))
        self.assertEqual(evs, [])
        self.assertIn("plan", errors(probs)[0].message)
        _, evs, probs = parse1(use(billing="plan", provider="claude-sdk"), use(t=2, cost_usd=0.5))
        self.assertEqual((len(evs), probs), (2, []))

    def test_numeric_bounds(self):
        bad = [use(input=1_000_000_000), use(input=-1), use(input=1.5), use(input=True), use(output="5"), use(cache_read=10 ** 10),
               use(cost_usd=0.1234567), use(cost_usd=-1), use(cost_usd=1_000_000), use(cost_usd=True)]
        for line in bad:
            _, evs, probs = parse1(line)
            self.assertEqual((evs, len(errors(probs))), ([], 1), line)
        good = use(input=999_999_999, output=0, cache_read=1, cache_write=2, cost_usd=0.123456)
        self.assertEqual(parse1(good)[1][0]["input"], 999_999_999)

    def test_ids_provider_model_pair_and_billing(self):
        for line in (use(provider="Bad_Provider"), use(model="bad model!"), use(billing="free"), use(provider=None), use(model=None),
                     ev(provider="openai"), ev(model="gpt-5")):
            _, evs, probs = parse1(line)
            self.assertEqual((evs, len(errors(probs))), ([], 1), line)
        _, evs, probs = parse1(ev(provider="openai", model="gpt-5"))
        self.assertEqual((len(evs), probs), (1, []))

    def test_unknown_ids_warn_once_not_error(self):
        lines = [use(t=1, provider="mystery-ai", model="m1"), use(t=2, provider="mystery-ai", model="m1"),
                 use(t=3, provider="openai", model="gpt-9"), use(t=4, provider="deepseek", model="deepseek-chat", billing="plan")]
        _, evs, probs = parse1(*lines, providers=CATALOGUE)
        self.assertEqual(len(evs), 4)
        self.assertEqual([p.level for p in probs], ["warning"] * 3)
        self.assertEqual([p.line for p in probs], [2, 4, 5])
        self.assertIn("'mystery-ai'", probs[0].message)
        self.assertIn("'gpt-9'", probs[1].message)
        self.assertIn("event wins", probs[2].message)
        self.assertEqual(parse1(*lines)[2], [])   # no catalogue: no catalogue warnings

    def test_edge_fixture_levels(self):
        text = V1_EDGE.read_text(encoding="utf-8")
        cat, _ = providers.load_providers(REPO / "offices/ai-office")
        h, evs, probs = events.parse_log(text, agents=AGENTS, stages=STAGES, providers=cat)
        self.assertEqual(len(evs), 5)
        self.assertEqual(sorted(p.level for p in probs), ["error"] * 8 + ["warning"] * 3)
        self.assertEqual({e["model"] for e in evs}, {"mystery-1", "gpt-9-preview", "deepseek-chat", "claude-opus-4-5"})

    def test_data_rule_names_the_model_field_never_the_value(self):
        for field, val in (("model", "a.b@example.com"), ("model", "x1234567890123456"), ("provider", "acme-corp")):
            _, evs, probs = parse1(use(**{field: val}), forbidden=("acme-corp",))
            self.assertEqual(evs, [])
            msg = errors(probs)[0].message
            self.assertIn(f"field '{field}'", msg)
            self.assertTrue(events.is_data_problem(msg))
            self.assertNotIn(val, msg)

    def test_cli_runs_v1_files(self):
        code, out, _ = run("events", "ai-office", str(V1_FIXTURE))
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors, 0 warnings", out)
        code, out, _ = run("events", "ai-office", str(V1_EDGE))
        self.assertEqual(code, 1)
        self.assertIn("3 warnings", out)


if __name__ == "__main__":
    unittest.main()
