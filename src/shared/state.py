"""Shared ProposalState used by all three paths (ADK, LangGraph, Hybrid)."""

from __future__ import annotations
from typing import TypedDict, List, Dict, Optional, Annotated, Literal
from operator import add
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SectionDraft(TypedDict, total=False):
    content: str
    version: int
    last_updated: str
    status: Literal["draft", "revised", "approved", "needs_work"]


class CritiqueItem(TypedDict, total=False):
    reviewer_role: str
    severity: Literal["fatal", "major", "minor", "suggestion"]
    location: str
    comment: str
    suggested_fix: Optional[str]
    addressed: bool


class ComplianceIssue(TypedDict, total=False):
    rule_source: str
    rule_id: str
    description: str
    severity: Literal["blocker", "warning", "info"]
    location: str
    status: Literal["open", "resolved", "waived"]


class BudgetLine(TypedDict, total=False):
    category: str
    description: str
    amount: float
    year: int
    linked_aim: Optional[str]


class BudgetSummary(TypedDict, total=False):
    total_direct: float
    total_indirect: float
    total_costs: float
    years: int
    modular: bool
    justification: str
    lines: List[BudgetLine]
    effort_by_role: Dict[str, float]


class PackageSnapshot(TypedDict, total=False):
    package_id: str
    version_tag: str
    created_at: str
    path: str
    contents: List[str]
    approved_by: Optional[str]
    git_ref: Optional[str]


class ProposalState(TypedDict, total=False):
    proposal_id: str
    mechanism: Literal["R01", "R21", "R03", "K99/R00", "K08", "K23", "other"]
    institute_center: Optional[str]
    foa_or_nosi: Optional[str]
    deadline: Optional[str]
    research_idea_summary: str
    central_hypothesis: str
    preliminary_data_summary: str
    team_and_environment: str
    specific_aims: SectionDraft
    significance: SectionDraft
    innovation: SectionDraft
    approach: Dict[str, SectionDraft]
    budget: BudgetSummary
    critiques: Annotated[List[CritiqueItem], add]
    compliance_issues: Annotated[List[ComplianceIssue], add]
    guideline_versions: Dict[str, str]
    last_knowledge_refresh: Optional[str]
    package_snapshot: Optional[PackageSnapshot]
    current_stage: Literal[
        "intake", "aims_draft", "full_draft",
        "review", "compliance", "revision", "pi_review",
        "packaging", "final"
    ]
    iteration_count: int
    human_feedback: Optional[str]
    final_package_ready: bool


def new_proposal_state(
    proposal_id: str,
    mechanism: str = "R01",
    research_idea_summary: str = "",
    central_hypothesis: str = "",
) -> ProposalState:
    """Factory for a clean initial state."""
    empty_section: SectionDraft = {
        "content": "",
        "version": 0,
        "last_updated": _now(),
        "status": "draft",
    }
    return ProposalState(
        proposal_id=proposal_id,
        mechanism=mechanism,  # type: ignore
        institute_center=None,
        foa_or_nosi=None,
        deadline=None,
        research_idea_summary=research_idea_summary,
        central_hypothesis=central_hypothesis,
        preliminary_data_summary="",
        team_and_environment="",
        specific_aims=empty_section.copy(),
        significance=empty_section.copy(),
        innovation=empty_section.copy(),
        approach={},
        budget={
            "total_direct": 0.0,
            "total_indirect": 0.0,
            "total_costs": 0.0,
            "years": 5 if mechanism == "R01" else 2,
            "modular": True,
            "justification": "",
            "lines": [],
            "effort_by_role": {},
        },
        critiques=[],
        compliance_issues=[],
        guideline_versions={},
        last_knowledge_refresh=None,
        package_snapshot=None,
        current_stage="intake",
        iteration_count=0,
        human_feedback=None,
        final_package_ready=False,
    )
