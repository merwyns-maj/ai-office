"""Resolve an office's agents (with `extends`) into .claude/agents/ for Claude Code.

Usage: python scripts/build_agents.py <office-id>
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _fm import split, dump

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEYS = ["name", "description", "tools", "model"]

def build(office):
    src = ROOT / "offices" / office / "agents"
    if not src.is_dir():
        sys.exit(f"No such office: {office}")
    out = ROOT / ".claude" / "agents"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.md"):
        old.unlink()
    built = []
    for f in sorted(src.glob("*.md")):
        fm, body = split(f.read_text())
        base_ref = fm.pop("extends", None)
        if base_ref:
            name = base_ref.split("/", 1)[1] if base_ref.startswith("base/") else base_ref
            base_path = ROOT / "base" / "agents" / (name + ".md")
            if not base_path.exists():
                sys.exit(f"{f.name}: extends {base_ref}, but {base_path} is missing")
            bfm, bbody = split(base_path.read_text())
            merged = {**bfm, **{k: v for k, v in fm.items() if v}}
            body = bbody.rstrip() + "\n\n## Office-specific\n" + body.strip() + "\n"
            fm = merged
        missing = [k for k in ("name", "description") if not fm.get(k)]
        if missing:
            sys.exit(f"{f.name}: missing {missing}")
        header = f"<!-- generated from offices/{office}/agents/{f.name} by scripts/build_agents.py; do not edit -->\n"
        (out / f.name).write_text(dump(fm, KEYS) + header + body)
        built.append(fm["name"])
    print(f"{office}: built {len(built)} agents -> .claude/agents/ ({', '.join(built)})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
