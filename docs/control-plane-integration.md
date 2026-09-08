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
| Observability        | Integrated                                         | Langfuse + structured logging + Cloud Trace hooks |

## How it is wired

1. Every call from the Orchestrator into the LangGraph graph (or ADK sub-agent) goes through a thin `control_plane.guard()` façade.
2. The façade performs:
   - Identity / trust tier check
   - Kill-switch / ring check
   - Optional policy evaluation (LiteGovernor-style or simple rule list)
   - Audit event emission
3. HITL decisions are also recorded as first-class audit events.
4. Final institutional package contains a compliance evidence bundle.

See `src/control_plane/` for the concrete implementation.
