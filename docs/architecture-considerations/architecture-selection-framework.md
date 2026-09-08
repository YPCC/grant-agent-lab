# Architecture Component Selection Framework

A reusable way to **choose** (and later **re-choose**) components for this multi-agent grant platform: functionality, cloud CSP and services, security and compliance, and cost (infra, tokens, maintenance).

Use this **before** locking a vendor or runtime, and again at each major increment (pilot → limited production → enterprise).

**Context for scoring:** MCC / GCP, OSPA-mediated NIH (and related) proposals, human-in-the-loop, HIPAA/HITRUST-aligned controls. Operational data already lives in **Cloud SQL** and **BigQuery**.

---

## 1. How to use the framework

Work **top-down**. Do not pick a model or a database first. Ask the [discovery questions](architecture-discovery-questions.md) first; treat unanswered gate questions as blockers.

```
1. Lock non-negotiables (compliance, residency, institutional gate)
2. Map capabilities to components (what must exist)
3. Score candidate components (same rubric every time)
4. Estimate TCO (infra + tokens + people + lock-in)
5. Record the decision + review date
6. Re-score when volume, FOA rules, or CSP contracts change
```

**Rule:** a component that fails a **gate** (section 3) is out, even if it is cheaper or more capable.

---

## 2. Capability map (functionality first)

Every selected component must serve at least one capability. If it serves none, it is not in the architecture.

| Capability ID | Capability | Must exist | Typical component class |
|---------------|------------|------------|-------------------------|
| C1 | Identity & access (PI, Navigator, OSPA, Admin) | Yes | SSO + IAP + IAM |
| C2 | Intake / portals | Yes | Cloud Run front ends |
| C3 | Deterministic multi-step agent workflow | Yes | Orchestrator (ADK and/or LangGraph) |
| C4 | Document parse / extract | Yes | Document AI + parser service |
| C5 | Scientific draft / critique | Yes | LLM + skill prompts + Reviewer agent |
| C6 | Compliance & budget validation | Yes | Rules engine + validator agents |
| C7 | Knowledge freshness (FOA, RePORTER) | Yes | Scheduler + API client + index |
| C8 | HITL approve / revise | Yes | Graph interrupt + UI task |
| C9 | Versioned package + evidence | Yes | GCS + Package Creator |
| C10 | Durable metadata | Yes | Cloud SQL |
| C11 | Live session / checkpoints | Yes | Memorystore + checkpointer |
| C12 | Analytics | Yes | BigQuery |
| C13 | Retrieval over guidelines / similar grants | Should | Vector Search |
| C14 | Control plane (policy, kill-switch, audit) | Yes | AGT-style guard + audit log |
| C15 | Institutional handoff (MIRIS / OSPA) | Yes | Connector + no bypass of OSPA |
| C16 | Observability / eval | Yes | Cloud Trace + prompt traces |

If two products cover the same capability, keep **one** primary and mark the other as fallback.

---

## 3. Gates (security & compliance) — pass / fail

Score these **before** cost. Any **Fail** disqualifies the option for production.

| Gate | Question | Pass looks like | Fail looks like |
|------|----------|-----------------|-----------------|
| G1 Data classification | Can this component hold the data class we will put in it? | Research-admin data only in approved stores; no PHI in logs/prompts unless BAA + DLP | Proposal text or personnel data in an unapproved SaaS |
| G2 BAA / HITRUST | Is there a BAA (or equivalent) and HITRUST-aligned path on this CSP? | GCP org with CMEK, VPC-SC, Access Approval available | Consumer API key in a laptop process talking to a public model |
| G3 Residency | Can data stay in the approved region / org? | Region pinned; no silent cross-region training use | Vendor trains on tenant prompts |
| G4 Identity | Does it honor institutional SSO and least privilege? | IAP + IAM roles mapped to PI / Navigator / OSPA / Admin | Shared service account for all portals |
| G5 Audit | Can we prove who did what, including HITL overrides? | Immutable audit log; control-plane events on every agent/tool call | LLM output with no trace of rule or user |
| G6 Secrets | Are keys only in Secret Manager / workload identity? | No long-lived keys in code or Cloud Run env files | API keys in repo or chat logs |
| G7 Egress | Is outbound access to NIH / eRA explicitly allow-listed? | Restricted egress; RePORTER and ASSIST as named endpoints | Open internet from agent runtime |
| G8 Human authority | Can the system submit **without** OSPA when policy forbids it? | Submission Agent only hands off to OSPA unless policy allows | Agent posts directly to Grants.gov in prod |
| G9 Prompt / log hygiene | Are prompts, traces, and eval sets free of secrets and unnecessary PII? | DLP on logs; redaction; retention limits | Full proposal text in a third-party observability cloud with no BAA |
| G10 Model use policy | Is the model endpoint approved for this data class? | Vertex in-tenant / approved model garden | Shadow IT model with unknown retention |

**OSPA-specific gate:** the platform may **prepare and score** a package; it may not become the official submitting office.

---

## 4. Scoring rubric (same 1–5 scale for every option)

Score only options that passed the gates.

| Dimension | Weight (default) | 1 | 3 | 5 |
|-----------|------------------|---|---|---|
| **Functional fit** | 25% | Partial capability; heavy custom code | Covers the capability with known gaps | Native fit; maps cleanly to C1–C16 |
| **CSP alignment** | 15% | Multi-cloud glue or unsupported on MCC | Works on GCP with extra ops | First-class GCP / MCC service |
| **Security & compliance depth** | 20% | Meets gates only | Gates + encryption, IAM, audit baked in | Gates + CMEK, VPC-SC, DLP, Access Approval ready |
| **Operability / maintenance** | 15% | Team owns patches, HA, upgrades | Shared ops with runbooks | Platform-managed; on-call is thin |
| **Cost (12–24 mo TCO)** | 15% | High or unpredictable | Acceptable and forecastable | Lowest credible TCO at expected volume |
| **Lock-in / exit** | 10% | Proprietary state you cannot export | Exportable with work | State in SQL/GCS/`ProposalState` you already own |

**Weighted score** = Σ (score × weight). Record the rater, date, and assumed volume.

Suggested bar: **≥ 3.5** to adopt; **3.0–3.4** pilot only; **< 3.0** reject or defer.

---

## 5. CSP and associated services (GCP / MCC default)

MCC is a **GCP** platform. Prefer native services unless a gate or score says otherwise.

| Capability | Default service | Credible alternative | When to pick the alternative |
|------------|-----------------|----------------------|------------------------------|
| Compute (UI + agents) | Cloud Run | GKE | You need sidecars, sticky long-lived workers, or custom mesh beyond Run |
| Orchestration surface | Vertex AI Agent Engine + ADK | Self-hosted LangGraph on Run | Pure science-loop experiments (Part B) |
| Deterministic loops | LangGraph on Cloud Run | ADK Workflow only | Loops are trivial (Part A pilot) |
| LLM | Vertex Gemini (in-tenant) | Other Vertex Model Garden models | Quality eval wins **and** G2/G3/G10 still pass |
| OCR / layout | Document AI | Custom parse only | Document AI quality fails on NIH PDFs |
| OLTP | **Cloud SQL PostgreSQL** (already present) | AlloyDB | High concurrency / analytical HTAP you cannot get from SQL + BQ split |
| Analytics | **BigQuery** (already present) | Looker on BQ | Never replace BQ for warehouse |
| Session / checkpoints | Memorystore Redis | SQL-backed checkpointer only | Volume is tiny and Redis cost dominates |
| Files | Cloud Storage | — | Do not store packages only in SQL |
| Retrieval | Vertex Vector Search | BQ vector | Small corpus, simpler ops |
| API edge | Apigee + IAP | Cloud Endpoints / Load Balancer + IAP | No partner/API product needs |
| Secrets | Secret Manager + Workload Identity | — | — |
| Async | Pub/Sub + Cloud Scheduler | Cloud Workflows | Simple cron only |
| Observability | Cloud Logging / Trace + approved prompt store | Langfuse **only if** G2/G9 pass | Self-host Langfuse in VPC if SaaS BAA is missing |
| DLP / CMEK / VPC-SC | Cloud DLP, Cloud KMS, VPC Service Controls | — | Required as volume and sensitivity grow |

**Multi-cloud rule:** do not add a second CSP for the agent runtime unless a gate fails on GCP. Extra CSPs multiply identity, audit, and token paths.

---

## 6. Runtime selection (ties back to the decision matrix)

| Option | Functional strength | CSP fit | Security posture | Maintenance | Cost shape |
|--------|---------------------|---------|------------------|-------------|------------|
| **Part A Pure ADK** | Good agents; weaker custom loops | Best | Best IAM / A2A | Low–medium | Platform + tokens |
| **Part B Pure LangGraph** | Best loops / checkpoints | Neutral | You must wrap guard() + IAM | Medium | Compute + tokens; less platform tax |
| **Part C Hybrid** | Best overall fit for this product | High | ADK identity + graph control | Higher (two runtimes) | Platform + compute + tokens |

**Framework outcome (current):** Part C unless a pilot is explicitly Vertex-only (A) or lab-only (B). Re-score if ADK Workflow gains native looping/checkpointers equivalent to LangGraph.

---

## 7. Cost model (do not score on list price alone)

Estimate **annual TCO** as four buckets. Recompute when proposal volume or tokens per package change.

### 7.1 Formula

```
TCO ≈ Infra + Tokens + People + Risk
```

| Bucket | What to include | Drivers |
|--------|-----------------|---------|
| **Infra** | Cloud Run CPU/RAM/requests, Cloud SQL, Memorystore, GCS, BigQuery scans, Vector Search, Apigee, Document AI pages, networking, CMEK | Concurrent users, package size, retention |
| **Tokens** | Input + output tokens × model price × retries × eval runs × HITL re-runs | Aims vs full Research Strategy; reviewer + compliance extra passes |
| **People** | Platform on-call, prompt/rule maintenance, FOA/skill updates, OSPA liaison, eval set curation | Number of mechanisms (R01/R21/K) and institutes supported |
| **Risk / lock-in** | Exit cost, dual-run during cutover, audit findings, idle reserved capacity | Proprietary agent state; single-model dependency |

### 7.2 Token cost (usually the swing factor)

Treat tokens as a **product metric**, not an afterthought.

| Lever | Effect | Selection implication |
|-------|--------|------------------------|
| Draft full Research Strategy every loop | Tokens explode | Cache sections; only rewrite changed aims |
| Mock study section + compliance + budget each iteration | 3–6× a single draft call | Route cheap/small models to extraction; reserve frontier models for critique |
| Eval harness on every PR | Continuous token burn | Sample evals; nightly full suite |
| Long context (FOA + prior aims + RePORTER dumps) | Input tokens dominate | RAG (Vector Search) over stuffing |
| HITL “try again” | Unbounded | Cap iterations; show cost-to-date in the UI |
| Logging full prompts to a vendor | Tokens + compliance risk | Log hashes + short spans unless G9 passes |

**Worked planning sketch (replace with your rates):**

```
tokens_per_package ≈
    parse/extract
  + writer (aims + optional sections)
  + reviewer
  + compliance/budget (mostly rules; small LLM)
  + readiness narrative
  × expected_iterations (HITL)

monthly_token_$ ≈ packages_per_month × tokens_per_package × $ / 1M tokens
```

Use **two model tiers** in the architecture so the selection is not “one model for everything”:

| Tier | Jobs | Cost posture |
|------|------|----------------|
| Tier 1 (frontier, Vertex Gemini high tier) | Aims quality, reviewer critique, readiness explanation | Higher $/1M; cap concurrency |
| Tier 2 (smaller / flash-class) | Classification, extraction, rubric checks, routing | Default for volume |

Budget Scrutinizer and most SF424 checks should stay **rules-first** (cheap, deterministic). Do not spend frontier tokens to re-derive “modular ≤ $250k.”

### 7.3 Infrastructure cost (relative)

| Service | Cost behavior | Control |
|---------|---------------|---------|
| Cloud Run FE | Low if scale-to-zero | Min instances only for reviewer SLA |
| Cloud Run agents | Grows with concurrent graphs | Queue + max instances; no FE min instances on agents |
| Cloud SQL | Steady + storage | Shared instance; right-size vCPU; PITR window |
| Memorystore | Steady | Size from checkpoint payload, not “large by default” |
| GCS | Cheap storage; egress is the trap | Same-region; lifecycle on drafts |
| BigQuery | Scan-priced | Partition by date; do not dump raw prompts as the warehouse |
| Document AI | Per page | Skip re-OCR when hash unchanged |
| Apigee | Product/proxy tax | One gateway; don’t duplicate per portal |
| Vector Search | Nodes + queries | Small index first (FOA + SF424 + samples) |

### 7.4 Maintenance cost (often larger than infra)

| Workstream | Cadence | Who | If you skip it |
|------------|---------|-----|----------------|
| FOA / SF424 / salary-cap / modular rules | Every NIH notice | Knowledge Updater + Compliance owner | Silent non-compliance |
| Skill / prompt regression | Every model bump | Eval owner | Quality drift |
| Control-plane policies | Quarterly | Security + OSPA | Audit gaps |
| Dependency / image patching | Continuous | Platform | CVE debt on Cloud Run |
| Dual-runtime (hybrid) | Ongoing | Platform | ADK and LangGraph diverge |
| Human review queue UX | Ongoing | Product + OSPA | HITL becomes a bottleneck |

**Selection implication:** prefer components the existing MCC platform team already operates (Cloud SQL, BQ, Run, Secret Manager) over a new product that needs a new on-call rotation—unless a gate forces it.

### 7.5 Hidden and transfer costs

- Dual-write during hybrid rollout (ADK session + LangGraph checkpoint).
- Re-processing historical packages when rules change.
- Observability vendor seats and retained traces.
- Reserved GPU/TPU: **not** required if you stay on managed Vertex APIs.
- Data egress if eval or logging leaves the org.

---

## 8. Worked example (illustrative scoring)

Assumptions: MCC GCP, ~50 packages/month in year 1, HITL required, OSPA is the submitter.

| Component decision | Options | Gate | Weighted score (illustrative) | Decision |
|--------------------|---------|------|-------------------------------|----------|
| Runtime | A / B / C | All pass in-org | C ≈ 4.2, A ≈ 3.6, B ≈ 3.7 | **C Hybrid** |
| OLTP | Cloud SQL vs AlloyDB vs new SaaS DB | SaaS DB fails G2/G3 unless BAA | Cloud SQL ≈ 4.5 | **Keep Cloud SQL** |
| LLM | Vertex Gemini vs public consumer API | Consumer API fails G2/G3/G10 | Vertex ≈ 4.4 | **Vertex only in prod** |
| Observability | Cloud Trace only vs Langfuse SaaS vs self-host | SaaS needs BAA | Trace + in-VPC traces ≈ 4.0 | **GCP native first**; add Langfuse only if gated |
| Checkpoints | Redis vs SQL-only | Both pass | Redis ≈ 4.1 at >10 concurrent graphs | **Memorystore** |

*Re-score when packages/month or tokens/package move by ~3×.*

---

## 9. Decision record (copy per component)

```
Component:
Capability IDs served:
CSP / service:
Options considered:
Gates (G1–G10): Pass / Fail + notes
Weighted scores:
12–24 month TCO sketch (infra / tokens / people):
Residual risk:
Owner:
Review date:
```

Store records next to this file (or in the EA packet). Do not leave “we picked X” only in chat history.

---

## 10. Review triggers

Re-run the framework when any of these happen:

- NIH policy or salary-cap / modular rules change
- New model generation on Vertex (quality or price step-change)
- Package volume triples
- HITRUST / internal audit finding
- ADK Workflow gains (or loses) looping / checkpoint feature parity
- OSPA requires a new system of record besides MIRIS

---

## Related

- [Architecture considerations README](README.md) — stack, Cloud SQL, flows, runtime decision matrix
- [Control plane](../control-plane-integration.md)
- [Budget Scrutinizer](../budget-and-package-agent.md)
