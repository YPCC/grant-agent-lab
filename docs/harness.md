# Eval harness (in-lab feature)

The eval cage lives **in this repo**, not in a sibling package.

Harness cases invoke **the same Part B `GrantGraph`** as the workbench. There is one pipeline:

`knowledge → reviewer → missing essentials → intake → HITL → freeze / ORA package`

Every node is mediated by `control_plane.guard` (ALLOW / DENY / ASK).

- Cases: `data/harness/cases/`
- Knowledge packs: `config/checklists/` + `config/policies/` + `data/harness/packs/`
- Runner / MCP / CLI: `src/harness/` (runner calls `src.part_b_langgraph.graph.build_graph`)
- Policies: `src/harness/policies.py` wired in `src/control_plane/guard.py`
- Workbench: `ui-copilotkit/serve_workbench.py` (Review tab + Harness tab)

```bash
PYTHONPATH=. python3 -m src.harness list-cases
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 -m src.harness mcp
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py   # :8080
```
