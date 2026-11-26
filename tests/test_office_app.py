import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import office_app  # noqa: E402

from engine.runtime import events, providers  # noqa: E402
from tests._helpers import REPO  # noqa: E402

HTML = REPO / "engine/app/office.html"
TEMPLATE = REPO / "engine/app/office.template.html"
OFFICE = REPO / "offices/ai-office"
ALL_TYPES = REPO / "tests/fixtures/events-all-types.jsonl"
SPRINT3 = REPO / "engine/app/fixtures/sprint-03.jsonl"
TEST_CFG = REPO / "tests/fixtures/providers-test.yaml"


def block(html, sid):
    m = re.search(r'<script[^>]*id="%s"[^>]*>(.*?)</script>' % sid, html, re.S)
    assert m, sid
    return m.group(1)


class Generator(unittest.TestCase):
    def test_committed_page_is_up_to_date(self):
        data, probs = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE)
        self.assertEqual(probs, [])
        self.assertEqual(HTML.read_text(encoding="utf-8"), office_app.render(TEMPLATE.read_text(encoding="utf-8"), data))
        self.assertEqual(office_app.main(["ai-office", "--check"]), 0)

    def test_placeholder_must_appear_exactly_once(self):
        data, _ = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE)
        for text in ("<html></html>", office_app.PLACEHOLDER_LINE * 2):
            with self.assertRaises(office_app.BuildError):
                office_app.render(text, data)
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "t.html"
            t.write_text("nothing", encoding="utf-8")
            old = office_app.TEMPLATE
            office_app.TEMPLATE = t
            try:
                self.assertEqual(office_app.main(["ai-office", "--out", str(Path(tmp) / "o.html")]), 1)
            finally:
                office_app.TEMPLATE = old

    def test_data_block_round_trips_and_script_end_is_escaped(self):
        data, _ = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE)
        data["events"][0]["reason"] = "x</script><b> "
        html = office_app.render(TEMPLATE.read_text(encoding="utf-8"), data)
        blob = block(html, "office-data")
        self.assertNotIn("</", blob)
        self.assertEqual(json.loads(blob)["events"][0]["reason"], "x</script><b> ")
        self.assertEqual(len(re.findall(r"</script>", html)), 3)

    def test_data_has_8_agents_rooms_with_rect_and_desks_with_at(self):
        data = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        self.assertEqual(len(data["agents"]), 8)
        self.assertTrue(all(len(r["rect"]) == 4 for r in data["theme"]["rooms"]))
        self.assertTrue(all(len(d["at"]) == 2 for d in data["theme"]["desks"]))
        self.assertEqual(data["theme"]["door"], [12, 0])
        self.assertEqual(data["skipped"], [])

    def test_theme_without_layout_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "offices" / "ai-office"
            shutil.copytree(OFFICE, root, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(REPO / "base", Path(tmp) / "base")
            (Path(tmp) / "workspaces.yaml").write_text((REPO / "workspaces.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            th = root / "theme" / "theme.yaml"
            th.write_text(re.sub(r", rect: \[[^\]]*\]", "", th.read_text(encoding="utf-8")), encoding="utf-8")
            with self.assertRaises(office_app.BuildError):
                office_app.build_data(root, office_app.DEFAULT_FIXTURE)

    def test_bad_log_line_exits_1_unless_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.jsonl"
            bad.write_text(office_app.DEFAULT_FIXTURE.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
            out = Path(tmp) / "o.html"
            self.assertEqual(office_app.main(["ai-office", "--fixture", str(bad), "--out", str(out)]), 1)
            self.assertEqual(office_app.main(["ai-office", "--fixture", str(bad), "--out", str(out), "--allow-errors"]), 0)
            data = json.loads(block(out.read_text(encoding="utf-8"), "office-data"))
            self.assertEqual(len(data["skipped"]), 1)
            self.assertEqual(len(data["events"]), 84)

    def test_data_rule_problem_always_exits_1_and_never_echoes_the_value(self):
        secrets = ["1234567890123456", "jane.doe@example.com"]
        base = office_app.DEFAULT_FIXTURE.read_text(encoding="utf-8")
        leaks = [json.dumps({"t": 200 + i, "type": "needs_merwyn", "agent": "pmo", "task": "T-043", "src": "x.md", "reason": f"v {s}"})
                 for i, s in enumerate(secrets)]
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "leak.jsonl"
            bad.write_text(base + "\n".join(leaks) + "\n{broken\n", encoding="utf-8")
            for extra in ([], ["--allow-errors"]):
                out = Path(tmp) / "o.html"
                r = subprocess.run([sys.executable, str(REPO / "scripts/office_app.py"), "ai-office", "--fixture", str(bad),
                                    "--out", str(out), *extra], cwd=REPO, capture_output=True, text=True)
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertFalse(out.exists(), "no file may be written")
                for sec in secrets:
                    self.assertNotIn(sec, r.stdout + r.stderr)
                self.assertIn("field 'reason'", r.stderr)
            # the same in-process: no output file, and the skipped block (if it were built) carries no value
            data, probs = office_app.build_data(OFFICE, bad)
            for sec in secrets:
                self.assertNotIn(sec, json.dumps(data) + " ".join(str(p) for p in probs))


class PageRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")

    def test_script_hosts_and_version(self):
        urls = re.findall(r"https?://[^\s'\"<>)]+", self.html)
        hosts = {"cdnjs.cloudflare.com", "unpkg.com", "cdn.jsdelivr.net"}
        for u in urls:
            self.assertIn(u.split("/")[2], hosts, u)
            self.assertTrue("r128" in u or "0.128.0" in u, u)
        self.assertEqual(len(urls), 3)
        self.assertNotRegex(self.html, r'<script[^>]+src=')
        self.assertIn("./three.min.js", self.html)

    def test_no_network_apis_or_external_assets(self):
        for pat in (r"\bfetch\s*\(", r"XMLHttpRequest", r"\bWebSocket\b", r"\bEventSource\b", r"\bimport\s*\(", r"<link[^>]+href", r"<img\b", r"@import"):
            self.assertIsNone(re.search(pat, self.html), pat)

    def test_page_passes_the_data_scan(self):
        forbidden = events.forbidden_terms(REPO)
        low = self.html.lower()
        for f in forbidden:
            self.assertNotIn(f, low)
        scrubbed = re.sub(r"https?://[^\s'\"<>)]+|@(media|supports|keyframes|import)|#[0-9a-fA-F]{3,8}", "", self.html)
        for p in events.DATA_PATTERNS:
            self.assertIsNone(p.search(scrubbed), p.pattern)

    def test_size_limit(self):
        self.assertLessEqual(len(self.html.encode("utf-8")), 200 * 1024)

    def test_three_min_js_is_not_committed(self):
        r = subprocess.run(["git", "ls-files", "engine/app/three.min.js"], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "")


CORE_CHECK = r"""
const fs = require('fs');
const h = fs.readFileSync(process.argv[2], 'utf8');
const g = id => h.match(new RegExp('<script[^>]*id="' + id + '"[^>]*>([\\s\\S]*?)</script>'))[1];
eval(g('office-core'));
const C = OfficeCore, assert = require('assert');
const D = JSON.parse(g('office-data'));
const mode = process.argv[3] || 'sprint3', extra = process.argv[4] ? JSON.parse(fs.readFileSync(process.argv[4], 'utf8')) : null;
const full = mode === 'all' ? extra : null;
if (mode === 'sprint3') D.events = extra.events;   // the page now defaults to the v1 synthetic log; Sprint 3 data comes in as JSON
function run(D) {
  const tl = C.timeline(D.events), out = {};
  let s = C.initState(D);
  D.events.forEach((e, i) => C.apply(s, e, tl[i].start));
  return { s, tl };
}
if (mode === 'sprint3') {
  { const tl = C.timeline(D.events); let n = 0;   // merged starts only after the task's earlier beats (review_pass) have finished
    D.events.forEach((e, i) => { if (e.type !== 'merged') return; n++;
      D.events.forEach((p, j) => { if (j < i && p.task === e.task) assert.ok(tl[i].start >= tl[j].end - 1e-9, e.task + ' merged before event ' + j + ' ended'); }); });
    assert.ok(n >= 1); }
  let s = C.initState(D), tl = C.timeline(D.events);
  for (let i = 0; i < 3; i++) C.apply(s, D.events[i], tl[i].start);
  assert.strictEqual(C.agentStatus(s, 'pmo'), 'waiting');
  assert.strictEqual(s.agents.pmo.waiting.length, 3);
  assert.strictEqual(C.needs(s), 3);
  assert.strictEqual(C.stripOrder(s)[0].id, 'pmo');
  for (let i = 3; i < 6; i++) C.apply(s, D.events[i], tl[i].start);
  assert.strictEqual(C.needs(s), 0);
  assert.strictEqual(s.agents.pmo.holds.length, 0);
  const end = run(D);
  ['T-043', 'T-044', 'T-045'].forEach(t => assert.strictEqual(end.s.tasks[t].stage, 'done'));
  Object.values(end.s.agents).forEach(a => assert.strictEqual(a.holds.length, 0));
  assert.deepStrictEqual(end.s.unknown, []);
  assert.ok(end.tl.total > 120 && end.tl.total < 300, 'replay length ' + end.tl.total);
  for (let i = 1; i < tl.length; i++) assert.ok(tl[i].start >= tl[i - 1].start);
  for (const t of [0, 7, 33, 61, 99, 140, 190, 1e9]) {
    const a = C.stateAt(D, t), b = C.initState(D), n = C.countDue(D, t);
    for (let i = 0; i < n; i++) C.apply(b, D.events[i], tl[i].start);
    b.now = t;
    assert.deepStrictEqual(a, b);
  }
  assert.ok(C.sentence(D.events[0], {pmo: 'Janice'}).includes('Janice waits for you'));
  assert.strictEqual(C.sentence({type: 'zzz'}, {}).startsWith('Unknown event'), true);
  console.log('core ok', tl.total.toFixed(1));
} else if (mode === 'all') {
  const E = full.events, d2 = Object.assign({}, D, { events: E }), tl = C.timeline(E);
  let s = C.initState(d2), seen = {};
  E.forEach((e, i) => { C.apply(s, e, tl[i].start); Object.keys(s.agents).forEach(a => seen[C.agentStatus(s, a) + (C.tagWord(s, a) ? ':' + C.tagWord(s, a) : '')] = 1); });
  assert.ok(seen['blocked:Blocked'], 'blocked state');
  assert.ok(seen['blocked:Rejected'], 'rejected state');
  assert.ok(seen.waiting && seen.working);
  assert.strictEqual(s.tasks['T-901'].stage, 'done');
  assert.deepStrictEqual(s.unknown, []);
  console.log('all-types ok');
} else if (mode === 'usage') {
  /* totals vs a Python sum: print, for each replay time, the due event count and the page's totals */
  const tl = C.timeline(D.events), out = [];
  for (const t of extra.times) {
    const s = C.stateAt(D, t), U = C.usageTotals(s, D.providers), n = C.countDue(D, t);
    const slim = r => ({ input: r.input, output: r.output, cache_read: r.cache_read, cache_write: r.cache_write });
    const rows = o => Object.fromEntries(Object.entries(o).map(([k, r]) => [k, slim(r)]));
    out.push({ t, n, total: slim(U.total), providers: rows(U.providers), agents: rows(U.agents), cost: C.costText(U.total) });
  }
  console.log(JSON.stringify({ total: tl.total, out }));
} else if (mode === 'pricing') {
  /* hand-written exact cases against the TEST catalogue (made-up prices) */
  const P = extra.providers, mk = (agent, provider, model, billing, o) => Object.assign({ agent, provider, model, billing, input: 0, output: 0, cache_read: 0, cache_write: 0 }, o);
  const cost = b => C.eventCost(b, P);
  // per-token: 123456 in at 0.3125, 40000 out at 1.8125, 80000 cache_read at 0.0625 (micro-USD, each class rounded)
  let c = cost(mk('a', 'token-test', 'tok-model', 'per_token', { input: 123456, output: 40000, cache_read: 80000 }));
  assert.deepStrictEqual(c, { state: 'usd', micro: 38580 + 72500 + 5000 });
  assert.strictEqual(c.micro, 116080);
  // a nonzero class with a null price makes the bucket unset, a zero count does not
  assert.strictEqual(cost(mk('a', 'token-test', 'tok-model', 'per_token', { input: 10, cache_write: 1 })).state, 'unset');
  assert.strictEqual(cost(mk('a', 'token-test', 'tok-model', 'per_token', { input: 10 })).state, 'usd');
  // a plan bucket never carries money, even if the catalogue were to hold a price
  c = cost(mk('a', 'plan-test', 'plan-model', 'plan', { input: 5e6, output: 5e6 }));
  assert.deepStrictEqual(c, { state: 'plan', micro: 0 });
  assert.strictEqual(C.costText({ input: 0, output: 0, cache_read: 0, cache_write: 0, micro: 0, usd: 0, plan: 2, unset: 0, none: 0, dates: [] }), 'plan');
  // unknown provider or model
  assert.strictEqual(cost(mk('a', 'nobody', 'x', 'per_token', { input: 5 })).state, 'none');
  assert.strictEqual(cost(mk('a', 'token-test', 'nope', 'per_token', { input: 5 })).state, 'none');
  // a state with usage and totals over several agents
  const D2 = { agents: [{ id: 'a' }, { id: 'b' }], events: [] };
  const s = C.initState(D2);
  const ev = (agent, provider, model, billing, o) => Object.assign({ type: 'usage', agent, task: 'T-901', provider, model, billing, t: 0 }, o);
  C.apply(s, ev('a', 'token-test', 'tok-model', 'per_token', { input: 123456, output: 40000, cache_read: 80000 }), 1);
  C.apply(s, ev('a', 'token-test', 'tok-model', 'per_token', { input: 4, output: 4 }), 2);    // same bucket: adds up
  C.apply(s, ev('b', 'plan-test', 'plan-model', 'plan', { input: 1000, output: 10 }), 3);
  C.apply(s, ev('b', 'nobody', 'x-model', 'per_token', { input: 7 }), 4);
  C.apply(s, ev('b', 'token-test', 'tok-model', 'per_token', { input: 9, cache_write: 3 }), 5);
  const U = C.usageTotals(s, P);
  assert.strictEqual(U.agents.a.micro, 38581 + 72507 + 5000);   // round(123460*0.3125)=38581, round(40004*1.8125)=72507, 5000
  assert.strictEqual(C.costText(U.agents.a), '$0.12 est.');
  assert.strictEqual(C.costText(U.providers['token-test']), '$0.12 est. + 1 unpriced');
  assert.strictEqual(C.costText(U.agents.b), 'plan runs + 1 unpriced + 1 unknown');
  assert.strictEqual(C.costText(U.providers['plan-test']), 'plan');
  assert.strictEqual(C.costText(U.providers.nobody), '--');
  assert.strictEqual(C.costText(U.total), '$0.12 est. + plan runs + 1 unpriced + 1 unknown');
  assert.deepStrictEqual(U.providers['token-test'].dates, ['2000-01-01']);
  assert.strictEqual(U.providers['plan-test'].micro, 0);
  assert.ok(!C.costText(U.providers['plan-test']).includes('$') && !C.costText(U.agents.b).includes('$'));
  assert.strictEqual(U.total.input, 123460 + 1000 + 7 + 9);
  assert.strictEqual(C.costText(C.usageTotals(C.initState(D2), P).total), '--');
  // model labels: known, unknown provider, unknown model, long raw id
  assert.deepStrictEqual(C.modelLabel(P, 'token-test', 'tok-model'), { code: 'TOK', short: 'tok-m', colour: '#5b8def', known: true, modelKnown: true, full: 'token-test / tok-model' });
  let ml = C.modelLabel(P, 'mystery-ai', 'mystery-model-with-a-long-id');
  assert.strictEqual(ml.code, 'MYS'); assert.strictEqual(ml.colour, null); assert.strictEqual(ml.known, false);
  assert.strictEqual(ml.short, 'mystery-mod…'); assert.strictEqual(ml.short.length, 12);
  ml = C.modelLabel(P, 'token-test', 'new-model');
  assert.strictEqual(ml.short, 'new-model'); assert.strictEqual(ml.colour, '#5b8def'); assert.strictEqual(ml.modelKnown, false);
  // planned model: event model wins; the page only compares families
  assert.strictEqual(C.plannedDiffers('sonnet', P, 'token-test', 'tok-model'), false);
  assert.strictEqual(C.plannedDiffers('opus', P, 'token-test', 'tok-model'), true);
  assert.strictEqual(C.plannedDiffers('sonnet', P, 'nobody', 'x'), true);
  assert.strictEqual(C.plannedDiffers(null, P, 'nobody', 'x'), false);
  // a model switch is recorded and shows the event's model
  const s2 = C.initState({ agents: [{ id: 'a' }], events: [] });
  C.apply(s2, { type: 'step_started', agent: 'a', task: 'T-901', provider: 'plan-test', model: 'plan-model' }, 1);
  assert.strictEqual(s2.agents.a.switchedAt, null); assert.strictEqual(s2.lastSwitch, null);
  C.apply(s2, { type: 'step_started', agent: 'a', task: 'T-901', provider: 'token-test', model: 'tok-model' }, 9);
  assert.strictEqual(s2.agents.a.switchedAt, 9); assert.strictEqual(s2.agents.a.model.model, 'tok-model');
  assert.strictEqual(s2.agents.a.prevModel.provider, 'plan-test'); assert.strictEqual(s2.lastSwitch.to.provider, 'token-test');
  assert.strictEqual(C.switchSentence(s2.lastSwitch, { a: 'Ann' }, P), 'Ann  plan-m → tok-m (PLN → TOK)');
  C.apply(s2, { type: 'usage', agent: 'a', task: 'T-901', provider: 'token-test', model: 'tok-model', billing: 'per_token', input: 1, output: 1 }, 10);
  assert.strictEqual(s2.lastSwitch, null); assert.strictEqual(s2.agents.a.switchedAt, 9);   // same model: no switch
  assert.deepStrictEqual(s2.unknown, []);
  // zero-length usage events do not take animation time, other types keep the 0.4 default
  assert.strictEqual(C.evDur({ type: 'usage' }), 0); assert.strictEqual(C.evDur({ type: 'zzz' }), 0.4);
  console.log('pricing ok');
}
"""


@unittest.skipUnless(shutil.which("node"), "node not installed")
class CoreUnderNode(unittest.TestCase):
    def node(self, *args):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "check.js"
            f.write_text(CORE_CHECK, encoding="utf-8")
            r = subprocess.run(["node", str(f), *args], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def json_file(self, tmp, name, obj):
        f = Path(tmp) / name
        f.write_text(json.dumps(obj), encoding="utf-8")
        return str(f)

    def test_sprint3_replay_still_works(self):
        # the page default is now the v1 synthetic log; the Sprint 3 (v0) log is passed in as JSON
        data, probs = office_app.build_data(OFFICE, SPRINT3)
        self.assertEqual(probs, [])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn("core ok", self.node(str(HTML), "sprint3", self.json_file(tmp, "s3.json", {"events": data["events"]})))

    def test_all_types_log(self):
        data, probs = office_app.build_data(OFFICE, ALL_TYPES)
        self.assertEqual(probs, [])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn("all-types ok", self.node(str(HTML), "all", self.json_file(tmp, "all.json", {"events": data["events"]})))

    def test_usage_totals_equal_the_sum_of_events_due_and_scrubbing_back_lowers_them(self):
        data = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        with tempfile.TemporaryDirectory() as tmp:
            probe = self.node(str(HTML), "usage", self.json_file(tmp, "t.json", {"times": [0, 60, 1e9, 60, 120, 0]}))
        res = json.loads(probe)
        runs = res["out"]
        self.assertEqual(runs[0]["n"], runs[5]["n"])
        fields = ("input", "output", "cache_read", "cache_write")

        def expect(n):
            tot = dict.fromkeys(fields, 0)
            by_p, by_a = {}, {a["id"]: dict.fromkeys(fields, 0) for a in data["agents"]}
            for e in data["events"][:n]:
                if e["type"] != "usage":
                    continue
                row = {f: e.get(f, 0) for f in fields}
                for dst in (tot, by_p.setdefault(e["provider"], dict.fromkeys(fields, 0)), by_a[e["agent"]]):
                    for f in fields:
                        dst[f] += row[f]
            return tot, by_p, by_a

        for r in runs:
            tot, by_p, by_a = expect(r["n"])
            self.assertEqual(r["total"], tot, r["t"])
            self.assertEqual(r["providers"], by_p, r["t"])
            self.assertEqual(r["agents"], by_a, r["t"])
        self.assertEqual(runs[0]["total"], dict.fromkeys(fields, 0))
        self.assertEqual(runs[0]["cost"], "--")
        mid, end = sum(runs[1]["total"].values()), sum(runs[2]["total"].values())
        self.assertTrue(0 < mid < end)
        self.assertEqual(runs[3]["total"], runs[1]["total"])          # back to mid: same as the first visit
        self.assertTrue(sum(runs[4]["total"].values()) > mid)
        self.assertEqual(runs[2]["n"], len(data["events"]))
        # the shipped config has no price, so the page never builds a dollar amount
        for r in runs:
            self.assertNotIn("$", r["cost"])
        self.assertEqual(runs[2]["cost"], "plan runs + 3 unpriced")

    def test_pricing_and_labels_with_exact_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(TEST_CFG, Path(tmp) / providers.FILE)
            cat, probs = providers.load_providers(tmp)
            self.assertEqual(probs, [])
            self.assertIn("pricing ok", self.node(str(HTML), "pricing", self.json_file(tmp, "p.json", {"providers": cat})))


class NoLiterals(unittest.TestCase):
    """The page and the generator hold no price or provider data: it all comes from offices/<office>/providers.yaml."""

    @classmethod
    def setUpClass(cls):
        cls.files = {p: p.read_text(encoding="utf-8") for p in (TEMPLATE, REPO / "scripts/office_app.py")}

    def test_no_price_numbers_provider_ids_or_live_claims(self):
        cat, _ = providers.load_providers(OFFICE)
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(TEST_CFG, Path(tmp) / providers.FILE)
            test_cat, _ = providers.load_providers(tmp)
        prices = {str(m[k]) for c in (cat, test_cat) for p in c.values() for m in p["models"].values() for k in providers.PRICE_KEYS if m.get(k)}
        self.assertIn("0.0625", prices)
        prices = {x for x in prices if len(x) >= 5}   # short numbers such as 1.5 or 3 occur in layout code; the test config uses distinctive ones
        self.assertIn("1.8125", prices)
        for path, text in self.files.items():
            for pid in cat:
                self.assertNotIn(pid, text, f"{path.name} names provider {pid}")
            for pr in prices:
                self.assertNotIn(pr, text, f"{path.name} holds price {pr}")
            self.assertIsNone(re.search(r"\$\s*\d", text), path.name)
            self.assertIsNone(re.search(r"current price|live (price|cost|usage)", text, re.I), path.name)

    def test_dollar_sign_is_built_in_exactly_one_place(self):
        text = self.files[TEMPLATE]
        self.assertEqual(text.count("'$'"), 1)
        m = re.search(r"function costText.*?\n  }\n", text, re.S)
        self.assertIn("'$'", m.group(0))

    def test_committed_page_data_has_no_dollar_sign_or_price_in_the_log(self):
        data = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        self.assertNotIn("$", json.dumps(data))
        self.assertTrue(all("cost_usd" not in e for e in data["events"]))

    def test_page_labels_usage_as_synthetic(self):
        data = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        self.assertEqual(data["log"]["usage_source"], "synthetic")
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["v"], 1)
        self.assertEqual(sorted(data["providers"]), ["anthropic-api", "claude-sdk", "deepseek", "openai"])
        planned = {a["id"]: a["planned_model"] for a in data["agents"]}
        self.assertEqual(planned, {"architect": "opus", "reviewer": "opus", "pm": "sonnet", "pmo": "sonnet", "engineer": "sonnet",
                                   "compliance": "sonnet", "curator": "sonnet", "designer": "sonnet"})
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('class="synpill" data-syn>synthetic</span>', html)   # the panel header pill
        self.assertGreaterEqual(html.count('<span class="syn">synthetic</span>'), 1)   # the suffix after every figure group


class Providers(unittest.TestCase):
    def test_bad_catalogue_fails_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "offices" / "ai-office"
            shutil.copytree(OFFICE, root, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(REPO / "base", Path(tmp) / "base")
            (Path(tmp) / "workspaces.yaml").write_text((REPO / "workspaces.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            f = root / providers.FILE
            f.write_text(f.read_text(encoding="utf-8").replace("input: null", "input: 3", 1), encoding="utf-8")
            with self.assertRaises(office_app.BuildError) as cm:
                office_app.build_data(root, office_app.DEFAULT_FIXTURE)
            self.assertIn("prices.source", str(cm.exception))
            out = Path(tmp) / "o.html"
            self.assertEqual(office_app.main([str(root), "--out", str(out)]), 1)
            self.assertFalse(out.exists())

    def test_unknown_provider_still_builds_and_is_listed_as_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "u.jsonl"
            lines = office_app.DEFAULT_FIXTURE.read_text(encoding="utf-8").splitlines()
            extra = {"t": 400, "type": "usage", "agent": "engineer", "task": "T-904", "provider": "mystery-ai", "model": "mystery-1",
                     "billing": "per_token", "input": 5, "output": 5, "src": "x.md"}
            log.write_text("\n".join(lines + [json.dumps(extra)]) + "\n", encoding="utf-8")
            data, probs = office_app.build_data(OFFICE, log)
        self.assertEqual([p.level for p in probs], ["warning"])
        self.assertEqual(len(data["warnings"]), 1)
        self.assertIn("mystery-ai", data["warnings"][0]["message"])
        self.assertEqual(data["skipped"], [])


if __name__ == "__main__":
    unittest.main()
