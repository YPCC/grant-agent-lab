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

Runs when the **Office of Research Aid intake form** is complete (`can_submit_to_office=True`).

- Writes `output/packages/<ORA-tracking>/` (`MANIFEST.json`, `intake-form.json`, findings, excerpt)
- Registers the packet in the **office database** (demo)
- Returns a **tracking number** (`ORA-YYYYMMDD-xxxxxx`) to the PI

This is **not** an NIH ASSIST / Grants.gov submit.

Implementation: `src/shared/packaging.py` · intake catalog: `config/checklists/ora_intake.yaml`.

## Graph fragment

```
… → compliance → budget_scrutinizer → HITL → package → END
                                    ↘ (not ready) → writer
```
