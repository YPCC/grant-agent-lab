# Grant Agent Lab — one page

**What this repo is.** A lab for a multi-agent NIH (R01-style) grant assistant. A PI or navigator drafts and reviews Specific Aims, scores Missing Essentials, fills a grouped Office of Research Aid intake form, pauses for a human, then packages the packet. A tracking number comes back. **The lab does not submit to NIH ASSIST / Grants.gov.** That step stays with office staff, out of band.

**What it showcases.** Not “an LLM that writes grants.” It showcases a **governed agent graph**: typed LangGraph state, human-in-the-loop before freeze, control-plane ALLOW / DENY / ASK on every risky act, YAML catalogs instead of prompt folklore, an eval cage that must fail weak aims, and optional **Langfuse traces** so each agent is visible (without replacing the guard). Three runtimes share those catalogs so the *product* stays the same while the *engine* is swapped.

```text
knowledge → reviewer (GPA + SSRB) → missing essentials → intake → HITL freeze → ORA package
                 ↑ guard() + Langfuse span per agent              ✕ NIH ASSIST (denied)
```

## Features

| Feature | What you can point at |
|---------|------------------------|
| **LangGraph agent (Part B, default)** | `GrantGraph`: invoke / resume, interrupt-before-freeze. Same nodes as the workbench, harness, and MCP. |
| **ADK and hybrid (Parts A / C)** | Pure Google ADK 2.0, or ADK outer + LangGraph inner. Switch in `config/runtime.yaml`. |
| **Control plane** | `guard()` wraps nodes. **ALLOW** review/checklist/intake. **ASK** freeze and office submit. **DENY** NIH ASSIST, invented budget, auto `PI_CERTIFY`. Audit log + kill-switch. |
| **Langfuse observability** | Optional. Parent trace per invoke/resume; child span per agent. DENY = ERROR, ASK = WARNING. No keys → no-op (CI still green). |
| **Eval harness** | YAML cases + deterministic graders + GitHub Actions. Weak aims cannot freeze. Optional DeepTeam is a **red-team lane**, not the cage. |
| **MCP / Copilot / Grok plugin** | `grant-harness mcp` (pipx analog of NPX). Skill is a *driver*. Graph stays here. |
| **Catalogs** | `r01_essentials.yaml`, `ora_intake.yaml`, SF424 rules, GPA four questions, SSRB issue classes. |
| **Budget scrutinizer** | Checks modular/detailed norms. Does **not** invent a budget. |
| **HITL + RBAC** | PI / Navigator / Office / Admin. PI can submit to the **office** database only. |
| **UIs** | Python workbench, CopilotKit, **desktop** (`python -m src.desktop`). Settings tab: Vertex / Gemini / OpenAI / xAI. |

## What success looks like

- Vague Aims **cannot freeze**. Complete packet + human approve → tracking `ORA-YYYYMMDD-xxxxxx`.
- A Copilot or Omnigent session may *drive* the graph. They must not *replace* it.
- Green CI means the cage still holds — not that a model “wrote a good grant.”
- With Langfuse keys: one trace tree per run, one span per agent. Without keys: the lab still runs.

Deeper: [desktop / embed](guides/how-to-use-desktop-and-embedded-agent.md) · [architecture](architecture.md) · [governance](governance.md) · [packaging](packaging-and-deploy.md) · [C4](architecture-considerations/c4-infographics/README.md) · [observability](observability.md) · [control plane](control-plane-integration.md).
