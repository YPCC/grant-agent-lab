"""Part B — grant graph. One pipeline for harness, workbench, and Copilot MCP.

Default engine is GrantGraph (deterministic invoke/resume). Same node functions
are used if LangGraph is compiled via GRANT_GRAPH_ENGINE=langgraph.
Every agent call goes through control_plane.guard (ALLOW / DENY / ASK).
"""
from __future__ import annotations

import os
from typing import Any, TypedDict

from src.control_plane.guard import PolicyAsk, get_audit_log, guard
from src.harness.checklist import evaluate_checklist
from src.harness.intake import fill_intake
from src.harness.knowledge import resolve_packs
from src.harness.packaging import create_office_package
from src.harness.review import review_text


class ProposalState(TypedDict, total=False):
    text: str
    documents: list
    filename: str
    mechanism: str
    proposal_id: str
    findings: list
    review: dict
    checklist: dict
    intake: dict
    intake_overrides: dict
    knowledge: dict
    knowledge_pack: list
    hitl: dict
    package_ready: bool
    package: dict
    decision: str
    allow_package: bool
    audit: list


def knowledge_node(state: ProposalState) -> ProposalState:
    packs = state.get("knowledge_pack")
    knowledge = guard("knowledge_updater", "refresh", resolve_packs, packs)
    state["knowledge"] = {
        "guideline_versions": knowledge.get("guideline_versions"),
        "last_knowledge_refresh": knowledge.get("last_knowledge_refresh"),
    }
    return state


def reviewer_node(state: ProposalState) -> ProposalState:
    review = guard(
        "GrantReviewer",
        "review",
        review_text,
        state.get("text") or "",
        mechanism=state.get("mechanism") or "R01",
    )
    state["review"] = review
    findings = list(state.get("findings") or [])
    for c in review.get("critiques") or []:
        findings.append({
            "agent": "GrantReviewer",
            "severity": c.get("severity"),
            "location": c.get("location"),
            "rule_id": c.get("class"),
            "comment": c.get("comment"),
        })
    state["findings"] = findings
    return state


def missing_essentials_node(state: ProposalState) -> ProposalState:
    check = guard(
        "MissingEssentials",
        "score_checklist",
        evaluate_checklist,
        state.get("text") or "",
        documents=state.get("documents") or [],
    )
    state["checklist"] = check
    state["package_ready"] = bool(check.get("can_freeze"))
    return state


def intake_node(state: ProposalState) -> ProposalState:
    form = guard(
        "intake",
        "fill_intake",
        fill_intake,
        state.get("text") or "",
        filename=state.get("filename") or "proposal.docx",
        overrides=state.get("intake_overrides") or {},
    )
    state["intake"] = form
    return state


def hitl_interrupt_node(state: ProposalState) -> ProposalState:
    """Pause before freeze. Resume via GrantGraph.resume / HITL button."""
    pending = {
        "type": "pi_review",
        "prompt": "Approve freeze for Office of Research Aid, request revision, or waive a finding?",
        "checklist_summary": (state.get("checklist") or {}).get("summary"),
        "can_freeze": (state.get("checklist") or {}).get("can_freeze"),
    }
    prev = state.get("hitl") or {}
    state["hitl"] = {
        "status": "awaiting_human",
        "payload": pending,
        "prompt": pending["prompt"],
        "can_freeze": pending["can_freeze"],
        "decisions": list(prev.get("decisions") or []),
        "decision": state.get("decision") or "",
    }
    if not state.get("decision"):
        state["decision"] = ""
    return state


def freeze_package_node(state: ProposalState) -> ProposalState:
    approved = state.get("decision") == "approve"
    try:
        guard("hitl", "freeze", lambda: True, human_approved=approved)
    except PolicyAsk:
        state["package_ready"] = False
        return state

    checklist = state.get("checklist") or {}
    intake = state.get("intake") or {}
    if not checklist.get("can_freeze"):
        state["package_ready"] = False
        return state
    state["package_ready"] = True
    if not state.get("allow_package"):
        return state
    if not intake.get("can_submit_to_office"):
        state["package"] = None
        return state

    def _create() -> dict:
        return create_office_package(
            proposal_id=state.get("proposal_id") or "PR-GRAPH",
            filename=state.get("filename") or "proposal.docx",
            intake=intake,
            findings=state.get("findings") or [],
            text_excerpt=state.get("text") or "",
            submitted_by="PI",
        )

    state["package"] = guard(
        "package_creator",
        "submit_office",
        _create,
        human_approved=True,
    )
    return state


def route_after_hitl(state: ProposalState) -> str:
    hitl = state.get("hitl") or {}
    if hitl.get("status") == "awaiting_human" and not state.get("decision"):
        return "wait"
    if state.get("decision") == "approve":
        return "freeze"
    return "revise"


def snapshot(state: ProposalState) -> dict[str, Any]:
    """Harness / workbench payload from graph state."""
    review = state.get("review") or {}
    checklist = state.get("checklist") or {}
    intake = dict(state.get("intake") or {})
    return {
        "proposal_id": state.get("proposal_id"),
        "mechanism": state.get("mechanism") or "R01",
        "path": "part_b_langgraph",
        "filename": state.get("filename") or "proposal.docx",
        "full_text": state.get("text") or "",
        "excerpt": (state.get("text") or "")[:4000],
        "knowledge": state.get("knowledge") or {},
        "review": review,
        "findings": state.get("findings") or [],
        "checklist": checklist,
        "readiness_score": checklist.get("readiness_score"),
        "summary": " ".join(
            p for p in (review.get("summary"), checklist.get("summary"), intake.get("summary")) if p
        ),
        "intake": intake,
        "hitl": state.get("hitl") or {},
        "package_ready": bool(state.get("package_ready")),
        "package": state.get("package"),
        "audit": list(state.get("audit") or get_audit_log()[-30:]),
        "destination_policy": {"office_of_research_aid": True, "nih_assist": False},
    }


def _run_prefix(state: ProposalState) -> ProposalState:
    s = knowledge_node(state)
    s = reviewer_node(s)
    s = missing_essentials_node(s)
    s = intake_node(s)
    return hitl_interrupt_node(s)


class GrantGraph:
    """Deterministic stand-in: same nodes, HITL pause/resume, thread checkpoint."""

    def __init__(self):
        self.threads: dict[str, ProposalState] = {}

    def invoke(self, state: ProposalState, config: dict | None = None) -> ProposalState:
        tid = (config or {}).get("configurable", {}).get("thread_id", "default")
        s: ProposalState = {**self.threads.get(tid, {}), **state}
        s["findings"] = list(state.get("findings") or [])
        s["decision"] = ""
        s = _run_prefix(s)
        self.threads[tid] = s
        return s

    def resume(self, thread_id: str, decision: str, **updates: Any) -> ProposalState:
        s = dict(self.threads.get(thread_id) or {})
        s.update(updates)
        s["decision"] = decision
        hitl = dict(s.get("hitl") or {})
        decisions = list(hitl.get("decisions") or [])
        decisions.append(decision)
        hitl["decisions"] = decisions
        hitl["decision"] = decision
        hitl["status"] = "resumed"
        s["hitl"] = hitl
        nxt = route_after_hitl(s)
        if nxt == "freeze":
            s = freeze_package_node(s)
        elif nxt == "revise":
            s = reviewer_node(s)
            s = missing_essentials_node(s)
            s = intake_node(s)
            s = hitl_interrupt_node(s)
            s["decision"] = decision
            s["hitl"] = {**(s.get("hitl") or {}), "status": "resumed", "decision": decision, "decisions": decisions}
        elif nxt == "wait":
            s = hitl_interrupt_node(s)
        self.threads[thread_id] = s
        return s


def build_graph():
    """Return GrantGraph (default) or a LangGraph compile if explicitly requested."""
    if os.environ.get("GRANT_GRAPH_ENGINE") == "langgraph":
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import END, StateGraph

            g = StateGraph(ProposalState)
            g.add_node("knowledge", knowledge_node)
            g.add_node("reviewer", reviewer_node)
            g.add_node("missing_essentials", missing_essentials_node)
            g.add_node("intake", intake_node)
            g.add_node("hitl", hitl_interrupt_node)
            g.add_node("freeze", freeze_package_node)
            g.set_entry_point("knowledge")
            g.add_edge("knowledge", "reviewer")
            g.add_edge("reviewer", "missing_essentials")
            g.add_edge("missing_essentials", "intake")
            g.add_edge("intake", "hitl")
            g.add_conditional_edges(
                "hitl",
                route_after_hitl,
                {"wait": END, "freeze": "freeze", "revise": "reviewer"},
            )
            g.add_edge("freeze", END)
            compiled = g.compile(checkpointer=MemorySaver())
            compiled.resume = GrantGraph().resume  # type: ignore[attr-defined]
            return compiled
        except ImportError:
            pass
    return GrantGraph()
