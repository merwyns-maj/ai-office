# RAID log — ai-office

Kept by Janice (PMO). Review at every sprint plan and phase change. Close entries, never delete them.

| ID | Type | Item | Owner | Opened | Next action / verify by | Status |
|---|---|---|---|---|---|---|
| R-1 | Dependency | Claude GitHub app not installed on impact-credit-solutions; blocks company-repo tasks (T-003, T-017, T-018, T-025) | Merwyn | 2026-11-25 | Org owner installs the app (T-002) | Open |
| R-2 | Risk | SDK credit overspend once the engine runs agents in loops | Janice | 2026-11-25 | Cost logging (T-026) before scheduled BAU; cap in office.yaml | Open |
| R-3 | Assumption | Claude app skills (skill-creator, diagram-design, ...) are available to agents in chat sessions but not yet in the SDK engine | Fang | 2026-11-25 | Verify when T-024 starts | Open |
| R-4 | Issue | Laptop bridge drops intermittently; local repos (klik-workspace) unreachable from cloud sessions | Merwyn | 2026-11-25 | Prefer GitHub access over the laptop link | Open |
| R-5 | Risk | T-019 and T-024 need company repos or paid SDK runs to finish; sprint 1 builds only the repo-only slices (T-040, T-039). Remainders stay in T-019 and T-024 | Janice | 2026-11-25 | Revisit at sprint 2 plan, after T-002 | Open |
| R-6 | Assumption | Claude Code PreToolUse hook contract: stdin JSON with `tool_name` and `tool_input` (`tool_input.command` for Bash); exit 2 blocks and stderr is shown to Claude; exit 0 allows; configured under `hooks.PreToolUse` with a regex matcher; MCP tools are named `mcp__<server>__<tool>`; a hook timeout or non-2 non-zero exit is non-blocking; per-hook `timeout` key exists; the command runs via a POSIX shell (so `|| exit 2` works). T-040 design depends on it | Fang | 2026-11-25 | Engineer checks current Claude Code hook docs before the T-040 PR and cites the URL in Build notes | Open |
