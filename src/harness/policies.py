"""Omnigent-compatible ALLOW / DENY / ASK policies for the grant graph.

Handlers match docs/POLICIES.md in omnigent-ai/omnigent:
  event["type"] in {request, response, tool_call, tool_result}
  return {"result": "ALLOW"|"DENY"|"ASK", "reason": str} or None to abstain.

These run without Omnigent installed. Wire them from agents/grant-navigator.yaml.
"""
from __future__ import annotations

from typing import Any

PolicyEvent = dict[str, Any]
PolicyResponse = dict[str, Any]

ASSIST_NEEDLES = (
    "nih_assist",
    "assist",
    "grants.gov",
    "grants_gov",
    "era_commons_submit",
    "submit_to_nih",
)
BUDGET_INVENT_NEEDLES = (
    "invent_budget",
    "generate_budget",
    "create_budget_dollars",
    "propose_direct_costs",
)
CERTIFY_NEEDLES = ("pi_certify", "auto_certify")
ASK_NEEDLES = ("freeze", "submit_office", "submit-office", "package_office", "waive")


def _name(event: PolicyEvent) -> str:
    data = event.get("data") or {}
    return str(data.get("name") or event.get("target") or "").lower()


def _blob(event: PolicyEvent) -> str:
    data = event.get("data") or {}
    args = data.get("arguments") or {}
    return " ".join(str(v) for v in (event.get("target"), data.get("name"), args, event)).lower()


def nih_assist_forbidden(event: PolicyEvent) -> PolicyResponse | None:
    """DENY any NIH ASSIST / Grants.gov submit tool."""
    if event.get("type") not in {"tool_call", "request"}:
        return None
    blob = _blob(event)
    name = _name(event)
    if any(n in name or n in blob for n in ASSIST_NEEDLES):
        if "office of research aid" in blob and "assist" not in name:
            return None
        if any(n in name or n in blob for n in ("nih_assist", "grants.gov", "grants_gov", "era_commons", "submit_to_nih")):
            return {
                "result": "DENY",
                "reason": "NIH ASSIST / Grants.gov is out of band. Office of Research Aid only.",
            }
        if name in {"assist", "submit_assist"}:
            return {
                "result": "DENY",
                "reason": "NIH ASSIST / Grants.gov is out of band. Office of Research Aid only.",
            }
    return None


def budget_invention_forbidden(event: PolicyEvent) -> PolicyResponse | None:
    """DENY tools that invent dollar amounts. Presence-only budget checks are ALLOW."""
    if event.get("type") != "tool_call":
        return None
    name = _name(event)
    if any(n in name for n in BUDGET_INVENT_NEEDLES):
        return {
            "result": "DENY",
            "reason": "Budget scrutinizer does not invent dollar amounts. Presence of a budget element only.",
        }
    return None


def pi_certify_human_only(event: PolicyEvent) -> PolicyResponse | None:
    """DENY auto-checking PI_CERTIFY."""
    if event.get("type") != "tool_call":
        return None
    name = _name(event)
    args = str((event.get("data") or {}).get("arguments") or "").lower()
    if any(n in name for n in CERTIFY_NEEDLES) or "pi_certify" in args and "auto" in name:
        return {"result": "DENY", "reason": "PI_CERTIFY is human-only."}
    return None


def ask_on_freeze_or_office_submit(event: PolicyEvent) -> PolicyResponse | None:
    """ASK before freeze, office package, or waiver."""
    if event.get("type") != "tool_call":
        return None
    name = _name(event)
    if any(n in name for n in ASK_NEEDLES):
        return {
            "result": "ASK",
            "reason": "HITL required: freeze / Office of Research Aid submit / waiver.",
        }
    return None


def evaluate(event: PolicyEvent) -> PolicyResponse:
    """Stack used by tests and a local control-plane façade (DENY short-circuits)."""
    for fn in (
        nih_assist_forbidden,
        budget_invention_forbidden,
        pi_certify_human_only,
        ask_on_freeze_or_office_submit,
    ):
        verdict = fn(event)
        if verdict and verdict.get("result") == "DENY":
            return verdict
    for fn in (ask_on_freeze_or_office_submit,):
        verdict = fn(event)
        if verdict and verdict.get("result") == "ASK":
            return verdict
    return {"result": "ALLOW"}


POLICY_REGISTRY = [
    {
        "handler": "src.harness.policies.nih_assist_forbidden",
        "name": "nih_assist_forbidden",
        "description": "DENY NIH ASSIST / Grants.gov submit",
    },
    {
        "handler": "src.harness.policies.budget_invention_forbidden",
        "name": "budget_invention_forbidden",
        "description": "DENY inventing budget dollars",
    },
    {
        "handler": "src.harness.policies.pi_certify_human_only",
        "name": "pi_certify_human_only",
        "description": "DENY auto PI_CERTIFY",
    },
    {
        "handler": "src.harness.policies.ask_on_freeze_or_office_submit",
        "name": "ask_on_freeze_or_office_submit",
        "description": "ASK before freeze / ORA submit / waiver",
    },
]
