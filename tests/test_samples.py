"""Evaluation tests using the public / synthetic Specific Aims samples."""

from __future__ import annotations
from pathlib import Path

import pytest

from src.shared.state import new_proposal_state
from src.part_c_hybrid.nodes import grant_reviewer_node, compliance_node
from src.part_c_hybrid.compliance_full import evaluate_rules

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def _load(name: str) -> str:
    return (SAMPLES / name).read_text()


def test_good_aims_have_no_fatal_critiques():
    text = _load("good_aims_auditory.txt")
    state = new_proposal_state(
        "GOOD-001",
        mechanism="R01",
        central_hypothesis="NMDA-dependent LTP in A1 is required for perceptual learning",
    )
    state["specific_aims"] = {"content": text, "version": 1, "status": "draft"}
    result = grant_reviewer_node(state)
    fatals = [c for c in result.get("critiques", []) if c.get("severity") == "fatal"]
    assert len(fatals) == 0, f"Unexpected fatals: {fatals}"


def test_weak_aims_trigger_fatal_or_major():
    text = _load("weak_aims_vague.txt")
    state = new_proposal_state("WEAK-001", mechanism="R01", central_hypothesis="")
    state["specific_aims"] = {"content": text, "version": 1, "status": "draft"}
    result = grant_reviewer_node(state)
    serious = [c for c in result.get("critiques", []) if c.get("severity") in ("fatal", "major")]
    assert len(serious) >= 1, "Expected at least one fatal or major critique on weak aims"


def test_compliance_rules_load_and_fire():
    state = new_proposal_state("COMP-001", mechanism="R01", central_hypothesis="")
    issues = evaluate_rules(state)
    ids = {i["rule_id"] for i in issues}
    assert "HYPOTHESIS_REQUIRED" in ids or "MECHANISM_DECLARED" in ids
