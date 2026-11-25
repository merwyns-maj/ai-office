"""Tiny frontmatter helpers (stdlib only)."""
import re

def split(text):
    """Return (frontmatter dict, body) from a markdown file with --- frontmatter."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.split(" #")[0].strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        fm[k.strip()] = v
    return fm, m.group(2)

def dump(fm, keys_order):
    lines = ["---"]
    for k in keys_order:
        if k in fm and fm[k] not in (None, ""):
            lines.append(f"{k}: {fm[k]}")
    lines.append("---")
    return "\n".join(lines) + "\n"

def as_list(v):
    v = (v or "").strip().strip("[]")
    return [x.strip() for x in v.split(",") if x.strip()]
