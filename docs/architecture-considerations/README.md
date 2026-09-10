# Architecture Considerations

Enterprise-architecture notes for the **MCC (Mayo Clinic Cloud Platform) Office of Research Aid Grant Submission Platform** and the **Grant Agent Lab** multi-agent implementation.

This folder holds the written considerations (this document) and the generated **draw.io** diagrams. Open `.drawio` files in [app.diagrams.net](https://app.diagrams.net) or draw.io desktop.

**Assumption used throughout:** operational data already exists in **Cloud SQL** and **BigQuery**.

How to **choose** components (function, CSP, security gates, tokens, TCO): [Architecture component selection framework](architecture-selection-framework.md).

Questions to ask before choosing (function, UX, security, compliance, audit, control plane, governance): [Architecture discovery questions](architecture-discovery-questions.md).

PI-facing product (R01 workbench, intake form, office submit + tracking): [PI R01 workflow UI](pi-r01-workflow-ui.md). Narrative: [intake and office submit](../intake-and-office-submit.md).

Rendered Mermaid: [Architecture (Mermaid)](../architecture.md). **C4 infographics (posters):** [c4-infographics](c4-infographics/README.md). Configure: [how-to-configure](../guides/how-to-configure.md). Launch UI: [how-to-launch-ui](../guides/how-to-launch-ui.md).

---

## Diagrams in this folder

| File | EA use | What it shows |
|------|--------|----------------|
| [c4-infographics/](c4-infographics/README.md) | C4 posters | Infographic system context + L1–L3 triptychs |
| [ea-container-infrastructure.drawio](ea-container-infrastructure.drawio) | Container / infrastructure | Cloud Run FE vs BE, Cloud SQL, BigQuery, stack per container |
| [ea-integration-flows.drawio](ea-integration-flows.drawio) | Integration | Which stage output becomes the next stage input |
| [hybrid-architecture.drawio](hybrid-architecture.drawio) | Agent runtime (recommended) | ADK outer + LangGraph inner |
| [pure-adk-architecture.drawio](pure-adk-architecture.drawio) | Agent runtime path A | Pure Google ADK 2.0 Graph Workflow |
| [pure-langgraph-architecture.drawio](pure-langgraph-architecture.drawio) | Agent runtime path B | Pure LangGraph + checkpointer |
| [mcc-office-of-research-aid-c4-source.jpg](mcc-office-of-research-aid-c4-source.jpg) | Source reference | Original MCC C4 / GCP deployment sketch |
| [pi-r01-workflow-ui.drawio](pi-r01-workflow-ui.drawio) | PI product UX | R01 workbench → intake form → office database → tracking # |
| [mcc-office-of-research-aid-gcp-reference-architecture.drawio](mcc-office-of-research-aid-gcp-reference-architecture.drawio) | Full GCP reference (3 pages) | Deployment view + C4 containers + ADK/LangGraph/MCP orchestration with official draw.io GCP2 icons |

### Color legend (used consistently)

| Color | Meaning |
|-------|---------|
| Blue (`#dae8fc` / `#6c8ebf`) | Front ends, ADK / outer orchestration |
| Green (`#d5e8d4` / `#82b366`) | Back-end agents, LangGraph nodes |
| Yellow (`#fff2cc` / `#d6b656`) | Knowledge / guidelines / edge access |
| Purple (`#e1d5e7` / `#9673a6`) | Shared state and data stores |
| Rose (`#f8cecc` / `#b85450`) | Human-in-the-loop |
| Gray | External systems |

---

## 1. Technology stack for each container

| Container / logical service | Role | Stack |
|----------------------------|------|--------|
| Intake Web App | PI upload, package start | Cloud Run · React/Next (or equivalent) · Apigee + IAP/SSO |
| Reviewer Web App | Office of Research Aid / reviewer UI | Cloud Run · same FE stack · role-gated APIs |
| Navigator App | PI-support guidance | Cloud Run · assistant UI · agent APIs |
| Admin Console | Rules, users, monitoring | Cloud Run · admin UI · config APIs |
| Agent Orchestrator | Route goals across agents | Cloud Run · Google ADK 2.0 · LangGraph · Vertex AI (Gemini) |
| Document Intelligence | OCR, parse, extract | Cloud Run · Document AI |
| Compliance Agent | NIH / FOA / Office of Research Aid rules | Cloud Run · rules engine + LLM · policy YAML / Firestore |
| Budget Scrutinizer | NIH modular / effort norms | Cloud Run · validator only (does not invent budgets) |
| Readiness / Missing-Component | Gap detection, score | Cloud Run · same agent runtime |
| Knowledge Updater | FOA / SF424 / RePORTER refresh | Cloud Run or Scheduler job |
| Submission / Package Creator | Versioned packet + evidence | Cloud Run · writes to GCS + Cloud SQL |
| Shared session / workflow state | Live agent state | Memorystore (Redis) · LangGraph checkpointer |
| Relational metadata | Users, projects, versions | **Cloud SQL** (PostgreSQL) |
| Analytics | Metrics, score trends | **BigQuery** |
| Documents / packages | Binaries and artifacts | Cloud Storage |
| Semantic index | FOA, guidelines, similar grants | Vertex AI Vector Search |
| API edge | Auth, routing, rate limit | Apigee · IAP · institutional SSO |
| Observability | Traces, prompts, audit | Cloud Logging / Trace · Langfuse hooks |
| Control plane | Policy, kill-switch, audit | Thin AGT-style façade around agent/tool calls |

See the **Decision matrix** below for how to choose a path. Recommended diagrams: [hybrid-architecture.drawio](hybrid-architecture.drawio), [pure-adk-architecture.drawio](pure-adk-architecture.drawio), [pure-langgraph-architecture.drawio](pure-langgraph-architecture.drawio).

---

## Decision matrix

### A. Agent runtime path

Use this when choosing **Part A (pure ADK)**, **Part B (pure LangGraph)**, or **Part C (hybrid)**.

| Criterion | Part A — Pure ADK 2.0 | Part B — Pure LangGraph | Part C — Hybrid (recommended) |
|-----------|------------------------|-------------------------|-------------------------------|
| **Choose when** | Institutional GCP / Vertex AI Agent Engine, native IAM and A2A matter most | Maximum control of state, time-travel, and cloud-agnostic loops matter most | Need ADK production surface **and** deterministic revision loops |
| **Orchestration** | ADK Graph / Workflow + `LlmAgent` | `StateGraph` + conditional edges | ADK outer; LangGraph inner |
| **State model** | ADK session state | Typed `ProposalState` + reducers + MemorySaver | Same `ProposalState` as Part B, wrapped by ADK |
| **HITL** | ADK native pause / resume | Graph interrupt + checkpoint resume | LangGraph interrupt; ADK surfaces the human task |
| **Checkpoint / time-travel** | Session replay (platform) | First-class checkpointer | LangGraph checkpointer behind ADK |
| **Deploy / IAM / A2A** | Native | You own it | Native (ADK / Agent Engine) |
| **Observability** | Cloud Logging / Trace | Langfuse + your traces | Both: ADK platform + LangGraph node spans |
| **Control plane (AGT)** | Guard around agent calls | Guard around nodes | Guard at the ADK → graph boundary |
| **Where LangGraph is used** | Not used | Entire workflow | Writer → Reviewer → Compliance → Budget → HITL → Package |
| **Where ADK is used** | Entire workflow | Not used | Portals, IAM, A2A, outer agent identity |
| **Cost / complexity** | Medium (platform-managed) | Medium (you own runtime) | Higher (two runtimes) — justified for production MCC |
| **Lab status** | Scaffold | Working graph + checkpointer | Primary working showcase |

**Default for MCC / Office of Research Aid production:** Part C.

**Default for local science-loop experiments:** Part B.

**Default for Vertex-only pilots with little custom looping:** Part A.

### B. Data store

| Need | Store | Not for |
|------|--------|---------|
| Users, projects, versions, workflow status, package manifests | **Cloud SQL** (shared PostgreSQL) | Session blobs, raw PDFs |
| Live session + LangGraph checkpoints | **Memorystore (Redis)** | Long-term reporting |
| Raw uploads, generated sections, versioned packages | **Cloud Storage** | Structured queries |
| Usage metrics, score trends, audit aggregates | **BigQuery** | OLTP from web apps |
| FOA / guideline / similar-grant retrieval | **Vertex Vector Search** | Authoritative workflow state |
| Rules-as-data (optional) | Firestore or YAML in repo | Large documents |

**Decision:** one shared Cloud SQL instance for all web apps and agents. Do not stand up a Cloud SQL per portal.

### C. Cloud Run placement

| Workload | Place on | Reason |
|----------|----------|--------|
| Intake / Reviewer / Navigator / Admin UI | Cloud Run **front end** | Stateless UI; IAP/SSO at the edge |
| Orchestrator + specialist agents | Cloud Run **back end** | Long agent runs, private VPC to SQL/Redis |
| Knowledge Updater (scheduled) | Cloud Run job + Cloud Scheduler | Periodic, not user-latency-critical |
| Package write + handoff | Cloud Run **back end** (Submission) | Needs GCS + SQL + audit |

**Decision:** never run the agent loop inside a front-end container.

### D. When to use LangGraph inside ADK (hybrid)

| Situation | Use LangGraph inner graph? |
|-----------|----------------------------|
| Multi-step write → review → compliance → HITL with possible loops | **Yes** |
| Need typed reducers (`critiques`, `compliance_issues` accumulate) | **Yes** |
| Need checkpoint resume after PI review | **Yes** |
| Single-shot LLM call (summarize one doc) | No — ADK `LlmAgent` is enough |
| IAM / A2A / portal identity | Stay on ADK outer |
| Budget / package side effects after approval | LangGraph node, still behind `guard()` |

---

## 2. Are some Cloud Runs front ends and some back ends?

**Yes.**

| Kind | Cloud Run services |
|------|---------------------|
| **Front ends (UI)** | Intake Portal, Reviewer Portal, Navigator App, Admin Console |
| **Back ends (API / workers)** | Orchestrator, Document Intelligence, Compliance, Budget Scrutinizer, Readiness, Knowledge Updater, Submission / Package Creator |

Front ends are thin, authenticated UIs. They call back-end Cloud Run services (through Apigee) for agent runs, document processing, and persistence. Long-running agent loops do **not** live in the UI containers.

---

## 3. Persistent Cloud SQL for the web applications?

**Yes — one shared persistent relational store, not one database per UI.**

- **Cloud SQL (PostgreSQL)** holds durable data used by *all* web apps and agents:
  - users / roles (PI, Navigator, Office of Research Aid reviewer, admin)
  - proposals / projects / versions
  - workflow status, HITL decisions, audit pointers
  - rule/version metadata, package manifests
- Web apps are **stateless Cloud Run**; they reach Cloud SQL over private networking (VPC connector).
- **Live session and agent-turn state** belongs in **Memorystore (Redis)** (and LangGraph checkpoints), not only Cloud SQL.
- **BigQuery** is analytics / historical reporting, not OLTP for the live apps.
- Document binaries stay in **Cloud Storage**; Cloud SQL stores metadata and object pointers.

---

## 4. How components are integrated (infrastructure)

```
[PI / RA / Navigator / Office of Research Aid Reviewer]
        │  HTTPS + SSO (IAP / Apigee)
        ▼
┌─────────────────── Front-end Cloud Runs ───────────────────┐
│ Intake │ Reviewer │ Navigator │ Admin                      │
└────────────┬───────────────────────────────────────────────┘
             │ REST (authZ by role)
             ▼
┌─────────────────── API / Orchestration ────────────────────┐
│ Apigee → Agent Orchestrator (ADK + LangGraph)              │
│   control_plane.guard() on every critical call             │
└───┬──────────┬──────────┬──────────┬──────────┬────────────┘
    ▼          ▼          ▼          ▼          ▼
 Doc Intel  Compliance  Budget     Readiness  Submission
             │
             ▼
┌──────── Shared data plane ─────────────────────────────────┐
│ Cloud SQL · Memorystore · Cloud Storage · BigQuery         │
│ Vertex Vector Search · (optional Firestore rules-as-data)  │
└────────────────────────────────────────────────────────────┘
             │
             ▼
    External: NIH RePORTER · Office of Research Aid database · SSO
```

### Output → input chain

| Stage | Output | Becomes input to |
|-------|--------|------------------|
| Intake | Validated files + proposal metadata | Document Intelligence |
| Document Intelligence | Parsed text, sections, entities | Compliance, Missing-Component, Writer / Reviewer |
| Knowledge Updater | Fresh FOA / SF424 / RePORTER snapshot | Writer, Compliance, Budget Scrutinizer |
| Grant Writer | Specific Aims / section drafts | Reviewer |
| Grant Reviewer | Critiques (fatal / major / minor) | Compliance, Writer (revision) |
| Compliance + Budget Scrutinizer | Issues (blocker / warning) | HITL + Readiness |
| HITL (PI / Office of Research Aid) | Approve / revise / certify intake | Writer (loop) or Package Creator |
| Package Creator | Versioned package + intake JSON | Office of Research Aid database |
| Office ingest | Tracking number `ORA-…` | PI record, Cloud SQL, notifications |

Integration mechanisms: HTTPS APIs, Pub/Sub for async jobs, shared Cloud SQL + Memorystore, GCS object paths, and typed **`ProposalState`** as the contract between agents.

See [ea-integration-flows.drawio](ea-integration-flows.drawio) and [ea-container-infrastructure.drawio](ea-container-infrastructure.drawio).

---

## 5. Information flowing between systems (system context)

### Actors → platform

- Research idea, hypothesis, mechanism (R01 / R21 / …), FOA, internal deadline
- Uploaded drafts (Aims, Research Strategy, budget narrative, biosketches, Other Support)
- HITL decisions (approve, revise, override)
- Role identity via SSO (PI, Navigator, Office of Research Aid, Admin)

### Inside the platform

- Parsed document structure and extracted entities
- Critiques, compliance findings, budget validation results
- Readiness score and remediation list
- Workflow stage, iteration count, package version tags
- Audit events (who / what / when; control-plane allow / block)

### Platform → stores

| Store | Information |
|-------|-------------|
| **Cloud SQL** | Users, projects, proposal versions, workflow status, HITL outcomes, package manifests |
| **BigQuery** | Usage metrics, score trends, compliance flag rates, operational analytics |
| **Cloud Storage** | Raw uploads, generated sections, final packages |
| **Memorystore** | Live session and LangGraph checkpoint state |
| **Vector Search** | Embeddings of FOAs, guidelines, successful aims |

### Platform → external

- **NIH RePORTER:** search criteria → abstracts / activity codes / PIs
- **Office of Research Aid database:** completed intake packet; tracking number returned to PI
- **NIH ASSIST / Grants.gov:** **out of this lab** (office process after ingest)
- **Email / notifications:** readiness alerts, HITL requests, office tracking number

### Security / compliance context

- HIPAA / HITRUST-aligned controls (VPC, CMEK, IAM, audit logs).
- Office of Research Aid remains the institutional gate. The platform prepares, scores, and **ingests packets into the office database**. It does not submit to NIH.

See [ea-system-context.drawio](ea-system-context.drawio).

---

## Short answers for an EA packet

1. **Stack per container** — Cloud Run for UIs and agent services; Vertex AI + ADK/LangGraph for orchestration; Cloud SQL + Memorystore + GCS + BigQuery + Vector Search for data; Apigee/IAP for the edge.
2. **Cloud Run split** — Yes: four front-end portals + multiple back-end agent/API services.
3. **Cloud SQL** — Yes: one shared persistent relational store for web apps and backends (not per-app databases).
4. **Integration** — Front ends → Apigee → Orchestrator → specialist agents; shared SQL / Redis / GCS; stage outputs feed the next stage (table above).
5. **Information flow** — Documents, critiques, compliance/budget findings, readiness scores, HITL decisions, packages, and audit events circulate among actors, agents, Cloud SQL / BigQuery / GCS, and external NIH / Office of Research Aid systems.

---

## Related lab documentation

- [Architecture component selection framework](architecture-selection-framework.md)
- [Architecture discovery questions](architecture-discovery-questions.md)
- [End-to-end workflow](../end-to-end-workflow.md)
- [Control plane (AGT-style)](../control-plane-integration.md)
- [Budget Scrutinizer & Package Creator](../budget-and-package-agent.md)
- [Datasets & validation](../datasets-and-validation.md)
- [How to add an agent](../guides/how-to-add-agent.md) (if present)
- [How to use the lab](../guides/how-to-use.md) (if present)

## How to cite

```bibtex
@software{grant_agent_lab_2026,
  title  = {Grant Agent Lab: Multi-Agent System for NIH Grant Proposal Drafting, Review, Compliance, Budget Validation, and Packaging},
  year   = {2026},
  url    = {https://github.com/YPCC/grant-agent-lab}
}
```
