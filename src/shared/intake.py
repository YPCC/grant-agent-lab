"""Office of Research Aid intake form — agent fill + human override."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.shared.checklist import _parse_simple_yaml

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
INTAKE_CATALOG = ROOT / "config" / "checklists" / "ora_intake.yaml"

YES = {"yes", "y", "true", "present", "1"}
NO = {"no", "n", "false", "0"}
NA = {"not_applicable", "n/a", "na", "none"}


def load_intake_catalog(path: Path | None = None) -> dict[str, Any]:
    p = path or INTAKE_CATALOG
    text = p.read_text(encoding="utf-8")
    if yaml:
        data = yaml.safe_load(text)
    else:
        data = _parse_simple_yaml(text)
        # extra fields the simple parser may miss
        data.setdefault("destination", "office_database")
        data.setdefault("groups", [])
    return data


def _detect_value(item: dict, hay: str, filename: str, char_count: int) -> tuple[str, str]:
    """Return (value, note). value is yes/no/not_applicable/unknown."""
    if item.get("human_only"):
        return "unknown", "Human attestation required"
    rule = item.get("rule")
    if rule == "aims_char_limit":
        ok = char_count <= 4500
        return ("yes" if ok else "no"), f"Extracted {char_count} characters (limit ~4500)"
    if rule == "filename":
        name = (filename or "").lower()
        ok = "r01" in name and name.endswith(".docx")
        return ("yes" if ok else "no"), f"Filename {filename or '(none)'}"

    needles = [n.lower() for n in (item.get("detect") or []) if n]
    kind = item.get("type", "yes_no")
    if not needles:
        return "unknown", "Not inferable from text — PI may override"
    hit = any(n in hay for n in needles)
    if kind == "yes_no":
        return ("yes" if hit else "no"), "Detected in document" if hit else "Not found in document"
    # enum: if hit → yes (involved/present); else no
    if hit:
        return "yes", "Language in document"
    # For involvement questions, absence usually means no rather than unknown
    if item["id"] in {"SELECT_AGENTS", "COST_SHARING", "SUBAWARDS", "EXPORT_CONTROL"}:
        return "no", "No mention; default no"
    if item["id"] in {"HUMAN_SUBJECTS", "VERTEBRATE_ANIMALS"}:
        if "not applicable" in hay or "n/a" in hay:
            return "not_applicable", "Document says N/A"
        return "no", "No mention; default no"
    if item["id"] == "RS_PAGE_LIMIT":
        return "not_applicable", "Aims-only draft assumed unless Research Strategy is present" if not hit else "yes"
    return "unknown", "Needs PI confirmation"


def fill_intake(
    text: str,
    filename: str = "",
    catalog: dict | None = None,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    catalog = catalog or load_intake_catalog()
    hay = (text or "").lower()
    char_count = len(text or "")
    overrides = overrides or {}
    rows = []
    for item in catalog.get("items", []):
        auto, note = _detect_value(item, hay, filename, char_count)
        oid = item["id"]
        if oid in overrides and str(overrides[oid]).strip():
            value = _normalize(overrides[oid])
            source = "human"
        else:
            value = auto
            source = "agent"
        required = bool(item.get("required", True))
        complete = value not in ("", "unknown", None)
        if item.get("human_only") and source != "human":
            complete = False
        opts = list(item.get("options") or ["yes", "no"])
        if value not in opts:
            opts = [value] + opts
        if "unknown" not in opts:
            opts.append("unknown")
        rows.append({
            "id": oid,
            "label": item.get("label", oid),
            "group": item.get("group", ""),
            "type": item.get("type", "yes_no"),
            "options": opts,
            "required": required,
            "help": item.get("help", ""),
            "human_only": bool(item.get("human_only")),
            "agent_value": auto,
            "value": value,
            "source": source,
            "note": note,
            "complete": complete,
        })
    required_rows = [r for r in rows if r["required"]]
    incomplete = [r for r in required_rows if not r["complete"]]
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["group"] or "Other", []).append(r)
    can_submit = len(incomplete) == 0
    return {
        "agent": "IntakeAgent",
        "title": catalog.get("title", "Office of Research Aid intake form"),
        "destination": catalog.get("destination", "office_database"),
        "items": rows,
        "groups": [{"name": g, "items": items} for g, items in groups.items()],
        "incomplete_required": [r["id"] for r in incomplete],
        "complete_required": len(required_rows) - len(incomplete),
        "total_required": len(required_rows),
        "can_submit_to_office": can_submit,
        "summary": (
            f"{len(required_rows) - len(incomplete)}/{len(required_rows)} required intake items answered. "
            + ("Ready to submit to Office of Research Aid." if can_submit else
               f"Still needed: {', '.join(r['id'] for r in incomplete)}.")
        ),
    }


def _normalize(raw: str) -> str:
    s = str(raw).strip().lower().replace(" ", "_")
    if s in YES:
        return "yes"
    if s in NO:
        return "no"
    if s in NA or s in {"not_applicable", "n/a"}:
        return "not_applicable"
    if s in {"unknown", "unk"}:
        return "unknown"
    return s


def apply_overrides(form: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    """Return a new form with human overrides applied (keeps agent_value)."""
    text_blob = ""  # not re-detected; patch values
    items = deepcopy(form.get("items") or [])
    by_id = {r["id"]: r for r in items}
    for oid, val in (overrides or {}).items():
        if oid not in by_id:
            continue
        r = by_id[oid]
        r["value"] = _normalize(val)
        r["source"] = "human"
        r["complete"] = r["value"] not in ("", "unknown")
        r["note"] = "Overridden by human"
    required_rows = [r for r in items if r["required"]]
    incomplete = [r for r in required_rows if not r["complete"]]
    groups: dict[str, list] = {}
    for r in items:
        groups.setdefault(r["group"] or "Other", []).append(r)
    can_submit = len(incomplete) == 0
    out = deepcopy(form)
    out["items"] = items
    out["groups"] = [{"name": g, "items": gi} for g, gi in groups.items()]
    out["incomplete_required"] = [r["id"] for r in incomplete]
    out["complete_required"] = len(required_rows) - len(incomplete)
    out["total_required"] = len(required_rows)
    out["can_submit_to_office"] = can_submit
    out["summary"] = (
        f"{len(required_rows) - len(incomplete)}/{len(required_rows)} required intake items answered. "
        + ("Ready to submit to Office of Research Aid." if can_submit else
           f"Still needed: {', '.join(r['id'] for r in incomplete)}.")
    )
    return out
