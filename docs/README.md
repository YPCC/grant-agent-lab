# Documentation

| Doc | Contents |
|-----|----------|
| [One-pager](one-pager.md) | What this repo is, what it showcases (LangGraph, guard, harness, Langfuse) |
| [How to configure](guides/how-to-configure.md) | `runtime.yaml`, agents, HITL, checklist, env vars |
| [How to launch the UI](guides/how-to-launch-ui.md) | Workbench on :8080 and CopilotKit Next.js |
| [How to create demo files](guides/how-to-create-demo-files.md) | Record MP4 + stills (Playwright / ffmpeg) |
| [Demo videos](demo/README.md) | CopilotKit UI + Python workbench walkthroughs (MP4) |
| [Architecture (Mermaid)](architecture.md) | C4 context + containers, one pipeline, RBAC |
| [C4 infographics](architecture-considerations/c4-infographics/README.md) | SVG context + containers + JPG posters |
| [Intake & office submit](intake-and-office-submit.md) | Form groups, packaging agent, tracking number |
| [Part B LangGraph + HITL](part-b-langgraph-hitl.md) | Interrupt-before-freeze |
| [End-to-end workflow](end-to-end-workflow.md) | Draft → office database (not NIH) |
| [Architecture considerations](architecture-considerations/README.md) | EA packet, Cloud Run, Cloud SQL, draw.io |
| [PI R01 workflow UI](architecture-considerations/pi-r01-workflow-ui.md) | Product spec and RBAC |
| [Control plane](control-plane-integration.md) | AGT-style guard |
| [Governance profiles](governance.md) | Local vs production (fail-closed) |
| [Observability (Langfuse)](observability.md) | Per-agent traces; optional keys |
| [Budget & package](budget-and-package-agent.md) | Scrutinizer (not planner) |
| [Eval harness](harness.md) | In-lab cases, graders, MCP/CLI |
| [What the harness is vs Omnigent](harness-vs-omnigent.md) | Call-out: our eval cage vs Omni meta-harness |
| [DeepTeam in the harness](deepteam-adoption.md) | Optional red-team lane; does not replace YAML graders |
| [Omnigent adapter](omnigent-adoption.md) | Optional outer driver; not a rewrite |
| [Datasets](datasets-and-validation.md) | Public NIH samples / RePORTER |
| [Archive: original harness design](archive/harness-design-note-2026-09-10.md) | 2026-09-10 note (superseded by in-repo cage) |
