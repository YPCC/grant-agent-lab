"""Configurable LLM backend. Default is none (deterministic graders only)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OVERRIDE = Path(os.environ.get("GRANT_LLM_SETTINGS") or "output/desktop-settings.json")

PROVIDERS = ("none", "vertex", "gemini", "openai", "xai")


@dataclass
class LlmSettings:
    provider: str = "none"
    model: str = "gemini-2.5-flash"
    project: str = ""
    location: str = "us-central1"
    enrich_review: bool = True

    @property
    def enabled(self) -> bool:
        return (self.provider or "none").lower() not in {"none", "deterministic", ""}


def _runtime_llm() -> dict[str, Any]:
    path = ROOT / "config" / "runtime.yaml"
    if not path.exists():
        return {}
    from src.harness.yaml_lite import parse_simple_yaml

    data = parse_simple_yaml(path.read_text(encoding="utf-8"))
    block = data.get("llm") if isinstance(data, dict) else None
    return block if isinstance(block, dict) else {}


def _overrides() -> dict[str, Any]:
    if not OVERRIDE.exists():
        return {}
    try:
        data = json.loads(OVERRIDE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_llm() -> LlmSettings:
    raw = {**_runtime_llm(), **_overrides()}
    provider = (
        os.environ.get("GRANT_LLM_PROVIDER")
        or raw.get("provider")
        or "none"
    ).strip().lower()
    if provider not in PROVIDERS:
        provider = "none"
    model = os.environ.get("GRANT_LLM_MODEL") or str(raw.get("model") or "gemini-2.5-flash")
    project = (
        os.environ.get("VERTEX_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or str(raw.get("project") or "")
    )
    location = os.environ.get("VERTEX_LOCATION") or str(raw.get("location") or "us-central1")
    enrich = raw.get("enrich_review")
    if os.environ.get("GRANT_LLM_ENRICH") is not None:
        enrich = os.environ.get("GRANT_LLM_ENRICH", "1").lower() in {"1", "true", "yes"}
    return LlmSettings(
        provider=provider,
        model=model,
        project=project,
        location=location,
        enrich_review=bool(enrich if enrich is not None else True),
    )


def save_overrides(fields: dict[str, Any]) -> LlmSettings:
    current = asdict(load_llm())
    allowed = {"provider", "model", "project", "location", "enrich_review"}
    for k, v in fields.items():
        if k in allowed:
            current[k] = v
    OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return load_llm()


def as_public(s: LlmSettings | None = None) -> dict[str, Any]:
    s = s or load_llm()
    return {
        "provider": s.provider,
        "model": s.model,
        "project": s.project,
        "location": s.location,
        "enrich_review": s.enrich_review,
        "enabled": s.enabled,
        "providers": list(PROVIDERS),
    }
