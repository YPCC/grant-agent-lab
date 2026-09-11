# Packaging and deployment

How individuals install this, how it compares to a Grok skill / plugin / `npx` MCP, and how to run it as a centralized Cloud Run service.

**The product is the governed graph** (Part B `GrantGraph` + `guard()` + ORA packet). Everything else is a *driver* or a *host*.

```text
Grok skill / Copilot plugin / npx MCP     ← installable driver (thin)
        │  stdio MCP or HTTP
        ▼
Grant Agent Lab  (catalogs + graph + policies + eval cage)
        │
        ├── local: pipx / desktop workbench
        └── institutional: Cloud Run FE + Cloud Run agents
                    │
                    ▼
         Office of Research Aid database   ✕ NIH ASSIST
```

## Four shapes (pick by audience)

| Shape | Who | What they install | Agent runs where | Use when |
|-------|-----|-------------------|------------------|----------|
| **1. Grok / Copilot / Claude plugin** | PI who already lives in Grok, Copilot, Cursor | Skill + MCP config | Their machine (stdio) or your Cloud Run URL | “Teach my assistant the ORA rules” |
| **2. CLI / pipx (the `npx` analog)** | Developers, Navigators | `pipx install grant-agent-lab` → `grant-harness` | Local process | Scripted review, eval cage, MCP |
| **3. Workbench PWA / desktop** | PI who wants the Review + Intake UI | Browser bookmark or thin desktop wrapper | Local or Cloud Run | Demo and office intake |
| **4. Cloud Run (central)** | Institution | Nothing — SSO URL | Your VPC | Production governance, audit, SSO |

Do **not** ship the LangGraph, Cloud SQL, and production profile inside a SKILL.md. A Grok skill is a *prompt + tool handle*. This lab is a *system*.

Same split as [Omnigent](omnigent-adoption.md): outer driver vs inner graph.

## 1. Like a Grok agent / plugin (yes, as a driver)

Grok Skills (`SKILL.md`) and Grok Build plugins (skills + MCP + hooks) are how xAI ships *reusable instructions and tools*. [YPCC/grok-custom-skills](https://github.com/YPCC/grok-custom-skills) already has GPA / SSRB skills this lab cites.

What to ship for Grok / Copilot / Claude:

| File | Role |
|------|------|
| [`skills/grant-agent-harness/SKILL.md`](../skills/grant-agent-harness/SKILL.md) | When to call the harness; ORA-only invariant |
| [`plugin/vscode/mcp.json`](../plugin/vscode/mcp.json) | stdio: `python3 -m src.harness mcp` |
| [`plugin/grok/.mcp.json`](../plugin/grok/.mcp.json) | Same MCP for Grok Build / Grok Desktop |
| `agents/grant-navigator.yaml` | Optional Omnigent/Copilot driver |

Install for an individual (local graph):

```bash
pipx install 'grant-agent-lab @ git+https://github.com/YPCC/grant-agent-lab.git'
grant-harness mcp          # stdio for Grok / Copilot / Cursor / Claude
grant-harness preflight
```

Grok Build then points MCP at that command (or at `npx` only if we later publish a Node shim). There is **no official `npx @ypcc/grant-agent` today** — Python is the runtime. Closest npm pattern:

```json
{ "command": "grant-harness", "args": ["mcp"] }
```

or, if we add a tiny Node wrapper later:

```json
{ "command": "npx", "args": ["-y", "@ypcc/grant-harness-mcp"] }
```

The wrapper would still **exec the Python graph**. Do not rewrite Part B in Node to chase NPX.

**Mobile Grok (iOS/Android skills):** the *skill text* can travel with the user. The *graph* cannot — no Cloud SQL, no HITL freeze, no production audit on a phone. Mobile should call the **Cloud Run HTTP API** (`review`, `intake`, `approve freeze`), not embed LangGraph.

## 2. Desktop / mobile apps

| Option | Verdict |
|--------|---------|
| **PWA of the workbench** | Yes. Same UI, installable on laptop. Easiest “desktop app.” |
| **Electron / Tauri wrapping :8080** | Only if air-gapped laptops cannot use a browser against Cloud Run. Extra updater + secret-store work. |
| **Native iOS/Android agent** | No. Long graphs, DOCX, HITL, identity, and DENY-ASSIST do not belong in an app-store binary. |
| **Native mobile companion** | Yes, later: status, push “PI certify?”, open tracking `ORA-…`. Backend remains Cloud Run. |

HITL freeze is a **paused server-side thread**, not a local notification in a store app. Production profile ([governance.md](governance.md)) wants `GRANT_ACTOR` / `GRANT_ROLE` from SSO, not a device keychain full of eRA secrets (forbidden).

## 3. Cloud Run — centralized FE + agents

This is the institutional product. It matches [architecture-considerations](architecture-considerations/README.md) §C: **never run the agent loop inside a front-end container.**

```text
PI browser  ──IAP/SSO──►  Cloud Run FE (workbench / CopilotKit)
                              │ HTTPS
                              ▼
                         Apigee / IAP
                              │
                              ▼
                    Cloud Run BE  (GrantGraph + guard)
                         │        │         │
                    Cloud SQL   GCS    Memorystore
                         │        │         │
                    audit + Langfuse     packages
                              │
                              ▼
                 Office of Research Aid database
```

### What to split

| Service | Image | Timeout / CPU | Notes |
|---------|-------|---------------|--------|
| **FE** | Nginx/Next or `serve_workbench.py` | 15–30s, scale to zero OK | Stateless. No `guard()`, no freeze. |
| **BE orchestrator** | Python Part B (+ ADK if hybrid) | **3600s max**, CPU always allocated | One request = `invoke` *or* `resume`, not the whole PI day. |
| **Jobs** | Same BE image | Cloud Run Job | Eval cage, static red-team, knowledge refresh |

HITL: `invoke` returns `awaiting_human` and **ends the request**. Checkpoint `thread_id` in Memorystore or SQL. `resume` is a **new** request. Do not hold an HTTP socket for hours.

### Production profile is mandatory on BE

```bash
GRANT_PROFILE=production
GRANT_ACTOR=   # from IAP / SSO email
GRANT_ROLE=    # PI | Navigator | Office of Research Aid | Admin
LANGFUSE_*     # Secret Manager
GRANT_AUDIT_LOG=  # or Cloud Logging sink; fail-closed
```

Workbench and `GrantGraph.invoke` already call `assert_runtime_ready()`. On Cloud Run, missing identity or Langfuse **must 503**, not fall back to local.

### Considerations that actually bite

1. **Timeout vs graph.** Review+intake is seconds; DeepTeam `--live` is minutes and stays a Job, not a user request. Static red-team is a **release Job**, not per-click.
2. **Checkpoints.** In-process `GrantGraph.threads` dies when the instance scales to zero. Production needs Redis or SQL checkpointer (`thread_id` is the HITL handle).
3. **CPU allocation.** LangGraph on Cloud Run needs `--cpu-boost` / CPU always on *during the request*, or the freeze/resume path stalls.
4. **Min instances.** FE can scale to zero. Office-hours BE often wants `minScale=1` or a queue (Pub/Sub → Run) so the first PI of the day is not a cold Python import.
5. **Identity.** IAP at the edge → BE reads authenticated user; map to `GRANT_ACTOR`/`GRANT_ROLE`. Do not accept role from the JSON body.
6. **Secrets.** Secret Manager + Workload Identity. No eRA passwords in the process ([governance.md](governance.md)). Langfuse keys as secrets, not env in the Dockerfile.
7. **Data plane.** Packages → GCS; metadata → Cloud SQL; traces → Langfuse (BAA or self-host in VPC); audit JSONL → Cloud Logging + retained bucket. VPC connector + private SQL.
8. **NIH / PHI adjacent.** Treat Aims drafts as sensitive. VPC-SC, CMEK, no copy to a personal Grok skill transcript by default. MCP against Cloud Run should be OAuth, not a long-lived PAT in `mcp.json`.
9. **Control plane.** Kill-switch is a BE flag (Firestore/SQL), not a local global. DENY NIH ASSIST stays in-process policy — Cloud Run does not get an ASSIST connector.
10. **Eval gates.** Cloud Build / GitHub Actions: existing `eval-cage` + `production-preflight`. Promote an image only if both are green. `preflight --gates` as a Cloud Run Job on a schedule.
11. **One region, one SQL.** Do not stand up a Cloud SQL per portal. FE and BE share it.
12. **Do not** put Vertex + LangGraph + workbench in one fat container “to keep it simple.” You will not be able to scale UI separately from 60-minute agent jobs.

### Suggested first Cloud Run slice

Not the full MCC diagram. A **lab-to-prod** slice:

1. Containerize Part B + workbench static assets + `grant-harness`.
2. Two services: `grant-fe`, `grant-be`.
3. SQL for proposals + HITL threads; GCS for packages.
4. IAP on both; BE production profile.
5. MCP remote: `grant-harness` HTTP (when added) or keep stdio only for local.

Grok/Copilot at the institution then point MCP **at the BE URL**, not at `python3` on the laptop. That is the production version of “install it like a Grok agent”: the skill stays small; the graph is central; audit and DENY-ASSIST are one place.

## What not to do

- Publish the whole lab as an npm package and hope NPX runs NIH policy.
- Ship a mobile app that “submits the grant.”
- Run HITL freeze inside a 60-second Cloud Run FE.
- Let a Grok skill bypass `guard()` or set `GRANT_PROFILE=local` in production.
- Store eRA Commons passwords next to Langfuse keys.

## See also

[Governance](governance.md) · [Cloud Run placement](architecture-considerations/README.md) · [How to launch UI](guides/how-to-launch-ui.md) · [MCP harness](harness.md)
