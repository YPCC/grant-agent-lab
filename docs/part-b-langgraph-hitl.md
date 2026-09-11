# Part B — Pure LangGraph + HITL + Missing Essentials

Configuration lives in `config/runtime.yaml`:

```yaml
path: part_b_langgraph
hitl:
  enabled: true
  interrupt_before: freeze_package
  resume_roles: [PI, "Office of Research Aid", Admin]
agents:
  missing_essentials: {enabled: true}
```

## Graph

`knowledge → reviewer → missing_essentials → intake → hitl (interrupt) → freeze | revise`

- **Reviewer** uses the GPA + SSRB issue classes (`src/harness/review.py`).
- **Missing Essentials** scores the draft against `config/checklists/r01_essentials.yaml`.
- **Intake** fills `config/checklists/ora_intake.yaml` (PI_CERTIFY is human-only).
- **HITL** pauses before package freeze. PI/Office of Research Aid choose `approve` / `revise` / `waive`.
- **Package** registers with the Office of Research Aid database only. NIH ASSIST is **denied** by `control_plane.guard`.
- The **eval harness** and **workbench** call this same graph.
- Optional **Langfuse**: `invoke` / `resume` are parent traces; each `guard()` call is a child span ([observability.md](observability.md)).

Default engine is `GrantGraph` (`invoke` / `resume`). Set `GRANT_GRAPH_ENGINE=langgraph` to compile a real `StateGraph` + `MemorySaver` when the package is installed.

## UI

Workbench (`PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py`, **:8080**):

- Review findings + Missing Essentials
- Intake form + HITL approve freeze
- Harness tab (same cases as CI)
- Role chip: PI **can** submit to the office database (not NIH)
