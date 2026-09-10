# How to launch the UI

Two UIs exist. Start with the Python workbench — it needs **no npm and no model key**.

## Option A — Workbench (recommended demo)

Reviews a grant `.docx`, shows Missing Essentials, Copilot-style chat rail, and RBAC.

```bash
cd grant-agent-lab
pip install python-docx
python3 ui-copilotkit/serve_workbench.py
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080).

Recorded walkthroughs:

- CopilotKit Next.js: [docs/demo/e2e-copilotkit-demo.mp4](../demo/e2e-copilotkit-demo.mp4) (32s)
- Python workbench: [docs/demo/e2e-workbench-demo.mp4](../demo/e2e-workbench-demo.mp4) (43s)

Notes: [demo README](../demo/README.md).  
Re-record: [how to create demo files](how-to-create-demo-files.md).

| Action | What happens |
|--------|----------------|
| Review sample DOCX | Loads `data/samples/r01-aims-draft-for-review.docx`, runs reviewer + intake agent |
| Upload `.docx` | Same pipeline on your file |
| Intake form | Grouped Compliance / Formatting / Institutional; agent-filled, human override |
| Submit to Office of Research Aid | Enabled when required intake items are answered; packaging agent uploads; tracking number returns |
| HITL: revise / approve freeze | Resumes Part B graph (`GrantGraph.resume`) |
| Harness tab | Runs `data/harness/cases` on the same graph |
| Role chip | PI, Navigator, Office of Research Aid, Admin — PI **can** submit to the office database |

The workbench calls **one pipeline**:

- `src/part_b_langgraph/graph.py` — knowledge → reviewer → checklist → intake → HITL
- `src/control_plane/guard.py` — ALLOW / DENY / ASK
- `src/shared/docx_text.py` — extract `.docx` text


## Option B — CopilotKit React (Next.js)

Official [`CopilotSidebar`](https://docs.copilotkit.ai), `useCopilotAction("reviewGrantDocx")`, document context via `useCopilotReadable`.

```bash
cd grant-agent-lab/ui-copilotkit
npm install --legacy-peer-deps
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Set `OPENAI_API_KEY` only if you want free-form chat. Structured DOCX review still uses `/api/review` and does not need a model.

This UI does **not** embed inside Microsoft Word. It reviews `.docx` files and produces a report `.docx`.

## Headless (no UI)

```bash
cd grant-agent-lab
PYTHONPATH=. python -m pytest tests/test_checklist.py -q
```

Part B graph (when `langgraph` is installed, uses MemorySaver; otherwise `GrantGraph`):

```python
from src.part_b_langgraph.graph import build_graph
g = build_graph()
s = g.invoke({"text": open("data/samples/weak_aims_vague.txt").read()},
             {"configurable": {"thread_id": "demo"}})
# s["hitl"]["status"] == "awaiting_human"
s = g.resume("demo", "revise")
```

## What you should see

1. Weak sample Aims → many **missing** checklist rows (hypothesis, DMS, PI effort, …).
2. **Submit** disabled while role is PI.
3. HITL message after Approve / Revise.

Full product spec: [PI R01 workflow UI](../architecture-considerations/pi-r01-workflow-ui.md).  
Architecture (Mermaid): [architecture.md](../architecture.md).
