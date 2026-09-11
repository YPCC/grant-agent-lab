# Observability — Langfuse traces per agent

Every node on the Part B graph already goes through `control_plane.guard()`. That call is now also an **observation**: one parent trace per `invoke` / `resume`, and a child span per agent (`knowledge_updater.refresh`, `GrantReviewer.review`, `MissingEssentials.score_checklist`, `intake.fill_intake`, `hitl.freeze`, `package_creator.submit_office`).

Langfuse is **optional**. Without keys the eval cage, CI, and workbench still run. Spans are kept in memory (workbench chip + `/api/observability`) and, when configured, exported to [Langfuse Cloud](https://cloud.langfuse.com) or a self-hosted instance.

```text
grant-graph.invoke                         ← parent trace
  ├─ knowledge_updater.refresh
  ├─ GrantReviewer.review
  ├─ MissingEssentials.score_checklist
  ├─ intake.fill_intake
  └─ (HITL pause)
grant-graph.resume  decision=approve       ← second parent
  ├─ hitl.freeze           ASK unless human
  └─ package_creator.submit_office
```

DENY (NIH ASSIST, invented budget) is span **ERROR**. ASK (freeze / office submit without a human) is **WARNING**. ALLOW is the default.

## Enable

```bash
pip install -e ".[observability]"     # langfuse + OpenTelemetry

export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your host
# LANGFUSE_HOST is accepted as an alias of BASE_URL
```

Create keys in the Langfuse project settings (cloud or self-host). Put them in gitignored `.env`. Then:

```bash
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py
```

The workbench header chip reads **Langfuse on** when keys are present. Open the project in Langfuse and filter tags `grant-agent-lab` / `part_b`.

`LANGFUSE_ENABLED=0` forces a no-op even if keys exist.

## What is not sent

Full proposal text is truncated. Span output is a slim dict (`summary`, `can_freeze`, `tracking_number`, …) so NIH drafts do not land wholesale in a SaaS project unless you change the clip limit. Audit JSONL (`output/audit_log.jsonl`) remains the on-prem trail.

## Harness scores

After `run-case`, a `harness_passed` score (0/1) is attached to the current trace when the SDK is live. Locally you still see `harness.grade` in `/api/observability`.

## Relation to the control plane

| Layer | Job |
|-------|-----|
| `guard()` | ALLOW / DENY / ASK — *blocks* illegal acts |
| Audit JSONL | Tamper-evident local log |
| Langfuse | *Watch* latency, verdict, and agent order |

Langfuse does not replace the guard. A pretty trace of a DENY is still a DENY.

See [control-plane-integration.md](control-plane-integration.md) and [one-pager](one-pager.md).
