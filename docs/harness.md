# Eval harness (in-lab feature)

Call-out (what this harness is, vs Omnigent’s meta-harness): [harness-vs-omnigent.md](harness-vs-omnigent.md).


Harness cases invoke **the same Part B `GrantGraph`** as the workbench. There is one pipeline:

`knowledge → reviewer → missing essentials → intake → HITL → freeze / ORA package`

Every node is mediated by `control_plane.guard` (ALLOW / DENY / ASK). Optional Langfuse: span per agent ([observability.md](observability.md)).

- Cases: `data/harness/cases/`
- Knowledge packs: `config/checklists/` + `config/policies/` + `data/harness/packs/`
- Runner / MCP / CLI: `src/harness/` (runner calls `src.part_b_langgraph.graph.build_graph`)
- Policies: `src.harness.policies.py` wired in `src/control_plane/guard.py`
- Workbench: `ui-copilotkit/serve_workbench.py` (Review tab + Harness tab)
- CI: `.github/workflows/harness.yml` — same pytest set on every push/PR. Weak aims must not freeze; NIH ASSIST must stay denied.

```bash
PYTHONPATH=. python3 -m src.harness list-cases
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 -m src.harness mcp
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py   # :8080
PYTHONPATH=. python3 -m pytest tests/test_harness.py tests/test_harness_mcp.py tests/test_harness_policies.py tests/test_control_plane.py tests/test_observability.py tests/test_graph_pipeline.py tests/test_checklist.py tests/test_intake_office.py -q
```
