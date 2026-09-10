"""Path-agnostic eval runner with scripted HITL. Uses lab shared catalog/intake/package."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from src.harness.checklist import evaluate_checklist
from src.harness.graders import grade_run
from src.harness.intake import fill_intake
from src.harness.knowledge import resolve_packs
from src.harness.packaging import create_office_package
from src.harness.review import review_text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_pipeline(
    text: str,
    *,
    mechanism: str = "R01",
    filename: str = "proposal.docx",
    knowledge_pack: list[str] | None = None,
    hitl_script: list[str] | None = None,
    intake_overrides: dict[str, str] | None = None,
    proposal_id: str = "PR-HARNESS",
    allow_package: bool = False,
) -> dict[str, Any]:
    audit: list[dict[str, Any]] = []

    def event(kind: str, **payload: Any) -> None:
        audit.append({"ts": _now(), "event": kind, **payload})

    knowledge = resolve_packs(knowledge_pack)
    event("knowledge_refresh", packs=list(knowledge.get("guideline_versions") or {}))

    review = review_text(text, mechanism=mechanism)
    event("review", fatal_or_major=review["fatal_or_major"], classes=review["critique_classes"])

    checklist = evaluate_checklist(text)
    event("checklist", score=checklist["readiness_score"], can_freeze=checklist["can_freeze"])

    intake = fill_intake(text, filename=filename, overrides=intake_overrides)
    event("intake", can_submit=intake["can_submit_to_office"], incomplete=intake["incomplete_required"])

    script = list(hitl_script or ["revise"])
    hitl = {
        "status": "awaiting_human",
        "prompt": "Approve freeze for Office of Research Aid, request revision, or waive a finding?",
        "can_freeze": checklist["can_freeze"],
        "decisions": [],
    }
    decision = ""
    for step in script:
        decision = step
        hitl["decisions"].append(step)
        event("hitl_decision", decision=step)
        if step == "revise":
            review = review_text(text, mechanism=mechanism)
            checklist = evaluate_checklist(text)
        elif step == "waive":
            event("waive", note="Waivers are recorded; checklist presence rules still apply.")
        elif step == "approve":
            break
    hitl["status"] = "resumed"
    hitl["decision"] = decision or "revise"

    package = None
    package_ready = bool(
        checklist["can_freeze"] and hitl["decision"] == "approve" and intake["can_submit_to_office"]
    )
    if allow_package and package_ready:
        package = create_office_package(
            proposal_id=proposal_id,
            filename=filename,
            intake=intake,
            findings=review.get("critiques") or [],
            text_excerpt=text,
            submitted_by="PI",
        )
        event("office_package", tracking=package["tracking_number"])
    elif allow_package and not package_ready:
        event("office_package_blocked", reason="checklist, HITL approve, or intake incomplete")

    return {
        "proposal_id": proposal_id,
        "mechanism": mechanism,
        "path": "harness_v0",
        "knowledge": {
            "guideline_versions": knowledge.get("guideline_versions"),
            "last_knowledge_refresh": knowledge.get("last_knowledge_refresh"),
        },
        "review": review,
        "checklist": checklist,
        "intake": intake,
        "hitl": hitl,
        "package_ready": package_ready,
        "package": package,
        "audit": audit,
        "destination_policy": {"office_of_research_aid": True, "nih_assist": False},
    }


def run_case(case: dict[str, Any], *, allow_package: bool | None = None) -> dict[str, Any]:
    expect = case.get("expect") or {}
    if allow_package is None:
        allow_package = bool(expect.get("office_submit"))
    overrides = (case.get("input") or {}).get("intake_overrides") or {}
    run = run_pipeline(
        case.get("_text") or "",
        mechanism=case.get("mechanism", "R01"),
        filename=(case.get("input") or {}).get("filename") or "proposal.docx",
        knowledge_pack=case.get("knowledge_pack"),
        hitl_script=case.get("hitl_script") or ["revise"],
        intake_overrides=overrides,
        proposal_id=case.get("id", "PR-HARNESS"),
        allow_package=allow_package,
    )
    run["grade"] = grade_run(case, run)
    return run


def run_case_id(case_id: str, **kwargs: Any) -> dict[str, Any]:
    from src.harness.cases import load_case

    return run_case(load_case(case_id), **kwargs)


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)
