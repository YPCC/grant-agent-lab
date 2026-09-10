"""Deterministic reviewer aligned to GPA + SSRB issue classes. No LLM required."""
from __future__ import annotations

import re
from typing import Any

ISSUE_CLASSES = {
    "vague_hypothesis": "Hypothesis is missing, exploratory, or not falsifiable.",
    "aim_dependency": "A later aim depends on success of an earlier aim.",
    "missing_controls": "Approach language lacks controls, comparison, or vehicle/sham.",
    "missing_expected_outcome": "Aim does not state an expected outcome.",
    "weak_innovation": "Innovation is generic ('new things', 'advance the field').",
    "missing_gap": "No explicit knowledge-gap statement.",
    "scope_ambition": "Aims characterize/explore without a bounded test.",
    "hidden_assumption": "Causal claim without preliminary-data language.",
    "alternative_design_needed": "No alternative if the primary manipulation fails.",
}

HYPOTHESIS_RE = re.compile(
    r"\b(we hypothesize|central hypothesis|test whether|is required for|causes|via)\b",
    re.I,
)
DEPEND_RE = re.compile(
    r"(building on aim\s*1|depends on (the success of )?aim|after successful (learning|completion) in aim)",
    re.I,
)
INDEPENDENT_RE = re.compile(
    r"(independent of aim|does not depend|aims are independent|can proceed if)",
    re.I,
)
CONTROL_RE = re.compile(r"\b(control|vehicle|sham|placebo|comparison)\b", re.I)
OUTCOME_RE = re.compile(r"(expected outcome|we predict|will show|will fail to)", re.I)
GAP_RE = re.compile(r"\b(gap|unknown|poorly understood|elucidate|not known)\b", re.I)
PRELIM_RE = re.compile(r"(preliminary|pilot|unpublished data|we have shown)", re.I)
VAGUE_AIM_RE = re.compile(r"\b(characterize|investigate|explore|look for interesting)\b", re.I)
GENERIC_IMPACT_RE = re.compile(r"(advance the field|may one day help|learn new things)", re.I)


def review_text(text: str, mechanism: str = "R01") -> dict[str, Any]:
    t = text or ""
    critiques: list[dict[str, Any]] = []

    def add(cls: str, severity: str, location: str, comment: str) -> None:
        critiques.append({
            "class": cls,
            "severity": severity,
            "location": location,
            "comment": comment,
            "description": ISSUE_CLASSES.get(cls, cls),
        })

    if not HYPOTHESIS_RE.search(t) or len(t) < 200:
        add("vague_hypothesis", "fatal", "opening", "No testable central hypothesis detected.")
    if DEPEND_RE.search(t) and not INDEPENDENT_RE.search(t):
        add("aim_dependency", "fatal", "aims", "Later aim appears to depend on earlier aim success.")
    if INDEPENDENT_RE.search(t):
        pass
    elif "aim 2" in t.lower() and not INDEPENDENT_RE.search(t):
        add("aim_dependency", "major", "aims", "Independence language not found across multiple aims.")
    if VAGUE_AIM_RE.search(t) and not OUTCOME_RE.search(t):
        add("scope_ambition", "major", "aims", "Aims use characterize/investigate without expected outcomes.")
    if not CONTROL_RE.search(t):
        add("missing_controls", "major", "approach", "No control / vehicle / comparison language.")
    if not OUTCOME_RE.search(t):
        add("missing_expected_outcome", "major", "aims", "No expected-outcome statements.")
    if GENERIC_IMPACT_RE.search(t):
        add("weak_innovation", "minor", "closing", "Impact language is generic.")
    if not GAP_RE.search(t):
        add("missing_gap", "major", "opening", "No explicit gap / unknown.")
    if HYPOTHESIS_RE.search(t) and not PRELIM_RE.search(t):
        add("hidden_assumption", "minor", "opening", "Causal hypothesis without preliminary-data language.")
    if "fail" not in t.lower() and "alternative" not in t.lower() and "if aim" not in t.lower():
        add("alternative_design_needed", "minor", "approach", "No alternative if a primary manipulation fails.")

    gpa = {
        "testable_hypothesis": bool(HYPOTHESIS_RE.search(t)) and "characterize neural activity" not in t.lower(),
        "why_now_gap": bool(GAP_RE.search(t)),
        "specific_innovation": bool(HYPOTHESIS_RE.search(t)) and not GENERIC_IMPACT_RE.search(t),
        "feasible_independent_aims": bool(INDEPENDENT_RE.search(t)) and not DEPEND_RE.search(t),
    }
    serious = [c for c in critiques if c["severity"] in ("fatal", "major")]
    return {
        "agent": "GrantReviewer",
        "lens": ["grant-proposal-assistant", "scientific-strategic-review-board"],
        "mechanism": mechanism,
        "gpa_core": gpa,
        "gpa_score": int(round(100 * sum(1 for v in gpa.values() if v) / 4)),
        "critiques": critiques,
        "critique_classes": [c["class"] for c in critiques],
        "fatal_or_major": len(serious),
        "summary": (
            f"{len(critiques)} critiques ({len(serious)} fatal/major). "
            f"GPA core {sum(1 for v in gpa.values() if v)}/4."
        ),
    }
