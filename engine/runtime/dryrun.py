"""Pick the next eligible task and describe what a run would do. Read-only."""
from .loader import Office, Task

PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}


def task_number(task_id):
    """'T-039' -> 39 (numeric, so T-100 sorts after T-99)."""
    tail = task_id.rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else 10 ** 9


def eligible(office):
    out = []
    for t in office.tasks.values():
        if t.status in office.terminal or t.status not in office.stage_ids:
            continue
        if t.owner == "human":
            continue
        # a cross-office dependency cannot be verified offline: counts as not done
        if any(d not in office.tasks or office.tasks[d].status != "done" for d in t.depends_on):
            continue
        out.append(t)
    out.sort(key=lambda t: (PRIORITY_RANK.get(t.priority, 99), task_number(t.id)))
    return out


def pick_next(office):
    found = eligible(office)
    return found[0] if found else None


def plan(office, task):
    stage = office.stage(task.status) or {}
    agent = office.agents.get(task.owner)
    org = {a.get("id"): a for a in office.org.get("agents", []) if isinstance(a, dict)}
    name = org.get(task.owner, {}).get("name")
    owner = f"{task.owner} ({name})" if name else task.owner
    section = stage.get("output_section")
    if section is None:
        section = f"none (exit: {stage.get('exit')})"
    rows = [
        ("task", f"{task.id} {task.title}"),
        ("file", office.rel(task.path)),
        ("stage", task.status),
        ("owner", owner),
        ("profile", office.rel(agent.path) if agent else "none"),
        ("base_skills", ", ".join(office.default_base_skills + (agent.base_skills if agent else [])) or "none"),
        ("office_skills", ", ".join(agent.office_skills) if agent and agent.office_skills else "none"),
        ("skill_files", ", ".join(office.skill_files(agent)) if agent and office.skill_files(agent) else "none"),
        ("external_skills", ", ".join(agent.external_skills) if agent and agent.external_skills else "none"),
        ("output_section", section),
    ]
    consults = [
        f"{c['agent']} ({org.get(c['agent'], {}).get('name', c['agent'])}) writes {c['output_section']} when {c['when']}"
        for c in office.workflow.get("consults") or []
        if isinstance(c, dict) and c.get("stage") == task.status
    ]
    if consults:
        rows.append(("consults", "; ".join(consults)))
    if stage.get("owner") and stage["owner"] != task.owner:
        rows.append(("note", f"task owner {task.owner} differs from stage owner {stage['owner']}"))
    return rows


def format_plan(office, rows):
    head = f"{office.id}: dry-run (no files changed, no SDK or network calls)"
    return "\n".join([head] + [f"{k}: {v}" for k, v in rows])
