"""Eval runner — drives Part B GrantGraph (same nodes as the workbench)."""
from __future__ import annotations

import json
from typing import Any

from src.control_plane.guard import get_audit_log
from src.control_plane.observability import score_case
from src.harness.graders import grade_run
from src.part_b_langgraph.graph import build_graph, snapshot


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
    graph=None,
) -> dict[str, Any]:
    g = graph or build_graph()
    tid = proposal_id
    script = list(hitl_script or ["revise"])
    state = g.invoke(
        {
            "text": text,
            "mechanism": mechanism,
            "filename": filename,
            "knowledge_pack": knowledge_pack,
            "intake_overrides": intake_overrides or {},
            "proposal_id": proposal_id,
            "allow_package": allow_package,
        },
        {"configurable": {"thread_id": tid}},
    )
    for step in script:
        if not hasattr(g, "resume"):
            break
        state = g.resume(tid, step, allow_package=allow_package)
        if step == "approve":
            break
    result = snapshot(state)
    if (result.get("hitl") or {}).get("status") == "awaiting_human" and script:
        result["hitl"] = {
            **result["hitl"],
            "status": "resumed",
            "decision": script[-1],
            "decisions": script,
        }
    result["audit"] = result.get("audit") or get_audit_log()[-30:]
    result["path"] = "part_b_langgraph"
    return result


def run_case(case: dict[str, Any], *, allow_package: bool | None = None, graph=None) -> dict[str, Any]:
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
        graph=graph,
    )
    run["grade"] = grade_run(case, run)
    score_case(run["grade"])
    return run


def run_case_id(case_id: str, **kwargs: Any) -> dict[str, Any]:
    from src.harness.cases import load_case

    return run_case(load_case(case_id), **kwargs)


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)
