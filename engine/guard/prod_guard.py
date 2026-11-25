#!/usr/bin/env python3
"""Claude Code PreToolUse hook: default-deny guard for prod writes (Bash and MCP tools).

Exit 0 = allow (no output). Exit 2 = block (one line on stderr). No other exit codes.
Stdlib only. stderr never contains payload text. See README.md in this folder.
"""
import sys

try:
    import argparse
    import json
    import os
    import pathlib
    import re
    import signal
    from typing import NamedTuple
except BaseException:
    sys.stderr.write("prod-guard BLOCKED [rule=internal-error] tool=<unknown>. "
                     "Guard failed to start; ask Merwyn.\n")
    sys.exit(2)

MAX_INPUT = 1_048_576
DEFAULT_DEADLINE = 5
CHAIN_CHARS = (";", "&", "|", "`", "$(", ">", "<", "\n", "\r")
ALLOWLIST_ACTION = "submit-change-issue"
_FLAGS = re.IGNORECASE | re.DOTALL   # DOTALL: `.` crosses newlines, so a multi-line command cannot dodge a rule

# In code, not config, so a config cannot weaken it. [\s\S] so it matches across newlines.
K8S_SECRET_BASH = re.compile(r"\bkubectl\b[\s\S]*?\b(?:get|describe|edit)\b[\s\S]*?\bsecrets?\b",
                             re.IGNORECASE)
_SECRET_WORD = re.compile(r"\bsecrets?\b", re.IGNORECASE)
_KUBECTL_TOOL = re.compile(r"__kubectl_", re.IGNORECASE)
_APPLY_WORDS = re.compile(r"\b(?:apply|rollout|approve|deploy|execute|run-now)\b", re.IGNORECASE)
_TOOL_OK = re.compile(r"[A-Za-z0-9_.:-]{1,128}")

_WRITE_WORDS = ("INSERT UPDATE DELETE MERGE UPSERT REPLACE CREATE ALTER DROP TRUNCATE RENAME GRANT "
                "REVOKE COPY CALL DO EXEC EXECUTE SET RESET LOCK VACUUM REINDEX CLUSTER COMMENT "
                "REFRESH IMPORT LOAD INTO").split()
_SQL_WRITE_RE = re.compile(
    r"\b(?:" + "|".join(_WRITE_WORDS) + r")\b|\bFOR\s+SHARE\b|nextval\s*\(|setval\s*\(|"
    r"pg_terminate_backend|pg_cancel_backend|lo_import|lo_export|dblink", re.IGNORECASE)
_READ_FIRST = {"SELECT", "WITH", "SHOW", "EXPLAIN", "DESCRIBE", "DESC", "TABLE", "VALUES"}

REASONS = {
    "malformed-input": "The hook input could not be understood.",
    "input-too-large": "The hook input is larger than the 1 MiB limit.",
    "config-error": "The guard config is missing or invalid.",
    "internal-error": "The guard failed unexpectedly.",
    "k8s-secret-read": "Reading Kubernetes secrets is blocked in every context.",
    "sql-write": "The SQL contains a write or DDL keyword.",
    "sql-multi-statement": "The SQL contains more than one statement.",
    "sql-not-read-only": "The SQL is not recognised as read-only.",
    "default-deny": "The call targets prod and is neither read-only nor on the allowlist.",
    "config-rule": "The call matches a prod write rule.",
}


class ConfigError(Exception):
    pass


Decision = NamedTuple("Decision", [("allow", bool), ("rule", str), ("reason", str)])


def _block(rule: str) -> Decision:
    return Decision(False, rule, REASONS.get(rule.split(":", 1)[0], REASONS["config-rule"]))


def _allow(rule: str) -> Decision:
    return Decision(True, rule, "")


# ---------------------------------------------------------------- config

def _rules(section: object, where: str) -> list:
    if not isinstance(section, list):
        raise ConfigError(f"{where} must be a list")
    out = []
    for r in section:
        if not isinstance(r, dict) or not isinstance(r.get("id"), str) \
                or not isinstance(r.get("pattern"), str):
            raise ConfigError(f"{where}: each rule needs string id and pattern")
        try:
            out.append((r["id"], re.compile(r["pattern"], _FLAGS)))
        except re.error:
            raise ConfigError(f"bad regex in rule {_clean(r['id'])}") from None
    return out


def _clean(s: str) -> str:
    return re.sub(r"[^\w:.-]", "?", s)[:100]


def load_config(path: pathlib.Path) -> dict:
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except OSError:
        raise ConfigError("cannot read config file") from None
    except UnicodeDecodeError:
        raise ConfigError("config is not UTF-8") from None
    except ValueError:
        raise ConfigError("config is not valid JSON") from None
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ConfigError("config must be an object with version 1")
    try:
        bash, mcp, allow = data["bash"], data["mcp"], data["allowlist"]
        cfg = {
            "bash": {k: _rules(bash[k], f"bash.{k}") for k in ("prod_targets", "write", "read_only")},
            "mcp": {k: _rules(mcp[k], f"mcp.{k}")
                    for k in ("prod_tools", "write_tools", "read_tools", "sql_tools")},
        }
        fields = mcp["sql_fields"]
    except (KeyError, TypeError):
        raise ConfigError("missing or malformed section") from None
    if not isinstance(fields, list) or not fields or not all(isinstance(f, str) for f in fields):
        raise ConfigError("mcp.sql_fields must be a non-empty list of strings")
    cfg["mcp"]["sql_fields"] = list(fields)
    if not isinstance(allow, list):
        raise ConfigError("allowlist must be a list")
    entries = []
    for e in allow:
        if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ("id", "tool", "command")):
            raise ConfigError("allowlist entry needs string id, tool and command")
        if e.get("action") != ALLOWLIST_ACTION:
            raise ConfigError(f"allowlist entry {_clean(e['id'])}: action must be {ALLOWLIST_ACTION}")
        try:
            entries.append({"id": e["id"], "tool": re.compile(e["tool"], _FLAGS),
                            "command": re.compile(e["command"], _FLAGS)})
        except re.error:
            raise ConfigError(f"bad regex in allowlist entry {_clean(e['id'])}") from None
    cfg["allowlist"] = entries
    cfg["n_rules"] = (sum(len(v) for v in cfg["bash"].values())
                      + sum(len(v) for k, v in cfg["mcp"].items() if k != "sql_fields") + len(entries))
    return cfg


def find_config(cli_path: str | None) -> pathlib.Path:
    if cli_path:
        return pathlib.Path(os.path.expanduser(cli_path))
    env = os.environ.get("PROD_GUARD_CONFIG")
    if env:
        return pathlib.Path(os.path.expanduser(env))
    return pathlib.Path(__file__).resolve().parent / "prod_guard.json"


# ---------------------------------------------------------------- SQL

def _strip_sql_comments(sql: str) -> str:
    out, i, n, quote = [], 0, len(sql), None
    while i < n:
        c = sql[i]
        if quote:
            out.append(c)
            if c == quote:
                if sql[i + 1:i + 2] == quote:
                    out.append(quote)
                    i += 1
                else:
                    quote = None
        elif c in ("'", '"'):
            quote = c
            out.append(c)
        elif sql.startswith("--", i):
            while i < n and sql[i] != "\n":
                i += 1
            continue
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def sql_write_keyword(text: str) -> str | None:
    m = _SQL_WRITE_RE.search(text)
    return re.sub(r"[\s(]+", " ", m.group(0)).strip().upper() if m else None


def classify_sql(sql: str) -> tuple[bool, str]:
    """(read_only, rule). Rule is "" when read-only. Keywords are scanned on the raw text
    (comments and string literals included) so hiding a write inside either cannot pass."""
    stripped = _strip_sql_comments(sql)
    if "/*!" in sql:                      # MySQL executable comment
        return False, "sql-not-read-only"
    if re.search(r";\s*\S", stripped):
        return False, "sql-multi-statement"
    kw = sql_write_keyword(sql)
    if kw:
        return False, f"sql-write:{kw}"
    m = re.match(r"[\s(]*([A-Za-z]+)", stripped)
    first = m.group(1).upper() if m else ""
    if first not in _READ_FIRST or (first == "EXPLAIN" and re.search(r"\banalyze\b", stripped, re.I)):
        return False, "sql-not-read-only"
    return True, ""


def _sql_values(tool_input: dict, fields: list) -> list:
    return [tool_input[f] for f in fields if isinstance(tool_input.get(f), str)]


# ---------------------------------------------------------------- rules

def allowlist_eligible(command: str) -> bool:
    if any(c in command for c in CHAIN_CHARS):
        return False
    if ".." in command:
        return False
    return not _APPLY_WORDS.search(command)


def mentions_k8s_secret(tool_name: str, tool_input: object, command: str | None) -> bool:
    if command is not None:
        return bool(K8S_SECRET_BASH.search(command))
    if not _KUBECTL_TOOL.search(tool_name):
        return False
    if "secret" in tool_name.lower():
        return True
    stack = [tool_input]
    while stack:
        x = stack.pop()
        if isinstance(x, str):
            if _SECRET_WORD.search(x):
                return True
        elif isinstance(x, dict):
            stack.extend(x.values())
        elif isinstance(x, (list, tuple)):
            stack.extend(x)
    return False


def _first(rules: list, text: str) -> str | None:
    for rid, rx in rules:
        if rx.search(text):
            return rid
    return None


def _allowlisted(config: dict, tool_name: str, text: str) -> str | None:
    if not allowlist_eligible(text):
        return None
    for e in config["allowlist"]:
        if e["tool"].fullmatch(tool_name) and e["command"].fullmatch(text):
            return e["id"]
    return None


def decide(payload: object, config: dict) -> Decision:
    if not isinstance(payload, dict):
        return _block("malformed-input")
    name = payload.get("tool_name")
    if not isinstance(name, str) or not name:
        return _block("malformed-input")
    is_bash, is_mcp = name == "Bash", name.startswith("mcp__")
    if not (is_bash or is_mcp):
        return _allow("other-tool")
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return _block("malformed-input")

    if is_bash:
        cmd = tool_input.get("command")
        if not isinstance(cmd, str) or not cmd.strip():
            return _block("malformed-input")
        if mentions_k8s_secret(name, tool_input, cmd):
            return _block("k8s-secret-read")
        b = config["bash"]
        if _first(b["prod_targets"], cmd) is None:
            return _allow("no-prod-target")
        hit = _allowlisted(config, name, cmd)
        if hit:
            return _allow(f"allowlist:{hit}")
        rid = _first(b["write"], cmd)
        if rid:
            return _block(rid)
        kw = sql_write_keyword(cmd)
        if kw:
            return _block(f"sql-write:{kw}")
        if _first(b["read_only"], cmd):
            return _allow("read-only")
        return _block("default-deny")

    if mentions_k8s_secret(name, tool_input, None):
        return _block("k8s-secret-read")
    m = config["mcp"]
    if _first(m["prod_tools"], name) is None:
        return _allow("no-prod-target")
    sqls = _sql_values(tool_input, m["sql_fields"])
    for s in sqls:
        hit = _allowlisted(config, name, s)
        if hit:
            return _allow(f"allowlist:{hit}")
    rid = _first(m["write_tools"], name)
    if rid:
        return _block(rid)
    for s in sqls:
        ok, rule = classify_sql(s)
        if not ok:
            return _block(rule)
    if _first(m["read_tools"], name):
        return _allow("read-tool")
    if _first(m["sql_tools"], name):
        return _allow("read-only-sql") if sqls else _block("malformed-input")
    return _block("default-deny")


# ---------------------------------------------------------------- output / entry

def format_block(rule: str, tool_name: object, extra: str = "") -> str:
    """The only stderr writer's formatter: rule id, sanitised tool name, fixed reason. No payload text."""
    if tool_name is None:
        tool = "<unknown>"
    elif isinstance(tool_name, str) and _TOOL_OK.fullmatch(tool_name):
        tool = tool_name
    else:
        tool = "<invalid>"
    reason = REASONS.get(rule.split(":", 1)[0], REASONS["config-rule"])
    msg = f"prod-guard BLOCKED [rule={_clean(rule)}] tool={tool}. {reason}"
    if extra:
        msg += " (" + " ".join(extra.split())[:300] + ")"
    return msg + " Prod writes go through an allowlisted Bytebase change issue; ask Merwyn."


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("bad arguments")


def _tool_of(payload: object) -> object:
    return payload.get("tool_name") if isinstance(payload, dict) else None


def _run(args, stdin, stderr) -> int:
    def block(rule, tool=None, extra=""):
        stderr.write(format_block(rule, tool, extra) + "\n")
        return 2

    cfg_path = find_config(args.config)
    if args.check_config:
        try:
            cfg = load_config(cfg_path)
        except ConfigError as e:
            return block("config-error", None, f"config error in {cfg_path}: {e}")
        sys.stdout.write(f"prod-guard: config OK ({cfg['n_rules']} rules)\n")
        return 0
    raw = stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        return block("input-too-large")
    try:
        text = raw.decode("utf-8")
        if not text.strip():
            return block("malformed-input")
        payload = json.loads(text)
    except ValueError:                    # UnicodeDecodeError and JSONDecodeError
        return block("malformed-input")
    try:
        cfg = load_config(cfg_path)
    except ConfigError as e:
        return block("config-error", _tool_of(payload), f"config error in {cfg_path}: {e}")
    d = decide(payload, cfg)
    if d.allow:
        return 0
    return block(d.rule, _tool_of(payload))


def main(argv: list[str] | None = None, stdin=None, stderr=None) -> int:
    stdin = sys.stdin if stdin is None else stdin
    stderr = sys.stderr if stderr is None else stderr
    p = _Parser(add_help=False)
    p.add_argument("--config")
    p.add_argument("--deadline", type=int, default=DEFAULT_DEADLINE)
    p.add_argument("--check-config", action="store_true")
    args = p.parse_args(argv)
    armed = args.deadline > 0 and hasattr(signal, "SIGALRM")
    if armed:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)   # default action: kernel kills us, wrapper exits 2
        signal.alarm(args.deadline)
    try:
        return _run(args, stdin, stderr)
    finally:
        if armed:
            signal.alarm(0)


def _entry() -> None:
    try:
        code = main()
    except BaseException as e:            # incl. SystemExit, KeyboardInterrupt
        try:
            sys.stderr.write(format_block("internal-error", None, type(e).__name__) + "\n")
        except BaseException:
            pass
        code = 2
    sys.exit(code if code in (0, 2) else 2)


if __name__ == "__main__":
    _entry()
