"""Resolve an office's agents (with `extends`) into .claude/agents/ for Claude Code.

Usage: python scripts/build_agents.py <office-id>
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _fm import split, dump, as_list, read_flat

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULTS_MISSING = "warning: base/defaults.yaml is missing, so agents will get no base skills"
KEYS = ["name", "description", "tools", "model"]

def skill_paths(fm, office, root, fname):
    """Repo-relative SKILL.md paths for one agent: base defaults, agent base_skills, office_skills."""
    def has_base(sk):
        return (root / "base" / "skills" / sk / "SKILL.md").exists()
    paths = []
    for sk in as_list(read_flat(root / "base" / "defaults.yaml").get("base_skills")):
        if not has_base(sk):
            sys.exit(f"base/defaults.yaml: base_skills names '{sk}', but base/skills/{sk}/SKILL.md is missing")
        paths.append(f"base/skills/{sk}/SKILL.md")
    for sk in as_list(fm.get("base_skills")):
        if not has_base(sk):
            sys.exit(f"{fname}: base_skills names '{sk}', but base/skills/{sk}/SKILL.md is missing")
        paths.append(f"base/skills/{sk}/SKILL.md")
    for sk in as_list(fm.get("office_skills")):
        if not (root / "offices" / office / "skills" / sk / "SKILL.md").exists():
            sys.exit(f"{fname}: office_skills names '{sk}', but offices/{office}/skills/{sk}/SKILL.md is missing")
        if has_base(sk):
            sys.exit(f"skill '{sk}' exists in both base/skills/ and offices/{office}/skills/; keep one")
        paths.append(f"offices/{office}/skills/{sk}/SKILL.md")
    odir = root / "offices" / office / "skills"
    if odir.is_dir():
        for d in sorted(odir.iterdir()):
            if (d / "SKILL.md").exists() and has_base(d.name):
                sys.exit(f"skill '{d.name}' exists in both base/skills/ and offices/{office}/skills/; keep one")
    return list(dict.fromkeys(paths))

def merged(f, root):
    """Frontmatter and body of an agent file after resolving `extends`."""
    fm, body = split(f.read_text())
    base_ref = fm.pop("extends", None)
    if base_ref:
        name = base_ref.split("/", 1)[1] if base_ref.startswith("base/") else base_ref
        base_path = root / "base" / "agents" / (name + ".md")
        if not base_path.exists():
            sys.exit(f"{f.name}: extends {base_ref}, but {base_path} is missing")
        bfm, bbody = split(base_path.read_text())
        fm = {**bfm, **{k: v for k, v in fm.items() if v}}
        body = bbody.rstrip() + "\n\n## Office-specific\n" + body.strip() + "\n"
    return fm, body

def build(office, root=ROOT):
    root = pathlib.Path(root)
    src = root / "offices" / office / "agents"
    if not src.is_dir():
        sys.exit(f"No such office: {office}")
    if not (root / "base" / "defaults.yaml").is_file():
        print(DEFAULTS_MISSING, file=sys.stderr)
    # every check runs before .claude/agents/ is touched
    sources = set(re.findall(r"^  ([\w-]+):", (root / "workspaces.yaml").read_text().split("skill_sources:")[-1], re.M))
    plan = []
    for f in sorted(src.glob("*.md")):
        fm, body = merged(f, root)
        paths = skill_paths(fm, office, root, f.name)
        ext = as_list(fm.get("external_skills"))
        for e in ext:
            if ":" not in e or e.split(":")[0] not in sources:
                sys.exit(f"{f.name}: external skill '{e}' must be source:name with a source listed under skill_sources in workspaces.yaml")
        missing = [k for k in ("name", "description") if not fm.get(k)]
        if missing:
            sys.exit(f"{f.name}: missing {missing}")
        plan.append((f, fm, body, paths, ext))
    out = root / ".claude" / "agents"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.md"):
        old.unlink()
    built = []
    for f, fm, body, paths, ext in plan:
        name, title = fm.get("display_name"), fm.get("role_title")
        if name and fm.get("description"):
            fm["description"] = f"{name} ({title or fm['name']}). " + fm["description"]
        if paths:
            body = body.rstrip() + "\n\n## Skills\nBefore your step, read and follow:\n" + "".join(f"- {p}\n" for p in paths)
        if ext:
            body = body.rstrip() + "\n\n## External skills (use when available)\n" + "".join(f"- {e}\n" for e in ext) + \
                "These live outside this repo. In a Claude app session, call the Skill tool with the name after the colon. If a skill is not available, carry on and say so in your section of the task file.\n"
        header = f"<!-- generated from offices/{office}/agents/{f.name} by scripts/build_agents.py; do not edit -->\n"
        (out / f.name).write_text(dump(fm, KEYS) + header + body)
        built.append(fm["name"])
    print(f"{office}: built {len(built)} agents -> .claude/agents/ ({', '.join(built)})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
