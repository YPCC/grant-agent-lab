# Omnigent vs Grant Agent Lab — adopt, adapt, or ignore

**What the lab harness *is* (pieces, cases, invariants) vs Omnigent’s meta-harness:** [harness-vs-omnigent.md](harness-vs-omnigent.md). This page is the adopt / ignore list.

Source: [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) (Apache-2.0, Databricks OSS, 2026).
Date: 2026-09-10.

## Two different meanings of “harness”

| Word | Omnigent | Grant Agent Lab |
|------|----------|-----------------|
| **Harness** | Wrapper around a *coding* agent runtime (Claude Code, Codex, Cursor, Copilot CLI, Pi, ACP). Loop + tools + session. | Domain **eval cage**: YAML cases, GPA/SSRB graders, scripted HITL, ORA packet, never NIH ASSIST. |
| **Meta-harness** | Layer *above* those runtimes: one runner + policy server + shareable session. | Not a concept we have. Closest analog is `control_plane.guard` + path A/B/C switch in `runtime.yaml`. |
| **Agent YAML** | Portable spec: executor, tools (MCP / Python / sub-agent), policies ALLOW/DENY/ASK. | `config/runtime.yaml` + checklists. Not an Omnigent spec. |
| **Bench** | `tests/harness_bench`: live probes of *runtime* capabilities (streaming, fork, policy ASK). | `data/harness/cases`: scientific/compliance gold vs weak aims. |

Omnigent does **not** replace LangGraph, ADK, R01 essentials, intake, or Office of Research Aid packaging. It is an optional *outer* session layer.

```text
[optional] Omnigent session  (PI / Navigator copilot)
   YAML agent + policies ALLOW/DENY/ASK
   tools → MCP grant-harness  OR  function: src.harness.runner
        │
        ▼
grant-agent-lab  (domain inner — source of truth)
   knowledge → writer → reviewer → compliance → budget scrutinizer
   → missing essentials → intake → HITL freeze → ORA package
   eval cases + graders live here
```

## What is worth adopting (patterns, not a rewrite)

1. **Policy verdicts ALLOW / DENY / ASK**  
   Map 1:1 onto the lab:
   - DENY: any NIH ASSIST / Grants.gov submit, inventing budget dollars, auto-checking `PI_CERTIFY`.
   - ASK: HITL freeze, office submit, waivers.
   - ALLOW: review, checklist, intake fill, knowledge packs.  
   This is a stricter, event-based version of the AGT control-plane façade already specified in `docs/control-plane-integration.md`.

2. **Custom agent YAML as a Copilot/Claude *driver***  
   A thin `agents/grant-navigator.yaml` that calls lab MCP tools. Lets Copilot, Claude Code, or Codex *drive* the graph without becoming the graph.

3. **Sub-agents with mixed executors (Debby pattern)**  
   Mock study section can fan out: GPA-style reviewer on one model, SSRB contrarian on another, synthesize. Domain graders still decide pass/fail.

4. **Capability-bench *shape***  
   Borrow “probe + expected verdict + DRIFT” for path A vs B vs C (HITL interrupt, tracking-number format, ASSIST blocked). Do **not** import `tests/harness_bench` — it tests Claude/Codex transports, not NIH packets.

5. **ASK as first-class elicitation**  
   Stronger than our current `awaiting_human` flag: policy engine pauses the *tool call*, not just a graph node.

## What not to adopt

- Replacing Part B `GrantGraph` / Part C hybrid with Claude Code sessions.
- Omnigent Desktop / tmux / phone sync as the PI workbench (we already have workbench + CopilotKit; submit path is ORA).
- Databricks-profile auth as default (MCC/OSPA is GCP + Cloud SQL).
- `sandbox: linux_bwrap` as a substitute for institutional RBAC (PI vs Office vs Admin).
- Making Omnigent a required runtime. Python 3.12, Node 22, bubblewrap, vendor CLIs — wrong blast radius for an NIH packet lab.

## Adapter (in this repo)

Optional extra — Omnigent is **not** required to run the lab.

```text
grant-agent-lab/
  agents/grant-navigator.yaml    # Copilot/Omnigent spec; MCP → python3 -m src.harness mcp
  src/harness/policies.py        # DENY ASSIST, ASK freeze/submit, DENY budget invention
  docs/omnigent-adoption.md
```

Policies are also unit-tested without Omnigent installed (`tests/test_harness_policies.py`).

