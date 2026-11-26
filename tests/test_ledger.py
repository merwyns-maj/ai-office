import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.runtime import events, ledger
from tests._helpers import REPO, run

AGENTS = {"pmo", "pm", "architect", "engineer", "reviewer", "compliance", "curator", "designer"}
REAL = REPO / "offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl"
EDGE = REPO / "tests/fixtures/ledger-edge.jsonl"
HDR = ('{"log":"agent-runs","v":1,"office":"ai-office","session":"session_TEST0001","source":"s","recorded_by":"r",'
       '"covers":"c","date":"2026-11-26","not_reported":["split"]}')


def run_line(n, **k):
    d = {"n": n, "sprint": 1, "agent": "pm", "tasks": ["T-901"], "step": "spec", "tokens": 10, "tool_uses": 1, "duration_ms": 5}
    d.update(k)
    return json.dumps(d)


def parse(*lines, header=HDR, **kw):
    return ledger.parse_ledger("\n".join(([header] if header else []) + list(lines)), agents=AGENTS, **kw)


def errs(probs):
    return [p for p in probs if p.level == "error"]


class RealLedger(unittest.TestCase):
    def setUp(self):
        self.h, self.runs, self.probs = ledger.load_ledger(REAL, agents=AGENTS, office="ai-office",
                                                           forbidden=events.forbidden_terms(REPO))

    def test_loads_clean(self):
        self.assertEqual(self.probs, [])
        self.assertEqual(self.h["session"], REAL.stem)
        self.assertEqual(self.h["not_reported"], ["split", "model", "main_session"])
        self.assertGreaterEqual(len(self.runs), 35)

    def test_run_22_is_not_reported_and_run_8_has_its_note(self):
        by = {r["n"]: r for r in self.runs}
        self.assertEqual([by[22][k] for k in ledger.NUMS], [None, None, None])   # null, never 0
        self.assertEqual(sum(1 for r in self.runs if r["tokens"] is None), 1)
        self.assertIn("general-purpose agent", by[8]["note"])

    def test_totals_add_up_everywhere(self):
        t = ledger.totals(self.runs)
        total = sum(r["tokens"] or 0 for r in self.runs)
        self.assertEqual(t["session"]["tokens"], total)
        self.assertEqual(sum(r["tokens"] for r in t["agents"].values()), total)
        self.assertEqual(sum(r["tokens"] for r in t["sprints"].values()), total)
        self.assertEqual(sum(r["solo_tokens"] for r in t["tasks"].values()) + t["shared"]["tokens"], total)
        self.assertEqual(t["session"]["not_reported"], 1)
        self.assertEqual(sum(r["runs"] for r in t["agents"].values()), len(self.runs))

    def test_seed_numbers_at_build(self):
        if len(self.runs) == 35:   # Janice appends later runs; the numbers below are for the file as built
            t = ledger.totals(self.runs)
            self.assertEqual((t["session"]["tokens"], t["shared"]["tokens"], t["shared"]["runs"]), (2_520_926, 734_647, 11))

    def test_converts_to_a_clean_v1_log(self):
        txt = ledger.to_event_log(self.h, self.runs)
        h, evs, probs = events.parse_log(txt, agents=AGENTS, stages={"todo"})
        self.assertEqual(probs, [])
        self.assertEqual((h["v"], h["usage_source"]), (1, "recorded"))
        self.assertEqual(len(evs), len(self.runs))
        self.assertIsNone(next(e for e in evs if e["run"] == 22)["total"])
        self.assertEqual(sum(e["total"] or 0 for e in evs), ledger.totals(self.runs)["session"]["tokens"])
        self.assertTrue(all(e["src"].endswith(f"#n={e['run']}") for e in evs))

    def test_no_dollar_or_percent_of_plan_in_the_file(self):
        text = REAL.read_text(encoding="utf-8")
        self.assertNotIn("$", text)
        self.assertNotIn("%", text)


class Totals(unittest.TestCase):
    def test_null_shared_and_solo(self):
        _, runs, probs = parse(run_line(1), run_line(2, tasks=["T-901", "T-902"], tokens=None, tool_uses=None, duration_ms=None),
                               run_line(3, tasks=["T-902", "T-903"], tokens=7), run_line(4, agent="engineer", tasks=["T-902"], tokens=3))
        self.assertEqual(probs, [])
        t = ledger.totals(runs)
        self.assertEqual(t["session"], {"runs": 4, "not_reported": 1, "tokens": 20, "tool_uses": 3, "duration_ms": 15,
                                        "tasks": ["T-901", "T-902", "T-903"]})
        self.assertEqual(t["shared"]["tokens"], 7)
        self.assertEqual(t["shared"]["runs"], 2)
        self.assertEqual(t["tasks"]["T-902"], {"runs": 3, "solo_runs": 1, "solo_tokens": 3, "shared_runs": 2,
                                               "tokens_with_shared": 10, "not_reported": 1})
        self.assertEqual(sum(r["solo_tokens"] for r in t["tasks"].values()) + t["shared"]["tokens"], t["session"]["tokens"])
        self.assertEqual(t["agents"]["pm"]["not_reported"], 1)


class Parser(unittest.TestCase):
    def test_edge_fixture(self):
        h, runs, probs = ledger.parse_ledger(EDGE.read_text(encoding="utf-8"), agents=AGENTS, office="ai-office",
                                             forbidden=("acmecorp",))
        self.assertEqual(h["session"], "session_EDGE0000")
        by = {}
        for p in probs:
            by.setdefault(p.line, []).append(p)
        text = lambda n: " ".join(p.message for p in by.get(n, []))
        self.assertEqual([p.level for p in by[1]], ["warning"])             # unknown header field kept
        self.assertIn("n must increase", text(3))                           # duplicate n
        self.assertIn("tasks must be", text(4))                             # bad task id
        self.assertEqual([p.level for p in by[5]], ["warning"])             # null run kept (gap warning only)
        self.assertEqual(by.get(6), None)                                   # 0 is a number, kept
        self.assertIn("input and output are required" if False else "tokens must equal", text(7))   # split sum mismatch
        self.assertEqual([p for p in by.get(8, []) if p.level == "error"], [])   # a correct split is fine
        self.assertIn("unknown agent", text(9))
        self.assertIn("mood", text(10))                                     # unknown run field: warning, kept
        for n, kind in ((11, "email address"), (12, "16-digit run"), (13, "forbidden term")):
            self.assertIn(kind, text(n))
            self.assertIn("'note'", text(n))
            self.assertTrue(events.is_data_problem(by[n][0].message))
        self.assertNotIn("someone@", " ".join(p.message for p in probs))
        self.assertNotIn("1234567890123456", " ".join(p.message for p in probs))
        self.assertNotIn("acmecorp", " ".join(p.message for p in probs))
        self.assertEqual([r["n"] for r in runs], [1, 3, 4, 6, 9, 13])
        self.assertIsNone(next(r for r in runs if r["n"] == 3)["tokens"])
        self.assertEqual(next(r for r in runs if r["n"] == 4)["tokens"], 0)

    def test_bad_headers_reject_the_file(self):
        bad = [HDR.replace("agent-runs", "x"), HDR.replace('"v":1', '"v":0'), HDR.replace("session_TEST0001", "sess"),
               HDR.replace('"source":"s"', '"source":""'), HDR.replace("2026-11-26", "2026-13-26"),
               HDR.replace('["split"]', '["cost"]'), HDR.replace('"ai-office"', '"other"'), HDR.replace('"v":1,', ""), "{nope",
               HDR.replace('"covers":"c"', '"covers":"someone@example.invalid"')]
        for hdr in bad:
            h, runs, probs = parse(run_line(1), header=hdr, office="ai-office")
            self.assertEqual((h, runs), (None, []), hdr)
            self.assertTrue(errs(probs), hdr)

    def test_n_must_increase_and_a_gap_warns(self):
        _, runs, probs = parse(run_line(1), run_line(3), run_line(2))
        self.assertEqual([r["n"] for r in runs], [1, 3])
        self.assertEqual([(p.level, p.line) for p in probs], [("warning", 3), ("error", 4)])

    def test_zero_is_a_number_and_not_reported_is_null(self):
        _, runs, probs = parse(run_line(1, tokens=0), run_line(2, tokens=None))
        self.assertEqual((probs, runs[0]["tokens"], runs[1]["tokens"]), ([], 0, None))
        for bad in ('"tokens":"5"', '"tokens":-1', '"tokens":1.5', '"tokens":true', '"tokens":1000000000'):
            line = run_line(1).replace('"tokens": 10', bad.replace(":", ": "))
            self.assertEqual(len(errs(parse(line)[2])), 1, bad)

    def test_split_must_sum(self):
        ok = run_line(1, tokens=10, input=4, output=4, cache_read=2)
        self.assertEqual(parse(ok)[2], [])
        self.assertIn("tokens must equal", errs(parse(run_line(1, tokens=11, input=4, output=4, cache_read=2))[2])[0].message)
        self.assertEqual(len(errs(parse(run_line(1, input=5))[2])), 1)   # input without output

    def test_duplicate_key_long_line_and_blank_lines(self):
        _, runs, probs = parse("", run_line(1).replace('"n": 1', '"n": 1, "n": 2'), "x" * 2001, run_line(2), "")
        self.assertEqual([r["n"] for r in runs], [2])
        self.assertEqual(len(errs(probs)), 2)
        self.assertIsNone(parse("x" * 2001, header=None)[0])

    def test_header_data_hit_rejects_and_names_no_text(self):
        h, _, probs = parse(run_line(1), header=HDR.replace('"covers":"c"', '"covers":"acmecorp"'), forbidden=("acmecorp",))
        self.assertIsNone(h)
        self.assertIn("covers", probs[0].message)
        self.assertNotIn("acmecorp", probs[0].message)

    def test_header_provider_must_be_in_providers_yaml(self):
        hdr = HDR.replace('"date"', '"provider":"claude-code","date"')
        self.assertIsNotNone(parse(run_line(1), header=hdr, providers={"claude-code"})[0])
        h, runs, probs = parse(run_line(1), header=hdr, providers={"claude-sdk"})
        self.assertEqual((h, runs), (None, []))
        self.assertIn("providers.yaml", errs(probs)[0].message)
        self.assertIsNotNone(parse(run_line(1), header=hdr)[0])                  # no catalogue given: not checked
        real = ledger.load_ledger(REAL, agents=AGENTS, office="ai-office", providers={"anthropic-api"})
        self.assertIsNone(real[0])
        code, out, _ = run("ledger", "ai-office", str(REAL))
        self.assertEqual(code, 0)                                               # the real catalogue has claude-code

    def test_file_stem_must_equal_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "session_OTHER000.jsonl"
            f.write_text(HDR + "\n" + run_line(1) + "\n", encoding="utf-8")
            _, runs, probs = ledger.load_ledger(f, agents=AGENTS)
            self.assertEqual(len(runs), 1)
            self.assertIn("file name", errs(probs)[0].message)
            g = Path(tmp) / "session_TEST0001.jsonl"
            g.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            self.assertEqual(ledger.load_ledger(g, agents=AGENTS)[2], [])


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        code, out, _ = run("ledger", "ai-office", str(REAL))
        self.assertEqual(code, 0)
        self.assertIn("0 errors", out)
        self.assertIn("1 not reported", out)
        code, out, _ = run("ledger", "ai-office", str(EDGE))
        self.assertEqual(code, 1)
        self.assertNotIn("someone@", out)
        self.assertEqual(run("ledger", "ai-office", "/nonexistent.jsonl")[0], 2)
        self.assertEqual(run("ledger", "ai-office")[0], 2)   # usage error


if __name__ == "__main__":
    unittest.main()
