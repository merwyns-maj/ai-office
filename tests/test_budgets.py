import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import office_app  # noqa: E402

from engine.runtime import budgets, events, ledger, miniyaml, providers  # noqa: E402
from tests._helpers import REPO  # noqa: E402
from tests.test_ledger import AGENTS, errs, parse, run_line  # noqa: E402

OFFICE = REPO / "offices/ai-office"
LEDGER = REPO / "offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl"
PROV = {"claude-code", "claude-sdk", "anthropic-api", "openai", "deepseek"}
WHO = {"set_by": "Merwyn", "set_on": "2026-11-26"}


def good():
    return {"period": "session", "main_session": "pmo", "providers": {
        "claude-code": dict(tokens=1000, note="n", agents={"engineer": dict(share=60, **WHO), "pm": dict(share=40, **WHO)}, **WHO)}}


def resolve(d, **kw):
    return budgets.resolve(d, agents=AGENTS, providers=PROV, **kw)


def probs(mutate):
    d = good()
    mutate(d)
    r, p = resolve(d)
    assert r is None, "expected a problem"
    return " | ".join(p)


class Parsing(unittest.TestCase):
    def test_good_file_resolves_shares_to_tokens(self):
        r, p = resolve(good())
        self.assertEqual(p, [])
        cc = r["providers"]["claude-code"]
        self.assertEqual(cc["tokens"], 1000)
        self.assertEqual({k: v["tokens"] for k, v in cc["agents"].items()}, {"engineer": 600, "pm": 400})
        self.assertEqual(cc["agents"]["pm"]["set_by"], "Merwyn")
        self.assertEqual(r["main_session"], "pmo")
        self.assertFalse(r["synthetic"])
        self.assertTrue(resolve(good(), synthetic=True)[0]["synthetic"])

    def test_shares_use_largest_remainder_and_add_to_the_provider_total(self):
        for total in (1, 7, 100, 999_999, 5_000_001):
            for shares in ([33, 33, 34], [50, 25, 25], [1, 2, 97], [33.3, 33.3, 33.4]):
                got = budgets._split(total, shares)
                self.assertEqual(sum(got), total, (total, shares))
                self.assertTrue(all(abs(g - total * s / 100) < 1 for g, s in zip(got, shares)))
        self.assertEqual(budgets._split(10, [33, 33, 34]), [3, 3, 4])
        self.assertEqual(budgets._split(5_000_000, [43, 30, 13, 6, 5, 2, 1]), [2_150_000, 1_500_000, 650_000, 300_000, 250_000, 100_000, 50_000])

    def test_amounts_instead_of_shares(self):
        d = good()
        d["providers"]["claude-code"]["agents"] = {"engineer": dict(tokens=300, **WHO), "pm": dict(tokens=900, **WHO)}
        r, p = resolve(d)
        self.assertEqual(p, [])   # amounts may exceed the provider budget: that is the owner's call
        self.assertEqual(r["providers"]["claude-code"]["agents"]["pm"]["tokens"], 900)

    def test_provider_without_a_budget_is_allowed_and_carries_none(self):
        d = good()
        del d["providers"]["claude-code"]["tokens"], d["providers"]["claude-code"]["agents"], d["providers"]["claude-code"]["set_by"], d["providers"]["claude-code"]["set_on"]
        r, p = resolve(d)
        self.assertEqual(p, [])
        self.assertNotIn("tokens", r["providers"]["claude-code"])   # the page says "budget not set", it never fills a number in

    def test_shares_must_add_to_100(self):
        self.assertIn("add to 99, must be 100", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(share=39)))
        self.assertIn("add to 101", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(share=41)))

    def test_no_negatives_and_types(self):
        self.assertIn("no negatives", probs(lambda d: d["providers"]["claude-code"].update(tokens=-5)))
        self.assertIn("no negatives", probs(lambda d: d["providers"]["claude-code"].update(tokens=0)))
        self.assertIn("no negatives", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(share=-1)))
        self.assertIn("share must be", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(share=101)))
        self.assertIn("share must be", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(share=True)))
        self.assertIn("tokens must be", probs(lambda d: d["providers"]["claude-code"].update(tokens=1.5)))
        self.assertIn("tokens must be", probs(lambda d: d["providers"]["claude-code"].update(tokens="5")))
        d = good()
        d["providers"]["claude-code"]["agents"] = {"engineer": dict(tokens=-1, **WHO)}
        self.assertIn("no negatives", " ".join(resolve(d)[1]))

    def test_every_value_carries_who_and_when(self):
        self.assertIn("set_by is required", probs(lambda d: d["providers"]["claude-code"].pop("set_by")))
        self.assertIn("set_on is required", probs(lambda d: d["providers"]["claude-code"].update(set_on="26 Nov")))
        self.assertIn("set_on is required", probs(lambda d: d["providers"]["claude-code"].update(set_on="2026-02-30")))
        self.assertIn("set_by is required", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].pop("set_by")))
        self.assertIn("set_on is required", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].pop("set_on")))

    def test_ids_period_mixes_and_unknown_keys(self):
        self.assertIn("not an id in providers.yaml", probs(lambda d: d["providers"].update({"mystery": dict(tokens=5, **WHO)})))
        self.assertIn("not an agent id", probs(lambda d: d["providers"]["claude-code"]["agents"].update({"zzz": dict(share=0, **WHO)})))
        self.assertIn("main_session must be an agent id", probs(lambda d: d.update(main_session="zzz")))
        self.assertIn("period must be", probs(lambda d: d.update(period="month")))
        self.assertIn("period must be", probs(lambda d: d.pop("period")))
        self.assertIn("all shares or all amounts", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(share=None) or d["providers"]["claude-code"]["agents"].update({"pm": dict(tokens=5, **WHO)})))
        self.assertIn("exactly one of share or tokens", probs(lambda d: d["providers"]["claude-code"]["agents"]["pm"].update(tokens=5)))
        self.assertIn("unknown key", probs(lambda d: d.update(extra=1)))
        self.assertIn("unknown key", probs(lambda d: d["providers"]["claude-code"].update(limit=1)))
        self.assertIn("need the provider tokens budget", probs(lambda d: d["providers"]["claude-code"].pop("tokens")))
        self.assertIn("at least one provider", probs(lambda d: d.update(providers={})))
        self.assertIn("must be a map", " ".join(budgets.resolve([], agents=AGENTS, providers=PROV)[1]))

    def test_no_file_is_not_an_error_and_a_broken_file_is(self):
        self.assertEqual(budgets.load_budgets("/nonexistent-office", agents=AGENTS, providers=PROV), (None, []))
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / budgets.FILE).write_text("period: [", encoding="utf-8")
            r, p = budgets.load_budgets(tmp, agents=AGENTS, providers=PROV)
            self.assertIsNone(r)
            self.assertEqual(len(p), 1)


class Thresholds(unittest.TestCase):
    """T-062: warn_at and alert_at, 0 < warn_at < alert_at <= 100, with who and when."""
    T = dict(warn_at=70, alert_at=90, set_by="Merwyn", set_on="2026-11-26")

    def with_t(self, **kw):
        d = good()
        d["thresholds"] = dict(self.T, **kw)
        return d

    def test_defaults_when_absent(self):
        r, p = resolve(good())
        self.assertEqual(p, [])
        self.assertEqual(r["thresholds"], {"warn_at": 70, "alert_at": 90, "set_by": "default", "set_on": None})

    def test_valid_pair_is_kept_with_who_and_when(self):
        r, p = resolve(self.with_t(warn_at=50, alert_at=100))
        self.assertEqual(p, [])
        self.assertEqual(r["thresholds"], dict(self.T, warn_at=50, alert_at=100))
        self.assertEqual(resolve(self.with_t(warn_at=0.5, alert_at=99.5))[1], [])

    def test_bad_values_are_rejected(self):
        for kw in (dict(warn_at=0), dict(warn_at=-1), dict(warn_at=90), dict(warn_at=95), dict(alert_at=101), dict(alert_at=70),
                   dict(warn_at="70"), dict(alert_at=None), dict(warn_at=True), dict(alert_at=[90])):
            r, p = resolve(self.with_t(**kw))
            self.assertIsNone(r, kw)
            self.assertIn("0 < warn_at < alert_at <= 100", " ".join(p), kw)

    def test_who_when_and_keys_are_required(self):
        d = self.with_t(); del d["thresholds"]["set_by"]
        self.assertIn("set_by is required", " ".join(resolve(d)[1]))
        self.assertIn("set_on is required", " ".join(resolve(self.with_t(set_on="soon"))[1]))
        self.assertIn("unknown key", " ".join(resolve(self.with_t(extra=1))[1]))
        d = good(); d["thresholds"] = 70
        self.assertIn("thresholds: must be a map", " ".join(resolve(d)[1]))

    def test_shipped_file_carries_70_and_90_set_by_janice(self):
        cat, _ = providers.load_providers(OFFICE)
        ids = {a["id"] for a in miniyaml.loads((OFFICE / "org.yaml").read_text(encoding="utf-8"))["agents"]}
        r, p = budgets.load_budgets(OFFICE, agents=ids, providers=set(cat))
        self.assertEqual(p, [])
        self.assertEqual(r["thresholds"], {"warn_at": 70, "alert_at": 90, "set_by": "Janice (pmo)", "set_on": "2026-11-26"})


class ShippedFile(unittest.TestCase):
    def setUp(self):
        cat, _ = providers.load_providers(OFFICE)
        self.cat = cat
        self.ids = {a["id"] for a in miniyaml.loads((OFFICE / "org.yaml").read_text(encoding="utf-8"))["agents"]}
        self.r, self.p = budgets.load_budgets(OFFICE, agents=self.ids, providers=set(cat))

    def test_valid_and_dated(self):
        self.assertEqual(self.p, [])
        cc = self.r["providers"]["claude-code"]
        self.assertIsInstance(cc["tokens"], int)
        self.assertGreater(cc["tokens"], 0)
        self.assertTrue(cc["set_by"])
        import datetime
        datetime.date.fromisoformat(cc["set_on"])
        self.assertEqual(sum(v["tokens"] for v in cc["agents"].values()), cc["tokens"])
        self.assertEqual(self.r["main_session"], "pmo")
        self.assertNotIn("pmo", cc["agents"])   # the main session has no share: its tokens are not reported

    def test_starting_use_of_the_first_48_runs_is_76_percent_of_the_original_5m(self):
        _, runs, _ = ledger.load_ledger(LEDGER, agents=self.ids, office="ai-office", forbidden=events.forbidden_terms(REPO))
        # the starting values were set from the first 48 runs (T-060); later runs are appended as they finish (T-061)
        used = sum(r["tokens"] or 0 for r in runs if r["n"] <= 48)
        self.assertEqual(used, 3_813_702)
        self.assertEqual(round(100 * used / 5_000_000), 76)


class Page(unittest.TestCase):
    def test_recorded_page_carries_the_resolved_budgets(self):
        data, probs_ = office_app.build_data(OFFICE, None, LEDGER)
        self.assertEqual(probs_, [])
        cat, _ = providers.load_providers(OFFICE)
        ids = {a["id"] for a in miniyaml.loads((OFFICE / "org.yaml").read_text(encoding="utf-8"))["agents"]}
        want, _ = budgets.load_budgets(OFFICE, agents=ids, providers=set(cat))
        self.assertEqual(data["budgets"]["providers"]["claude-code"]["tokens"], want["providers"]["claude-code"]["tokens"])
        self.assertFalse(data["budgets"]["synthetic"])

    def test_synthetic_page_has_its_own_marked_budgets_and_the_header_does_not_repeat_them(self):
        data, _ = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE)
        self.assertTrue(data["budgets"]["synthetic"])
        self.assertNotIn("budgets", data["log"])
        self.assertNotIn("deepseek", data["budgets"]["providers"])   # used in the demo, no budget: shows "budget not set"
        self.assertNotEqual(data["budgets"], office_app.build_data(OFFICE, None, LEDGER)[0]["budgets"])

    def test_log_without_budgets_gives_null_and_the_ledger_page_without_a_file_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "u.jsonl"
            lines = office_app.DEFAULT_FIXTURE.read_text(encoding="utf-8").splitlines()
            h = json.loads(lines[0])
            del h["budgets"]
            log.write_text("\n".join([json.dumps(h)] + lines[1:]) + "\n", encoding="utf-8")
            self.assertIsNone(office_app.build_data(OFFICE, log)[0]["budgets"])
            root = Path(tmp) / "offices" / "ai-office"
            shutil.copytree(OFFICE, root, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(REPO / "base", Path(tmp) / "base")
            (Path(tmp) / "workspaces.yaml").write_text((REPO / "workspaces.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            (root / budgets.FILE).unlink()
            self.assertIsNone(office_app.build_data(root, None, LEDGER)[0]["budgets"])

    def test_bad_budgets_fail_the_build_and_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "offices" / "ai-office"
            shutil.copytree(OFFICE, root, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(REPO / "base", Path(tmp) / "base")
            (Path(tmp) / "workspaces.yaml").write_text((REPO / "workspaces.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            f = root / budgets.FILE
            f.write_text(f.read_text(encoding="utf-8").replace("share: 43", "share: 44"), encoding="utf-8")
            with self.assertRaises(office_app.BuildError) as cm:
                office_app.build_data(root, None, LEDGER)
            self.assertIn("add to 101", str(cm.exception))
            out = Path(tmp) / "o.html"
            self.assertEqual(office_app.main([str(root), "--ledger", str(LEDGER), "--out", str(out)]), 1)
            self.assertFalse(out.exists())

    def test_bad_synthetic_budgets_fail_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "u.jsonl"
            lines = office_app.DEFAULT_FIXTURE.read_text(encoding="utf-8").splitlines()
            h = json.loads(lines[0])
            h["budgets"]["providers"]["openai"]["tokens"] = -3
            log.write_text("\n".join([json.dumps(h)] + lines[1:]) + "\n", encoding="utf-8")
            with self.assertRaises(office_app.BuildError):
                office_app.build_data(OFFICE, log)


class LedgerDate(unittest.TestCase):
    def test_date_is_optional_and_validated(self):
        _, runs, p = parse(run_line(1), run_line(2, date="2026-11-26"))
        self.assertEqual(errs(p), [])
        self.assertEqual(p, [])   # a known field: no "not defined" warning
        self.assertEqual(runs[1]["date"], "2026-11-26")
        for bad in ("26 Nov", "2026-13-01", "2026-02-30", "2026-1-1", 20261126, None, ""):
            _, runs, p = parse(run_line(1, date=bad))
            self.assertEqual(len(errs(p)), 1, bad)
            self.assertIn("date must be YYYY-MM-DD", errs(p)[0].message)
            self.assertEqual(runs, [])

    def test_recorded_page_is_unchanged_by_a_dated_line(self):
        _, runs, _ = parse(run_line(1, date="2026-11-26"))
        self.assertEqual(ledger.totals(runs)["session"]["tokens"], 10)


if __name__ == "__main__":
    unittest.main()
