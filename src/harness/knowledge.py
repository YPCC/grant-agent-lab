"""Versioned knowledge packs. Checklists/SF424 are the lab config, not copies."""
from __future__ import annotations

import json
from typing import Any

from src.harness.paths import CHECKLISTS_DIR, FIXTURES_DIR, LAB_ROOT, PACKS_DIR, POLICIES_DIR
from src.harness.yaml_lite import parse_simple_yaml

PACK_FILES = {
    "r01_essentials": CHECKLISTS_DIR / "r01_essentials.yaml",
    "ora_intake": CHECKLISTS_DIR / "ora_intake.yaml",
    "sf424": POLICIES_DIR / "nih_sf424_rules.yaml",
    "gpa_core_questions": PACKS_DIR / "gpa_core_questions.md",
    "ssrb_issue_classes": PACKS_DIR / "ssrb_issue_classes.md",
    "invariants": PACKS_DIR / "invariants.md",
    "reporter_frozen": FIXTURES_DIR / "reporter" / "auditory_cortex_2024.json",
}


def list_packs() -> list[str]:
    return sorted(PACK_FILES)


def load_pack(name: str) -> dict[str, Any]:
    path = PACK_FILES.get(name)
    if path is None:
        raise KeyError(f"Unknown pack {name}. Known: {list_packs()}")
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        payload: Any = parse_simple_yaml(text)
    elif path.suffix == ".json":
        payload = json.loads(text)
    else:
        payload = text
    try:
        rel = str(path.relative_to(LAB_ROOT))
    except ValueError:
        rel = str(path)
    return {"id": name, "path": rel, "version": "2026-09-10", "content": payload}


def resolve_packs(names: list[str] | None = None) -> dict[str, Any]:
    wanted = names or list_packs()
    packs = [load_pack(n) for n in wanted]
    return {
        "guideline_versions": {p["id"]: p["version"] for p in packs},
        "packs": packs,
        "last_knowledge_refresh": "fixture",
    }
