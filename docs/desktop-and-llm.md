# Desktop app and configurable LLM

**Walkthrough (clicks, MCP, Python embed):** [How to use the desktop app and the embedded agent](guides/how-to-use-desktop-and-embedded-agent.md).

Run the same GrantGraph in a **desktop window**, with Vertex AI Gemini (or Gemini API / OpenAI / xAI) as an **optional narrative backend**. Deterministic GPA/SSRB graders and the freeze checklist do **not** depend on the LLM.

```bash
pip install -e ".[desktop,vertex]"
# Vertex (recommended in-tenant)
export GOOGLE_CLOUD_PROJECT=your-gcp-project
gcloud auth application-default login
export GRANT_LLM_PROVIDER=vertex
export GRANT_LLM_MODEL=gemini-2.5-flash

python -m src.desktop
# or
grant-harness desktop
```

Without pywebview, the launcher opens the system browser on a loopback port.

## Providers

| `llm.provider` | Auth | Typical model |
|----------------|------|----------------|
| `none` (default) | — | Graders only. CI / eval cage. |
| `vertex` | ADC / `GOOGLE_APPLICATION_CREDENTIALS` + `GOOGLE_CLOUD_PROJECT` | `gemini-2.5-flash` |
| `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `gemini-2.5-flash` |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `xai` | `XAI_API_KEY` | `grok-3` |

YAML in [`config/runtime.yaml`](../config/runtime.yaml):

```yaml
llm:
  provider: vertex
  model: gemini-2.5-flash
  project: my-gcp-project
  location: us-central1
  enrich_review: true
```

Env wins: `GRANT_LLM_PROVIDER`, `GRANT_LLM_MODEL`, `VERTEX_PROJECT`, `VERTEX_LOCATION`.

The workbench **Settings** tab writes `output/desktop-settings.json` (gitignored). Keys never go in that file.

## What the LLM is allowed to do

- After the deterministic reviewer, `review_llm` may add a short narrative (`review.llm.text`).
- It **must not** invent budget dollars or tell the PI to file NIH ASSIST (prompt + `guard()`).
- `can_freeze` still comes from `r01_essentials.yaml`. Weak aims still fail the eval cage with `provider: none`.

## Vertex notes

- Prefer Vertex over the public Gemini API for institutional drafts (VPC, CMEK, no consumer key).
- Region: `us-central1` unless your org mandates another.
- The desktop app talks to Vertex **from the laptop** using ADC. For Cloud Run, set the same `llm:` block on the BE and use the service account (see [packaging-and-deploy.md](packaging-and-deploy.md)).

## Package as a desktop binary (later)

`pip install -e ".[desktop]"` + pywebview is the supported path. PyInstaller / Tauri can wrap `python -m src.desktop` if you need an `.app` / `.exe`; not required to use the lab.
