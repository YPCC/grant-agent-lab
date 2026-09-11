# Control Plane Integration (AGT-style)

We reuse the architectural pattern from [YPCC/agent-control-lab](https://github.com/YPCC/agent-control-lab):

> **Agent execution plane** (what the agents do and in what order)  
> vs  
> **Governance / control plane** (policy, identity, privilege, reliability, audit, observability)

## Mapping to Microsoft AGT Concepts

| AGT Concept          | Status in Grant Agent Lab                          | Mechanism |
|----------------------|----------------------------------------------------|-----------|
| Agent OS / ACS       | Integrated (thin)                                  | Policy checks before tool / critical agent calls |
| Agent Mesh           | Projected                                          | Simple trust tiers + agent identity |
| Agent Runtime        | Partial                                            | Privilege rings + kill-switch flag |
| Agent SRE            | Partial                                            | Circuit-breaker state file |
| Agent Compliance     | Integrated                                         | GO / NO-GO gate + compliance_evidence.json |
| Agent Marketplace    | Projected                                          | Skill / tool fingerprint placeholders |
| Observability        | Integrated                                         | Langfuse spans per agent (optional keys) + audit JSONL |

## How it is wired

1. Every Part B graph node (`knowledge`, `review`, `checklist`, `intake`, `freeze`, `submit_office`) goes through `control_plane.guard()`.
2. The façade performs:
   - Kill-switch check
   - Policy evaluation from `src.harness.policies` — **DENY** NIH ASSIST / invented budget / auto-certify; **ASK** freeze / office submit / waiver unless `human_approved=True`
   - Audit event emission (`output/audit_log.jsonl`)
   - A Langfuse span per agent when `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` are set ([observability.md](observability.md))
3. HITL decisions are first-class (`GrantGraph.resume`); the workbench Submit button is the human approval for ORA packaging.
4. Harness cases and the workbench call the same graph. There is no parallel toy runner.

See `src/control_plane/` for the concrete implementation.
