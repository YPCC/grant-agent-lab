"""Missing Essentials — same catalog as the workbench (config/checklists)."""
from __future__ import annotations

from typing import Any

from src.shared.checklist import evaluate_checklist as _evaluate
from src.shared.checklist import load_catalog


def evaluate_checklist(text: str, documents: list[str] | None = None, catalog: dict | None = None) -> dict[str, Any]:
    result = _evaluate(text, documents=documents, catalog=catalog)
    missing = result.get("missing_required") or []
    result["missing_required"] = [m["id"] if isinstance(m, dict) else m for m in missing]
    return result


__all__ = ["evaluate_checklist", "load_catalog"]
