# Part B — Pure LangGraph + HITL + Missing Essentials

Configuration lives in `config/runtime.yaml`:

```yaml
path: part_b_langgraph
hitl:
  enabled: true
  interrupt_before: freeze_package
  resume_roles: [PI, OSPA, Admin]
agents:
  missing_essentials: {enabled: true}
```

## Graph

`reviewer → missing_essentials → hitl (interrupt) → freeze | revise`

- **Missing Essentials** scores the draft against `config/checklists/r01_essentials.yaml`.
- **HITL** pauses before package freeze. PI/OSPA choose `approve` / `revise` / `waive`.
- Official NIH submit is still **not** in this graph (`submission_assistant.enabled: false`).

If the `langgraph` package is installed, `build_graph()` compiles a real `StateGraph` + `MemorySaver`. If not, `GrantGraph` uses the same nodes and a thread checkpoint.

## UI

Workbench (`python3 ui-copilotkit/serve_workbench.py`):

- Checklist of required items (present / missing)
- HITL buttons: revise / approve freeze
- Role chip: PI cannot Submit
