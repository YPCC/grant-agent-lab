"""Missing Essentials agent — score a grant draft against the R01 checklist."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "config" / "checklists" / "r01_essentials.yaml"


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Minimal YAML subset so the agent runs without PyYAML."""
    items: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    mechanism, title = "R01", "checklist"
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("mechanism:"):
            mechanism = line.split(":", 1)[1].strip()
        elif line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.startswith("  - id:"):
            if cur:
                items.append(cur)
            cur = {"id": line.split(":", 1)[1].strip(), "required": True, "detect": []}
        elif cur is None:
            continue
        elif line.startswith("    label:"):
            cur["label"] = line.split(":", 1)[1].strip()
        elif line.startswith("    required:"):
            cur["required"] = "true" in line.lower()
        elif line.startswith("    group:"):
            cur["group"] = line.split(":", 1)[1].strip()
        elif line.startswith("    detect:"):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("[") and rest.endswith("]"):
                cur["detect"] = [p.strip(" '\"") for p in rest[1:-1].split(",") if p.strip()]
    if cur:
        items.append(cur)
    return {"mechanism": mechanism, "title": title, "items": items}


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_CATALOG
    text = p.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text)
    return _parse_simple_yaml(text)


def evaluate_checklist(text: str, documents: list[str] | None = None, catalog: dict | None = None) -> dict[str, Any]:
    catalog = catalog or load_catalog()
    blob = (text or "").lower()
    extra = " ".join(documents or []).lower()
    hay = blob + "\n" + extra
    rows = []
    missing_required = []
    for item in catalog.get("items", []):
        needles = [n.lower() for n in item.get("detect") or []]
        present = any(n and n in hay for n in needles)
        status = "present" if present else "missing"
        row = {
            "id": item["id"],
            "label": item.get("label", item["id"]),
            "group": item.get("group", ""),
            "required": bool(item.get("required", True)),
            "status": status,
        }
        rows.append(row)
        if row["required"] and status == "missing":
            missing_required.append(row)
    total_req = sum(1 for r in rows if r["required"])
    present_req = total_req - len(missing_required)
    score = int(round(100 * present_req / total_req)) if total_req else 100
    return {
        "agent": "MissingEssentials",
        "mechanism": catalog.get("mechanism", "R01"),
        "title": catalog.get("title", ""),
        "items": rows,
        "missing_required": missing_required,
        "present_required": present_req,
        "total_required": total_req,
        "readiness_score": score,
        "can_freeze": len(missing_required) == 0,
        "summary": (
            f"{present_req}/{total_req} required items present. "
            + ("Ready to freeze for OSPA." if not missing_required else f"Missing: {', '.join(m['id'] for m in missing_required)}.")
        ),
    }
