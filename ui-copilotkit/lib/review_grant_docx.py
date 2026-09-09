#!/usr/bin/env python3
"""Extract text from a grant .docx and produce structured review findings."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import RGBColor, Pt, Inches

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.shared.checklist import evaluate_checklist


INDEPENDENCE_HINTS = (
    "independent",
    "independently",
    "does not depend",
    "can proceed if",
    "does not rely",
)
HYPOTHESIS_HINTS = ("hypothesis", "we hypothesize", "central hypothesis", "we test whether")
MECHANISM_HINTS = ("r01", "r21", "r03", "k99", "k08", "k23")


def extract_text(path: str | Path) -> str:
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def review_text(text: str, filename: str = "upload.docx") -> dict:
    low = text.lower()
    findings = []

    if not any(h in low for h in HYPOTHESIS_HINTS) or "no explicit, testable central hypothesis" in low:
        findings.append({
            "agent": "GrantReviewer",
            "severity": "fatal",
            "location": "Specific Aims — Opening",
            "rule_id": "HYPOTHESIS_REQUIRED",
            "comment": "No clear, testable central hypothesis. Reviewers treat this as a common fatal flaw.",
            "suggested_fix": "State: “The central hypothesis is that X causes Y via Z, based on [prelim / literature].”",
        })

    if not any(h in low for h in INDEPENDENCE_HINTS) or "cannot proceed if aim 1 fails" in low or "building on aim 1" in low:
        findings.append({
            "agent": "GrantReviewer",
            "severity": "major",
            "location": "Aim 2",
            "rule_id": "AIMS_INDEPENDENCE",
            "comment": "Aim 2 appears dependent on Aim 1 succeeding. A collapsed first aim would sink the project.",
            "suggested_fix": "Rework Aim 2 so it can proceed if Aim 1 fails; say so explicitly.",
        })

    if "expected outcome" not in low and "expected outcomes are not specified" in low:
        findings.append({
            "agent": "GrantReviewer",
            "severity": "major",
            "location": "Aim 1",
            "rule_id": "EXPECTED_OUTCOMES",
            "comment": "Aim 1 does not state a predicted, measurable outcome.",
            "suggested_fix": "Add one sentence: what changes, in what assay, if the hypothesis is true.",
        })

    if len(text) > 4500:
        findings.append({
            "agent": "ComplianceChecker",
            "severity": "warning",
            "location": "Specific Aims",
            "rule_id": "SPECIFIC_AIMS_LENGTH",
            "comment": f"Extracted text is {len(text)} characters; NIH Aims must fit one page (~≤4500 chars).",
            "suggested_fix": "Cut background; keep hypothesis + 2–3 independent aims + impact.",
        })

    if not any(m in low for m in MECHANISM_HINTS):
        findings.append({
            "agent": "ComplianceChecker",
            "severity": "blocker",
            "location": "Header",
            "rule_id": "MECHANISM_DECLARED",
            "comment": "Grant mechanism (R01, R21, …) is not declared in the document.",
            "suggested_fix": "Put mechanism and FOA in the header.",
        })

    if "person-month" not in low and "person months" not in low and "effort" not in low:
        findings.append({
            "agent": "BudgetScrutinizer",
            "severity": "blocker",
            "location": "Budget / personnel",
            "rule_id": "PI_EFFORT_MISSING",
            "comment": "PD/PI effort in person-months is not declared. NIH requires measurable PI effort > 0.",
            "suggested_fix": "Add a personnel justification with PD/PI person-months (not a planned dollar table).",
        })

    if "dms" not in low and "data management" not in low:
        findings.append({
            "agent": "ComplianceChecker",
            "severity": "warning",
            "location": "Package",
            "rule_id": "DMS_PLAN",
            "comment": "No Data Management and Sharing plan language in this file.",
            "suggested_fix": "Attach a labeled DMS plan even if direct costs are $0.",
        })

    if "interesting patterns" in low or "hope to learn new things" in low:
        findings.append({
            "agent": "GrantReviewer",
            "severity": "major",
            "location": "Aims language",
            "rule_id": "VAGUE_LANGUAGE",
            "comment": "Language is exploratory (“interesting patterns”, “hope to learn”) rather than hypothesis-driven.",
            "suggested_fix": "Replace with a causal claim and a disconfirmable prediction.",
        })

    blockers = [f for f in findings if f["severity"] in ("fatal", "blocker")]
    majors = [f for f in findings if f["severity"] == "major"]
    ready = len(blockers) == 0
    score = max(0, 100 - 25 * len(blockers) - 12 * len(majors) - 5 * (len(findings) - len(blockers) - len(majors)))

    checklist = evaluate_checklist(text)
    return {
        "filename": filename,
        "char_count": len(text),
        "excerpt": text[:1200],
        "full_text": text,
        "readiness_score": min(score, checklist["readiness_score"]),
        "package_ready": ready and checklist["can_freeze"],
        "submit_enabled_for_pi": False,
        "findings": findings,
        "checklist": checklist,
        "summary": (
            f"{len(findings)} finding(s): {len(blockers)} blocker/fatal, {len(majors)} major. "
            + checklist["summary"]
        ),
    }


def write_review_docx(result: dict, out_path: str | Path) -> None:
    doc = Document()
    doc.add_heading("Grant review report (agent run)", level=1)
    meta = doc.add_paragraph()
    meta.add_run("Source file: ").bold = True
    meta.add_run(result.get("filename", "") + "\n")
    meta.add_run("Readiness: ").bold = True
    meta.add_run(f"{result.get('readiness_score', 0)} / 100\n")
    meta.add_run("Summary: ").bold = True
    meta.add_run(result.get("summary", ""))

    doc.add_paragraph(
        "RBAC: PI can run review and freeze science. Official submit stays with Office of Research Aid / AOR. "
        "This report is evidence for institutional routing, not an eRA submission."
    )

    doc.add_heading("Findings", level=2)
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Severity"
    hdr[1].text = "Agent"
    hdr[2].text = "Rule"
    hdr[3].text = "Location"
    hdr[4].text = "Comment / fix"
    for f in result.get("findings", []):
        row = table.add_row().cells
        row[0].text = f.get("severity", "")
        row[1].text = f.get("agent", "")
        row[2].text = f.get("rule_id", "")
        row[3].text = f.get("location", "")
        row[4].text = f.get("comment", "") + "  →  " + f.get("suggested_fix", "")

    doc.add_heading("Extracted source (plain text)", level=2)
    doc.add_paragraph(result.get("full_text", "")[:8000])
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)


def main():
    src = Path(sys.argv[1])
    out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/review.json")
    out_docx = Path(sys.argv[3]) if len(sys.argv) > 3 else out_json.with_suffix(".docx")
    text = extract_text(src)
    result = review_text(text, src.name)
    write_review_docx(result, out_docx)
    result["review_docx"] = str(out_docx)
    # do not dump full_text twice into huge json for API — keep excerpt
    slim = {k: v for k, v in result.items() if k != "full_text"}
    slim["full_text"] = result["full_text"]
    out_json.write_text(json.dumps(slim, indent=2))
    print(json.dumps({"ok": True, "json": str(out_json), "docx": str(out_docx), "n": len(result["findings"])}))


if __name__ == "__main__":
    main()
