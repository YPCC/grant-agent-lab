# Demos

## 1. CopilotKit Next.js UI (port 3000)

[e2e-copilotkit-demo.mp4](e2e-copilotkit-demo.mp4) — 32s, 1440×900, H.264.

Official `@copilotkit/react-ui` **CopilotSidebar** on the grant workbench.

1. CopilotKit workbench (role **PI**)
2. **Review sample DOCX** — Specific Aims extract + findings rail
3. CopilotSidebar (“Type a message…”)
4. PI **Submit to NIH** stays disabled
5. Switch role to **Office of Research Aid** — Submit enables (demo, no eRA login)

Stills: [still-copilotkit-review.png](still-copilotkit-review.png) · [still-copilotkit-ora.png](still-copilotkit-ora.png)

```bash
cd grant-agent-lab/ui-copilotkit
npm install --legacy-peer-deps
npm run dev
# http://localhost:3000
```

## 2. Python workbench (port 8765)

[e2e-workbench-demo.mp4](e2e-workbench-demo.mp4) — 43s, 1440×900, H.264.

No npm. HITL revise/approve + Missing Essentials checklist.

```bash
cd grant-agent-lab
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py
# http://127.0.0.1:8765
```

How to launch: [../guides/how-to-launch-ui.md](../guides/how-to-launch-ui.md).  
How to **re-record** these files: [../guides/how-to-create-demo-files.md](../guides/how-to-create-demo-files.md).
