import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.runtime import events, ledger
from tests._helpers import REPO, appended_copy, run

AGENTS = {"pmo", "pm", "architect", "engineer", "reviewer", "compliance", "curator", "designer"}
REAL = REPO / "offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl"
EDGE = REPO / "tests/fixtures/ledger-edge.jsonl"
FIXTURE = REPO / "tests/fixtures/session_FIXTURE072.jsonl"   # exact numbers live here, never in the live ledger (T-072)
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
    """T-072: the live ledger is append-only, so these tests check invariants only. Exact numbers come from FIXTURE."""
    LEDGER = REAL

    def setUp(self):
        self.h, self.runs, self.probs = ledger.load_ledger(self.LEDGER, agents=AGENTS, office="ai-office",
                                                           forbidden=events.forbidden_terms(REPO))

    def test_loads_clean(self):
        self.assertEqual(self.probs, [])
        self.assertEqual(self.h["session"], self.LEDGER.stem)
        self.assertEqual(self.h["not_reported"], ["split", "model", "main_session"])
        self.assertGreaterEqual(len(self.runs), 35)

    def test_run_22_is_not_reported_and_run_8_has_its_note(self):
        by = {r["n"]: r for r in self.runs}
        self.assertEqual([by[22][k] for k in ledger.NUMS], [None, None, None])   # null, never 0
        self.assertEqual(ledger.totals(self.runs)["session"]["not_reported"], sum(1 for r in self.runs if r["tokens"] is None))
        self.assertIn("general-purpose agent", by[8]["note"])

    def test_totals_add_up_everywhere(self):
        t = ledger.totals(self.runs)
        total = sum(r["tokens"] or 0 for r in self.runs)
        self.assertEqual(t["session"]["tokens"], total)
        self.assertEqual(sum(r["tokens"] for r in t["agents"].values()), total)
        self.assertEqual(sum(r["tokens"] for r in t["sprints"].values()), total)
        self.assertEqual(sum(r["solo_tokens"] for r in t["tasks"].values()) + t["shared"]["tokens"], total)
        self.assertEqual(t["session"]["not_reported"], sum(r["tokens"] is None for r in self.runs))
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
        self.assertEqual(len(evs), sum(1 for r in self.runs if r["tasks"]))
        chat = [r for r in self.runs if not r["tasks"]]
        self.assertFalse({r["n"] for r in chat} & {e["run"] for e in evs})        # a chat run is not in the event log
        self.assertEqual(sum(e["total"] or 0 for e in evs) + sum(r["tokens"] or 0 for r in chat),
                         ledger.totals(self.runs)["session"]["tokens"])
        self.assertIsNone(next(e for e in evs if e["run"] == 22)["total"])          # old lines never change
        self.assertTrue(all(e["src"].endswith(f"#n={e['run']}") for e in evs))

    def test_no_dollar_or_percent_of_plan_in_the_file(self):
        text = self.LEDGER.read_text(encoding="utf-8")
        self.assertNotIn("$", text)
        self.assertNotIn("%", text)

    def test_main_lines_are_not_in_run_totals_or_events(self):
        h, runs, main, probs = ledger.load_ledger_full(self.LEDGER, agents=AGENTS, office="ai-office")
        self.assertEqual(runs, self.runs)
        self.assertNotIn("cache_read", ledger.to_event_log(h, runs))
        self.assertTrue(all("tokens" not in m for m in main))


class RealLedgerAppended(RealLedger):
    """T-072 guard: the live ledger plus 3 valid lines (a not-reported run, a chat run, a main-session reading) must pass
    every invariant test above. Appending a valid line must never break the suite."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.LEDGER = appended_copy(REAL, cls._tmp.name)
        code, out, _ = run("ledger", "ai-office", str(cls.LEDGER))
        assert code == 0 and "0 errors" in out, out

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_appended_lines_were_read(self):
        live = ledger.load_ledger(REAL, agents=AGENTS)[1]
        self.assertEqual(len(self.runs), len(live) + 2)
        self.assertIsNone(self.runs[-2]["tokens"])
        self.assertEqual(self.runs[-1]["tasks"], [])


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


class FixtureTotals(unittest.TestCase):
    """The exact numbers, pinned once, on the synthetic fixture (T-072)."""

    def test_pinned_numbers(self):
        h, runs, probs = ledger.load_ledger(FIXTURE, agents=AGENTS, office="ai-office")
        self.assertEqual(probs, [])
        t = ledger.totals(runs)
        self.assertEqual((t["session"]["runs"], t["session"]["not_reported"], t["session"]["tokens"]), (7, 1, 10_500))
        self.assertEqual((t["shared"]["tokens"], t["shared"]["runs"]), (4_500, 2))      # the 2-task run and the chat run
        self.assertEqual(t["tasks"]["T-902"]["solo_tokens"], 3_000)
        h, evs, probs = events.parse_log(ledger.to_event_log(h, runs), agents=AGENTS, stages={"todo"})
        self.assertEqual((probs, len(evs), sum(e["total"] or 0 for e in evs)), ([], 6, 10_000))   # chat run's 500 is not an event


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


def main_line(window=1, **k):
    d = {"kind": "main_session", "window": window, "date": "2026-11-26", "source": "explain-usage skill", "since": "last context summary",
         "requests": 103, "input": 250, "cache_write": 211583, "cache_read": 26678886, "output": 52012}
    d.update(k)
    return json.dumps(d)


class MainSession(unittest.TestCase):
    """kind:'main_session' lines (T-070): their own source, never in run totals, the invariant or the event log."""

    def test_valid_line_is_kept_apart_and_runs_are_unchanged(self):
        h, runs, main, probs = ledger.parse_ledger_full("\n".join([HDR, run_line(1), main_line(), run_line(2)]), agents=AGENTS)
        self.assertEqual(probs, [])
        self.assertEqual([r["n"] for r in runs], [1, 2])
        self.assertEqual(len(main), 1)
        t = ledger.totals(runs)
        self.assertEqual(t["session"]["tokens"], 20)
        self.assertEqual(sum(a["tokens"] for a in t["agents"].values()), t["session"]["tokens"])
        self.assertEqual(sum(a["tokens"] for a in t["sprints"].values()), t["session"]["tokens"])
        self.assertEqual(len(parse(run_line(1), main_line())[1]), 1)      # the 3-tuple wrapper still returns runs only
        self.assertEqual(errs(parse(run_line(1), main_line())[2]), [])
        self.assertNotIn("main", ledger.to_event_log(h, runs))
        self.assertEqual(ledger.to_event_log(h, runs), ledger.to_event_log(h, [r for r in runs]))

    def test_event_log_ignores_main_lines(self):
        h, runs, main, _ = ledger.parse_ledger_full("\n".join([HDR, run_line(1), main_line()]), agents=AGENTS)
        evs = ledger.to_event_log(h, runs).splitlines()
        self.assertEqual(len(evs), 2)                                       # header + one run
        self.assertNotIn("26678886", "".join(evs))

    def test_errors(self):
        cases = {
            "tokens": main_line(tokens=5),
            "missing": json.dumps({k: v for k, v in json.loads(main_line()).items() if k != "cache_read"}),
            "type": main_line(output="9"),
            "window": main_line(window=0),
            "kind": json.dumps({"kind": "other", "window": 1}),
            "n": main_line(n=3),
        }
        for name, line in cases.items():
            h, runs, main, probs = ledger.parse_ledger_full(HDR + "\n" + line, agents=AGENTS)
            self.assertEqual(main, [], name)
            self.assertEqual(len(errs(probs)), 1, name)
        self.assertIn("no tokens total", errs(parse(main_line(tokens=5))[2])[0].message)

    def test_decrease_in_window_and_window_decrease(self):
        _, _, main, probs = ledger.parse_ledger_full("\n".join([HDR, main_line(1), main_line(1, output=1)]), agents=AGENTS)
        self.assertEqual(len(main), 1)
        self.assertIn("new window", errs(probs)[0].message)
        _, _, main, probs = ledger.parse_ledger_full("\n".join([HDR, main_line(2), main_line(1)]), agents=AGENTS)
        self.assertEqual(len(main), 1)
        self.assertIn("window must not decrease", errs(probs)[0].message)
        # a lower figure is fine in a new window
        _, _, main, probs = ledger.parse_ledger_full("\n".join([HDR, main_line(1), main_line(2, output=1)]), agents=AGENTS)
        self.assertEqual((len(main), probs), (2, []))

    def test_last_reading_per_window_counts_and_windows_add(self):
        lines = [main_line(1, input=1, cache_write=2, cache_read=3, output=4, requests=10),
                 main_line(1, input=10, cache_write=20, cache_read=30, output=40, requests=20),
                 main_line(2, input=100, cache_write=200, cache_read=300, output=400, requests=None, since="summary 2")]
        _, _, main, probs = ledger.parse_ledger_full("\n".join([HDR] + lines), agents=AGENTS)
        self.assertEqual(probs, [])
        m = ledger.main_totals(main)
        self.assertEqual((m["input"], m["cache_write"], m["cache_read"], m["output"], m["requests"]), (110, 220, 330, 440, 20))
        self.assertEqual((m["windows"], m["readings"], m["since"]), (2, 3, "summary 2"))
        self.assertIsNone(ledger.main_totals([]))

    def test_data_rule_hit_in_since_is_rejected(self):
        h, runs, main, probs = ledger.parse_ledger_full(HDR + "\n" + main_line(since="mail someone@example.com"), agents=AGENTS)
        self.assertEqual(main, [])
        self.assertEqual(len(errs(probs)), 1)
        self.assertNotIn("someone@", errs(probs)[0].message)

    def test_cli_accepts_a_file_with_a_main_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "session_TEST0001.jsonl"
            f.write_text(HDR + "\n" + run_line(1) + "\n" + main_line() + "\n", encoding="utf-8")
            self.assertEqual(run("ledger", "ai-office", str(f))[0], 0)
            f.write_text(HDR + "\n" + main_line(tokens=1) + "\n", encoding="utf-8")
            self.assertEqual(run("ledger", "ai-office", str(f))[0], 1)


class Cli(unittest.TestCase):
    LEDGER = REAL

    def test_exit_codes(self):
        code, out, _ = run("ledger", "ai-office", str(self.LEDGER))   # live: only what stays true as honest lines are appended
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 0 warnings", out)
        self.assertRegex(out, r"\(\d+ not reported\)")
        code, out, _ = run("ledger", "ai-office", str(FIXTURE))      # exact numbers come from the fixture
        self.assertEqual(code, 0)
        self.assertIn("7 runs kept (1 not reported), 10,500 tokens", out)
        code, out, _ = run("ledger", "ai-office", str(EDGE))
        self.assertEqual(code, 1)
        self.assertNotIn("someone@", out)
        self.assertEqual(run("ledger", "ai-office", "/nonexistent.jsonl")[0], 2)
        self.assertEqual(run("ledger", "ai-office")[0], 2)   # usage error


class CliAppended(Cli):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.LEDGER = appended_copy(REAL, cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
