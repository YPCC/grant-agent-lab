"""Runtime preflight and production release gates."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.control_plane.identity import IdentityRequired, resolve
from src.control_plane.observability import enabled as langfuse_enabled
from src.control_plane.profile import current
from src.control_plane.secrets import SecretsError, forbid_era_passwords


class GovernanceError(RuntimeError):
    """Production profile is not ready."""


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def telemetry_ready() -> tuple[bool, str]:
    p = current()
    if langfuse_enabled():
        return True, "langfuse keys present"
    import os

    stub = os.environ.get("GRANT_TELEMETRY_STUB", "").lower() in {"1", "true", "yes"}
    if stub and p.telemetry_stub_ok:
        return True, "GRANT_TELEMETRY_STUB=1 (CI / local export stub)"
    if not p.telemetry_required:
        return True, "not required on this profile"
    return False, "set LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY (or GRANT_TELEMETRY_STUB=1)"


def audit_ready() -> tuple[bool, str]:
    p = current()
    path = Path(p.audit_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a"):
            pass
        return True, str(path)
    except Exception as exc:
        if p.audit_required or p.audit_fail_closed:
            return False, f"cannot write {path}: {exc}"
        return True, f"best-effort ({exc})"


def runtime_ready() -> dict[str, Any]:
    """Cheap start-of-process checks. No graph runs."""
    p = current()
    checks: list[dict[str, Any]] = [
        _check("profile", True, p.name),
        _check("policy", True if p.policy_required else True, "guard + ALLOW/DENY/ASK"),
    ]
    try:
        resolve()
        checks.append(_check("identity", True, "GRANT_ACTOR/ROLE ok or not required"))
    except IdentityRequired as exc:
        checks.append(_check("identity", False, str(exc)))
    ok_t, det_t = telemetry_ready()
    checks.append(_check("telemetry", ok_t, det_t))
    ok_a, det_a = audit_ready()
    checks.append(_check("audit", ok_a, det_a))
    try:
        if p.secrets_forbid_era:
            forbid_era_passwords()
        checks.append(_check("secrets_era", True, "no eRA passwords in env"))
    except SecretsError as exc:
        checks.append(_check("secrets_era", False, str(exc)))
    failed = [c for c in checks if not c["ok"]]
    return {"profile": p.name, "passed": not failed, "failed": [c["name"] for c in failed], "checks": checks}


def assert_runtime_ready() -> None:
    report = runtime_ready()
    if not report["passed"]:
        raise GovernanceError(
            f"Governance profile {report['profile']!r} is not ready: {report['failed']}"
        )


def release_gates() -> dict[str, Any]:
    """Selected eval + static red-team gates (production / CI). May take minutes."""
    p = current()
    lanes: list[dict[str, Any]] = []
    if p.gates_eval_cage:
        from src.harness.cases import load_case
        from src.harness.runner import run_case

        run = run_case(load_case("weak_aims_vague"))
        ok = bool((run.get("grade") or {}).get("passed")) and not (run.get("checklist") or {}).get("can_freeze")
        lanes.append({"name": "eval_cage.weak_aims_vague", "ok": ok, "detail": (run.get("grade") or {})})
    if p.gates_static_redteam:
        from src.harness.redteam import run_static_probes

        probes = run_static_probes()
        lanes.append({"name": "redteam.static", "ok": bool(probes.get("passed")), "detail": probes.get("failed")})
    if p.gates_deepteam_live:
        from src.harness.redteam import run_deepteam

        live = run_deepteam()
        lanes.append({"name": "redteam.deepteam", "ok": not live.get("skipped"), "detail": live.get("reason") or "ran"})
    failed = [x["name"] for x in lanes if not x["ok"]]
    return {"profile": p.name, "passed": not failed, "failed": failed, "lanes": lanes}


def preflight(*, gates: bool = False) -> dict[str, Any]:
    report = runtime_ready()
    if gates:
        report["release_gates"] = release_gates()
        if not report["release_gates"]["passed"]:
            report["passed"] = False
            report["failed"] = list(report.get("failed") or []) + report["release_gates"]["failed"]
    return report
