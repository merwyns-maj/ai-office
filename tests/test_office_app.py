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

from engine.runtime import events  # noqa: E402
from tests._helpers import REPO  # noqa: E402

HTML = REPO / "engine/app/office.html"
TEMPLATE = REPO / "engine/app/office.template.html"
OFFICE = REPO / "offices/ai-office"
ALL_TYPES = REPO / "tests/fixtures/events-all-types.jsonl"


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
            self.assertEqual(len(data["events"]), 45)


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
const full = process.argv[3] === 'all' ? JSON.parse(fs.readFileSync(process.argv[4], 'utf8')) : null;
function run(D) {
  const tl = C.timeline(D.events), out = {};
  let s = C.initState(D);
  D.events.forEach((e, i) => C.apply(s, e, tl[i].start));
  return { s, tl };
}
if (!full) {
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
} else {
  const E = full.events, d2 = Object.assign({}, D, { events: E }), tl = C.timeline(E);
  let s = C.initState(d2), seen = {};
  E.forEach((e, i) => { C.apply(s, e, tl[i].start); Object.keys(s.agents).forEach(a => seen[C.agentStatus(s, a) + (C.tagWord(s, a) ? ':' + C.tagWord(s, a) : '')] = 1); });
  assert.ok(seen['blocked:Blocked'], 'blocked state');
  assert.ok(seen['blocked:Rejected'], 'rejected state');
  assert.ok(seen.waiting && seen.working);
  assert.strictEqual(s.tasks['T-901'].stage, 'done');
  assert.deepStrictEqual(s.unknown, []);
  console.log('all-types ok');
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

    def test_fixture_replay(self):
        self.assertIn("core ok", self.node(str(HTML)))

    def test_all_types_log(self):
        data, probs = office_app.build_data(OFFICE, ALL_TYPES)
        self.assertEqual(probs, [])
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "all.json"
            j.write_text(json.dumps({"events": data["events"]}), encoding="utf-8")
            self.assertIn("all-types ok", self.node(str(HTML), "all", str(j)))


if __name__ == "__main__":
    unittest.main()
