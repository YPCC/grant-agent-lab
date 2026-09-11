# Grant Agent Lab — one page

**What this repo is.** A lab for a multi-agent NIH (R01-style) grant assistant. A PI or navigator drafts and reviews Specific Aims, scores Missing Essentials, fills a grouped Office of Research Aid intake form, pauses for a human, then packages the packet. A tracking number comes back. **The lab does not submit to NIH ASSIST / Grants.gov.** That step stays with office staff, out of band.

**What it showcases.** Not “an LLM that writes grants.” It showcases a **governed agent graph**: typed state, human-in-the-loop before freeze, policy verdicts on every risky act, catalogs instead of prompt folklore, and an eval cage that must fail weak aims. Three runtimes share those catalogs so the *product* stays the same while the *engine* is swapped.

```text
knowledge → reviewer (GPA + SSRB) → missing essentials → intake → HITL freeze → ORA package
                              ✕ NIH ASSIST (denied)
```

## Features

| Feature | What you can point at |
|---------|------------------------|
| **LangGraph agent (Part B, default)** | `GrantGraph`: invoke / resume, interrupt-before-freeze, MemorySaver or in-process threads. Same nodes as the workbench. |
| **ADK and hybrid (Parts A / C)** | Pure Google ADK 2.0, or ADK outer + LangGraph inner. Switch in `config/runtime.yaml` — no rewrite of checklists. |
| **Control plane** | `guard()` wraps nodes. **ALLOW** review/checklist/intake. **ASK** freeze and office submit. **DENY** NIH ASSIST, invented budget dollars, auto `PI_CERTIFY`. Audit log + kill-switch. |
| **Langfuse observability** | Optional. One parent trace per graph invoke/resume; a child span per agent. DENY = ERROR, ASK = WARNING. Keys off → no-op (CI still green). |
| **Eval harness** | YAML cases (weak aims, good aims, HITL, incomplete, complete ORA). Deterministic graders. CI on every push. Workbench Harness tab runs the **same graph**. |
| **MCP / Copilot plugin** | `python3 -m src.harness mcp` — Copilot, Cursor, Claude, optional Omnigent driver. Domain truth stays in this repo. |
| **Catalogs, not vibes** | `r01_essentials.yaml`, `ora_intake.yaml`, SF424 rules, GPA four questions, SSRB issue classes. |
| **Budget scrutinizer** | Checks modular/detailed norms. Does **not** invent a budget. |
| **HITL + RBAC** | PI / Navigator / Office of Research Aid / Admin. PI **can** submit to the office database; nobody here submits to NIH. |
| **UIs** | Python workbench (Review, Intake, Harness) and CopilotKit Next.js. No model key required for the demo path. |

## What success looks like

- Vague Aims **cannot freeze**. Complete packet + human approve → tracking `ORA-YYYYMMDD-xxxxxx`.
- A Copilot session or an Omnigent YAML file may *drive* the graph. They must not *replace* it.
- Green CI means the cage still holds, not that a model “wrote a good grant.”

Deeper: [architecture](architecture.md) · [harness vs Omnigent](harness-vs-omnigent.md) · [control plane](control-plane-integration.md) · [Part B HITL](part-b-langgraph-hitl.md).
