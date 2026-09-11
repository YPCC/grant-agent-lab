"""Local vs production governance profiles.

GRANT_PROFILE env overrides config/runtime.yaml `profile:`.
Default is local (lightweight). Production fail-closes on policy, audit,
identity, telemetry, secrets, and selected harness/red-team gates.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GovernanceProfile:
    name: str
    policy_required: bool
    audit_required: bool
    audit_fail_closed: bool
    telemetry_required: bool
    telemetry_stub_ok: bool
    identity_required: bool
    identity_roles: tuple[str, ...]
    secrets_redact: bool
    secrets_forbid_era: bool
    secrets_scan_package: bool
    gates_eval_cage: bool
    gates_static_redteam: bool
    gates_deepteam_live: bool
    audit_path: str = "output/audit_log.jsonl"

    @property
    def is_production(self) -> bool:
        return self.name == "production"


_CACHE: GovernanceProfile | None = None

_DEFAULTS = {
    "name": "local",
    "policy_required": True,
    "audit_required": False,
    "audit_fail_closed": False,
    "telemetry_required": False,
    "telemetry_stub_ok": True,
    "identity_required": False,
    "identity_roles": ["PI", "Navigator", "Office of Research Aid", "Admin"],
    "secrets_redact": True,
    "secrets_forbid_era": True,
    "secrets_scan_package": False,
    "gates_eval_cage": False,
    "gates_static_redteam": False,
    "gates_deepteam_live": False,
}


def reset_profile() -> None:
    global _CACHE
    _CACHE = None


def _parse(path: Path) -> dict[str, Any]:
    from src.harness.yaml_lite import parse_simple_yaml

    if not path.exists():
        return {}
    data = parse_simple_yaml(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _requested_name() -> str:
    env = (os.environ.get("GRANT_PROFILE") or "").strip().lower()
    if env in {"local", "production"}:
        return env
    runtime = _parse(ROOT / "config" / "runtime.yaml")
    name = str(runtime.get("profile") or "local").strip().lower()
    return name if name in {"local", "production"} else "local"


def load_profile(name: str | None = None) -> GovernanceProfile:
    chosen = (name or _requested_name()).lower()
    raw = dict(_DEFAULTS)
    file_data = _parse(ROOT / "config" / "profiles" / f"{chosen}.yaml")
    raw.update({k: v for k, v in file_data.items() if k in _DEFAULTS or k == "name"})
    roles = raw.get("identity_roles") or _DEFAULTS["identity_roles"]
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",") if r.strip()]
    audit = os.environ.get("GRANT_AUDIT_LOG") or raw.get("audit_path") or "output/audit_log.jsonl"
    return GovernanceProfile(
        name=str(raw.get("name") or chosen),
        policy_required=bool(raw.get("policy_required")),
        audit_required=bool(raw.get("audit_required")),
        audit_fail_closed=bool(raw.get("audit_fail_closed")),
        telemetry_required=bool(raw.get("telemetry_required")),
        telemetry_stub_ok=bool(raw.get("telemetry_stub_ok")),
        identity_required=bool(raw.get("identity_required")),
        identity_roles=tuple(str(r) for r in roles),
        secrets_redact=bool(raw.get("secrets_redact")),
        secrets_forbid_era=bool(raw.get("secrets_forbid_era")),
        secrets_scan_package=bool(raw.get("secrets_scan_package")),
        gates_eval_cage=bool(raw.get("gates_eval_cage")),
        gates_static_redteam=bool(raw.get("gates_static_redteam")),
        gates_deepteam_live=bool(raw.get("gates_deepteam_live")),
        audit_path=str(audit),
    )


def current() -> GovernanceProfile:
    global _CACHE
    if _CACHE is None:
        _CACHE = load_profile()
    return _CACHE


def as_dict(p: GovernanceProfile | None = None) -> dict[str, Any]:
    p = p or current()
    return {
        "name": p.name,
        "is_production": p.is_production,
        "policy_required": p.policy_required,
        "audit_required": p.audit_required,
        "audit_fail_closed": p.audit_fail_closed,
        "telemetry_required": p.telemetry_required,
        "identity_required": p.identity_required,
        "identity_roles": list(p.identity_roles),
        "secrets_redact": p.secrets_redact,
        "secrets_forbid_era": p.secrets_forbid_era,
        "secrets_scan_package": p.secrets_scan_package,
        "gates_eval_cage": p.gates_eval_cage,
        "gates_static_redteam": p.gates_static_redteam,
        "gates_deepteam_live": p.gates_deepteam_live,
        "audit_path": p.audit_path,
    }
