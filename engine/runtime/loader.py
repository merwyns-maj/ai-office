"""Load an office folder and validate it against engine/schema/office.md (v0). Read-only."""
import re
from dataclasses import dataclass, field
from pathlib import Path

from .miniyaml import YamlError, loads, split_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIORITIES = ("P0", "P1", "P2")
OFFICE_KEYS = ("id", "name", "purpose", "brain", "projects", "human", "budget", "defaults")
TASK_KEYS = ("id", "title", "status", "priority", "owner")
_EXTERNAL = re.compile(r"^[\w.-]+:[\w.-]+$")


@dataclass(frozen=True)
class Problem:
    file: str
    message: str

    def __str__(self):
        return f"{self.file}: {self.message}"


@dataclass
class Agent:
    id: str
    path: Path
    meta: dict
    office_skills: list
    external_skills: list
    display_name: "str | None"
    base_skills: list = field(default_factory=list)


@dataclass
class Task:
    id: str
    path: Path
    title: str
    status: str
    priority: str
    owner: str
    depends_on: list
    meta: dict


@dataclass
class Office:
    id: str
    root: Path
    repo_root: Path
    office: dict
    org: dict
    workflow: dict
    agents: dict = field(default_factory=dict)
    tasks: dict = field(default_factory=dict)
    skills: set = field(default_factory=set)
    base_skills: set = field(default_factory=set)
    default_base_skills: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def stage_ids(self):
        return [s.get("id") for s in _as_list(self.workflow.get("stages")) if isinstance(s, dict)]

    @property
    def terminal(self):
        return list(_as_list(self.workflow.get("terminal")))

    def stage(self, sid):
        for s in _as_list(self.workflow.get("stages")):
            if isinstance(s, dict) and s.get("id") == sid:
                return s
        return None

    def rel(self, path):
        return _rel(path, self.repo_root)

    def skill_files(self, agent):
        """Repo-relative SKILL.md paths for an agent: base defaults, its base_skills, its office_skills."""
        paths = [f"base/skills/{s}/SKILL.md" for s in self.default_base_skills]
        paths += [f"base/skills/{s}/SKILL.md" for s in agent.base_skills]
        paths += [f"{self.rel(self.root)}/skills/{s}/SKILL.md" for s in agent.office_skills]
        return list(dict.fromkeys(paths))


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _rel(path, repo_root):
    try:
        return str(Path(path).relative_to(repo_root))
    except ValueError:
        return str(path)


def resolve_office(arg, cwd):
    """Office id (-> offices/<id>) or a path to an office folder. Raises FileNotFoundError."""
    cwd = Path(cwd)
    p = Path(arg)
    if p.is_absolute() or len(p.parts) > 1:
        cands = [cwd / p]
    else:
        cands = [cwd / "offices" / arg, REPO_ROOT / "offices" / arg, cwd / p]
    for c in cands:
        if c.is_dir():
            return c.resolve()
    raise FileNotFoundError(f"office folder not found: {arg}")


def _parse_file(path, repo_root, problems, frontmatter=False):
    src = _rel(path, repo_root)
    try:
        text = path.read_text(encoding="utf-8")
        if frontmatter:
            return split_frontmatter(text, src)[0]
        return loads(text, src)
    except YamlError as e:
        problems.append(Problem(src, f"line {e.line}: {e.msg}"))
    except (OSError, UnicodeDecodeError) as e:
        problems.append(Problem(src, f"cannot read file: {e}"))
    return None


def load_office(root):
    """Return (Office | None, problems). None only if a required file is missing or unparseable."""
    root = Path(root).resolve()
    repo_root = root.parent.parent
    problems = []
    for name in ("office.yaml", "org.yaml", "workflow.yaml"):
        if not (root / name).is_file():
            problems.append(Problem(_rel(root / name, repo_root), "missing required file"))
    agent_files = sorted((root / "agents").glob("*.md")) if (root / "agents").is_dir() else []
    if not agent_files:
        problems.append(Problem(_rel(root / "agents", repo_root), "missing required file: agents/ with at least one *.md"))
    if not (root / "backlog").is_dir():
        problems.append(Problem(_rel(root / "backlog", repo_root), "missing required file: backlog/ directory"))
    if problems:
        return None, problems

    docs = {}
    for name in ("office.yaml", "org.yaml", "workflow.yaml"):
        docs[name] = _parse_file(root / name, repo_root, problems)
        if docs[name] is not None and not isinstance(docs[name], dict):
            problems.append(Problem(_rel(root / name, repo_root), "top level must be a mapping"))
            docs[name] = None
    if any(v is None for v in docs.values()):
        return None, problems

    office = Office(root.name, root, repo_root, docs["office.yaml"], docs["org.yaml"], docs["workflow.yaml"])

    for f in agent_files:
        meta = _parse_file(f, repo_root, problems, frontmatter=True)
        if meta is None:
            continue
        office.agents[f.stem] = Agent(
            id=f.stem, path=f, meta=meta,
            office_skills=list(_as_list(meta.get("office_skills"))),
            external_skills=list(_as_list(meta.get("external_skills"))),
            display_name=meta.get("display_name"),
            base_skills=list(_as_list(meta.get("base_skills"))))

    skills_dir = root / "skills"
    if skills_dir.is_dir():
        office.skills = {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()}

    bdir = repo_root / "base" / "skills"
    if bdir.is_dir():
        office.base_skills = {d.name for d in bdir.iterdir() if (d / "SKILL.md").is_file()}
    defaults = repo_root / "base" / "defaults.yaml"
    if defaults.is_file():
        doc = _parse_file(defaults, repo_root, problems)
        if doc is not None:
            if isinstance(doc, dict):
                office.default_base_skills = [str(x) for x in _as_list(doc.get("base_skills"))]
            else:
                problems.append(Problem(_rel(defaults, repo_root), "top level must be a mapping"))
    else:
        office.warnings.append(Problem("base/defaults.yaml", "is missing, so agents will get no base skills"))

    for f in sorted((root / "backlog").glob("T-*.md")):
        meta = _parse_file(f, repo_root, problems, frontmatter=True)
        if meta is None:
            continue
        tid = str(meta.get("id") or "-".join(f.name.split("-")[:2]))
        task = Task(
            id=tid, path=f, title=str(meta.get("title") or ""), status=str(meta.get("status") or ""),
            priority=str(meta.get("priority") or ""), owner=str(meta.get("owner") or ""),
            depends_on=[str(d) for d in _as_list(meta.get("depends_on"))], meta=meta)
        if tid in office.tasks:
            problems.append(Problem(_rel(f, repo_root), f"duplicate task id {tid} (also {_rel(office.tasks[tid].path, repo_root)})"))
            continue
        office.tasks[tid] = task
    return office, problems


def validate(office):
    """Check a loaded office against the schema rules. Returns all problems found."""
    P = []
    root, rr = office.root, office.repo_root

    def add(path, msg):
        P.append(Problem(_rel(path, rr), msg))

    # 3. office.yaml
    of = root / "office.yaml"
    for k in OFFICE_KEYS:
        if k not in office.office:
            add(of, f"missing key '{k}'")
    if "id" in office.office and office.office["id"] != root.name:
        add(of, f"id '{office.office['id']}' does not match folder name '{root.name}'")
    if "brain" in office.office and office.office["brain"] not in ("work", "personal"):
        add(of, f"brain '{office.office['brain']}' must be 'work' or 'personal'")
    human = office.office.get("human")
    if "human" in office.office and not (isinstance(human, dict) and human.get("name")):
        add(of, "human.name is missing")

    # 4. org.yaml
    og = root / "org.yaml"
    org_ids = []
    org_agents = office.org.get("agents")
    if not isinstance(org_agents, list):
        add(og, "'agents' must be a list")
        org_agents = []
    for a in org_agents:
        if not isinstance(a, dict) or not a.get("id"):
            add(og, "agent entry without 'id'")
            continue
        if a["id"] in org_ids:
            add(og, f"duplicate agent id '{a['id']}'")
        org_ids.append(a["id"])
    for a in org_agents:
        if not isinstance(a, dict) or not a.get("id"):
            continue
        if not (root / "agents" / f"{a['id']}.md").is_file():
            add(og, f"agent '{a['id']}' has no agents/{a['id']}.md")
        rt = a.get("reports_to")
        if rt != "human" and rt not in org_ids:
            add(og, f"agent '{a['id']}' reports_to '{rt}' which is neither 'human' nor an org agent")

    # 5. workflow.yaml
    wf = root / "workflow.yaml"
    stages = office.workflow.get("stages")
    if not isinstance(stages, list) or not stages:
        add(wf, "'stages' must be a non-empty list")
        stages = []
    for s in stages:
        if not isinstance(s, dict) or not s.get("id") or not s.get("owner"):
            add(wf, f"stage {s!r} needs 'id' and 'owner'")
        elif s["owner"] not in org_ids:
            add(wf, f"stage '{s['id']}' owner '{s['owner']}' is not an org agent")
    if not isinstance(office.workflow.get("terminal"), list):
        add(wf, "'terminal' must be a list")
    allowed_status = office.stage_ids + office.terminal
    for g in _as_list(office.workflow.get("gates")):
        if not isinstance(g, dict):
            add(wf, f"gate {g!r} must be a map with 'stage' and 'approver'")
            continue
        if g.get("stage") not in allowed_status:
            add(wf, f"gate stage '{g.get('stage')}' is not a workflow stage or terminal")
        if g.get("approver") != "human" and g.get("approver") not in org_ids:
            add(wf, f"gate approver '{g.get('approver')}' is neither 'human' nor an org agent")

    # 6. agents/*.md
    for sk in office.default_base_skills:
        if sk not in office.base_skills:
            P.append(Problem("base/defaults.yaml", f"base_skills '{sk}' has no base/skills/{sk}/SKILL.md"))
    for sk in sorted(office.skills & office.base_skills):
        add(root / "skills" / sk, f"skill '{sk}' also exists in base/skills/; keep one")
    for a in office.agents.values():
        if "name" not in a.meta:
            add(a.path, "frontmatter is missing 'name'")
        for sk in a.office_skills:
            if sk not in office.skills:
                add(a.path, f"office_skills '{sk}' has no skills/{sk}/SKILL.md")
        for sk in a.base_skills:
            if sk not in office.base_skills:
                add(a.path, f"base_skills '{sk}' has no base/skills/{sk}/SKILL.md")
        for sk in a.external_skills:
            if not isinstance(sk, str) or not _EXTERNAL.match(sk):
                add(a.path, f"external_skills '{sk}' must have the form source:name")
        ext = a.meta.get("extends")
        if ext is not None:
            m = re.match(r"^base/([\w.-]+)$", str(ext))
            if not m:
                add(a.path, f"extends '{ext}' must have the form base/<name>")
            elif not (rr / "base" / "agents" / f"{m.group(1)}.md").is_file():
                add(a.path, f"extends '{ext}' but base/agents/{m.group(1)}.md does not exist")

    # 7. backlog/T-*.md
    for t in office.tasks.values():
        for k in TASK_KEYS:
            if k not in t.meta:
                add(t.path, f"frontmatter is missing '{k}'")
        if "id" in t.meta and not t.path.name.startswith(f"{t.id}-"):
            add(t.path, f"file name must start with '{t.id}-'")
        if "status" in t.meta and t.status not in allowed_status:
            add(t.path, f"status '{t.status}' is not a workflow stage ({', '.join(allowed_status)})")
        if "priority" in t.meta and t.priority not in PRIORITIES:
            add(t.path, f"priority '{t.priority}' must be one of {', '.join(PRIORITIES)}")
        if "owner" in t.meta and t.owner != "human" and t.owner not in org_ids:
            add(t.path, f"owner '{t.owner}' is neither 'human' nor an org agent")
        for d in t.depends_on:
            if "/" in d:
                continue  # cross-office reference: not checked offline
            if d not in office.tasks:
                add(t.path, f"depends_on '{d}' does not exist in this backlog")
    return P
