# CopilotKit UI — R01 review + Office of Research Aid intake

Browser workbench that reviews an NIH R01 Specific Aims **.docx**, fills a grouped **intake form**, and lets the PI **submit the packet to the Office of Research Aid database**. A tracking number comes back. This is **not** an NIH submit.

## Run now (no npm)

```bash
cd grant-agent-lab
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py
```

Open http://127.0.0.1:8765

- Review sample DOCX or upload your own `.docx`
- Inspect agent-filled intake (Compliance / Formatting / Institutional)
- Override remaining unknowns, check **PI certify**
- **Submit to Office of Research Aid** → tracking number on the PI record

## Official CopilotKit React app

Sources under `app/` (`CopilotSidebar`, `useCopilotAction("reviewGrantDocx")`, `submitToOfficeOfResearchAid`).

```bash
cd grant-agent-lab/ui-copilotkit
npm install --legacy-peer-deps
npm run dev
```

http://localhost:3000 — `OPENAI_API_KEY` only for free-form chat.

## Sample files

- `../data/samples/r01-aims-draft-for-review.docx` — weak Aims
- `../data/samples/r01-aims-review-report.docx` — agent review report

## What this is / is not

| Yes | No |
|-----|----|
| CopilotKit rail + intake form + office tracking # | Embedding inside Microsoft Word |
| Submit to Office of Research Aid database | Storing eRA passwords / NIH ASSIST submit |
