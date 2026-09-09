# Demo: end-to-end workbench

Recorded walkthrough of the Grant Agent Lab UI (Python workbench on port 8765).

## Video

[e2e-workbench-demo.mp4](e2e-workbench-demo.mp4) — 43s, 1440×900, H.264.

What the recording shows:

1. Landing workbench (role **PI**)
2. Auto / **Review sample DOCX** — Specific Aims extract
3. Readiness score + reviewer / compliance findings
4. **Missing Essentials** checklist
5. Copilot-style rail (“Review this grant DOCX”)
6. **HITL: revise** then **HITL: approve freeze**
7. PI **Submit to NIH** stays disabled
8. Switch role to **Office of Research Aid** — Submit enables (demo only, no eRA login)

## Stills

| Step | File |
|------|------|
| After review | [still-review.png](still-review.png) |
| Checklist | [still-checklist.png](still-checklist.png) |
| Office of Research Aid RBAC | [still-office-of-research-aid-rbac.png](still-office-of-research-aid-rbac.png) |

## Re-run locally

```bash
cd grant-agent-lab
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py
# other terminal
python3 ui-copilotkit/serve_workbench.py   # then open http://127.0.0.1:8765
```

How to launch: [../guides/how-to-launch-ui.md](../guides/how-to-launch-ui.md).
