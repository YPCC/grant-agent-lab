# Grant Agent Lab

**Multi-agent system for drafting, reviewing, compliance-checking, budget-validating, and packaging NIH (and related) grant proposals, then submitting the packet to the Office of Research Aid database (not NIH).**

Start here: **[one-pager](docs/one-pager.md)** · **[configure](docs/guides/how-to-configure.md)** · **[launch UI](docs/guides/how-to-launch-ui.md)** · **[eval harness](docs/harness.md)** · **[create demos](docs/guides/how-to-create-demo-files.md)** · **[architecture](docs/architecture.md)** · **[C4 infographics](docs/architecture-considerations/c4-infographics/README.md)** · **[docs index](docs/README.md)**

[![Harness](https://github.com/YPCC/grant-agent-lab/actions/workflows/harness.yml/badge.svg)](https://github.com/YPCC/grant-agent-lab/actions/workflows/harness.yml)

## Architecture

```mermaid
flowchart TD
  PI[PI / Navigator] --> UI[Workbench :8080 / CopilotKit]
  PI --> MCP[MCP stdio · Copilot / Cursor / Claude]
  ORA["Office of Research Aid"] --> UI
  UI --> CP[Control plane<br/>ALLOW / DENY / ASK]
  MCP --> CP
  HARNESS[Eval harness cases] --> CP
  CP --> G[Part B GrantGraph]
  G --> RV[Reviewer GPA+SSRB]
  RV --> ME[Missing Essentials]
  ME --> INTAKE[Intake form]
  INTAKE --> HITL{HITL freeze}
  HITL -->|revise| RV
  HITL -->|PI certify + complete| PK[Package Creator]
  PK --> ODB[Office of Research Aid database]
  ODB --> TRACK[Tracking number returned to PI]
  CP -.->|DENY| ASSIST[NIH ASSIST — out of band]
```

Full diagrams: [docs/architecture.md](docs/architecture.md) (Mermaid) · [C4 SVG](docs/architecture-considerations/c4-infographics/c4-system-context-unified.svg) · [C4 infographics](docs/architecture-considerations/c4-infographics/README.md) · [draw.io](docs/architecture-considerations/README.md).

![C4 system context — unified](docs/architecture-considerations/c4-infographics/c4-system-context-unified.svg)


## What this lab does

1. **Drafts** Specific Aims using [grant-proposal-assistant](https://github.com/YPCC/grok-custom-skills/tree/main/skills/grant-proposal-assistant) frameworks.
2. **Reviews** from a mock study-section + [scientific-strategic-review-board](https://github.com/YPCC/grok-custom-skills) lens.
3. **Checks compliance** against NIH SF424-style rules and institutional policies.
4. **Scrutinizes the budget** against NIH modular/detailed norms (does **not** invent a budget).
5. **Scores Missing Essentials** (required R01 package items) and **pauses for HITL**.
6. **Packages** an approved proposal and submits it to the **Office of Research Aid database**. Completing the grouped intake form (compliance, formatting, institutional) unlocks submit. A **tracking number** comes back to the PI. This lab does **not** submit to NIH ASSIST.
7. **Eval cage** — YAML cases, MCP/CLI plugin, and GitHub Actions run the **same graph**. Weak aims cannot freeze. Control plane **DENY**s NIH ASSIST and invented budget dollars.

Three parallel implementations (catalogs and guard are shared). **Harness / workbench / MCP drive Part B:**

| Path | Stack | Best when |
|------|--------|-----------|
| **Part A** | Pure Google ADK 2.0 + Graph Workflow | Vertex AI Agent Engine, IAM, A2A |
| **Part B** (config default) | Pure LangGraph + MemorySaver / `GrantGraph` | Typed state, revision loops, HITL interrupt |
| **Part C** | **Hybrid**: ADK outer + LangGraph inner | Production ADK + deterministic inner loop |

Switch path in [`config/runtime.yaml`](config/runtime.yaml) (`path: part_a_adk | part_b_langgraph | part_c_hybrid`). Details: [how to configure](docs/guides/how-to-configure.md).

## Quick start — UI

No npm and no model key:

```bash
git clone https://github.com/YPCC/grant-agent-lab.git
cd grant-agent-lab
pip install python-docx
python3 ui-copilotkit/serve_workbench.py
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080). Review the sample R01 Aims, complete the grouped **intake form** (agent-filled; override as needed, including PI certify), then **Submit to Office of Research Aid**. The **Harness** tab runs the same `GrantGraph` cases. A tracking number comes back to the PI. There is no Submit to NIH.

**Recorded demos** (watch first):

| UI | Video |
|----|--------|
| CopilotKit Next.js (`:3000`) | [e2e-copilotkit-demo.mp4](docs/demo/e2e-copilotkit-demo.mp4) (46s, intake → office tracking) |
| Python workbench (`:8080`) | [e2e-workbench-demo.mp4](docs/demo/e2e-workbench-demo.mp4) (30s, intake → office tracking) |

CopilotKit Next.js (optional chat):

```bash
cd ui-copilotkit && npm install --legacy-peer-deps && npm run dev
```

See [how to launch the UI](docs/guides/how-to-launch-ui.md).

## Record a demo

Demos are Playwright walkthroughs encoded to H.264 MP4 (1440×900) in [`docs/demo/`](docs/demo/). Full recipe: [how to create demo files](docs/guides/how-to-create-demo-files.md).

```bash
pip install playwright python-docx
python3 -m playwright install chromium   # ffmpeg also required

# Terminal A — UI
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py

# Terminal B — record
PYTHONPATH=. python3 scripts/record_demo.py --target workbench
# or, with Next.js already on :3000:
PYTHONPATH=. python3 scripts/record_demo.py --target copilotkit
```

That overwrites `docs/demo/e2e-*-demo.mp4` plus matching `still-*.png`. Do not commit `node_modules/`, `.next/`, or raw WebM.

## Quick start — agents / tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=. python -m pytest tests/test_harness.py tests/test_harness_mcp.py tests/test_harness_policies.py tests/test_control_plane.py tests/test_observability.py tests/test_graph_pipeline.py tests/test_checklist.py tests/test_intake_office.py -q

# Eval harness (MCP plugin for Copilot / any LLM tool)
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 -m src.harness mcp
```

Optional LLM keys (gitignored `.env`): `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`. Optional traces: `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` — [observability](docs/observability.md).

## Repository layout

```
grant-agent-lab/
├── README.md
├── docs/
│   ├── README.md                 # docs index
│   ├── architecture.md           # Mermaid diagrams
│   ├── architecture-considerations/
│   │   ├── README.md             # EA notes + draw.io
│   │   └── c4-infographics/      # presentation C4 posters
│   ├── demo/                     # recorded E2E UI walkthrough
│   ├── guides/
│   │   ├── how-to-configure.md
│   │   ├── how-to-launch-ui.md
│   │   └── how-to-create-demo-files.md
├── scripts/
│   └── record_demo.py            # Playwright + ffmpeg recorder
├── config/
│   ├── runtime.yaml              # path, HITL, agents
│   ├── checklists/
│   │   ├── r01_essentials.yaml
│   │   └── ora_intake.yaml      # office intake form
│   └── policies/
├── src/
│   ├── shared/checklist.py
│   ├── shared/intake.py
│   ├── shared/packaging.py
│   ├── control_plane/
│   ├── part_a_adk/
│   ├── part_b_langgraph/
│   ├── part_c_hybrid/
│   └── harness/                  # eval cage + MCP/CLI + Omnigent policies
├── agents/                       # optional Omnigent/Copilot driver YAML
├── plugin/                       # Copilot / Cursor / Claude MCP snippets
├── ui-copilotkit/                # workbench + CopilotKit
├── data/samples/
├── data/harness/cases/           # YAML eval fixtures
└── tests/
```

## Diagram color legend

Used in [draw.io](docs/architecture-considerations/) files:

| Color | Meaning |
|-------|---------|
| Blue (`#dae8fc` / `#6c8ebf`) | UI / MCP / Copilot |
| Green (`#d5e8d4` / `#82b366`) | LangGraph / GrantGraph nodes |
| Yellow (`#fff2cc` / `#d6b656`) | Knowledge / FOA / control-plane policy |
| Rose (`#f8cecc` / `#b85450`) | Human-in-the-loop / eval harness |
| Purple (`#e1d5e7` / `#9673a6`) | Shared catalogs / state |

## Documentation

| Guide | Description |
|-------|-------------|
| [Docs index](docs/README.md) | All guides |
| [One-pager](docs/one-pager.md) | What this repo is and showcases |
| [How to configure](docs/guides/how-to-configure.md) | `runtime.yaml`, agents, HITL, env |
| [How to launch UI](docs/guides/how-to-launch-ui.md) | Workbench and CopilotKit |
| [How to create demo files](docs/guides/how-to-create-demo-files.md) | Record MP4 + stills |
| [Demo videos](docs/demo/README.md) | CopilotKit UI + Python workbench walkthroughs |
| [Architecture (Mermaid)](docs/architecture.md) | System context (C4), one pipeline, RBAC |
| [C4 infographics](docs/architecture-considerations/c4-infographics/README.md) | SVG context + containers + JPG posters |
| [Eval harness](docs/harness.md) | Cases, MCP/CLI, CI eval-cage |
| [Harness vs Omnigent](docs/harness-vs-omnigent.md) | Our eval cage vs Omni meta-harness |
| [Control plane](docs/control-plane-integration.md) | ALLOW / DENY / ASK guard |
| [Observability](docs/observability.md) | Langfuse traces per agent |
| [Omnigent adapter](docs/omnigent-adoption.md) | Optional outer driver |
| [Architecture considerations](docs/architecture-considerations/README.md) | EA packet, Cloud SQL, Cloud Run, draw.io C4 |
| [Intake & office submit](docs/intake-and-office-submit.md) | Form groups, packaging, tracking number |
| [Part B LangGraph + HITL](docs/part-b-langgraph-hitl.md) | Interrupt-before-freeze |
| [Budget & package](docs/budget-and-package-agent.md) | Scrutinizer + package creator |
| [Datasets](docs/datasets-and-validation.md) | NIH samples & RePORTER |
| [CopilotKit UI](ui-copilotkit/README.md) | DOCX review showcase |

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

When discussing the control-plane pattern, also cite [Agent Control Lab](https://github.com/YPCC/agent-control-lab) and Microsoft’s Agent Governance Toolkit (AGT).

## References

1. **grant-proposal-assistant skill** — https://github.com/YPCC/grok-custom-skills/tree/main/skills/grant-proposal-assistant
2. **scientific-strategic-review-board skill** — https://github.com/YPCC/grok-custom-skills
3. **Agent Control Lab** — https://github.com/YPCC/agent-control-lab
4. **Microsoft AGT** — https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/
5. **NIH RePORTER API v2** — https://api.reporter.nih.gov/
6. **NIH SF424 / Modular Budget** — https://grants.nih.gov/grants-process/write-application/advice-on-application-sections/develop-your-budget
7. **NIAID / NIDCD sample applications** — https://www.niaid.nih.gov/grants-contracts/sample-applications
8. **LangGraph** — https://github.com/langchain-ai/langgraph
9. **Google ADK 2.0** — https://google.github.io/adk-docs/

## License

Apache-2.0 (or align with institutional / upstream preferences).
