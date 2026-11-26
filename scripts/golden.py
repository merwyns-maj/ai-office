"""Check golden cases for the office's skills (T-049).

Usage: python scripts/golden.py <office> [-v]

Discovers base/skills/*/golden/*.json and offices/<office>/skills/*/golden/*.json.
Exit 0: all cases valid, all checks pass on expected_output, every bad_output fails
at least one check, data scan clean. Exit 1: any problem. Exit 2: usage error.
Problems print one per line as "<repo-relative path>: <problem>"; matched data is never echoed.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from engine.runtime.events import DATA_PATTERNS, PATTERN_KINDS, forbidden_terms  # noqa: E402

KEYS = {"skill", "rules", "input", "expected_output", "checks", "bad_output", "human_note", "why"}
REQUIRED_TEXT = ("input", "expected_output", "human_note", "why")
REGEX_TYPES = ("must_match", "must_not_match")
LITERAL_TYPES = ("must_contain", "must_not_contain")
MIN_CASES, MAX_CASES = 3, 5


def discover(repo, office):
    repo = Path(repo)
    files = sorted(repo.glob("base/skills/*/golden/*.json"))
    files += sorted(repo.glob(f"offices/{office}/skills/*/golden/*.json"))
    return files


def _rel(path, repo):
    try:
        return str(Path(path).resolve().relative_to(Path(repo).resolve()))
    except ValueError:
        return str(path)


def load_case(path):
    """Return (case or None, [problems]). Problems do not include the path."""
    try:
        case = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, [f"invalid JSON ({type(e).__name__})"]
    if not isinstance(case, dict):
        return None, ["case must be a JSON object"]
    problems = []
    for k in sorted(set(case) - KEYS):
        problems.append(f"unknown key '{k}'")
    for k in REQUIRED_TEXT:
        v = case.get(k)
        if not isinstance(v, str) or not v.strip():
            problems.append(f"missing or empty '{k}'")
    if "bad_output" in case and (not isinstance(case["bad_output"], str) or not case["bad_output"].strip()):
        problems.append("'bad_output' must be a non-empty string when present")
    rules = case.get("rules")
    if not isinstance(rules, list) or not rules or not all(isinstance(r, str) and r for r in rules):
        problems.append("missing or empty 'rules'")
    if not isinstance(case.get("skill"), str) or not case.get("skill"):
        problems.append("missing or empty 'skill'")
    elif case["skill"] != Path(path).parent.parent.name:
        problems.append(f"skill '{case['skill']}' does not match folder '{Path(path).parent.parent.name}'")
    checks = case.get("checks")
    if not isinstance(checks, list) or not checks:
        problems.append("empty 'checks'")
    else:
        musts = 0
        for i, c in enumerate(checks, 1):
            problems += _check_problems(i, c)
            if isinstance(c, dict) and c.get("type") in REGEX_TYPES + LITERAL_TYPES:
                musts += 1
        if musts == 0:
            problems.append("no must or must-not check in 'checks'")
    return case, problems


def _check_problems(i, c):
    if not isinstance(c, dict):
        return [f"check {i}: must be an object"]
    out = []
    t = c.get("type")
    if not isinstance(c.get("rule"), str) or not c.get("rule"):
        out.append(f"check {i}: missing 'rule'")
    if t in REGEX_TYPES:
        allowed = {"type", "pattern", "rule"}
        p = c.get("pattern")
        if not isinstance(p, str) or not p:
            out.append(f"check {i} ({t}): missing 'pattern'")
        else:
            try:
                re.compile(p, re.MULTILINE)
            except re.error as e:
                out.append(f"check {i} ({t}): invalid regex ({e})")
    elif t in LITERAL_TYPES:
        allowed = {"type", "text", "rule"}
        if not isinstance(c.get("text"), str) or not c.get("text"):
            out.append(f"check {i} ({t}): missing 'text'")
    elif t == "max_lines":
        allowed = {"type", "max", "rule"}
        m = c.get("max")
        if not isinstance(m, int) or isinstance(m, bool) or m < 1:
            out.append(f"check {i} (max_lines): 'max' must be a positive integer")
    else:
        return out + [f"check {i}: unknown check type '{t}'"]
    for k in sorted(set(c) - allowed):
        out.append(f"check {i} ({t}): unknown key '{k}'")
    return out


def run_check(check, text):
    """True when the check passes on text."""
    t = check["type"]
    if t == "must_match":
        return re.search(check["pattern"], text, re.MULTILINE) is not None
    if t == "must_not_match":
        return re.search(check["pattern"], text, re.MULTILINE) is None
    if t == "must_contain":
        return check["text"] in text
    if t == "must_not_contain":
        return check["text"] not in text
    if t == "max_lines":
        return len(text.strip().splitlines()) <= check["max"]
    raise ValueError(t)


def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def data_hits(raw_text, obj, forbidden):
    """Messages naming the kind of hit, never the matched text. Scans raw text and decoded strings."""
    texts = [raw_text] + list(_strings(obj))
    hits = []
    for p, kind in zip(DATA_PATTERNS, PATTERN_KINDS):
        if any(p.search(s) for s in texts):
            hits.append(f"personal-data pattern ({kind})")
    if any(f and f in s.lower() for s in texts for f in forbidden):
        hits.append("forbidden term (listed in workspaces.yaml)")
    return hits


def main(argv, repo=REPO):
    args = [a for a in argv if a != "-v"]
    verbose = "-v" in argv
    if len(args) != 1:
        print("usage: python scripts/golden.py <office> [-v]", file=sys.stderr)
        return 2
    office = args[0]
    repo = Path(repo)
    if not (repo / "offices" / office).is_dir():
        print(f"golden: office '{office}' not found", file=sys.stderr)
        return 2
    forbidden = forbidden_terms(repo)
    files = discover(repo, office)
    problems, per_skill, n_checks = [], {}, 0
    for f in files:
        rel = _rel(f, repo)
        raw = f.read_text(encoding="utf-8", errors="replace")
        case, probs = load_case(f)
        probs = list(probs)
        if case is not None:
            probs += data_hits(raw, case, forbidden)
            if not probs:
                for i, c in enumerate(case["checks"], 1):
                    n_checks += 1
                    if not run_check(c, case["expected_output"]):
                        probs.append(f"check {i} ({c['type']}, {c['rule']}) failed on expected_output")
                if "bad_output" in case and all(run_check(c, case["bad_output"]) for c in case["checks"]):
                    probs.append("bad_output passes every check (a check is too loose)")
        else:
            probs += data_hits(raw, {}, forbidden)
        problems += [f"{rel}: {p}" for p in probs]
        skill = f.parent.parent.name
        per_skill.setdefault((f.parent, skill), []).append(f)
        if verbose:
            print(f"{rel}: {'ok' if not probs else 'PROBLEM'}")
    for (folder, skill), cases in per_skill.items():
        if not MIN_CASES <= len(cases) <= MAX_CASES:
            problems.append(f"{_rel(folder, repo)}: {len(cases)} cases, expected {MIN_CASES} to {MAX_CASES}")
    if problems:
        for p in problems:
            print(p)
        print(f"golden: {len(files)} cases, {len(problems)} problems")
        return 1
    for (folder, skill), cases in sorted(per_skill.items(), key=lambda kv: kv[0][1]):
        print(f"{skill}: {len(cases)} cases OK")
    print(f"golden: {len(files)} cases, {n_checks} checks, 0 problems")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
