"""T-069: the usage sync plan (engine/runtime/usage_sync.py). Fixtures are invented (SYNTHETIC), no realistic ids or numbers."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.runtime import budgets as budgets_mod, chat, events, ledger, loader, providers, usage_sync as U
from tests._helpers import REPO

OFFICE = REPO / "offices/ai-office"
FIX = REPO / "tests/fixtures/session_FIXTURE069.jsonl"
AGENTS = {"pmo", "pm", "architect", "engineer", "reviewer", "compliance", "curator", "designer"}
RULES = [{"path": "chat", "read": "owner", "write": "owner"}, {"path": "usage", "read": "owner", "write": "owner"}]
NOW = "2026-11-27T01:00:00Z"
LATER = "2026-11-27T02:00:00Z"


def load(path=FIX):
    h, runs, main, probs = ledger.load_ledger_full(path, agents=AGENTS, office="ai-office", forbidden=())
    assert h is not None and not [p for p in probs if p.level == "error"], probs
    return h, runs, main


def budgets():
    cat, _ = providers.load_providers(OFFICE)
    b, probs = budgets_mod.load_budgets(OFFICE, agents=AGENTS, providers=set(cat))
    assert not probs
    return b


def run_plan(items=(), runs=None, now=NOW, bud=None, **kw):
    h, r, m = load()
    kw.setdefault("rules", RULES)
    return U.plan(h, r if runs is None else runs, m, budgets() if bud is None else bud, list(items), now=now, **kw)


def apply(actions, db):
    """A stand-in for Janice's db_write calls: honours ifVersion, so a wrong version fails the test."""
    for a in actions:
        cur = db.get(a["path"])
        if "ifVersion" in a:
            assert cur is not None and cur[1] == a["ifVersion"], a["path"]
        else:
            assert a["op"] == "set" and cur is None, a["path"]
        if a["op"] == "set":
            db[a["path"]] = (a["doc"], (cur[1] + 1) if cur else 1)
        else:
            del db[a["path"]]
    return db


def items(db):
    return [{"path": p, "data": d, "version": v} for p, (d, v) in db.items()]


class Plan(unittest.TestCase):
    def test_empty_db_gives_chunk_budgets_and_meta_in_that_order(self):
        out = run_plan()
        self.assertEqual([a["path"] for a in out["actions"]],
                         ["usage/office/chunks/session_FIXTURE069-001", "usage/budgets", "usage/office"])
        self.assertTrue(all("ifVersion" not in a for a in out["actions"]))
        rep = out["report"]
        self.assertEqual((rep["docs"], rep["chunks"], rep["writes"], rep["in_sync"], rep["runs"]), (3, 1, 3, False, 7))
        self.assertGreater(rep["largest_doc_bytes"], 0)

    def test_meta_totals_equal_the_ledger_and_main_totals(self):
        h, runs, main = load()
        meta = next(a["doc"] for a in run_plan()["actions"] if a["path"] == "usage/office")
        self.assertEqual(meta["totals"], json.loads(json.dumps(ledger.totals(runs))))
        self.assertEqual(meta["main"], ledger.main_totals(main))
        self.assertEqual((meta["main"]["output"], meta["runs"], meta["last_n"], meta["synced_at"], meta["by"]), (40, 7, 7, NOW, "pmo"))
        self.assertEqual(set(meta["header"]), {"provider", "not_reported", "covers"})   # never source or recorded_by (U2)
        chunk = next(a["doc"] for a in run_plan()["actions"] if "chunks" in a["path"])
        self.assertEqual(chunk["runs"], runs)                                  # null tokens kept
        self.assertIsNone(chunk["runs"][4]["tokens"])
        self.assertEqual(meta["chunks"][0]["sha256"], U.sha(chunk))

    def test_replanning_from_the_written_docs_gives_zero_writes_and_the_db_does_not_change(self):
        db = apply(run_plan()["actions"], {})
        before = json.dumps(db, sort_keys=True)
        out = run_plan(items(db), now=LATER)
        self.assertEqual((out["actions"], out["report"]["writes"], out["report"]["in_sync"]), ([], 0, True))
        self.assertEqual(out["report"]["synced_at"], NOW)                       # synced_at moves only on a sync that writes
        self.assertEqual(json.dumps(apply(out["actions"], db), sort_keys=True), before)

    def test_an_appended_run_rewrites_the_last_chunk_and_meta_only(self):
        db = apply(run_plan()["actions"], {})
        h, runs, main = load()
        more = runs + [{"n": 8, "sprint": 2, "agent": "pm", "tasks": ["T-903"], "step": "spec", "tokens": 70, "tool_uses": 1, "duration_ms": 5}]
        out = run_plan(items(db), runs=more, now=LATER)
        self.assertEqual([a["path"] for a in out["actions"]], ["usage/office/chunks/session_FIXTURE069-001", "usage/office"])
        self.assertTrue(all("ifVersion" in a for a in out["actions"]))
        db = apply(out["actions"], db)
        self.assertEqual(db["usage/office"][0]["runs"], 8)
        self.assertEqual(db["usage/office"][0]["synced_at"], LATER)
        self.assertEqual(run_plan(items(db), runs=more, now=LATER)["actions"], [])

    def test_a_budgets_change_gives_budgets_and_meta(self):
        db = apply(run_plan()["actions"], {})
        b = json.loads(json.dumps(budgets()))
        b["providers"]["claude-code"]["tokens"] += 1
        out = run_plan(items(db), bud=b, now=LATER)
        self.assertEqual([a["path"] for a in out["actions"]], ["usage/budgets", "usage/office"])
        meta = out["actions"][-1]["doc"]
        self.assertEqual(meta["budgets_sha256"], U.sha(b))

    def test_chunks_close_before_the_next_run_passes_the_byte_limit(self):
        h, runs, main = load()
        long = [dict(r, note="x" * 200) if r["n"] != 6 else r for r in runs]   # a chat run keeps its pointer note
        long = [r for r in long if r["n"] != 6]
        out = run_plan(runs=long, chunk_bytes=900)
        chunks = [a["doc"] for a in out["actions"] if "chunks" in a["path"]]
        self.assertGreater(len(chunks), 2)
        self.assertEqual([n for c in chunks for n in [r["n"] for r in c["runs"]]], [r["n"] for r in long])   # file order, nothing lost
        for c in chunks:
            self.assertLessEqual(U.size(c), 900)
            self.assertEqual((c["first_n"], c["last_n"]), (c["runs"][0]["n"], c["runs"][-1]["n"]))
        meta = out["actions"][-1]["doc"]
        self.assertEqual([c["last_n"] for c in meta["chunks"]], [c["last_n"] for c in chunks])
        self.assertEqual(out["report"]["docs"], 2 + len(chunks))

    def test_default_limit_is_half_the_doc_limit(self):
        self.assertEqual((U.CHUNK_BYTES * 2, U.MAX_DOC, U.MAX_DOCS), (U.MAX_DOC, 262144, 25000))


class Refusals(unittest.TestCase):
    def refused(self, **kw):
        with self.assertRaises(U.Refused) as cm:
            run_plan(**kw)
        return str(cm.exception), cm.exception.report

    def test_over_the_doc_size_limit_writes_nothing_and_reports_sizes(self):
        msg, rep = self.refused(max_doc=1000)
        self.assertIn("over the 1000 byte doc limit", msg)
        self.assertGreater(rep["largest_doc_bytes"], 1000)
        self.assertIn("docs", rep)

    def test_over_25000_docs_via_other_docs(self):
        msg, rep = self.refused(other_docs=24998)
        self.assertIn("25000 doc limit", msg)
        self.assertEqual(rep["docs"], 3)
        run_plan(other_docs=24997)   # exactly 25,000 is allowed

    def test_unknown_run_field_is_refused(self):   # U2
        h, runs, main = load()
        bad = [dict(runs[0], extra="x")] + runs[1:]
        msg, _ = self.refused(runs=bad)
        self.assertIn("allowlist", msg)
        self.assertNotIn("'x'", msg)

    def test_rules_missing_below_owner_or_wide(self):   # U3
        for rules in (None, [], [RULES[0]], [RULES[1]],
                      [RULES[0], {"path": "usage", "read": "view", "write": "owner"}],
                      [RULES[0], {"path": "usage", "read": "owner", "write": "interact"}],
                      RULES + [{"path": "usage/office", "read": "view", "write": "owner"}],
                      RULES + [{"path": "", "read": "view", "write": "owner"}],
                      RULES + [{"path": "*", "read": "owner", "write": "view"}],
                      [{"path": "chat", "read": "view", "write": "owner"}, RULES[1]]):
            self.refused(rules=rules)
        run_plan(rules=RULES + [{"path": "other", "read": "view", "write": "owner"}])

    def test_rules_problem_takes_a_path_and_the_chat_default_is_unchanged(self):
        self.assertIsNone(chat.rules_problem(RULES))
        self.assertIsNone(chat.rules_problem(RULES, "usage"))
        self.assertEqual(chat.rules_problem([RULES[1]]), "rules: need exactly one rule for path chat")
        self.assertEqual(chat.rules_problem([RULES[0]], "usage"), "rules: need exactly one rule for path usage")
        self.assertEqual(chat.rules_problem([{"path": "chat", "read": "view", "write": "owner"}]), "rules: chat must be read owner and write owner")

    def test_bad_other_docs(self):
        self.refused(other_docs=-1)
        self.refused(other_docs="3")


class Scan(unittest.TestCase):
    """U1/U7: one scan test on invented data. Each value is built from parts so no realistic number sits in the source."""

    def test_every_string_of_every_doc_is_scanned_and_only_the_kind_is_named(self):
        h, runs, main = load()
        digits = "".join(["0812", "3456", "7890"])
        for field, val, kind in (("run note", "call " + digits, "run of 10+ digits"), ("run note", "mail a" + "@" + "b.example", "email address"),
                                 ("run note", "token: " + "z9" * 8, "secret-like token"), ("run note", "tok " + "Ab1" * 12, "secret-like token")):
            runs2 = [dict(runs[0], note=val)] + runs[1:]
            with self.assertRaises(U.Refused) as cm:
                run_plan(runs=runs2)
            msg = str(cm.exception)
            self.assertIn(kind, msg, val)
            self.assertNotIn(val, msg)
            self.assertNotIn(digits, msg)
        # header covers, budgets set_by and note, and a forbidden term
        h2 = dict(h, covers="reach me " + digits)
        with self.assertRaises(U.Refused) as cm:
            U.plan(h2, runs, main, budgets(), [], rules=RULES, now=NOW)
        self.assertIn("run of 10+ digits", str(cm.exception))
        b = json.loads(json.dumps(budgets()))
        b["providers"]["claude-code"]["set_by"] = "Merwyn " + digits
        with self.assertRaises(U.Refused) as cm:
            run_plan(bud=b)
        self.assertIn("usage/budgets", str(cm.exception))
        with self.assertRaises(U.Refused) as cm:
            run_plan(runs=[dict(runs[0], note="see the acme-ledger repo")] + runs[1:], forbidden=("acme-ledger",))
        self.assertIn("forbidden term", str(cm.exception))
        self.assertNotIn("acme-ledger", str(cm.exception))

    def test_a_clean_ledger_with_a_session_id_of_32_characters_passes(self):
        # a real session id is 32 characters and would trip the long-token rule; the validated id itself is exempt (Build notes)
        h, runs, main = load()
        sid = "session_" + "Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8"
        out = U.plan(dict(h, session=sid), runs, main, budgets(), [], rules=RULES, now=NOW)
        self.assertEqual(out["report"]["writes"], 3)
        with self.assertRaises(U.Refused):   # but the same text anywhere else is still a hit
            U.plan(h, [dict(runs[0], note=sid)] + runs[1:], main, budgets(), [], rules=RULES, now=NOW)

    def test_u1a_a_session_value_that_fails_the_pattern_is_not_exempt(self):
        bad = "session_Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8-Qr9St0U"   # 40 chars with a hyphen: not SESSION_RE
        self.assertEqual(len(bad), 40)
        self.assertIn("secret-like token", U.scan_doc("p", {"session": bad}, (), bad))   # equal to the header value, still refused

    def test_the_exemption_needs_the_value_to_equal_the_header_session(self):
        sid = "session_" + "Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8"
        self.assertIsNone(U.scan_doc("p", {"session": sid}, (), sid))
        self.assertIn("secret-like token", U.scan_doc("p", {"session": sid[:-1] + "9"}, (), sid))   # valid-looking id, not the header's


class Orphans(unittest.TestCase):
    def test_a_chunk_the_repo_no_longer_has_is_reported_and_deleted_with_its_version(self):   # U6, U7
        db = apply(run_plan()["actions"], {})
        db["usage/office/chunks/session_OLDSESSION-001"] = ({"v": 1, "session": "session_OLDSESSION", "k": 1, "first_n": 1, "last_n": 1, "runs": []}, 4)
        db["usage/stray"] = ({"x": 1}, 1)
        out = run_plan(items(db), now=LATER)
        self.assertEqual(out["report"]["orphans"], ["usage/office/chunks/session_OLDSESSION-001"])
        self.assertEqual(out["report"]["unknown"], ["usage/stray"])
        self.assertEqual(out["actions"], [{"op": "delete", "path": "usage/office/chunks/session_OLDSESSION-001", "ifVersion": 4}])
        self.assertEqual((out["report"]["deletes"], out["report"]["in_sync"]), (1, False))
        db = apply(out["actions"], db)
        self.assertNotIn("usage/office/chunks/session_OLDSESSION-001", db)
        self.assertEqual(run_plan(items(db), now=LATER)["report"]["orphans"], [])

    def test_a_session_change_overwrites_meta_then_deletes_the_old_chunks(self):
        h, runs, main = load()
        db = apply(U.plan(dict(h, session="session_OLDSESSION"), runs, main, budgets(), [], rules=RULES, now=NOW)["actions"], {})
        out = run_plan(items(db), now=LATER)
        ops = [(a["op"], a["path"]) for a in out["actions"]]
        self.assertEqual(ops[-1], ("delete", "usage/office/chunks/session_OLDSESSION-001"))
        self.assertLess(ops.index(("set", "usage/office")), ops.index(ops[-1]))   # meta first: the page never points at a deleted chunk

    def test_no_budgets_file_deletes_the_budgets_doc(self):
        db = apply(run_plan()["actions"], {})
        h, runs, main = load()
        out = U.plan(h, runs, main, None, items(db), rules=RULES, now=LATER)
        self.assertEqual(out["report"]["orphans"], ["usage/budgets"])
        self.assertEqual([a["op"] for a in out["actions"]], ["set", "delete"])
        self.assertIsNone(out["actions"][0]["doc"]["budgets_sha256"])


class Cli(unittest.TestCase):
    def cli(self, stdin, ledger_path=FIX):
        r = subprocess.run([sys.executable, "-m", "engine.runtime", "usage", "plan", "ai-office", "--ledger", str(ledger_path), "--now", NOW],
                           input=stdin, capture_output=True, text=True, cwd=REPO, timeout=60)
        return r.returncode, r.stdout, r.stderr

    def test_plan_prints_actions_and_a_report(self):
        code, out, err = self.cli(json.dumps({"rules": RULES, "docs": [], "other_docs": 2}))
        self.assertEqual(code, 0, err)
        d = json.loads(out)
        self.assertEqual((len(d["actions"]), d["report"]["docs"], d["report"]["other_docs"]), (3, 3, 2))

    def test_refusal_exits_1_with_no_actions_and_still_reports_docs(self):
        code, out, err = self.cli(json.dumps({"rules": [RULES[0]], "docs": []}))
        self.assertEqual(code, 1)
        d = json.loads(out)
        self.assertEqual(d["actions"], [])
        self.assertIn("usage", d["error"])
        self.assertIn("docs", d["report"])

    def test_bad_stdin_and_bad_ledger(self):
        self.assertEqual(self.cli("not json")[0], 1)
        self.assertEqual(self.cli("[]")[0], 1)
        self.assertEqual(self.cli("{}")[0], 1)
        self.assertEqual(self.cli("{}", "/nonexistent.jsonl")[0], 2)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / FIX.name
            bad.write_text(FIX.read_text() + '{"n":9,"sprint":1,"agent":"pm","tasks":["T-901"],"step":"x","tokens":1,"tool_uses":1,"duration_ms":1,"note":"a' + '@b.example"}\n')
            code, out, err = self.cli(json.dumps({"rules": RULES, "docs": []}), bad)
            self.assertEqual(code, 1)
            self.assertNotIn("b.example", out + err)

    def test_the_real_ledger_plans_without_a_scan_hit(self):
        live = REPO / "offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl"
        code, out, err = self.cli(json.dumps({"rules": RULES, "docs": []}), live)
        self.assertEqual(code, 0, err)
        rep = json.loads(out)["report"]
        self.assertLess(rep["largest_doc_bytes"], U.CHUNK_BYTES)
        self.assertEqual(rep["chunks"], 1)

    def test_no_output_flag_and_the_plan_is_not_a_repo_file(self):
        text = (REPO / "engine/runtime/usage_sync.py").read_text()
        self.assertNotIn("open(", text)
        self.assertNotIn("write_text", text)


if __name__ == "__main__":
    unittest.main()
