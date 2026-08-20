# Part B – Pure LangGraph

This path implements the entire grant workflow as a single LangGraph `StateGraph`:

- Typed `ProposalState` with reducers
- Explicit nodes for Writer, Reviewer, Compliance, Budget Scrutinizer, KnowledgeUpdater, HITL, Package Creator
- Conditional edges for revision loops
- Checkpointing + time-travel for long drafting sessions

## Status

Working implementation reusing hybrid nodes with MemorySaver checkpointer.

## Key files

- `graph.py` – full StateGraph with checkpointing
- `demo.py` – local invoke with thread_id resume

## Why choose this path

- Maximum control over state transitions and revision loops
- Best-in-class checkpointing and time-travel debugging
- Cloud-agnostic
