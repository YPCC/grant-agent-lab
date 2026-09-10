#!/usr/bin/env python3
"""CLI used by the Next.js CopilotKit routes for intake + office submit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.shared.intake import apply_overrides, fill_intake
from src.shared.packaging import create_office_package


def main() -> None:
    action = sys.argv[1]
    payload = json.loads(Path(sys.argv[2]).read_text() if len(sys.argv) > 2 else sys.stdin.read())
    if action == "fill":
        out = fill_intake(payload.get("text") or "", payload.get("filename") or "")
        if payload.get("overrides"):
            out = apply_overrides(out, payload["overrides"])
    elif action == "apply":
        out = apply_overrides(payload["intake"], payload.get("overrides") or {})
    elif action == "submit":
        out = create_office_package(
            proposal_id=payload.get("proposal_id") or "PR-2026-014",
            filename=payload.get("filename") or "proposal.docx",
            intake=payload.get("intake") or {},
            findings=payload.get("findings") or [],
            text_excerpt=payload.get("excerpt") or "",
            submitted_by=payload.get("role") or "PI",
        )
    else:
        raise SystemExit(f"unknown action {action}")
    text = json.dumps(out)
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
