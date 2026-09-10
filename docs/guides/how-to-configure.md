# How to configure

Runtime behavior is selected in YAML. Change files under [`config/`](../../config/); do not hard-code path or HITL flags in agents.

## 1. Choose an implementation path

Edit [`config/runtime.yaml`](../../config/runtime.yaml):

```yaml
path: part_b_langgraph   # part_a_adk | part_b_langgraph | part_c_hybrid
```

| `path` | Stack | When to use |
|--------|--------|-------------|
| `part_a_adk` | Google ADK 2.0 workflow | Vertex AI Agent Engine, IAM, A2A |
| `part_b_langgraph` | Pure LangGraph + checkpointer | Typed state, revision loops, cloud-agnostic |
| `part_c_hybrid` | ADK outer + LangGraph inner | Production ADK surface **and** deterministic loops |

Current default in this repo is **Part B** so HITL and the Missing Essentials checklist run without ADK.

## 2. Human-in-the-loop

```yaml
hitl:
  enabled: true
  interrupt_before: freeze_package
  resume_roles: [PI, "Office of Research Aid", Admin]
  decisions: [approve, revise, waive]
```

- Graph **pauses** before package freeze.
- Only listed roles may resume.
- `approve` only freezes if the checklist has no required gaps.
- Official NIH submit is **not** a HITL decision (see `submission_assistant` below).

## 3. Enable or disable agents

```yaml
agents:
  knowledge_updater: {enabled: true}
  writer: {enabled: true}
  reviewer: {enabled: true}
  compliance: {enabled: true}
  budget_scrutinizer: {enabled: true}
  missing_essentials: {enabled: true}
  package_creator: {enabled: true}
  submission_assistant: {enabled: false}  # Office of Research Aid / AOR only; never autonomous
```

Keep `submission_assistant.enabled: false`. This lab submits to the **Office of Research Aid database** via the packaging agent, not to NIH. Never store eRA passwords.

## 4. Checklist catalog (Missing Essentials)

```yaml
checklist:
  catalog: config/checklists/r01_essentials.yaml
  mechanism: R01
```

Each item in [`config/checklists/r01_essentials.yaml`](../../config/checklists/r01_essentials.yaml) has:

- `id`, `label`, `group`
- `required: true|false`
- `detect:` keyword list used against extracted document text

To add a required form (for example a DMS plan variant), append an item and re-run review. No code change is required for keyword-based presence checks.

## 5. Control plane and audit

```yaml
observability:
  audit_log: output/audit_log.jsonl

control_plane:
  guard: true
  pi_cannot_submit: true
```

`pi_cannot_submit: true` is the RBAC rule shown in the UI (Submit disabled for PI).

NIH SF424-style rules live in [`config/policies/nih_sf424_rules.yaml`](../../config/policies/nih_sf424_rules.yaml).

## 6. Environment variables

| Variable | Used by | Required? |
|----------|---------|-----------|
| `PYTHONPATH=.` | Local Python demos / tests | Yes for `python -m` |
| `GOOGLE_API_KEY` | ADK / Gemini writer | Optional for checklist-only demo |
| `OPENAI_API_KEY` | CopilotKit free-form chat | Optional; workbench review works without it |
| `XAI_API_KEY` | Optional Grok-backed skills | Optional |
| `LANGSMITH_API_KEY` | LangGraph Platform | Optional |

Copy keys into a local `.env` (gitignored). Do not commit secrets.

## 7. Python install

```bash
cd grant-agent-lab
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# ADK path:
pip install -e ".[adk]"
```

`python-docx` is needed for the DOCX workbench:

```bash
pip install python-docx
```

See also [Part B HITL](../part-b-langgraph-hitl.md) and [control plane](../control-plane-integration.md).
