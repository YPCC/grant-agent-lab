---
name: grant-agent-harness
description: Evaluate NIH-style grant drafts with the in-lab Grant Agent Harness. Never submit to NIH ASSIST.
---

# Grant Agent Harness (in grant-agent-lab)

```bash
PYTHONPATH=. python3 -m src.harness review --file aims.txt
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 -m src.harness mcp
```

Invariants: Office of Research Aid only; no invented budget dollars; HITL before freeze; PI_CERTIFY is human-only.
