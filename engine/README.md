# Engine (planned)

Nothing here runs yet. Phase 1 runs offices inside Claude Code using generated subagents (`.claude/agents/`). The engine below replaces that once the workflow is proven.

| Component | What it does | Backlog |
|---|---|---|
| `runtime/` | Loads an office folder, runs the orchestrator and agents on the Claude Agent SDK, enforces workflow gates, logs every run. Loader + validate + dry-run built (T-039, see `runtime/README.md`); live runs T-024 | T-024 |
| `guard/` | PreToolUse hook that blocks agent writes to prod (Bash + MCP), default-deny, fail-closed. Built and tested here (T-040, see `guard/README.md`); not installed anywhere | T-040 |
| `costs/` | Tokens and cost per run and per agent, review-round cap | T-026 |
| `brain_mcp/` | MCP server over the brain repos: `search`, `read`, `append_log`, `propose_decision`, scoped work / personal | T-021 |
| `curator/` | Nightly: promotes logs into decisions, systems, open items as a PR | T-023 |
| `app/` | Office visualization (renders `theme/`), chat panel, approvals | T-027, T-028 |
| `telegram/` | Status and approvals on the phone | T-029 |

Auth: sign in with Claude Code using the Max plan; keep `ANTHROPIC_API_KEY` unset so runs use the SDK credit.
