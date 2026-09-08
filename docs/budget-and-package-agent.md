# Budget Scrutinizer & Grant Package Creator

## Budget Scrutinizer (validator — not a planner)

This agent **validates** an existing budget against NIH norms and the grant-proposal-assistant feasibility rules. It does **not** invent line items or dollar amounts.

### NIH norms checked

| Check | Source | Severity |
|-------|--------|----------|
| Budget justification narrative present | NIH Modular/Detailed + skill | blocker |
| Modular ceiling ≤ $250k direct/year | PHS 398 Modular Budget | blocker |
| Modules in $25k increments | PHS 398 Modular Budget | warning |
| PD/PI effort declared and > 0 person-months | NIH Personnel Justification | blocker |
| Budget lines linked to aims (`linked_aim`) | grant-proposal-assistant | warning |
| Scope vs typical mechanism direct-cost range | skill / reviewer practice | major |

Implementation: `src/part_c_hybrid/budget_scrutinizer.py`  
Graph position: after Compliance, before HITL.

### What the skill required

From [grant-proposal-assistant](https://github.com/YPCC/grok-custom-skills/tree/main/skills/grant-proposal-assistant):

- “Budget justification aligned to aims”
- “Scope too ambitious for time/budget” as a common fatal critique

Those are encoded as the aim-linkage and scope-vs-budget checks above.

## Grant Package Creator

Runs only when `final_package_ready=True` (post-HITL approval).

- Writes a versioned directory under `output/packages/<tag>/`
- Records `package_snapshot` on state (path, contents, version_tag, approved_by)
- Version tag: `{proposal_id}-v{aims_version}-i{iteration}-{UTC}`

This is the “push” of the approved packet into a durable, auditable form for institutional submission.

## Graph fragment

```
… → compliance → budget_scrutinizer → HITL → package → END
                                    ↘ (not ready) → writer
```
