# CopilotKit UI — R01 DOCX review showcase

Browser workbench that reviews an NIH R01 Specific Aims **.docx** with Grant Reviewer / Compliance / Budget Scrutinizer findings, a Copilot-style agent rail, and visible RBAC (PI cannot submit).

## Run now (no npm)

```bash
cd grant-agent-lab/ui-copilotkit
python3 serve_workbench.py
```

Open http://127.0.0.1:8765

- Review sample DOCX or upload your own `.docx`
- Download `review-report.docx`
- Switch role to **Office of Research Aid** to enable Submit (still a demo — no eRA login)

## Official CopilotKit React app

Sources are under `app/` (`CopilotKit` provider, `CopilotSidebar`, `useCopilotAction("reviewGrantDocx")`, `useCopilotReadable`).

```bash
cd grant-agent-lab/ui-copilotkit
npm install
npm run dev
```

http://localhost:3000 — set `OPENAI_API_KEY` for free-form chat. Structured DOCX review does not need a model key.

## Sample files

- `../data/samples/r01-aims-draft-for-review.docx` — weak Aims (vague hypothesis, dependent Aim 2)
- `../data/samples/r01-aims-review-report.docx` — agent review report

## What this is / is not

| Yes | No |
|-----|----|
| CopilotKit-pattern rail + optional official `@copilotkit/react-ui` | Embedding inside Microsoft Word |
| Review of `.docx` via `python-docx` | Storing eRA passwords / autonomous NIH submit |
| Role chip: PI / Navigator / Office of Research Aid / Admin | Production SSO |
