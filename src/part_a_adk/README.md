# Part A – Pure Google ADK 2.0

This path implements the entire grant workflow using only Google ADK 2.0:

- Root Orchestrator as `LlmAgent` or `Workflow`
- Specialist agents as `LlmAgent` (Task / Single-turn modes where appropriate)
- Graph-based `Workflow` for the deterministic Write → Review → Compliance → HITL sequence
- Native session state, HITL pause/resume, Cloud Logging / Trace, Vertex AI deployment

## Status

Scaffold only. The hybrid path (Part C) is the primary working implementation.
The ADK path will reuse the same skill prompts and `ProposalState` contract.

## Key files

- `agents.py` – LlmAgent definitions for Writer, Reviewer, Compliance, KnowledgeUpdater
- `workflow.py` – ADK 2.0 Workflow / graph edges

## Why choose this path

- Institutional GCP / Vertex AI Agent Engine deployment
- Native IAM, data residency, A2A protocol
- Built-in observability and evaluation tooling
