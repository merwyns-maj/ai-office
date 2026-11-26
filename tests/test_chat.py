import json
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine.runtime import chat, events, ledger, loader
from tests._helpers import REPO

OFFICE = REPO / "offices/ai-office"
FIX = REPO / "tests/fixtures"
IDS = ["pmo", "pm", "architect", "engineer", "reviewer", "compliance", "curator", "designer"]
NOW = datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc)


def hmap():
    office, _ = loader.load_office(OFFICE)
    return chat.handles([a for a in office.org["agents"] if isinstance(a, dict)])


def ago(s):
    return (NOW - timedelta(seconds=s)).strftime("%Y-%m-%dT%H:%M:%SZ")


def ask(n, mentions=("architect",), status="new", at=None, text="please look at this", all_=False, in_reply_to=None, reply_id=None, created=None):
    rec = {a: {"status": status, "reply_id": reply_id, "at": at or ago(5), "by": "page"} for a in (IDS if all_ else (mentions or ["pmo"]))}
    return {"v": 1, "kind": "ask", "id": f"m-aaaaaa{n:02d}-bbbb", "author": "merwyn", "author_uid": "u-test", "text": text,
            "created_at": created or ago(100 - n), "mentions": list(IDS if all_ else mentions), "all": all_, "unknown": [],
            "in_reply_to": in_reply_to, "recipients": rec}


def rep(a, agent, needs=False, n_created=50):
    return {"v": 1, "kind": "reply", "id": chat.reply_id(a["id"], agent), "reply_to": a["id"], "author": agent, "text": "ok",
            "created_at": ago(n_created), "needs_merwyn": needs, "question": "ok?" if needs else None, "task": None}


def build(parts):
    return "".join(p if isinstance(p, str) else p[1] * p[2] for p in parts)


class Mentions(unittest.TestCase):
    def test_shared_fixture(self):
        cases = json.loads((FIX / "chat-mentions.json").read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 40)
        h = hmap()
        for c in cases:
            m = chat.parse_mentions(c["text"], h)
            self.assertEqual((m.ids, m.all, m.unknown), (c["ids"], c["all"], c["unknown"]), c["text"])

    def test_route_defaults_to_pmo(self):
        h = hmap()
        self.assertEqual(chat.route(chat.parse_mentions("no mention", h)), ["pmo"])
        self.assertEqual(chat.route(chat.parse_mentions("@Bob only", h)), ["pmo"])
        self.assertEqual(chat.route(chat.parse_mentions("@Fang @Dinda", h)), ["architect", "designer"])
        self.assertEqual(chat.route(chat.parse_mentions("@all", h)), IDS)


class Scan(unittest.TestCase):
    def test_shared_fixture(self):
        cases = json.loads((FIX / "chat-scan.json").read_text(encoding="utf-8"))["cases"]
        for c in cases:
            self.assertEqual(chat.scan(build(c["parts"])), c["hit"], c["parts"])

    def test_forbidden_term_and_value_never_returned(self):
        self.assertEqual(chat.scan("talk about acme-corp", ("acme-corp",)), "forbidden term")
        secret = "a.b@example.test"
        self.assertNotIn("example", chat.scan(secret))

    def test_covers_events_kinds(self):
        for k in events.PATTERN_KINDS:
            self.assertIn(k, [c["hit"] for c in json.loads((FIX / "chat-scan.json").read_text(encoding="utf-8"))["cases"]])


class Schema(unittest.TestCase):
    def test_valid_ask_and_reply(self):
        a = ask(1)
        self.assertEqual(chat.validate(a, IDS), [])
        self.assertEqual(chat.validate(rep(a, "architect"), IDS), [])
        self.assertEqual(chat.validate(ask(2, mentions=(), all_=False), IDS), [])
        self.assertEqual(chat.validate(ask(3, all_=True), IDS), [])

    def test_problems_name_fields_not_text(self):
        a = ask(1, text="x" * 4001)
        self.assertEqual(chat.validate(a, IDS), ["text: length out of range"])
        b = ask(1)
        del b["recipients"]
        self.assertEqual(chat.validate(b, IDS), ["recipients: missing"])
        c = ask(1)
        c["extra"] = 1
        self.assertEqual(chat.validate(c, IDS), ["extra: not defined for a ask"])
        d = ask(1)
        d["recipients"]["engineer"] = d["recipients"]["architect"]
        self.assertEqual(chat.validate(d, IDS), ["recipients: do not match the routing of mentions and all"])
        e = ask(1)
        e["id"] = "bad id"
        self.assertEqual(chat.validate(e, IDS), ["id: bad pattern"])
        f = ask(1)
        f["author"] = "someone"
        self.assertIn("author: must be merwyn", chat.validate(f, IDS))
        g = ask(1)
        g["mentions"] = ["nobody"]
        self.assertIn("mentions: must be distinct agent ids", chat.validate(g, IDS))
        h = ask(1)
        h["recipients"]["architect"]["status"] = "bogus"
        self.assertEqual(chat.validate(h, IDS), ["recipients.architect.status: unknown status"])
        self.assertEqual(chat.validate({"kind": "x"}, IDS), ["kind: must be ask or reply"])
        r = rep(ask(1), "architect")
        r["id"] = "r-other"
        self.assertEqual(chat.validate(r, IDS), ["id: must be r-<ask id>-<agent id>"])
        r2 = rep(ask(1), "architect", needs=True)
        r2["question"] = None
        self.assertEqual(chat.validate(r2, IDS), ["question: required when needs_merwyn is true"])

    def test_transitions_allowed_and_rejected(self):
        ok = {("new", "picked"), ("picked", "replying"), ("picked", "new"), ("picked", "answered"), ("picked", "needs_merwyn"),
              ("replying", "answered"), ("replying", "needs_merwyn"), ("replying", "new"), ("needs_merwyn", "answered")}
        for a in chat.STATUSES:
            for b in chat.STATUSES:
                self.assertEqual(chat.can_move(a, b), (a, b) in ok, (a, b))
        self.assertFalse(chat.can_move("answered", "new"))
        self.assertFalse(chat.can_move("nope", "new"))

    def test_rules_check(self):
        self.assertIsNone(chat.rules_problem([{"path": "chat", "read": "owner", "write": "owner"}]))
        self.assertIsNotNone(chat.rules_problem([{"path": "chat", "read": "view", "write": "owner"}]))
        self.assertIsNotNone(chat.rules_problem([{"path": "chat", "read": "owner", "write": "interact"}]))
        self.assertIsNotNone(chat.rules_problem([]))
        self.assertIsNotNone(chat.rules_problem(None))
        self.assertIsNotNone(chat.rules_problem([{"path": "chat", "read": "owner", "write": "owner"}, {"path": "chat/office", "read": "view", "write": "owner"}]))
        own = {"path": "chat", "read": "owner", "write": "owner"}
        for wide in ({"path": "", "read": "view", "write": "owner"}, {"path": "/", "read": "owner", "write": "interact"}, {"path": "*", "read": "view", "write": "view"}):
            self.assertIsNotNone(chat.rules_problem([wide, own]), wide)
        self.assertIsNone(chat.rules_problem([{"path": "", "read": "owner", "write": "owner"}, own]))
        self.assertIsNone(chat.rules_problem([{"path": "other", "read": "view", "write": "owner"}, own]))


class Plan(unittest.TestCase):
    def plan(self, docs, **kw):
        return chat.plan(docs, NOW, IDS, **kw)

    def test_new_is_claimed_once_with_whole_recipients_map(self):
        a = ask(1, mentions=("architect", "designer"))
        acts, skipped = self.plan([a])
        self.assertEqual(skipped, [])
        self.assertEqual(len(acts), 1)
        x = acts[0]
        self.assertEqual((x["op"], x["agents"], x["path"]), ("claim", ["architect", "designer"], f"chat/office/messages/{a['id']}"))
        self.assertEqual({k: v["status"] for k, v in x["patch"]["recipients"].items()}, {"architect": "picked", "designer": "picked"})
        self.assertEqual(x["patch"]["recipients"]["architect"]["by"], "session")

    def test_ifversion_from_wrapper(self):
        a = ask(1)
        acts, _ = self.plan([{"id": a["id"], "data": a, "version": 7}])
        self.assertEqual(acts[0]["ifVersion"], 7)

    def test_picked_is_left_alone_until_lease_runs_out(self):
        self.assertEqual(self.plan([ask(1, status="picked", at=ago(60))])[0], [])
        acts, _ = self.plan([ask(1, status="replying", at=ago(1801))])
        self.assertEqual((acts[0]["op"], acts[0]["changes"][0]["to"]), ("reset", "new"))
        acts, _ = self.plan([ask(1, status="replying", at=ago(100))], lease_s=50)
        self.assertEqual(acts[0]["op"], "reset")

    def test_stale_lease_with_reply_is_repaired_not_reset(self):
        a = ask(1, status="replying", at=ago(4000))
        acts, _ = self.plan([a, rep(a, "architect")])
        self.assertEqual((acts[0]["op"], acts[0]["changes"][0]["to"]), ("repair", "answered"))
        self.assertEqual(acts[0]["patch"]["recipients"]["architect"]["reply_id"], chat.reply_id(a["id"], "architect"))
        acts, _ = self.plan([a, rep(a, "architect", needs=True)])
        self.assertEqual(acts[0]["changes"][0]["to"], "needs_merwyn")
        a2 = ask(1, status="replying", at=ago(10))   # a fresh lease with a reply doc is repaired too
        self.assertEqual(self.plan([a2, rep(a2, "architect")])[0][0]["op"], "repair")

    def test_close_by_followup_in_reply_to_or_mention(self):
        a = ask(1, status="needs_merwyn", reply_id="r-x")
        a["recipients"]["architect"]["reply_id"] = chat.reply_id(a["id"], "architect")
        self.assertEqual(self.plan([a])[0], [])
        f = ask(2, in_reply_to=chat.reply_id(a["id"], "architect"), status="picked")
        acts, _ = self.plan([a, f])
        self.assertEqual([x["op"] for x in acts], ["close"])
        self.assertEqual(acts[0]["ask"], a["id"])
        g = ask(3, mentions=("architect",), status="picked")
        self.assertEqual(self.plan([a, g])[0][0]["op"], "close")
        h = ask(4, mentions=("architect",), status="new")   # a follow-up that is still new does not close it yet; it is claimed
        self.assertEqual([x["op"] for x in self.plan([a, h])[0]], ["claim"])
        other = ask(5, mentions=("designer",), status="picked")
        self.assertEqual(self.plan([a, other])[0], [])

    def test_two_sessions_same_reply_id(self):
        a = ask(1, status="picked")
        p1, d1, _ = chat.reply(a, "architect", "one", False, None, None, NOW)
        p2, d2, _ = chat.reply(a, "architect", "two", False, None, None, NOW)
        self.assertEqual((p1, d1["id"]), (p2, d2["id"]))

    def test_invalid_docs_are_skipped_by_id_and_field(self):
        bad = ask(1, text="")
        acts, skipped = self.plan([bad, ask(2)])
        self.assertEqual(len(acts), 1)
        self.assertEqual(skipped, [f"{bad['id']}: text: length out of range"])

    def test_order_by_created_at_then_id_and_claims_first(self):
        old_stale = ask(1, status="replying", at=ago(9000), created=ago(500))
        late = ask(2, created=ago(30))
        early = ask(3, created=ago(60))
        acts, _ = self.plan([late, old_stale, early])
        self.assertEqual([x["op"] for x in acts], ["claim", "claim", "reset"])
        self.assertEqual([x["ask"] for x in acts[:2]], [early["id"], late["id"]])

    def test_scan_hit_ask_is_refused_and_never_claimed(self):
        bad = ask(1, text="my email is a.b@example.test")
        acts, _ = self.plan([bad])
        self.assertEqual([x["op"] for x in acts], ["post", "refuse"])
        post, refuse = acts
        self.assertEqual(post["doc"]["text"], chat.REFUSAL)
        self.assertEqual(refuse["patch"]["text"], chat.REMOVED)
        self.assertEqual({r["status"] for r in refuse["patch"]["recipients"].values()}, {"answered"})
        self.assertNotIn("example", json.dumps(acts))
        self.assertEqual(chat.validate(post["doc"], IDS), [])
        self.assertEqual(self.plan([dict(bad, text=chat.REMOVED, recipients={"architect": dict(bad["recipients"]["architect"], status="answered")})])[0], [])

    def test_all_recipients_get_claimed(self):
        acts, _ = self.plan([ask(1, all_=True)])
        self.assertEqual(sorted(acts[0]["agents"]), sorted(IDS))

    def test_answered_asks_produce_nothing(self):
        self.assertEqual(self.plan([ask(1, status="answered")])[0], [])


class Reply(unittest.TestCase):
    def test_deterministic_id_and_patch(self):
        a = ask(1, mentions=("architect", "designer"), status="replying")
        path, doc, patch = chat.reply(a, "architect", "fine", False, None, "T-063", NOW)
        self.assertEqual(path, f"chat/office/messages/r-{a['id']}-architect")
        self.assertEqual(chat.validate(doc, IDS), [])
        self.assertEqual(patch["recipients"]["architect"]["status"], "answered")
        self.assertEqual(patch["recipients"]["designer"]["status"], "replying")   # the whole map is kept
        _, doc2, patch2 = chat.reply(a, "designer", "q", True, "Which one?", None, NOW)
        self.assertEqual((doc2["needs_merwyn"], doc2["question"], patch2["recipients"]["designer"]["status"]), (True, "Which one?", "needs_merwyn"))

    def test_rejects_bad_input(self):
        a = ask(1, status="replying")
        for args in (("engineer", "x", False, None, None), ("architect", "", False, None, None), ("architect", "x", True, None, None),
                     ("architect", "x", False, None, "t-1"), ("architect", "x" * 8001, False, None, None)):
            with self.assertRaises(ValueError):
                chat.reply(a, *args[:4], args[4], NOW)
        with self.assertRaises(ValueError):
            chat.reply(ask(2, status="answered"), "architect", "x", False, None, None, NOW)
        with self.assertRaises(ValueError):
            chat.reply(ask(3, status="new"), "architect", "x", False, None, None, NOW)

    def test_status_step(self):
        a = ask(1, status="picked")
        _, patch = chat.set_status(a, "architect", "replying", NOW)
        self.assertEqual(patch["recipients"]["architect"]["status"], "replying")
        with self.assertRaises(ValueError):
            chat.set_status(ask(2), "architect", "replying", NOW)

    def test_pointer(self):
        self.assertEqual(chat.pointer("m-aaaaaa01-bbbb"), "chat message m-aaaaaa01-bbbb")


class Purge(unittest.TestCase):
    def test_deletes_old_answered_asks_and_their_replies_only(self):
        day = 86400
        old = ask(1, status="answered", created=ago(31 * day))
        old_open = ask(2, status="needs_merwyn", created=ago(40 * day))
        fresh = ask(3, status="answered", created=ago(29 * day))
        orphan = rep(ask(9), "architect", n_created=0)
        orphan["created_at"] = ago(35 * day)
        out = chat.purge([old, old_open, fresh, rep(old, "architect"), rep(fresh, "architect"), orphan], NOW)
        self.assertEqual({d["id"] for d in out}, {old["id"], chat.reply_id(old["id"], "architect"), orphan["id"]})
        self.assertTrue(all(d["op"] == "delete" and d["path"].startswith("chat/office/messages/") for d in out))

    def test_purge_carries_if_version_from_the_wrapper(self):
        day = 86400
        old = ask(1, status="answered", created=ago(31 * day))
        r = rep(old, "architect")
        out = chat.purge([{"id": old["id"], "data": old, "version": 7}, {"id": r["id"], "data": r, "version": 3}], NOW)
        self.assertEqual({d["id"]: d["ifVersion"] for d in out}, {old["id"]: 7, r["id"]: 3})
        self.assertIsNone(chat.purge([old], NOW)[0]["ifVersion"])


class LedgerChatRun(unittest.TestCase):
    HEADER = {"log": "agent-runs", "v": 1, "office": "ai-office", "session": "session_test0001", "source": "test", "recorded_by": "test", "date": "2026-11-26", "covers": "x", "not_reported": []}

    def run_line(self, **kw):
        r = {"n": 1, "sprint": 4, "agent": "pmo", "tasks": [], "step": "chat", "tokens": 100, "tool_uses": 1, "duration_ms": 10,
             "note": "chat message m-aaaaaa01-bbbb"}
        r.update(kw)
        return r

    def parse(self, run):
        text = json.dumps(self.HEADER) + "\n" + json.dumps(run) + "\n"
        h, runs, probs = ledger.parse_ledger(text, agents=set(IDS), office="ai-office")
        return runs, [p for p in probs if p.level == "error"]

    def test_chat_run_without_tasks_is_accepted_and_counted(self):
        runs, errs = self.parse(self.run_line())
        self.assertEqual((len(runs), errs), (1, []))
        t = ledger.totals(runs)
        self.assertEqual((t["session"]["tokens"], t["shared"]["tokens"], t["tasks"]), (100, 100, {}))
        self.assertEqual(ledger.to_event_log(self.HEADER, runs).count("\n"), 1)   # header only: no task, no usage event

    def test_empty_tasks_still_rejected_for_other_steps_or_without_pointer(self):
        self.assertEqual(self.parse(self.run_line(step="build"))[0], [])
        self.assertEqual(self.parse(self.run_line(note="hello"))[0], [])
        r = self.run_line()
        del r["note"]
        self.assertEqual(self.parse(r)[0], [])


class Cli(unittest.TestCase):
    def run_cli(self, args, stdin):
        r = subprocess.run([sys.executable, "-m", "engine.runtime", "chat", *args], input=stdin, capture_output=True, text=True, cwd=REPO, timeout=60)
        return r

    def test_mentions(self):
        r = self.run_cli(["mentions", "ai-office"], "@Fang and @Bob")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {"ids": ["architect"], "all": False, "unknown": ["bob"], "route": ["architect"]})

    def test_plan_needs_rules_and_prints_actions(self):
        a = ask(1)
        rules = [{"path": "chat", "read": "owner", "write": "owner"}]
        r = self.run_cli(["plan", "ai-office", "--now", NOW.strftime("%Y-%m-%dT%H:%M:%SZ")], json.dumps({"rules": rules, "docs": [a]}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)[0]["op"], "claim")
        bad = self.run_cli(["plan", "ai-office"], json.dumps({"rules": [{"path": "chat", "read": "view", "write": "owner"}], "docs": [a]}))
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(bad.stdout, "")
        self.assertEqual(self.run_cli(["plan", "ai-office"], json.dumps([a])).returncode, 1)
        self.assertEqual(self.run_cli(["plan", "ai-office"], "not json").returncode, 1)

    def test_reply_scan_hit_exits_1_and_prints_kind_only(self):
        a = ask(1, status="replying")
        leak = "a.b@example.test"
        r = self.run_cli(["reply", "ai-office", "--agent", "architect"], json.dumps({"ask": a, "text": "contact " + leak}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("email address", r.stderr)
        self.assertNotIn("example", r.stdout + r.stderr)
        self.assertEqual(r.stdout, "")
        ok = self.run_cli(["reply", "ai-office", "--agent", "architect", "--task", "T-070"], json.dumps({"ask": a, "text": "all good"}))
        self.assertEqual(ok.returncode, 0, ok.stderr)
        out = json.loads(ok.stdout)
        self.assertEqual((out["doc"]["task"], out["patch"]["recipients"]["architect"]["status"]), ("T-070", "answered"))

    def test_status_purge_and_rules(self):
        a = ask(1, status="picked")
        r = self.run_cli(["status", "ai-office", "--agent", "architect"], json.dumps({"ask": a}))
        self.assertEqual(json.loads(r.stdout)["patch"]["recipients"]["architect"]["status"], "replying")
        w = self.run_cli(["status", "ai-office", "--agent", "architect"], json.dumps({"ask": {"id": a["id"], "data": a, "version": 5}}))
        self.assertEqual(json.loads(w.stdout)["ifVersion"], 5)
        old = ask(1, status="answered", created=ago(31 * 86400))
        p = self.run_cli(["purge", "ai-office"], json.dumps([{"id": old["id"], "data": old, "version": 9}]))
        self.assertEqual(json.loads(p.stdout)[0]["ifVersion"], 9)
        self.assertEqual(self.run_cli(["purge", "ai-office"], "[]").stdout.strip(), "[]")
        self.assertEqual(self.run_cli(["rules", "ai-office"], json.dumps([{"path": "chat", "read": "owner", "write": "owner"}])).returncode, 0)
        self.assertEqual(self.run_cli(["rules", "ai-office"], "[]").returncode, 1)


if __name__ == "__main__":
    unittest.main()
