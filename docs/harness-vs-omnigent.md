# What the Grant Agent Lab harness is (and is not)

This is the call-out doc for **our harness**. It names the pieces, the invariants, and how that differs from [Omnigent](https://github.com/omnigent-ai/omnigent) — which also uses the word “harness,” for a different job.

Short version:

| | **Grant Agent Lab harness** | **Omnigent (Omni agent) harness** |
|---|---|---|
| Job | Domain **eval cage** for an NIH-style packet | **Meta-harness** around coding-agent runtimes |
| What it wraps | Part B `GrantGraph` (review → checklist → intake → HITL → ORA package) | Claude Code, Codex, Cursor, Copilot CLI, Pi, ACP, custom YAML agents |
| Pass/fail | YAML cases + deterministic graders (GPA / SSRB / freeze / destination) | Runtime probes (streaming, fork, policy ASK, session sync) |
| Destination | Office of Research Aid database only | Whatever the coding agent is allowed to touch |
| Required to run the lab? | Yes (CI gate) | No (optional outer driver) |

They can stack. They must not be swapped.

```text
[optional] Omnigent session     ← meta-harness: Copilot / Claude / Codex + ALLOW/DENY/ASK
        │  tools → MCP  python3 -m src.harness mcp
        ▼
Grant Agent Lab harness         ← domain eval cage (this repo)
        │  run_case / run_pipeline
        ▼
Part B GrantGraph               ← one product pipeline
knowledge → reviewer → missing essentials → intake → HITL → ORA package
        │
        ✕  NIH ASSIST / Grants.gov  (denied)
```

Adapter notes (YAML + policy handlers): [omnigent-adoption.md](omnigent-adoption.md). How to run cases: [harness.md](harness.md).

---

## 1. What we have

The harness is an **in-repo feature**, not a sibling package. Cases invoke the **same** `GrantGraph` as the PI workbench and the MCP plugin. If a case passes and the workbench would freeze a weak Aims page, the cage is broken.

### Pipeline under test

```text
knowledge → reviewer (GPA + SSRB) → missing essentials → ORA intake → HITL freeze → package
```

Every node goes through `control_plane.guard()`:

| Verdict | Examples |
|---------|----------|
| **ALLOW** | review, checklist, fill intake, knowledge packs |
| **ASK** | freeze, office submit, waiver — needs a human (`approve` / `revise` / `waive`) |
| **DENY** | NIH ASSIST, Grants.gov, invent budget dollars, auto-check `PI_CERTIFY` |

### Pieces

| Piece | Where | Role |
|-------|-------|------|
| Cases | `data/harness/cases/*.yaml` | Gold / weak / HITL / incomplete / complete ORA packet |
| Samples | `data/samples/` | Public or synthetic Aims text the cases point at |
| Knowledge packs | `config/checklists/` + `config/policies/` + `data/harness/packs/` | R01 essentials, ORA intake, SF424, GPA four questions, SSRB issue classes, invariants |
| Runner | `src/harness/runner.py` | `run_pipeline` / `run_case` → `GrantGraph.invoke` + scripted `resume` |
| Graders | `src/harness/graders.py` | Compare run vs `expect` + invariants. No LLM required |
| Reviewer | `src/harness/review.py` | Deterministic mock study section |
| Policies | `src/harness/policies.py` | ALLOW / DENY / ASK (Omnigent-compatible handlers, also used by `guard()`) |
| CLI | `python3 -m src.harness …` | `list-cases`, `run-case`, `review`, `checklist`, `intake`, `run`, `mcp` |
| MCP | stdio JSON-RPC | Copilot / Cursor / Claude / optional Omnigent tools |
| Workbench | Harness tab | Same `run-case` as CI |
| CI | `.github/workflows/harness.yml` | Eval-cage pytest on every push/PR |

### Bundled cases

| Case | Must happen |
|------|-------------|
| `weak_aims_vague` | Cannot freeze. Raises SSRB classes (vague hypothesis, aim dependency, missing controls). No office package. |
| `good_aims_auditory` | Cleaner than weak (GPA score, fewer fatal/major). |
| `incomplete_package` | Intake incomplete → cannot submit to office. |
| `complete_ora_packet` | HITL approve + complete intake → tracking `ORA-…`, destination Office of Research Aid, `not: NIH_ASSIST`. |
| `hitl_revise_then_approve` | Script `revise` then `approve`. Graph actually paused. |

A case is a small YAML contract: input text, knowledge packs, HITL script, `expect`, invariants. Example (`weak_aims_vague`):

- `expect.can_freeze: false`
- `expect.nih_submit: false`
- `expect.office_submit: false`
- `invariants`: HITL awaited a human; an audit event was emitted

### Surfaces (same graph)

| Surface | How |
|---------|-----|
| CLI | `PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague` |
| MCP | `PYTHONPATH=. python3 -m src.harness mcp` then Copilot/Cursor/Claude tools `grant_harness_*` |
| Workbench | Harness tab on the Python UI |
| CI | pytest files listed in [harness.md](harness.md) |

MCP tools: `list_cases`, `run_case`, `review_text`, `score_checklist`, `fill_intake`, `run`, `get_knowledge`, `list_packs`. None of them submit to NIH.

### Invariants the cage exists to protect

1. Weak / incomplete packets **do not freeze**.
2. Submit destination is the **Office of Research Aid database**. Tracking numbers look like `ORA-YYYYMMDD-xxxxxx`.
3. **NIH ASSIST / Grants.gov is not a lab actor.** Guard DENYs it even if a human clicks “approve.”
4. **PI_CERTIFY is human-only.** The intake agent may not auto-check it.
5. The harness does **not invent budget dollars**.
6. HITL is real: freeze is ASK until `approve` / `revise` / `waive`.
7. Catalogs are single-source: `config/checklists/r01_essentials.yaml` and `ora_intake.yaml` — not a second copy inside the harness.

---

## 2. What Omnigent’s harness is

[Omnigent](https://github.com/omnigent-ai/omnigent) (Apache-2.0, Databricks OSS) calls itself **the open-source meta-harness for all your AI agents**.

In their vocabulary:

| Word | Meaning |
|------|---------|
| **Harness** | A wrapper around a *coding* runtime: Claude Code, Codex, Cursor, Copilot CLI, Hermes, Pi, ACP, Grok Build, Devin, or a YAML agent. Loop + tools + PTY/session. |
| **Meta-harness** | One layer *above* those runtimes: shared session, policy server, sandbox, phone/desktop/browser sync, multi-agent (Polly / Debby). |
| **Agent YAML** | Portable spec: `executor.harness`, tools (MCP / Python / sub-agent), `policies` returning ALLOW / DENY / ASK. |
| **Bench** | `tests/harness_bench` — live probes of *runtime* capability (stream, fork, ASK elicitation), not scientific gold vs weak Aims. |

It is a session OS for coding agents. It is not an NIH packet grader.

---

## 3. Similarities (patterns we did take)

These are the overlapping ideas. We copied **shapes**, not the product.

| Pattern | In Omnigent | In this lab |
|---------|-------------|-------------|
| ALLOW / DENY / ASK | Policy handlers on tool events | `src/harness/policies.py` **and** `control_plane.guard()` on graph nodes |
| ASK before risky acts | Pause the *tool call* for a human | HITL interrupt before freeze; workbench Submit is the human approval for ORA package |
| Portable agent YAML | `executor` + MCP tools + policies | Optional `agents/grant-navigator.yaml` — Copilot/Omnigent *driver* only |
| MCP as the plug | Tools from any host | `grant_harness_*` stdio server |
| Sub-agents / debate | Debby (Claude + GPT heads) | *Not implemented.* Graders stay deterministic. Dual-model review is a later option |
| Capability bench shape | Probe + expected verdict + DRIFT | YAML `expect` + invariants. We did **not** import `harness_bench` |

So: same **governance vocabulary**, same **MCP plugin idea**, optional **YAML driver**. Different **object under test**.

---

## 4. Differences (do not confuse)

| | Grant lab harness | Omnigent harness |
|---|---|---|
| Object under test | R01 draft + intake + ORA packet | Coding-agent runtime + session |
| Graph | LangGraph / `GrantGraph` (and ADK paths) | Vendor CLI / SDK / ACP |
| Graders | Regex / checklist / destination — CI-stable | Live model + transport probes |
| HITL | Freeze / certify / waive a *proposal* | Approve a *tool call* or spend cap |
| UI | PI workbench + CopilotKit + Harness tab | Desktop, web `:6767`, phone, tmux |
| Auth / cloud | MCC/OSPA: GCP, Cloud SQL, institutional RBAC | Databricks profile, Modal/E2B/… sandboxes |
| Sandbox | Institutional roles (PI vs Office vs Admin) | `bwrap` / seatbelt / Job Object |
| NIH ASSIST | Hard DENY | Not in their world |
| Required runtime | Python 3, pytest | Python 3.12, Node 22, tmux, optional bwrap, vendor CLIs |
| Success | Weak aims fail; complete packet gets `ORA-…` | Session streams, fork works, policy ASK fires |

Omnigent does **not** know Specific Aims, SF424, Missing Essentials, or Office of Research Aid. Our harness does **not** supervise Claude Code worktrees or sync a session to a phone.

---

## 5. How they sit together (optional)

Omnigent (or Copilot, Cursor, Claude Desktop) may **drive** the lab. It must not **become** the lab.

```text
omnigent run agents/grant-navigator.yaml
        → MCP → python3 -m src.harness mcp
        → GrantGraph + graders + guard
```

Rules if someone turns that on:

- Domain source of truth stays here: catalogs, intake, package, cases.
- Policy handlers stay `src.harness.policies` (unit-tested without Omnigent installed).
- A green Omnigent session is not a green NIH packet. Only `run-case` / CI is.
- Desktop / tmux / phone sync is not the PI workbench. Submit path is still ORA.

What we will **not** adopt: replacing Part B with Claude Code sessions; Databricks as default auth; `linux_bwrap` as a stand-in for PI vs Office RBAC; making Omnigent a required dependency.

---

## 6. Pointers

| Want | Doc / path |
|------|------------|
| Run the cage | [harness.md](harness.md) |
| Adopt / ignore list | [omnigent-adoption.md](omnigent-adoption.md) |
| Guard wiring | [control-plane-integration.md](control-plane-integration.md) |
| Graph + HITL | [part-b-langgraph-hitl.md](part-b-langgraph-hitl.md) |
| Omnigent upstream | https://github.com/omnigent-ai/omnigent |
