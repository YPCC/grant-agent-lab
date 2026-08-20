"""Compile the LangGraph inner workflow for the Hybrid path."""

from __future__ import annotations
from langgraph.graph import StateGraph, END

from src.shared.state import ProposalState
from .nodes import grant_writer_node, grant_reviewer_node, compliance_node, hitl_node
from .compliance_full import compliance_full_node
from .knowledge_updater import knowledge_updater_node
from .budget_scrutinizer import budget_scrutinizer_node
from .package_creator import package_creator_node


def build_hybrid_graph(use_full_compliance: bool = True):
    """
    knowledge → writer → reviewer → compliance → budget_scrutinizer → HITL
         → (approved) package → END
         → (needs work) writer
    """
    workflow = StateGraph(ProposalState)

    workflow.add_node("knowledge", knowledge_updater_node)
    workflow.add_node("writer", grant_writer_node)
    workflow.add_node("reviewer", grant_reviewer_node)
    workflow.add_node(
        "compliance",
        compliance_full_node if use_full_compliance else compliance_node,
    )
    workflow.add_node("budget_scrutinizer", budget_scrutinizer_node)
    workflow.add_node("hitl", hitl_node)
    workflow.add_node("package", package_creator_node)

    workflow.set_entry_point("knowledge")
    workflow.add_edge("knowledge", "writer")
    workflow.add_edge("writer", "reviewer")
    workflow.add_edge("reviewer", "compliance")
    workflow.add_edge("compliance", "budget_scrutinizer")
    workflow.add_edge("budget_scrutinizer", "hitl")

    def route_after_hitl(state: ProposalState) -> str:
        if state.get("final_package_ready"):
            return "package"
        return "writer"

    workflow.add_conditional_edges(
        "hitl",
        route_after_hitl,
        {"writer": "writer", "package": "package"},
    )
    workflow.add_edge("package", END)

    return workflow.compile()
