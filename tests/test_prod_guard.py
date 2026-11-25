"""Tests for engine/guard/prod_guard.py. Fixtures only: no real host, credential or row, no network.

Run from the repo root:  python -m unittest -v
"""
import ast
import io
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from engine.guard import prod_guard

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "engine" / "guard" / "prod_guard.py"
EXAMPLE = REPO / "engine" / "guard" / "prod_guard.example.json"
FIX = REPO / "tests" / "fixtures" / "guard"
CONFIG = FIX / "config.json"
SQL_FIELDS = ("sql", "query", "statement")
PROD_TOOL = "mcp__remote-devices__nimbus-prod__"


def run_hook(stdin, *extra, config=CONFIG, script=SCRIPT, wrapper=False, python=None):
    """Run the hook as a subprocess. wrapper=True goes through the exact settings wrapper."""
    py = python or sys.executable
    data = stdin if isinstance(stdin, bytes) else stdin.encode("utf-8")
    if wrapper:
        cmd = " ".join(shlex.quote(str(x)) for x in [py, script, "--config", config, *extra]) + " || exit 2"
        argv = ["sh", "-c", cmd]
    else:
        argv = [py, str(script), "--config", str(config), *extra]
    return subprocess.run(argv, input=data, capture_output=True, timeout=30)


def payload_text(stdin):
    return stdin if isinstance(stdin, str) else json.dumps(stdin)


class CaseMixin:
    def check(self, case):
        r = run_hook(payload_text(case["stdin"]))
        out, err = r.stdout.decode(), r.stderr.decode()
        self.assertEqual(out, "", "stdout must be empty")
        if case["expect"] == "allow":
            self.assertEqual((r.returncode, err), (0, ""))
            return
        self.assertEqual(r.returncode, 2, err)
        self.assertEqual(len(err.strip().splitlines()), 1, "one stderr line")
        self.assertIn(f"rule={case['rule']}", err)
        self.assertIn("prod-guard BLOCKED", err)
        stdin = case["stdin"]
        if isinstance(stdin, dict) and isinstance(stdin.get("tool_input"), dict):
            ti = stdin["tool_input"]
            for v in [ti.get("command")] + [ti.get(f) for f in SQL_FIELDS]:
                if isinstance(v, str) and v.strip():
                    self.assertNotIn(v, err, "stderr must not echo payload text")


class TestCases(CaseMixin, unittest.TestCase):
    """One generated test per case in cases.json: test_<expect>_<name>."""


def _make(case):
    return lambda self: self.check(case)


CASES = json.loads((FIX / "cases.json").read_text(encoding="utf-8"))
for _c in CASES:
    setattr(TestCases, f"test_{_c['expect']}_{_c['name']}", _make(_c))


class TestCaseCoverage(unittest.TestCase):
    def test_minimum_case_counts(self):
        n = {k: sum(1 for c in CASES if c["expect"] == k) for k in ("block", "allow", "malformed")}
        self.assertGreaterEqual(n["block"], 3)
        self.assertGreaterEqual(n["allow"], 3)
        self.assertGreaterEqual(n["malformed"], 1)


class TestSentinelLeak(unittest.TestCase):
    def test_pii_sentinel_never_echoed(self):
        sql = "SELECT * FROM t WHERE nik = 'PII_SENTINEL_X'; DROP TABLE t"
        r = run_hook(json.dumps({"tool_name": PROD_TOOL + "pg_execute_query", "tool_input": {"query": sql}}))
        err = r.stderr.decode()
        self.assertEqual(r.returncode, 2)
        for bad in ("PII_SENTINEL_X", "nik", "DROP TABLE"):
            self.assertNotIn(bad, err)

    def test_hostile_tool_name_is_sanitised(self):
        r = run_hook(json.dumps({"tool_name": "mcp__x-prod__\nPII_SENTINEL_X pg_new", "tool_input": {}}))
        err = r.stderr.decode()
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("PII_SENTINEL_X", err)
        self.assertEqual(len(err.strip().splitlines()), 1)


class TestFailClosed(unittest.TestCase):
    OK = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})

    def test_wrapper_allows_normal_call(self):
        r = run_hook(self.OK, wrapper=True)
        self.assertEqual((r.returncode, r.stderr), (0, b""))

    def test_block_broken_import(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(SCRIPT, d)
            Path(d, "json.py").write_text("raise ImportError('shadow')\n")
            r = run_hook(self.OK, script=Path(d, "prod_guard.py"), wrapper=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"rule=internal-error", r.stderr)

    def test_block_syntax_error(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d, "prod_guard.py")
            shutil.copy(SCRIPT, dst)
            with open(dst, "a") as f:
                f.write("\n def (:\n")
            r = run_hook(self.OK, script=dst, wrapper=True)
        self.assertEqual(r.returncode, 2)

    def test_block_missing_interpreter(self):
        r = run_hook(self.OK, wrapper=True, python="/nonexistent/python3")
        self.assertEqual(r.returncode, 2)

    def test_malformed_undecodable_stdin(self):
        r = run_hook(b"\xff\xfe\x00", wrapper=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"rule=malformed-input", r.stderr)

    def test_block_oversize_stdin(self):
        r = run_hook(b" " * (prod_guard.MAX_INPUT + 1), wrapper=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"rule=input-too-large", r.stderr)

    def test_exactly_max_input_is_read(self):
        pad = prod_guard.MAX_INPUT - len(self.OK)
        r = run_hook(self.OK + " " * pad, wrapper=True)
        self.assertEqual(r.returncode, 0)

    @unittest.skipUnless(hasattr(signal, "SIGALRM"), "no SIGALRM on this platform")
    def test_block_deadline(self):
        stdin = json.dumps({"tool_name": "Bash", "tool_input": {"command": "a" * 40 + "!"}})
        t = time.monotonic()
        r = run_hook(stdin, "--deadline", "1", config=FIX / "slow_config.json", wrapper=True)
        self.assertEqual(r.returncode, 2)
        self.assertLess(time.monotonic() - t, 5)

    def test_block_internal_error(self):
        err = io.StringIO()
        stdin = mock.Mock(buffer=io.BytesIO(self.OK.encode()))
        with mock.patch.object(prod_guard, "decide", side_effect=RuntimeError("PII_SENTINEL_X")), \
                mock.patch.object(sys, "argv", ["prod_guard.py", "--config", str(CONFIG), "--deadline", "0"]), \
                mock.patch.object(sys, "stdin", stdin), redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                prod_guard._entry()
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("rule=internal-error", err.getvalue())
        self.assertIn("RuntimeError", err.getvalue())
        self.assertNotIn("PII_SENTINEL_X", err.getvalue())

    def test_bad_arguments_exit_2(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--nope"], input=b"", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"rule=internal-error", r.stderr)


class TestConfig(unittest.TestCase):
    OK = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})

    def cfg_with(self, mutate):
        data = json.loads(CONFIG.read_text())
        mutate(data)
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        self.addCleanup(os.unlink, f.name)
        json.dump(data, f)
        f.close()
        return f.name

    def assert_config_error(self, path):
        r = run_hook(self.OK, config=path)
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"rule=config-error", r.stderr)
        self.assertIn(b"config error", r.stderr)

    def test_missing_file(self):
        self.assert_config_error("/nonexistent/prod_guard.json")

    def test_bad_json(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        self.addCleanup(os.unlink, f.name)
        f.write("{nope")
        f.close()
        self.assert_config_error(f.name)

    def test_bad_regex(self):
        self.assert_config_error(self.cfg_with(
            lambda d: d["bash"]["write"].append({"id": "bash-bad", "pattern": "("})))

    def test_allowlist_action_apply_rejected(self):
        self.assert_config_error(self.cfg_with(lambda d: d["allowlist"][0].update(action="apply")))

    def test_allowlist_without_action_rejected(self):
        self.assert_config_error(self.cfg_with(lambda d: d["allowlist"][0].pop("action")))

    def test_wrong_version(self):
        self.assert_config_error(self.cfg_with(lambda d: d.update(version=2)))

    def test_example_config_valid(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--check-config", "--config", str(EXAMPLE)],
                           capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"prod-guard: config OK", r.stdout)

    def test_check_config_reports_error(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--check-config", "--config", "/nonexistent/x.json"],
                           capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 2)

    def test_lookup_env_then_script_folder(self):
        env = dict(os.environ, PROD_GUARD_CONFIG=str(CONFIG))
        r = subprocess.run([sys.executable, str(SCRIPT)], input=self.OK.encode(), capture_output=True,
                           env=env, timeout=30)
        self.assertEqual(r.returncode, 0)
        env.pop("PROD_GUARD_CONFIG")
        with tempfile.TemporaryDirectory() as d:     # no prod_guard.json next to the copy -> config error
            shutil.copy(SCRIPT, d)
            r = subprocess.run([sys.executable, str(Path(d, "prod_guard.py"))], input=self.OK.encode(),
                               capture_output=True, env=env, timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"rule=config-error", r.stderr)

    def test_allowlist_eligibility_enforced_in_decide(self):
        """A config whose write rules would not catch it: eligibility alone must deny."""
        def mutate(d):
            d["bash"]["write"] = []
            d["bash"]["read_only"] = []
            d["allowlist"][0]["command"] = "bytebase-submit-issue --project [^;]+"
        path = self.cfg_with(mutate)

        def go(cmd):
            return run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}), config=path)
        ok = go("bytebase-submit-issue --project PLACEHOLDER")
        self.assertEqual((ok.returncode, ok.stderr), (0, b""))
        for cmd in ("bytebase-submit-issue --project a..b",
                    "bytebase-submit-issue --project a > out",
                    "bytebase-submit-issue --project a apply",
                    "bytebase-submit-issue --project a\npsql x",
                    "bytebase-submit-issue --project $(id)"):
            r = go(cmd)
            self.assertEqual(r.returncode, 2, cmd)
            self.assertIn(b"rule=default-deny", r.stderr, cmd)


class TestUnits(unittest.TestCase):
    def test_classify_sql(self):
        c = prod_guard.classify_sql
        self.assertEqual(c("SELECT 1"), (True, ""))
        self.assertEqual(c("select 1;"), (True, ""))
        self.assertEqual(c("/* x */ SELECT 1 -- y"), (True, ""))
        self.assertEqual(c("WITH a AS (SELECT 1) SELECT * FROM a"), (True, ""))
        self.assertEqual(c("EXPLAIN SELECT 1"), (True, ""))
        self.assertEqual(c("SHOW search_path"), (True, ""))
        self.assertEqual(c("(SELECT 1)"), (True, ""))
        self.assertEqual(c("SELECT 1; SELECT 2"), (False, "sql-multi-statement"))
        self.assertEqual(c("SELECT 1; -- c\nDROP TABLE t"), (False, "sql-multi-statement"))
        self.assertEqual(c("EXPLAIN ANALYZE SELECT 1"), (False, "sql-not-read-only"))
        self.assertEqual(c("SELECT a INTO b FROM c"), (False, "sql-write:INTO"))
        self.assertEqual(c("SELECT * FROM t FOR UPDATE"), (False, "sql-write:UPDATE"))
        self.assertEqual(c("SELECT * FROM t FOR SHARE"), (False, "sql-write:FOR SHARE"))
        self.assertEqual(c("WITH d AS (DELETE FROM t RETURNING *) SELECT * FROM d"), (False, "sql-write:DELETE"))
        self.assertEqual(c("SELECT nextval('s')"), (False, "sql-write:NEXTVAL"))
        self.assertEqual(c("SELECT '--'; DROP TABLE t"), (False, "sql-multi-statement"))
        self.assertEqual(c("SELECT /*! DROP TABLE t */ 1"), (False, "sql-not-read-only"))
        self.assertEqual(c("SELECT 1 /* DROP */"), (False, "sql-write:DROP"))   # comments are scanned too
        self.assertEqual(c("VACUUM t"), (False, "sql-write:VACUUM"))
        self.assertEqual(c("BEGIN"), (False, "sql-not-read-only"))
        self.assertEqual(c(""), (False, "sql-not-read-only"))

    def test_sql_write_keyword(self):
        k = prod_guard.sql_write_keyword
        self.assertIsNone(k("select count(*) from t"))
        self.assertIsNone(k("select load_test from t"))
        self.assertEqual(k("please Delete x"), "DELETE")
        self.assertEqual(k("select pg_terminate_backend(1)"), "PG_TERMINATE_BACKEND")

    def test_allowlist_eligible(self):
        e = prod_guard.allowlist_eligible
        self.assertTrue(e("tool --project X --file migrations/a.sql"))
        for bad in ("a; b", "a && b", "a | b", "a `b`", "a $(b)", "a > b", "a < b", "a\nb", "x/../y",
                    "tool apply", "tool ROLLOUT", "tool approve", "tool deploy", "tool execute", "tool run-now"):
            self.assertFalse(e(bad), bad)

    def test_mentions_k8s_secret(self):
        m = prod_guard.mentions_k8s_secret
        self.assertTrue(m("Bash", {}, "kubectl get\n secrets"))
        self.assertTrue(m("Bash", {}, "KUBECTL GET SECRET x"))
        self.assertFalse(m("Bash", {}, "kubectl get pods"))
        self.assertFalse(m("Bash", {}, "echo secrets"))
        self.assertTrue(m("mcp__a__kubernetes__kubectl_get", {"a": {"b": ["secret"]}}, None))
        self.assertFalse(m("mcp__a__kubernetes__kubectl_get", {"a": "pods"}, None))
        self.assertFalse(m("mcp__a__other__pg_execute_query", {"q": "secrets"}, None))

    def test_format_block_has_no_payload_text(self):
        line = prod_guard.format_block("sql-write:DELETE", "mcp__x-prod__\nbad")
        self.assertIn("tool=<invalid>", line)
        self.assertNotIn("\n", line)
        self.assertIn("tool=<unknown>", prod_guard.format_block("default-deny", None))
        self.assertIn("rule=bash-helm-write", prod_guard.format_block("bash-helm-write", "Bash"))

    def test_decide_in_process(self):
        cfg = prod_guard.load_config(CONFIG)
        d = prod_guard.decide({"tool_name": "Bash", "tool_input": {"command": "ls"}}, cfg)
        self.assertTrue(d.allow)
        d = prod_guard.decide({"tool_name": "Bash", "tool_input": {"command": "kubectl get secrets"}}, cfg)
        self.assertEqual((d.allow, d.rule), (False, "k8s-secret-read"))
        self.assertEqual(d.reason, prod_guard.REASONS["k8s-secret-read"])


def _added_files():
    files = [p for p in (REPO / "engine" / "guard").iterdir() if p.is_file()]
    files += [p for p in FIX.iterdir() if p.is_file()]
    files.append(Path(__file__))
    return files


class TestHygiene(unittest.TestCase):
    # Detection patterns are built by concatenation so this file does not match itself.
    TLDS = "com|net|org|io|id|co|dev|app|cloud|local|internal|ai"
    DOMAIN = re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:" + TLDS + r")\b", re.I)
    ALLOWED_DOMAINS = ("code.claude.com", "example.com")
    URL_CRED = re.compile(r"://[^/\s:@]+:[^/\s@]+@")
    CRED = re.compile(r"(?:pass" r"word|pass" r"wd|sec" r"ret|tok" r"en)\s*[=:]\s*\S+", re.I)
    IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    LONG_DIGITS = re.compile(r"\b\d{16}\b")

    def test_no_real_hosts_credentials_or_data(self):
        problems = []
        for path in _added_files():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                where = f"{path.relative_to(REPO)}:{n}"
                for m in self.DOMAIN.finditer(line):
                    if not m.group(0).lower().endswith(self.ALLOWED_DOMAINS):
                        problems.append(f"{where} domain {m.group(0)}")
                for rx, label in ((self.URL_CRED, "url credentials"), (self.CRED, "credential"),
                                  (self.LONG_DIGITS, "16-digit number")):
                    if rx.search(line):
                        problems.append(f"{where} {label}")
                for m in self.IPV4.finditer(line):
                    if m.group(0) not in ("127.0.0.1", "0.0.0.0"):
                        problems.append(f"{where} ip {m.group(0)}")
        self.assertEqual(problems, [])

    def test_scan_covers_test_file_and_detects(self):
        self.assertIn(Path(__file__), _added_files())
        self.assertTrue(self.DOMAIN.search("db" ".klik" "acc" ".co" ".id"))
        self.assertTrue(self.CRED.search("pass" "word=abc"))
        self.assertTrue(self.IPV4.search("10" ".1" ".2" ".3"))

    def test_gitignore_and_no_installed_config(self):
        lines = (REPO / ".gitignore").read_text().splitlines()
        self.assertIn("prod_guard.json", [x.strip() for x in lines])
        self.assertFalse((REPO / "engine" / "guard" / "prod_guard.json").exists())


class TestNoNetwork(unittest.TestCase):
    @staticmethod
    def imports(path):
        names = set()
        for node in ast.walk(ast.parse(Path(path).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        return names

    def test_script_imports_stdlib_allowlist_only(self):
        allowed = {"argparse", "json", "os", "pathlib", "re", "signal", "sys", "typing"}
        self.assertEqual(self.imports(SCRIPT) - allowed, set())

    def test_tests_import_nothing_networked(self):
        banned = {"socket", "urllib", "http", "requests", "ssl", "ftplib", "smtplib", "asyncio"}
        self.assertEqual(self.imports(__file__) & banned, set())


if __name__ == "__main__":
    unittest.main()
