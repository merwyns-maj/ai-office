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
        data, probs = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE, chat=True)   # the AI Office artifact has chat (T-063)
        self.assertEqual(probs, [])
        self.assertEqual(HTML.read_text(encoding="utf-8"), office_app.render(TEMPLATE.read_text(encoding="utf-8"), data))
        self.assertEqual(office_app.main(["ai-office", "--chat", "--check"]), 0)
        self.assertEqual(office_app.main(["ai-office", "--check"]), 1)   # without the flag it is a different page

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
        # 200 KB until T-063. The chat (panel, phone sheet, combobox, notice, status chips, parser, scan) is about 40 KB of
        # hand-written, library-free page code; the committed AI Office page is built with it. Raised to 216 KB by Fang (about 6 KB headroom).
        self.assertLessEqual(len(self.html.encode("utf-8")), 216 * 1024)

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
} else if (mode === 'shares') {
  /* percentage maths: whole numbers, largest remainder, always 100, ties to the earlier item */
  const S = C.shares, sum = a => a.reduce((x, y) => x + y, 0);
  assert.deepStrictEqual(S([1, 1, 1]), [34, 33, 33]);
  assert.deepStrictEqual(S([50, 25, 25]), [50, 25, 25]);
  assert.deepStrictEqual(S([0, 0]), [0, 0]);
  assert.deepStrictEqual(S([]), []);
  assert.deepStrictEqual(S([5]), [100]);
  assert.deepStrictEqual(S([1, 0, 2]), [33, 0, 67]);
  assert.deepStrictEqual(S([887, 714, 430, 203, 189, 69, 31]).length, 7);
  let seed = 7;
  const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  for (let k = 0; k < 500; k++) {
    const v = Array.from({ length: 1 + Math.floor(rnd() * 9) }, () => Math.floor(rnd() * 1e6) * (rnd() < 0.2 ? 0 : 1));
    const p = S(v), T = sum(v);
    assert.ok(p.every(x => Number.isInteger(x) && x >= 0 && x <= 100));
    assert.strictEqual(sum(p), T ? 100 : 0, JSON.stringify(v));
    v.forEach((x, i) => { if (T) assert.ok(Math.abs(p[i] - 100 * x / T) < 1, JSON.stringify(v)); });   // within one point of the exact share
  }
  console.log('shares ok');
} else if (mode === 'provshares') {
  /* inside each provider: models and agents add to 100 within that provider, tokens match the buckets */
  const s = { usage: {
    'a|p1|m1|usd': { agent: 'a', provider: 'p1', model: 'm1', input: 1, output: 0, cache_read: 0, cache_write: 0 },
    'b|p1|m1|usd': { agent: 'b', provider: 'p1', model: 'm1', input: 1, output: 0, cache_read: 0, cache_write: 0 },
    'b|p1|m2|usd': { agent: 'b', provider: 'p1', model: 'm2', input: 0, output: 1, cache_read: 0, cache_write: 0 },
    'a|p2|m3|plan': { agent: 'a', provider: 'p2', model: 'm3', input: 5, output: 0, cache_read: 3, cache_write: 2 } } };
  const B = C.providerBreakdown(s), sum = a => a.reduce((x, r) => x + r.pct, 0);
  assert.deepStrictEqual(B.p1.models.map(r => [r.id, r.tokens, r.pct]), [['m1', 2, 67], ['m2', 1, 33]]);
  assert.deepStrictEqual(B.p1.agents.map(r => [r.id, r.tokens, r.pct]), [['b', 2, 67], ['a', 1, 33]]);
  assert.deepStrictEqual(B.p2.models.map(r => [r.id, r.tokens, r.pct]), [['m3', 10, 100]]);
  Object.values(B).forEach(p => { assert.strictEqual(sum(p.models), 100); assert.strictEqual(sum(p.agents), 100); });
  console.log('provshares ok');
} else if (mode === 'rec') {
  /* recorded page: replay every run; null runs add 0 tokens and are excluded from the percentages */
  const E = D.events, tl = C.timeline(E);
  let s = C.initState(D);
  E.forEach((e, i) => C.apply(s, e, tl[i].start));
  const R = C.recTotals(s), py = extra;
  assert.strictEqual(R.total.tokens, py.tokens);
  assert.strictEqual(R.total.runs, py.runs);
  assert.strictEqual(R.total.nr, py.nr);
  const ag = Object.values(R.agents);
  assert.strictEqual(ag.reduce((a, q) => a + q.pct, 0), 100);
  assert.strictEqual(ag.reduce((a, q) => a + q.tokens, 0), py.tokens);
  Object.keys(py.agents).forEach(k => assert.strictEqual(R.agents[k].tokens, py.agents[k]));
  assert.strictEqual(Object.values(s.runlog).reduce((a, l) => a + l.length, 0), E.length);   // every run listed under its agent
  const nr = Object.values(s.runlog).flat().filter(r => r.total === null);
  assert.strictEqual(nr.length, py.nr);
  assert.ok(nr.every(r => !JSON.stringify(r).includes('"total":0')));
  // the synthetic-style state is untouched by recorded events
  assert.deepStrictEqual(s.usage, {});
  console.log('rec ok');
} else if (mode === 'budgets') {
  /* T-060: used vs budget maths, Detail order, mode parsing, and the views on a recorded and a synthetic state */
  const R = C.budgetRow;
  let r = R(3813702, 5000000);
  assert.deepStrictEqual([r.state, r.pct, r.barPct, r.over, r.hatch], ['ok', 76, 76, 0, 0]);
  r = R(0, 5000000); assert.deepStrictEqual([r.state, r.pct, r.barPct], ['ok', 0, 0]);
  r = R(5000000, 5000000); assert.deepStrictEqual([r.state, r.pct, r.barPct, r.over], ['ok', 100, 100, 0]);   // exactly at budget is not over
  r = R(5000001, 5000000); assert.deepStrictEqual([r.state, r.over, r.barPct], ['over', 1, 100]);
  r = R(5210000, 5000000); assert.deepStrictEqual([r.state, r.pct, r.over, r.barPct], ['over', 104, 210000, 100]);
  assert.ok(Math.abs(r.hatch - 4.2) < 1e-9);                                  // overflow / budget, as a percent of the bar
  assert.strictEqual(R(9000000, 5000000).hatch, 50);                          // capped at half the bar
  assert.strictEqual(R(1e9, 5000000).pct, 20000);                             // the text keeps the real figure
  r = R(10, 0); assert.deepStrictEqual([r.state, r.pct, r.over, r.hatch], ['over', null, 10, 50]);   // a zero budget has no percentage
  r = R(0, 0); assert.deepStrictEqual([r.state, r.pct], ['ok', 0]);
  for (const b of [null, undefined, -1, NaN, 'x', Infinity]) { r = R(123, b); assert.deepStrictEqual([r.state, r.pct, r.barPct, r.over, r.budget], ['unset', null, 0, 0, null], String(b)); }
  assert.strictEqual(R(-5, 100).used, 0); assert.strictEqual(R(null, 100).pct, 0);
  // T-062 colour level from the rounded % the text shows: 69 ok, 70 near, 89 near, 90 alert, 100 alert (at budget, not over), over
  const L = (pct) => R(pct, 100).level;
  assert.deepStrictEqual([0, 69, 70, 89, 90, 100].map(L), ['ok', 'ok', 'near', 'near', 'alert', 'alert']);
  assert.deepStrictEqual([R(99.6, 100).level, R(101, 100).level, R(1, 0).level, R(0, 0).level, R(5, null).level], ['alert', 'over', 'over', 'ok', 'unset']);
  assert.strictEqual(R(69.6, 100).pct, 70); assert.strictEqual(R(69.6, 100).level, 'near');   // the colour follows the % the text shows
  const th = { warn_at: 50, alert_at: 80 };
  assert.deepStrictEqual([49, 50, 79, 80].map(p => R(p, 100, th).level), ['ok', 'near', 'near', 'alert']);   // thresholds come from budgets.yaml
  assert.strictEqual(R(75, 100, { warn_at: 'x' }).level, 'near'); assert.strictEqual(R(75, 100, null).level, 'near');   // bad or missing: the defaults
  // Detail order: by share of budget (not by tokens), unset after, main session last, ties by name
  const row = (name, used, budget, kind) => ({ name, kind: kind || 'agent', row: R(used, budget) });
  const names = C.sortDetail([row('Z main', 0, null, 'main'), row('B', 900, null), row('A', 50, 100), row('C', 120, 100), row('D', 50, 100), row('E', 5000, 100000), row('F', 901, null)]).map(x => x.name);
  assert.deepStrictEqual(names, ['C', 'A', 'D', 'E', 'F', 'B', 'Z main']);
  assert.deepStrictEqual(C.sortDetail([row('x', 0, 0), row('y', 5, 0)]).map(x => x.name), ['y', 'x']);   // zero budget with use sorts first
  // mode: anything but 'detail' is Summary, the key is versioned
  assert.deepStrictEqual(['detail', 'summary', null, undefined, '', 'DETAIL', '{}'].map(C.parseMode), ['detail', 'summary', 'summary', 'summary', 'summary', 'summary', 'summary']);
  assert.strictEqual(C.MODE_KEY, 'office.usage.mode.v1');
  const E = D.events, tl = C.timeline(E), full = C.stateAt(D, 1e9);
  const v = C.budgetView(full, D);
  if (D.log.usage_source === 'recorded') {
    const py = extra, B = D.budgets.providers[D.log.provider];
    assert.strictEqual(v.providers.length, 1); const p = v.providers[0];
    assert.strictEqual(p.row.used, py.tokens); assert.strictEqual(p.row.budget, B.tokens);
    assert.strictEqual(p.row.pct, Math.round(100 * py.tokens / B.tokens));
    assert.deepStrictEqual(D.budgets.thresholds.warn_at < D.budgets.thresholds.alert_at, true);
    p.agents.concat([p]).filter(a => a.kind !== 'main').forEach(a => assert.strictEqual(a.row.level, C.budgetLevel(a.row.pct, a.row.over, D.budgets.thresholds)));
    assert.strictEqual(p.agents.filter(a => a.kind === 'agent').length, Object.keys(py.agents).length);
    p.agents.filter(a => a.kind === 'agent').forEach(a => { assert.strictEqual(a.row.used, py.agents[a.id] || 0); assert.strictEqual(a.row.budget, B.agents[a.id].tokens); });
    assert.strictEqual(p.agents[p.agents.length - 1].kind, 'main'); assert.strictEqual(p.agents[p.agents.length - 1].id, D.budgets.main_session);
    const ratios = p.agents.filter(a => a.kind === 'agent').map(a => a.row.ratio); assert.deepStrictEqual(ratios.slice().sort((x, y) => y - x), ratios);
    assert.strictEqual(C.budgetView(C.initState(D), D).none, true);   // nothing replayed yet
    // no budgets in the data: everything is "unset", never 0% and no main-session row
    const D2 = Object.assign({}, D, { budgets: null }), v2 = C.budgetView(full, D2);
    assert.strictEqual(v2.providers[0].row.state, 'unset'); assert.ok(v2.providers[0].agents.every(a => a.row.state === 'unset' && a.kind === 'agent'));
    // a budget smaller than the use is over, by exactly the difference
    const D3 = JSON.parse(JSON.stringify(D)); D3.budgets.providers[D.log.provider].tokens = py.tokens - 1000;
    const o = C.budgetView(full, D3).providers[0].row; assert.deepStrictEqual([o.state, o.over], ['over', 1000]);
    console.log('budgets rec ok');
  } else {
    assert.strictEqual(v.synthetic, true);
    const by = {}; v.providers.forEach(p => by[p.id] = p);
    const U = C.usageTotals(full, D.providers);
    Object.keys(U.providers).forEach(k => assert.strictEqual(by[k].row.used, U.providers[k].input + U.providers[k].output + U.providers[k].cache_read + U.providers[k].cache_write, k));
    assert.strictEqual(by['deepseek'].row.state, 'unset');   // used, no budget: never 0%
    assert.ok(v.providers.some(p => p.row.state === 'over'));
    assert.ok(v.providers.every(p => p.agents.every(a => a.kind === 'agent')));   // synthetic runs report every agent
    console.log('budgets syn ok');
  }
} else if (mode === 'syn') {
  const E = D.events, tl = C.timeline(E);
  let s = C.initState(D);
  E.forEach((e, i) => C.apply(s, e, tl[i].start));
  const U = C.usageTotals(s, D.providers);
  assert.strictEqual(Object.values(U.providers).reduce((a, r) => a + r.pct, 0), 100);
  assert.strictEqual(Object.values(U.agents).reduce((a, r) => a + r.pct, 0), 100);
  console.log('syn ok');
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
} else if (mode === 'layout') {
  /* T-059 movable panels: pure layout maths, numbers only */
  const P = C.PANEL, B = C.panelBounds(1280, 800, 56);
  assert.deepStrictEqual(B, { left: 8, right: 1272, top: 56, bottom: 736 });
  const inside = (r, b) => r.x >= b.left && r.y >= b.top && r.x + r.w <= b.right && r.y + r.h <= b.bottom;
  // clamping: size first, then position; every result sits inside the window with the 8px margin
  assert.deepStrictEqual(C.clampRect({ x: -50, y: -50, w: 300, h: 300 }, B), { x: 8, y: 56, w: 300, h: 300 });
  assert.deepStrictEqual(C.clampRect({ x: 1200, y: 700, w: 300, h: 300 }, B), { x: 972, y: 436, w: 300, h: 300 });
  assert.deepStrictEqual(C.clampRect({ x: 0, y: 0, w: 9999, h: 9999 }, B), { x: 8, y: 56, w: 520, h: 680 });   // max 520 wide, window height minus the bars
  assert.deepStrictEqual(C.clampRect({ x: 100, y: 100, w: 10, h: 10 }, B), { x: 100, y: 100, w: 240, h: 120 });   // min 240 x 120
  let seed = 11; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  for (let k = 0; k < 600; k++) {
    const W = 900 + Math.floor(rnd() * 1500), H = 420 + Math.floor(rnd() * 900), b = C.panelBounds(W, H, rnd() < 0.5 ? 56 : 48);
    const r = C.clampRect({ x: (rnd() - 0.5) * 6000, y: (rnd() - 0.5) * 6000, w: rnd() * 3000, h: rnd() * 3000 }, b);
    assert.ok(inside(r, b), JSON.stringify([W, H, r]));
    assert.ok(r.w >= P.MIN_W && r.w <= P.MAX_W && r.h >= P.MIN_H, JSON.stringify(r));
    assert.deepStrictEqual(C.clampRect(r, b), r);   // idempotent
    const m = C.moveRect(r, (rnd() - 0.5) * 4000, (rnd() - 0.5) * 4000, b);
    assert.ok(inside(m, b) && m.w === r.w && m.h === r.h, 'a move keeps the size');
    const z = C.resizeRect(r, (rnd() - 0.2) * 3000, (rnd() - 0.2) * 3000, b);
    assert.ok(inside(z, b) && z.x === r.x && z.y === r.y && z.w >= P.MIN_W && z.h >= P.MIN_H, 'a resize keeps the corner and stays inside');
  }
  // a window too small for the minimum: the panel shows at its minimum at the top-left and overflows, it is never hidden or negative
  const tiny = C.panelBounds(200, 200, 56), t = C.clampRect({ x: 500, y: 500, w: 300, h: 300 }, tiny);
  assert.deepStrictEqual(t, { x: 8, y: 56, w: 240, h: 120 });
  // resizing cannot push the far edge out of the window
  assert.strictEqual(C.resizeRect({ x: 1000, y: 100, w: 272, h: 200 }, 900, 200, B).w, 272);
  assert.strictEqual(C.resizeRect({ x: 1000, y: 100, w: 272, h: 200 }, 100, 50, B).w, 240);
  assert.strictEqual(C.resizeRect({ x: 100, y: 600, w: 272, h: 100 }, 272, 900, B).h, 136);
  // a panel that starts below its minimum (today's 96px ticker) can be moved without growing
  assert.deepStrictEqual(C.moveRect({ x: 1004, y: 644, w: 264, h: 96 }, -10, 0, B), { x: 994, y: 640, w: 264, h: 96 });
  // snapping: within 12px of an edge margin, on all four edges, not beyond
  assert.deepStrictEqual(C.snapRect({ x: 20, y: 68, w: 300, h: 300 }, B), { x: 8, y: 56, w: 300, h: 300 });
  assert.deepStrictEqual(C.snapRect({ x: 21, y: 69, w: 300, h: 300 }, B), { x: 21, y: 69, w: 300, h: 300 });
  assert.deepStrictEqual(C.snapRect({ x: 960, y: 430, w: 300, h: 300 }, B), { x: 972, y: 436, w: 300, h: 300 });
  // keyboard steps: 8px, 32px with Shift
  assert.deepStrictEqual(C.keyDelta('ArrowLeft', false), [-8, 0]);
  assert.deepStrictEqual(C.keyDelta('ArrowDown', true), [0, 32]);
  assert.strictEqual(C.keyDelta('a', false), null);
  // opacity: blur holds at 8px down to 30% then fades to 0; shadow under 100; dim text and the dark text backing apply at 60 and below; edge at 0
  assert.deepStrictEqual([100, 92, 30, 15, 0].map(C.blurFor), [8, 8, 8, 4, 0]);
  assert.deepStrictEqual(C.textMode(100), { shadow: false, dim: false, edge: false });
  assert.deepStrictEqual(C.textMode(92), { shadow: true, dim: false, edge: false });
  assert.deepStrictEqual(C.textMode(61), { shadow: true, dim: false, edge: false });
  assert.deepStrictEqual(C.textMode(60), { shadow: true, dim: true, edge: false });
  assert.deepStrictEqual(C.textMode(0), { shadow: true, dim: true, edge: true });
  assert.strictEqual(C.opacityStep(92), 92); assert.strictEqual(C.opacityStep(91), 91);
  assert.strictEqual(C.opacityStep(40), 40); assert.strictEqual(C.opacityStep(150), 92); assert.strictEqual(C.opacityStep('9'), 92); assert.strictEqual(C.opacityStep(NaN), 92);
  assert.strictEqual(C.rectSentence('Usage', { x: 120, y: 80, w: 300, h: 240 }), 'Usage panel at 120, 80, size 300 by 240.');
  // saved state: valid, then every kind of corrupt storage falls back without throwing
  const good = { usage: { x: 100, y: 90, w: 300, h: 400, o: 40 }, ticker: { x: 900, y: 500, w: 260, h: 150, o: 0 }, chat: null };
  assert.deepStrictEqual(C.parseLayout(JSON.stringify(good)), good);
  assert.deepStrictEqual(C.parseLayout(C.serializeLayout(good)), good);
  const none = { usage: null, ticker: null, chat: null };   // T-063 added the chat panel id
  [null, undefined, '', 'null', '{', '[1,2]', '"x"', '42', 'true', '{"usage":5}', '{"usage":[]}', '{"usage":{}}', '\u0000￾'].forEach(x => assert.deepStrictEqual(C.parseLayout(x), none, String(x)));
  const bad = v => JSON.stringify({ usage: Object.assign({}, good.usage, v), ticker: good.ticker });
  [{ x: 'a' }, { y: null }, { w: 239 }, { w: 521 }, { h: 119 }, { x: 1e9 }, { w: NaN }, { h: -5 }].forEach(v => {
    const r = C.parseLayout(bad(v)); assert.strictEqual(r.usage, null, JSON.stringify(v)); assert.deepStrictEqual(r.ticker, good.ticker);   // a bad panel falls back alone
  });
  assert.strictEqual(C.parseLayout(bad({ o: 'x' })).usage.o, 92); assert.strictEqual(C.parseLayout(bad({ o: 140 })).usage.o, 92); assert.strictEqual(C.parseLayout(bad({ o: -1 })).usage.o, 92);
  assert.strictEqual(C.parseLayout('{"usage":{"x":1e999,"y":0,"w":300,"h":300}}').usage, null);   // Infinity
  // a saved layout bigger than the window is clamped on load
  const big = C.parseLayout(JSON.stringify({ usage: { x: 5000, y: 5000, w: 520, h: 9000 } })).usage;
  assert.ok(inside(C.clampRect(big, C.panelBounds(1000, 600, 56)), C.panelBounds(1000, 600, 56)));
  console.log('layout ok');
} else if (mode === 'chat') {
  /* T-063: pure chat logic; the same fixtures are read by tests/test_chat.py */
  const X = JSON.parse(fs.readFileSync(process.argv[4], 'utf8')), K = C.chat, A = D.chat.agents;
  assert.strictEqual(A.length, 8);
  X.mentions.forEach(c => { const p = K.parseMentions(c.text, A); assert.deepStrictEqual([p.ids, p.all, p.unknown], [c.ids, c.all, c.unknown], c.text); });
  assert.strictEqual(K.errCode({ code: 'unavailable' }), 'unavailable'); assert.strictEqual(K.errCode({ message: 'db is Unavailable now' }), 'unavailable'); assert.strictEqual(K.errCode(null), null);
  assert.strictEqual(K.canMove('constructor', 'new'), false); assert.strictEqual(K.newAsk('@constructor please check', D.chat, 1, () => 0.5, 'u').recipients.pmo.status, 'new');
  { let n = 0, slept = 0; K.retryOnce(() => (++n === 1 ? Promise.reject({ code: 'unavailable' }) : Promise.resolve('ok')), () => 0, (f, ms) => { slept = ms; f(); }).then(v => { assert.strictEqual([v, n, slept].join(), 'ok,2,400'); });
    let m = 0; K.retryOnce(() => { m++; return Promise.reject({ code: 'revoked' }); }).catch(e => { assert.strictEqual(m, 1); });
    let q = 0; K.retryOnce(() => { q++; return Promise.reject({ code: 'unavailable' }); }, () => 0, (f) => f()).catch(e => { assert.strictEqual(q, 2); }); }
  X.scan.forEach(c => assert.strictEqual(K.scan(c.text), c.hit, JSON.stringify(c.hit)));
  assert.deepStrictEqual(K.route(K.parseMentions('hello', A), 'pmo'), ['pmo']);
  assert.deepStrictEqual(K.route(K.parseMentions('@Fang @Dinda', A), 'pmo'), ['architect', 'designer']);
  // completions: trigger at the start or after whitespace only, caret decides the query
  let c = K.completions('hi @fa', 6, A); assert.deepStrictEqual([c.start, c.query, c.items.map(i => i.name)], [3, 'fa', ['Fang']]);
  c = K.completions('@', 1, A); assert.strictEqual(c.items.length, 9); assert.strictEqual(c.items[8].id, 'all');
  c = K.completions('@a', 2, A); assert.deepStrictEqual(c.items.map(i => i.name), ['April', 'all']);
  assert.strictEqual(K.completions('mail x@fa', 9, A), null);
  assert.strictEqual(K.completions('@fang and', 9, A), null);
  assert.strictEqual(K.completions('@fang', 2, A).query, 'f');
  assert.strictEqual(K.completions('no at', 5, A), null);
  assert.strictEqual(K.completions('@zzz', 4, A).items.length, 0);
  // newAsk shape
  const seq = [0.1, 0.5, 0.9, 0.3]; let q = 0; const ask = K.newAsk('@Fang and @Dinda, look', D.chat, 1764165240000, () => seq[q++ % 4], 'u-test', 'r-x');
  assert.deepStrictEqual(Object.keys(ask), ['v', 'kind', 'id', 'author', 'author_uid', 'text', 'created_at', 'mentions', 'all', 'unknown', 'in_reply_to', 'recipients']);
  assert.ok(/^m-[0-9a-z]{6,12}-[0-9a-z]{4}$/.test(ask.id), ask.id);
  assert.deepStrictEqual([ask.mentions, ask.all, ask.unknown, ask.in_reply_to, ask.author], [['architect', 'designer'], false, [], 'r-x', 'merwyn']);
  assert.deepStrictEqual(Object.keys(ask.recipients), ['architect', 'designer']);
  assert.deepStrictEqual(ask.recipients.architect, { status: 'new', reply_id: null, at: ask.created_at, by: 'page' });
  assert.ok(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(ask.created_at));
  assert.deepStrictEqual(Object.keys(K.newAsk('plain', D.chat, 1e12, Math.random, 'u').recipients), ['pmo']);
  assert.strictEqual(Object.keys(K.newAsk('@all go', D.chat, 1e12, Math.random, 'u').recipients).length, 8);
  assert.strictEqual(K.newAsk('   ', D.chat, 1e12, Math.random, 'u'), null);
  assert.strictEqual(K.newAsk('x'.repeat(4001), D.chat, 1e12, Math.random, 'u'), null);
  assert.ok(K.valid(ask)); assert.ok(!K.valid({ kind: 'ask' })); assert.ok(!K.valid(null));
  // transitions (same table as chat.py)
  const S5 = ['new', 'picked', 'replying', 'answered', 'needs_merwyn'], ok = new Set(['new>picked', 'picked>replying', 'picked>new', 'picked>answered', 'picked>needs_merwyn', 'replying>answered', 'replying>needs_merwyn', 'replying>new', 'needs_merwyn>answered']);
  S5.forEach(a => S5.forEach(b => assert.strictEqual(K.canMove(a, b), ok.has(a + '>' + b), a + b)));
  assert.strictEqual(K.label('new', 'Janice'), 'waiting for Janice to pick up'); assert.strictEqual(K.label('replying', 'Fang'), 'Fang is replying');
  assert.strictEqual(K.label('answered', 'x'), 'answered'); assert.strictEqual(K.label('needs_merwyn', 'x'), 'needs you'); assert.strictEqual(K.label('picked', 'Janice'), 'Janice picked this up');
  // threads: asks by time then id, replies grouped under their ask by time, skewed clocks, invalid docs dropped
  const mk = (id, t, extra) => Object.assign({ v: 1, kind: 'ask', id, text: 'x', created_at: t, recipients: { architect: { status: 'new' } } }, extra);
  const rp = (id, to, t, extra) => Object.assign({ v: 1, kind: 'reply', id, reply_to: to, author: 'architect', text: 'r', created_at: t }, extra);
  const th = K.threads([rp('r2', 'a2', '2026-11-26T10:00:05Z'), mk('a2', '2026-11-26T10:00:00Z'), mk('a1', '2026-11-26T10:00:00Z'), rp('r1', 'a2', '2026-11-26T09:59:00Z'), rp('lost', 'zzz', '2026-11-26T10:00:00Z'), { kind: 'ask' }, mk('a0', '2026-11-26T10:01:00.500Z')]);
  assert.deepStrictEqual(th.map(t => t.ask.id), ['a1', 'a2', 'a0']);
  assert.deepStrictEqual(th[1].replies.map(r => r.id), ['r1', 'r2']);   // the reply with the earlier clock sorts first inside its ask, and never leaves it
  // live waiting and the overlay
  const docs = [mk('a1', '2026-11-26T10:00:00Z', { recipients: { architect: { status: 'needs_merwyn' }, designer: { status: 'answered' } } }), mk('a2', '2026-11-26T10:05:00Z', { recipients: { architect: { status: 'needs_merwyn' }, pmo: { status: 'new' } } })];
  const live = K.liveWaiting(docs); assert.deepStrictEqual(live, { architect: ['a1', 'a2'] });
  const st = C.stateAt(D, 0), before = JSON.stringify(st), w = C.withLive(st, live);
  assert.strictEqual(JSON.stringify(st), before);   // the replay state is untouched
  assert.deepStrictEqual(w.agents.architect.waiting, ['chat:a1', 'chat:a2']); assert.strictEqual(C.needs(w), C.needs(st) + 2); assert.strictEqual(C.agentStatus(w, 'architect'), 'waiting');
  const s2 = C.stateAt(D, 40); K.setLive(s2, live); const n1 = C.needs(s2); K.setLive(s2, live); assert.strictEqual(C.needs(s2), n1);   // idempotent
  K.setLive(s2, {}); assert.strictEqual(C.needs(s2), C.needs(C.stateAt(D, 40)));   // cleared when the chat wait ends
  assert.strictEqual(C.needs(C.withLive(C.stateAt(D, 0), {})), 0);
  // office status and unseen replies
  assert.deepStrictEqual(K.officeStatus({ running: true, last_inbox_at: '2026-11-26T10:00:00Z' }, Date.parse('2026-11-26T10:14:00Z')).running, true);
  assert.strictEqual(K.officeStatus({ running: true, last_inbox_at: '2026-11-26T10:00:00Z' }, Date.parse('2026-11-26T10:16:00Z')).running, false);
  assert.strictEqual(K.officeStatus({ running: false, last_inbox_at: '2026-11-26T10:00:00Z' }, Date.parse('2026-11-26T10:01:00Z')).running, false);
  assert.deepStrictEqual(K.officeStatus(null, 0), { running: false, last: null });
  assert.strictEqual(K.unseen([rp('r1', 'a', '2026-11-26T10:00:00Z'), rp('r2', 'a', '2026-11-26T11:00:00Z'), mk('a', '2026-11-26T12:00:00Z')], '2026-11-26T10:30:00Z').length, 1);
  // markup injection: text only, https links only
  const evil = '<script>alert(1)</script> <img src=x onerror=1> javascript:alert(1) [x](javascript:alert(2)) http://plain.test https://good.test/a?b=1 and @Fang';
  const parts = K.blocks(evil, A)[0].parts;
  assert.deepStrictEqual(parts.filter(p => p.t === 'link'), [{ t: 'link', s: 'good.test', href: 'https://good.test/a?b=1' }]);
  assert.deepStrictEqual(parts.filter(p => p.t === 'men'), [{ t: 'men', s: '@Fang', id: 'architect' }]);
  assert.strictEqual(parts.map(p => p.s === undefined ? '' : (p.t === 'link' ? p.href : p.s)).join(''), evil);   // nothing is dropped or rewritten
  assert.ok(parts.every(p => ['text', 'link', 'men'].includes(p.t)));
  const code = K.blocks('before\n```js\n<b>x</b>\n```\nafter', A); assert.deepStrictEqual(code.map(b => b.t), ['p', 'code', 'p']); assert.strictEqual(code[1].s, '<b>x</b>');
  // the avatar colours: every written name reaches 4.5:1 on the bubble fill
  const BODY = new Function('return ' + h.match(/var BODY = (\{[^}]*\})/)[1])();
  assert.strictEqual(Object.keys(BODY).length, 8);
  Object.keys(BODY).forEach(k => assert.ok(K.contrast(K.nameCol(BODY[k]), K.FILL) >= 4.5, k));
  assert.strictEqual(K.nameCol('#eceae4'), '#eceae4');
  assert.notStrictEqual(K.nameCol('#4b3f72'), '#4b3f72');
  console.log('chat ok');
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

    def test_panel_layout_maths(self):
        self.assertIn("layout ok", self.node(str(HTML), "layout"))

    def test_chat_logic_under_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = REPO / "tests/fixtures"
            scan = [{"text": "".join(p if isinstance(p, str) else p[1] * p[2] for p in c["parts"]), "hit": c["hit"]}
                    for c in json.loads((fx / "chat-scan.json").read_text(encoding="utf-8"))["cases"]]
            x = {"mentions": json.loads((fx / "chat-mentions.json").read_text(encoding="utf-8"))["cases"], "scan": scan}
            self.assertIn("chat ok", self.node(str(HTML), "chat", self.json_file(tmp, "chat.json", x)))

    def test_layout_storage_is_always_inside_try_and_the_key_is_versioned(self):
        html = HTML.read_text(encoding="utf-8")
        lines = [l for l in html.splitlines() if "localStorage" in l]
        self.assertTrue(lines)
        for l in lines:
            self.assertRegex(l, r"try\s*\{[^}]*localStorage", l)   # every storage touch is wrapped: the page works when storage throws
        self.assertIn("office.layout.v1", html)

    def test_panel_controls_are_named_and_reset_is_in_the_gear_menu(self):
        html = HTML.read_text(encoding="utf-8")
        for needle in ("'Move ' + nm + ' panel'", "'Resize ' + nm + ' panel'", "Background opacity", "Reset layout", "Layout reset"):
            self.assertIn(needle, html)
        self.assertRegex(html, r"#stage\{position:absolute;left:0;right:0;")   # the stage runs full width behind the panels
        # at 60% and below each text line keeps a dark backing; the panel fill is not touched by it
        self.assertRegex(html, r"\.pp\.tpd :not\(:has\(\*\)\)[^{]*\{background:rgba\(12,13,22,\.8\)")   # any leaf element, not a tag list
        self.assertNotRegex(html, r"\.pp\.tpd :is\(")
        self.assertRegex(html, r'class="oprange" type="range" id="o-\' \+ id \+ \'" min="0" max="100" step="1"')   # 92 is reachable on the slider

    def test_percentage_maths(self):
        self.assertIn("shares ok", self.node(str(HTML), "shares"))

    def test_percentages_within_provider(self):
        self.assertIn("provshares ok", self.node(str(HTML), "provshares"))

    def test_recorded_replay_totals_and_percentages(self):
        data, _ = office_app.build_data(OFFICE, None, LEDGER)
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "r.html"
            self.assertEqual(office_app.main(["ai-office", "--ledger", str(LEDGER), "--out", str(page)]), 0)
            led = data["ledger"]
            py = {"tokens": led["session"]["tokens"], "runs": led["session"]["runs"], "nr": led["session"]["not_reported"],
                  "agents": {k: v["tokens"] for k, v in led["agents"].items()}}
            self.assertIn("rec ok", self.node(str(page), "rec", self.json_file(tmp, "p.json", py)))

    def test_budget_maths_and_views_recorded(self):
        data, _ = office_app.build_data(OFFICE, None, LEDGER)
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "r.html"
            self.assertEqual(office_app.main(["ai-office", "--ledger", str(LEDGER), "--out", str(page)]), 0)
            led = data["ledger"]
            py = {"tokens": led["session"]["tokens"], "agents": {k: v["tokens"] for k, v in led["agents"].items()}}
            self.assertIn("budgets rec ok", self.node(str(page), "budgets", self.json_file(tmp, "p.json", py)))

    def test_budget_maths_and_views_synthetic(self):
        self.assertIn("budgets syn ok", self.node(str(HTML), "budgets"))

    def test_synthetic_percentages_add_to_100(self):
        self.assertIn("syn ok", self.node(str(HTML), "syn"))

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
        self.assertEqual(sorted(data["providers"]), ["anthropic-api", "claude-code", "claude-sdk", "deepseek", "openai"])
        planned = {a["id"]: a["planned_model"] for a in data["agents"]}
        self.assertEqual(planned, {"architect": "opus", "reviewer": "opus", "pm": "sonnet", "pmo": "sonnet", "engineer": "sonnet",
                                   "compliance": "sonnet", "curator": "sonnet", "designer": "sonnet"})
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('class="synpill" data-syn>synthetic</span>', html)   # the panel header pill
        self.assertGreaterEqual(html.count('<span class="syn">synthetic</span>'), 1)   # the suffix after every figure group


LEDGER = REPO / "offices/ai-office/usage/session_01MDGJq3GfaeozLojJo8W5Td.jsonl"


class Recorded(unittest.TestCase):
    """--ledger: replay a recorded agent-run ledger (T-057)."""

    def test_ledger_page_data_is_recorded_with_totals(self):
        data, probs = office_app.build_data(OFFICE, None, LEDGER)
        self.assertEqual(probs, [])
        self.assertEqual(data["log"]["usage_source"], "recorded")
        self.assertEqual(data["log"]["not_reported"], ["split", "model", "main_session"])
        self.assertEqual(data["log"]["provider"], "claude-code")
        self.assertEqual(data["providers"]["claude-code"]["label"], "Claude Code subagents (Max plan)")
        self.assertEqual(data["ledger"]["session"]["tokens"], sum(e["total"] or 0 for e in data["events"]))
        self.assertTrue(all(e["type"] == "usage" and "total" in e for e in data["events"]))
        self.assertNotIn("$", json.dumps(data["events"]))

    def test_cli_writes_the_default_name_and_check_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "u.html"
            self.assertEqual(office_app.main(["ai-office", "--ledger", str(LEDGER), "--out", str(out)]), 0)
            self.assertEqual(office_app.main(["ai-office", "--ledger", str(LEDGER), "--out", str(out), "--check"]), 0)
            out.write_text("x", encoding="utf-8")
            self.assertEqual(office_app.main(["ai-office", "--ledger", str(LEDGER), "--out", str(out), "--check"]), 1)
        self.assertEqual(office_app.main(["ai-office", "--ledger", str(LEDGER), "--fixture", str(office_app.DEFAULT_FIXTURE)]), 2)
        self.assertEqual(office_app.main(["ai-office", "--ledger", "/nonexistent.jsonl"]), 2)

    def test_data_rule_hit_exits_1_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / LEDGER.name
            bad.write_text(LEDGER.read_text(encoding="utf-8") + '{"n":99,"sprint":4,"agent":"pm","tasks":["T-001"],"step":"x","tokens":1,'
                           '"tool_uses":1,"duration_ms":1,"note":"a@b.example"}\n', encoding="utf-8")
            out = Path(tmp) / "o.html"
            self.assertEqual(office_app.main(["ai-office", "--ledger", str(bad), "--out", str(out), "--allow-errors"]), 1)
            self.assertFalse(out.exists())

    def test_gitignored_default_page(self):
        self.assertIn("engine/app/usage-*.html", (REPO / ".gitignore").read_text(encoding="utf-8").splitlines())

    def test_recorded_panel_code_never_says_synthetic(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for fn in ("function focusRec", "function rowHTML", "function budgetBar", "function budgetText"):
            body = re.search(re.escape(fn) + r".*?\n\s{0,2}}\n", text, re.S).group(0)
            self.assertNotIn("synth", body.lower(), fn)
        self.assertIn("(REC ? ' (replay)' : ' (synth)')", text)                # clock label
        summary = re.search(r"function usageSummary.*?\n}\n", text, re.S).group(0)
        self.assertIn("SYN ?", summary)                                        # the synthetic tag only on the synthetic page
        self.assertIn("(SYN ?", re.search(r"function fillSheet.*?\n}\n", text, re.S).group(0))   # synthetic pill only when SYN
        self.assertIn("var SYN = !!(D.log && D.log.v === 1 && !REC);", text)

    def test_budget_wording_is_the_users_budget_never_capacity_or_plan(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("of your budget", text)
        self.assertIn("budget not set", text)
        for bad in ("of capacity", "of the plan", "% of plan", "capacity"):
            self.assertNotIn(bad, text)
        self.assertIn("Anthropic does not publish the Max plan", text)
        self.assertNotRegex(text, r"--warn[^;}]*;[^}]*\.hatch|\.hatch\{[^}]*(--warn|--bad)")   # over budget never uses the amber or red of needs-you

    def test_budget_colours_are_palette_tokens_and_never_the_needs_you_amber(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        theme = (REPO / "offices/ai-office/theme/theme.yaml").read_text(encoding="utf-8")
        self.assertIn('near: "#f0e04a"', theme)
        for cls in (".bar i.lv-near{background:var(--near)}", ".bar i.lv-alert,.bar i.lv-over{background:var(--bad)}"):
            self.assertIn(cls, text)
        self.assertNotRegex(text, r"\.(bar i|bx|bw|dh)[^{]*\.lv-[^{]*\{[^}]*(--warn|#f4a261)")   # budget states never use the amber
        self.assertNotRegex(text, r"\.bar i\.lv[^{]*\{[^}]*#")                                    # no hard-coded hex in the template rules

    def test_collapsed_summary_line_text_takes_the_state_colour(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for cls in (".usum .lv-ok{color:var(--accent)}", ".usum .lv-near{color:var(--near)}",
                    ".usum .lv-alert,.usum .lv-over{color:var(--bad-text)}"):
            self.assertIn(cls, text)

    def test_state_word_and_aria_label_carry_the_level(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("near: 'near budget', alert: 'at limit'", text)
        self.assertIn("', ' + LVWORD[r.level]", text)   # rowSentence: appended to the aria-label, no colour names
        for colour in ("green", "yellow", "red"):
            self.assertNotRegex(text, r"aria-label[^\n]*" + colour)

    def test_mode_is_remembered_in_try_and_shown_as_a_radiogroup(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("office.usage.mode.v1", text)
        for l in [l for l in text.splitlines() if "MODE_KEY" in l and "localStorage" in l]:
            self.assertRegex(l, r"try\s*\{[^}]*localStorage")
        self.assertIn('role="radiogroup" aria-label="Usage view"', text)
        self.assertIn("aria-checked", text)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class UsageSwitchUnderNode(unittest.TestCase):
    """Page-script pieces (fmtTok, fmtPair, segKey, the document keydown handler) are cut out of the template and run with stubs."""

    PROBE = r"""
const fs = require('fs'), assert = require('assert');
const src = fs.readFileSync(process.argv[2], 'utf8');
const grab = (start) => { const i = src.indexOf(start); assert.ok(i >= 0, start); let j = src.indexOf('\n}\n', i); return src.slice(i, j + 3); };
const fns = [grab('function fmtTok('), grab('function fmtPair('), grab('function segKey(')].join('\n');
const h0 = src.indexOf("document.addEventListener('keydown', function (e) {"); const h1 = src.indexOf('\n});', h0);
const handler = src.slice(h0, h1 + 4);
const calls = [];
const ctx = new Function('calls', 'document', '$', 'setMode', 'stepEv', 'setSpeed', 'closeMenus', 'closeSheet', 'focusAgent', 'SYSTEM_RM', 'REDUCED', 'focused', 'handlers',
  fns + '\n' + handler + '\nreturn {fmtTok, fmtPair, segKey};');
const handlers = [];
const radio = { dataset: { mode: 'summary' }, focus() {} };
const box = { querySelector: () => radio, classList: { contains: () => false } };
const target = { tagName: 'BUTTON', id: '', classList: { contains: () => false }, closest: (sel) => (sel === '[role=radio]' ? radio : (sel === '[role=radiogroup]' ? box : null)) };
const doc = { addEventListener: (n, f) => handlers.push(f) };
const api = ctx(calls, doc, () => box, (m) => calls.push('setMode:' + m), (d) => calls.push('step:' + d), () => calls.push('speed'), () => false, () => {}, () => {}, false, false, null, handlers);
const mk = (key) => { const e = { key, target, stopped: false, prevented: false, preventDefault() { this.prevented = true; }, stopPropagation() { this.stopped = true; } }; return e; };
if (process.argv[3] === 'tok') {
  const t = api.fmtTok;
  assert.strictEqual(t(999), '999'); assert.strictEqual(t(1500), '1.5k'); assert.strictEqual(t(999400), '999k');
  assert.strictEqual(t(999500), '1.0M'); assert.strictEqual(t(999600), '1.0M'); assert.strictEqual(t(1000000), '1.0M'); assert.strictEqual(t(2150000), '2.2M');
  for (let n = 0; n < 3e6; n += 137) assert.ok(!/^1000k$/.test(t(n)), n);
  console.log('tok ok');
} else if (process.argv[3] === 'pair') {
  const p = api.fmtPair;
  assert.strictEqual(p(1649066, 2150000, 77), '1.65M / 2.15M');
  assert.strictEqual(p(1125617, 1500000, 75), '1.13M / 1.5M');
  assert.strictEqual(p(30785, 50000, 62), '31k / 50k');
  assert.strictEqual(p(3813702, 5000000, 76), '3.8M / 5M');
  assert.strictEqual(p(100, 0, null), '100 / 0');
  // whatever is shown, the ratio of the shown figures rounds to the % (when 3 decimals are enough)
  for (const [u, b] of [[1649066, 2150000], [1125617, 1500000], [514115, 650000], [222869, 300000], [202660, 250000], [68590, 100000], [30785, 50000]]) {
    const pct = Math.round(100 * u / b), [a, c] = p(u, b, pct).split(' / ').map((x) => parseFloat(x));
    assert.strictEqual(Math.round(100 * a / c), pct, p(u, b, pct));
  }
  console.log('pair ok');
} else {
  for (const k of ['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp', 'Home', 'End']) {
    calls.length = 0; const e = mk(k);
    api.segKey(e);
    assert.ok(e.stopped && e.prevented, k + ' stopped at the switch');
    assert.deepStrictEqual(calls.length, 1); assert.ok(calls[0].startsWith('setMode:'));
    calls.length = 0; const e2 = mk(k); handlers[0](e2);   // even if one did reach the document handler
    assert.deepStrictEqual(calls, [], k + ' must not step or toggle the replay');
  }
  console.log('keys ok');
}
"""

    def run_probe(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "probe.js"
            f.write_text(self.PROBE, encoding="utf-8")
            r = subprocess.run(["node", str(f), str(TEMPLATE), mode], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def test_fmt_tok_rolls_over_to_millions(self):
        self.assertIn("tok ok", self.run_probe("tok"))

    def test_used_and_budget_show_enough_precision_to_read_like_the_percentage(self):
        self.assertIn("pair ok", self.run_probe("pair"))

    def test_arrow_keys_on_the_switch_do_not_reach_the_replay_shortcuts(self):
        self.assertIn("keys ok", self.run_probe("keys"))


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


class ChatBuild(unittest.TestCase):
    """T-063: the chat is a build flag; the recorded usage page and the default build never have it."""

    def test_flag_adds_data_chat_from_org(self):
        data, _ = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE, chat=True)
        self.assertEqual([a["name"] for a in data["chat"]["agents"]], ["Janice", "Emmy", "Fang", "Sebastian", "Cahyani", "Wulan", "April", "Dinda"])
        self.assertEqual((data["chat"]["default"], data["chat"]["all"], data["chat"]["max_len"], data["chat"]["lease_s"]), ("pmo", "all", 4000, 1800))
        committed = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        self.assertEqual(committed["chat"], data["chat"])

    def test_default_build_has_no_chat_key(self):
        data, _ = office_app.build_data(OFFICE, office_app.DEFAULT_FIXTURE)
        self.assertNotIn("chat", data)

    def test_chat_with_ledger_builds_the_one_published_page(self):
        only, _ = office_app.build_data(OFFICE, None, LEDGER)
        both, _ = office_app.build_data(OFFICE, None, LEDGER, chat=True)
        self.assertEqual({k: v for k, v in both.items() if k != "chat"}, only)
        committed = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        self.assertEqual(both["chat"], committed["chat"])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "one.html"
            argv = ["ai-office", "--ledger", str(LEDGER), "--chat", "--out", str(out)]
            self.assertEqual(office_app.main(argv), 0)
            self.assertEqual(office_app.main(argv + ["--check"]), 0)
            self.assertEqual(json.loads(block(out.read_text(encoding="utf-8"), "office-data")), json.loads(json.dumps(both)))
            out.write_text(out.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertEqual(office_app.main(argv + ["--check"]), 1)
            office_app.main(argv)
            if shutil.which("node"):
                led = both["ledger"]
                x = CoreUnderNode("test_recorded_replay_totals_and_percentages")
                py = {"tokens": led["session"]["tokens"], "runs": led["session"]["runs"], "nr": led["session"]["not_reported"],
                      "agents": {k: v["tokens"] for k, v in led["agents"].items()}}
                self.assertIn("rec ok", x.node(str(out), "rec", x.json_file(tmp, "p.json", py)))
                py = {"tokens": led["session"]["tokens"], "agents": {k: v["tokens"] for k, v in led["agents"].items()}}
                self.assertIn("budgets rec ok", x.node(str(out), "budgets", x.json_file(tmp, "b.json", py)))

    def test_claude_is_only_reached_through_chat_init_which_needs_the_flag(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\buse\('(db|user)'\)", html)), 2)
        a, b = html.index("function chatInit()"), html.index("function onChatDocs()")
        self.assertEqual(len(re.findall(r"\buse\('(db|user)'\)", html[a:b])), 2)
        self.assertIn("if (CFG) initChat();", html)
        self.assertEqual(html.count("initChat()"), 2)   # its definition and the one guarded call
        self.assertIn("if (!CFG) { ['chat', 'chatbtn']", html)   # no flag: panel and button are removed

    def test_chat_text_is_never_html(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        a, b = html.index("/* ---------- office chat (T-063)"), html.index("/* ---------- boot ---------- */")
        view = html[a:b]
        self.assertNotIn("innerHTML", view.replace("st.innerHTML = '<i></i>'", ""))   # the one fixed string, no db text
        self.assertNotIn("esc(", view)
        self.assertNotIn("insertAdjacentHTML", view)

    def test_page_without_chat_has_no_chat_data_or_button_after_removal(self):
        data = json.loads(block(HTML.read_text(encoding="utf-8"), "office-data"))
        self.assertIn("chat", data)
