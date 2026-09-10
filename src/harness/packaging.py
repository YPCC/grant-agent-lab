"""ORA packaging with an explicit NIH ASSIST deny."""
from __future__ import annotations

from typing import Any

from src.shared.packaging import create_office_package as _create

BLOCKED = ("NIH_ASSIST", "ASSIST", "GRANTS.GOV", "ERA_COMMONS_SUBMIT")


def create_office_package(
    *,
    proposal_id: str = "PR-HARNESS",
    filename: str = "proposal.docx",
    intake: dict[str, Any] | None = None,
    findings: list | None = None,
    text_excerpt: str = "",
    submitted_by: str = "PI",
    destination: str = "Office of Research Aid database",
) -> dict[str, Any]:
    dest_key = (destination or "").replace(" ", "_").upper()
    if any(b in dest_key for b in BLOCKED):
        raise PermissionError("Harness invariant: NIH ASSIST / Grants.gov submit is forbidden")
    return _create(
        proposal_id=proposal_id,
        filename=filename,
        intake=intake,
        findings=findings,
        text_excerpt=text_excerpt,
        submitted_by=submitted_by,
    )
