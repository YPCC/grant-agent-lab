"""Part B — pure LangGraph-style grant graph with HITL interrupt.

Uses langgraph when installed. Otherwise GrantGraph (same node contract + interrupt).
Config: config/runtime.yaml  path: part_b_langgraph
"""
from __future__ import annotations

from typing import Any, Callable, TypedDict

from src.shared.checklist import evaluate_checklist


class ProposalState(TypedDict, total=False):
    text: str
    documents: list
    findings: list
    checklist: dict
    hitl: dict
    package_ready: bool
    decision: str


def missing_essentials_node(state: ProposalState) -> ProposalState:
    check = evaluate_checklist(state.get("text", ""), state.get("documents") or [])
    state["checklist"] = check
    state["package_ready"] = bool(check.get("can_freeze"))
    return state


def reviewer_node(state: ProposalState) -> ProposalState:
    text = (state.get("text") or "").lower()
    findings = list(state.get("findings") or [])
    if "hypothesis" not in text:
        findings.append({"agent": "GrantReviewer", "rule_id": "HYPOTHESIS_REQUIRED", "severity": "fatal"})
    state["findings"] = findings
    return state


def hitl_interrupt_node(state: ProposalState) -> ProposalState:
    """Pause before freeze. Real LangGraph: interrupt(). Fallback: set awaiting_human."""
    pending = {
        "type": "pi_review",
        "prompt": "Approve freeze for OSPA, request revision, or waive a finding?",
        "checklist_summary": (state.get("checklist") or {}).get("summary"),
        "can_freeze": (state.get("checklist") or {}).get("can_freeze"),
    }
    try:
        from langgraph.types import interrupt  # type: ignore

        decision = interrupt(pending)
        state["decision"] = decision if isinstance(decision, str) else (decision or {}).get("decision", "revise")
        state["hitl"] = {"status": "resumed", "payload": pending}
    except Exception:
        state["hitl"] = {"status": "awaiting_human", "payload": pending}
        state["decision"] = state.get("decision") or ""
    return state


def freeze_package_node(state: ProposalState) -> ProposalState:
    if state.get("decision") != "approve":
        state["package_ready"] = False
        return state
    if not (state.get("checklist") or {}).get("can_freeze"):
        state["package_ready"] = False
        return state
    state["package_ready"] = True
    return state


def route_after_hitl(state: ProposalState) -> str:
    hitl = state.get("hitl") or {}
    if hitl.get("status") == "awaiting_human":
        return "wait"
    if state.get("decision") == "approve":
        return "freeze"
    return "revise"


def build_graph():
    """Return a compiled LangGraph if available, else GrantGraph."""
    try:
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, StateGraph

        g = StateGraph(ProposalState)
        g.add_node("reviewer", reviewer_node)
        g.add_node("missing_essentials", missing_essentials_node)
        g.add_node("hitl", hitl_interrupt_node)
        g.add_node("freeze", freeze_package_node)
        g.set_entry_point("reviewer")
        g.add_edge("reviewer", "missing_essentials")
        g.add_edge("missing_essentials", "hitl")
        g.add_conditional_edges(
            "hitl",
            route_after_hitl,
            {"wait": END, "freeze": "freeze", "revise": "reviewer"},
        )
        g.add_edge("freeze", END)
        return g.compile(checkpointer=MemorySaver())
    except ImportError:
        return GrantGraph()


class GrantGraph:
    """Deterministic stand-in: same nodes, HITL pause/resume, thread checkpoint."""

    def __init__(self):
        self.threads: dict[str, ProposalState] = {}

    def invoke(self, state: ProposalState, config: dict | None = None) -> ProposalState:
        tid = (config or {}).get("configurable", {}).get("thread_id", "default")
        s: ProposalState = {**self.threads.get(tid, {}), **state}
        s = reviewer_node(s)
        s = missing_essentials_node(s)
        s = hitl_interrupt_node(s)
        self.threads[tid] = s
        return s

    def resume(self, thread_id: str, decision: str) -> ProposalState:
        s = self.threads.get(thread_id) or {}
        s["decision"] = decision
        s["hitl"] = {**(s.get("hitl") or {}), "status": "resumed"}
        nxt = route_after_hitl(s)
        if nxt == "freeze":
            s = freeze_package_node(s)
        elif nxt == "revise":
            s = reviewer_node(s)
            s = missing_essentials_node(s)
            s = hitl_interrupt_node(s)
        self.threads[thread_id] = s
        return s
