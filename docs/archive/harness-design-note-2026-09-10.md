# Archive — original harness design note (2026-09-10)

**Superseded.** Kept so the early design is on GitHub. Current implementation: [harness.md](../harness.md) · [one-pager](../one-pager.md).

What landed after this note: in-repo eval cage (`src/harness/` + `data/harness/cases/`), one Part B `GrantGraph`, `control_plane.guard` ALLOW/DENY/ASK, MCP/CLI, Langfuse spans, DeepTeam as an optional red-team lane. Sibling package archived.

---

# Grant Agent Harness — design note

Status: proposed (not implemented)
Source of truth: https://github.com/YPCC/grant-agent-lab @ 421c59be
Date: 2026-09-10

## Why

The lab already has a workflow (writer → reviewer → compliance → budget scrutinizer → missing essentials → intake → HITL → package → Office of Research Aid), three runtimes (ADK / LangGraph / hybrid), checklists, samples, and pytest. What it does **not** have is a single **harness**: a fixture-driven runner that injects background knowledge, executes a path under the control plane, scripts HITL, and grades outcomes against gold.

Today’s gaps that a harness should close:

- Part B graph is a keyword stub (`"hypothesis" not in text`).
- Tests import `src.part_c_hybrid.nodes`, `compliance_full`, `reporter_client` that are not present on the current GitHub `src/` tree (graph.py imports them; files are missing). Local checkout is also thinner than GitHub (no `control_plane/`, no `state.py`, no `good_aims_auditory.txt`).
- Skills the README names (grant-proposal-assistant, scientific-strategic-review-board) are not wired as tools.
- Live RePORTER is a soft-fail smoke test, not a reproducible knowledge fixture.
- Control-plane invariants (no NIH ASSIST submit, HITL before freeze, audit log) are documented more than they are enforced in CI.

## What “harness” means here

Not a new product UI. A **eval + execution cage** around the existing agents:

1. Load a case (proposal excerpt + FOA stub + expected issue classes).
2. Attach a **knowledge pack** (SF424 rules, R01 essentials, GPA frameworks, SSRB critique classes, frozen RePORTER abstracts).
3. Run path A, B, or C through `control_plane.guard`.
4. Drive HITL with a scripted PI (`approve` / `revise` / `waive`).
5. Grade with deterministic checks first; optional LLM judge second.
6. Write a trace next to `output/audit_log.jsonl`.

Hard rules (same as the lab):

- Packet destination is the **Office of Research Aid database**, never NIH ASSIST.
- Budget agent **scrutinizes**, does not invent dollars.
- Only public or institutionally authorized proposal text.

## Proposed layout

```
src/harness/
  __init__.py
  cli.py                 # python -m src.harness run --case weak_aims --path part_b_langgraph
  runner.py              # path adapter + HITL script + guard
  cases.py               # load YAML cases
  knowledge.py           # pack resolver (files + skill excerpts)
  graders/
    checklist.py         # r01_essentials + ora_intake
    reviewer_classes.py  # expected critique classes
    control_plane.py     # no NIH submit, HITL fired, tracking format
    skill_gpa.py         # four core questions present
  fixtures/
    reporter/            # frozen RePORTER JSON
    foa/                 # PA/PAR excerpts
    office_db.py         # in-memory ORA submit + tracking numbers

data/harness/cases/
  weak_aims_vague.yaml
  good_aims_auditory.yaml
  incomplete_package.yaml
  hitl_revise_then_approve.yaml
```

## Case schema (minimum)

```yaml
id: weak_aims_vague
mechanism: R01
path: part_b_langgraph
input:
  text_file: data/samples/weak_aims_vague.txt
  foa: PA-25-301
knowledge_pack: [sf424, r01_essentials, gpa_core_questions, ssrb_issue_classes]
hitl_script: [revise, approve]
expect:
  can_freeze: false
  missing_required_any_of: [HYPOTHESIS, AIMS_INDEPENDENT, DMS_PLAN]
  critique_classes_any_of: [vague_hypothesis, aim_dependency, missing_controls]
  office_submit: false
  nih_submit: false
invariants:
  - hitl_status_was_awaiting_human
  - audit_event_emitted
```

## Graders (order)

1. **Deterministic (CI-required)**
2. **Skill-aligned (CI-required, no LLM)**
3. **Optional LLM judge (nightly)**

## Knowledge pack

Do not scrape NIH on every run. Pin versions in `guideline_versions` on `ProposalState`.

## Implementation order

1. Case YAML + deterministic checklist/HITL/office graders on Part B `GrantGraph`.
2. Restore or stub missing Part C modules.
3. Frozen RePORTER fixtures; live API stays opt-in.
4. Skill packs as read-only context, not new agents.
5. Optional LLM judge behind `HARNESS_LLM=1`.

## Out of scope for v0

- New CopilotKit screens
- Real Office of Research Aid production DB
- Cloud Run / Cloud SQL wiring
- Generating a full R01 Research Strategy
- Auto-submit anywhere
