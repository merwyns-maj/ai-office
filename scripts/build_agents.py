"""Resolve an office's agents (with `extends`) into .claude/agents/ for Claude Code.

Usage: python scripts/build_agents.py <office-id>
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _fm import split, dump, as_list

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEYS = ["name", "description", "tools", "model"]

def build(office):
    src = ROOT / "offices" / office / "agents"
    if not src.is_dir():
        sys.exit(f"No such office: {office}")
    for f in sorted(src.glob("*.md")):
        for sk in as_list(split(f.read_text())[0].get("office_skills")):
            if not (ROOT / "offices" / office / "skills" / sk / "SKILL.md").exists():
                sys.exit(f"{f.name}: office_skills names '{sk}', but offices/{office}/skills/{sk}/SKILL.md is missing")
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
        name, title = fm.get("display_name"), fm.get("role_title")
        if name and fm.get("description"):
            fm["description"] = f"{name} ({title or fm['name']}). " + fm["description"]
        skills = as_list(fm.get("office_skills"))
        for sk in skills:
            if not (ROOT / "offices" / office / "skills" / sk / "SKILL.md").exists():
                sys.exit(f"{f.name}: office_skills names '{sk}', but offices/{office}/skills/{sk}/SKILL.md is missing")
        if skills:
            body = body.rstrip() + "\n\n## Skills\nBefore your step, read and follow:\n" + "".join(
                f"- offices/{office}/skills/{sk}/SKILL.md\n" for sk in skills)
        ext = as_list(fm.get("external_skills"))
        sources = set(re.findall(r"^  ([\w-]+):", (ROOT / "workspaces.yaml").read_text().split("skill_sources:")[-1], re.M))
        for e in ext:
            if ":" not in e or e.split(":")[0] not in sources:
                sys.exit(f"{f.name}: external skill '{e}' must be source:name with a source listed under skill_sources in workspaces.yaml")
        if ext:
            body = body.rstrip() + "\n\n## External skills (use when available)\n" + "".join(f"- {e}\n" for e in ext) + \
                "These live outside this repo. In a Claude app session, call the Skill tool with the name after the colon. If a skill is not available, carry on and say so in your section of the task file.\n"
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
