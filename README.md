# Grant Agent Lab

**Multi-agent system for drafting, reviewing, compliance-checking, budget-validating, and packaging NIH (and related) grant proposals until they are ready for institutional review and submission.**

```
PI / RA Request
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│              AGENT CONTROL PLANE (AGT-style)                 │
│  Policy · Identity · Privilege rings · Kill-switch · Audit   │
│  Observability (Langfuse / OpenTelemetry hooks)              │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
                    Orchestration layer
                             │
    ┌────────────┬───────────┼───────────┬────────────┬──────────────┐
    ▼            ▼           ▼           ▼            ▼              ▼
 Knowledge   Grant       Grant      Compliance   Budget         Package
 Updater     Writer      Reviewer   Checker      Scrutinizer    Creator
 (RePORTER)  (skill)     (skill +   (SF424 +     (NIH modular   (versioned
              grant-      scientific institutional  / effort       submission
              proposal-   review)    policies)     norms)         packet)
              assistant)
                             │
                             ▼
                      Human-in-the-Loop
                        (PI / RA)
                             │
                             ▼
                 Institutional package ready
```

## What this lab does

1. **Drafts** Specific Aims (and related sections) using the [grant-proposal-assistant](https://github.com/YPCC/grok-custom-skills/tree/main/skills/grant-proposal-assistant) skill frameworks.
2. **Reviews** from a mock study-section + [scientific-strategic-review-board](https://github.com/YPCC/grok-custom-skills) perspective.
3. **Checks compliance** against NIH SF424-style rules and institutional policies.
4. **Scrutinizes the budget** against NIH modular/detailed norms (does **not** invent a budget).
5. **Pauses for human approval** (HITL).
6. **Packages** the approved proposal into a versioned submission directory with evidence for institutional audit.

Three parallel implementations are provided so teams can choose the right trade-off:

| Path | Stack | Best when |
|------|--------|-----------|
| **Part A** | Pure Google ADK 2.0 + Graph Workflow | Institutional GCP / Vertex AI Agent Engine, IAM, A2A |
| **Part B** | Pure LangGraph + MemorySaver checkpointer | Maximum state control, time-travel, cloud-agnostic |
| **Part C (primary)** | **Hybrid**: ADK outer + LangGraph inner | Production surface of ADK + precision of LangGraph |

### Decision matrix (runtime path)

| If you need… | Choose |
|--------------|--------|
| Vertex AI Agent Engine, native IAM / A2A, little custom looping | **Part A** — Pure ADK 2.0 |
| Typed state, revision loops, checkpoint / time-travel, cloud-agnostic | **Part B** — Pure LangGraph |
| ADK production surface **and** deterministic write→review→compliance→HITL loops | **Part C — Hybrid (default for MCC / OSPA)** |

Full matrices (runtime, data stores, Cloud Run FE vs BE, when LangGraph sits inside ADK): [docs/architecture-considerations/README.md](docs/architecture-considerations/README.md#decision-matrix).

## Quick start (Hybrid – Part C)

```bash
cd grant-agent-lab
python -m venv .venv && source .venv/bin/activate
pip install -e .
# Optional LLM keys: GOOGLE_API_KEY / OPENAI_API_KEY / XAI_API_KEY
PYTHONPATH=. python -m src.part_c_hybrid.demo
```

Pure LangGraph demo (with checkpoint resume):

```bash
PYTHONPATH=. python -m src.part_b_langgraph.demo
```

Tests:

```bash
PYTHONPATH=. python -m pytest tests/ -q
```

## Repository layout

```
grant-agent-lab/
├── README.md
├── docs/
│   ├── architecture-considerations/  # EA notes + all .drawio diagrams
│   ├── guides/                # how-to-use, how-to-add-agent
│   ├── budget-and-package-agent.md
│   ├── control-plane-integration.md
│   ├── datasets-and-validation.md
│   └── end-to-end-workflow.md
├── config/
│   └── policies/              # declarative NIH + skill rules
├── src/
│   ├── shared/                # ProposalState, RePORTER client, LLM helper
│   ├── control_plane/         # AGT-style guard, audit, kill-switch
│   ├── part_a_adk/            # Pure ADK 2.0
│   ├── part_b_langgraph/      # Pure LangGraph + checkpointer
│   └── part_c_hybrid/         # Hybrid (recommended showcase)
├── data/samples/              # public / synthetic Aims + Summary Statement excerpts
├── tests/
└── output/packages/           # versioned submission packages
```

## Diagram color legend

Used consistently in the `.drawio` diagrams under `docs/architecture-considerations/`:

| Color | Meaning |
|-------|---------|
| Blue (`#dae8fc` / stroke `#6c8ebf`) | ADK / outer orchestration / deployment |
| Green (`#d5e8d4` / stroke `#82b366`) | LangGraph nodes / deterministic scientific loop |
| Yellow (`#fff2cc` / stroke `#d6b656`) | Knowledge / guideline freshness |
| Red / rose (`#f8cecc` / stroke `#b85450`) | Human-in-the-loop |
| Purple (`#e1d5e7` / stroke `#9673a6`) | Shared state / memory |

## Documentation

| Guide | Description |
|-------|-------------|
| [Architecture considerations](docs/architecture-considerations/README.md) | EA answers, stack, Cloud SQL, integration, system context + diagrams |
| [Component selection framework](docs/architecture-considerations/architecture-selection-framework.md) | Gates, scoring rubric, CSP services, token/TCO/maintenance cost |
| [Discovery questions](docs/architecture-considerations/architecture-discovery-questions.md) | Function, UX, security, compliance, audit, control plane, governance |
| [How to use](docs/guides/how-to-use.md) | Running demos, interpreting packages |
| [How to add a new agent](docs/guides/how-to-add-agent.md) | Step-by-step extension pattern |
| [Budget & package](docs/budget-and-package-agent.md) | Budget Scrutinizer + Package Creator |
| [Control plane](docs/control-plane-integration.md) | AGT / agent-control-lab mapping |
| [Datasets](docs/datasets-and-validation.md) | Public NIH samples & RePORTER |
| [CopilotKit / DOCX review UI](ui-copilotkit/README.md) | Workbench + agent rail + R01 Aims `.docx` review |
| [Part B LangGraph + HITL](docs/part-b-langgraph-hitl.md) | Pure LangGraph config, Missing Essentials checklist, interrupt-before-freeze |

## How to cite this package

### BibTeX

```bibtex
@software{grant_agent_lab_2026,
  title        = {Grant Agent Lab: Multi-Agent System for NIH Grant Proposal Drafting, Review, Compliance, Budget Validation, and Packaging},
  author       = {{Grant Agent Lab Contributors}},
  year         = {2026},
  url          = {https://github.com/YPCC/grant-agent-lab},
  note         = {Hybrid Google ADK 2.0 + LangGraph implementation under an AGT-style control plane}
}
```

### Inline

> …using Grant Agent Lab (https://github.com/YPCC/grant-agent-lab), a multi-agent system for NIH proposal drafting through institutional packaging.

When discussing the control-plane pattern, also cite:

> Agent Control Lab (https://github.com/YPCC/agent-control-lab) and Microsoft’s Agent Governance Toolkit (AGT).

When using skill frameworks, cite the upstream skills (see References).

## References

1. **grant-proposal-assistant skill** — Specific Aims, Significance, Innovation, Approach frameworks; reviewer mindset; budget-justification-aligned-to-aims.  
   https://github.com/YPCC/grok-custom-skills/tree/main/skills/grant-proposal-assistant

2. **scientific-strategic-review-board skill** — Independent scientific/strategic critique patterns.  
   https://github.com/YPCC/grok-custom-skills (scientific-strategic-review-board)

3. **Agent Control Lab** — Spec-driven LangGraph multi-agent control plane under Microsoft AGT concepts.  
   https://github.com/YPCC/agent-control-lab

4. **Microsoft Agent Governance Toolkit (AGT)** — Seven-layer governance model for agent runtime security.  
   https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/

5. **NIH RePORTER API v2** — Live project search used by the Knowledge Updater.  
   https://api.reporter.nih.gov/

6. **NIH SF424 / Modular Budget guidance** — Modular ceiling ($250,000 direct/year), $25,000 modules, personnel justification in person-months.  
   - https://grants.nih.gov/grants/how-to-apply-application-guide/forms-i/general/g.320-phs-398-modular-budget-form.htm  
   - https://grants.nih.gov/grants-process/write-application/advice-on-application-sections/develop-your-budget  
   - https://www.niaid.nih.gov/grants-contracts/create-budget

7. **NIAID / NIDCD sample applications** — Public funded applications and Summary Statements used for evaluation fixtures.  
   - https://www.niaid.nih.gov/grants-contracts/sample-applications  
   - https://www.nidcd.nih.gov/funding/sample-grant-applications

8. **LangGraph** — Stateful multi-actor application framework (StateGraph, checkpointers).  
   https://github.com/langchain-ai/langgraph

9. **Google Agent Development Kit (ADK) 2.0** — Graph workflows, LlmAgent, Vertex AI Agent Engine.  
   https://google.github.io/adk-docs/ (documentation)

## License

Apache-2.0 (or align with institutional / upstream preferences).
