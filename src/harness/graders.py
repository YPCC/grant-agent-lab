"""Compare a run against case expectations and global invariants."""
from __future__ import annotations

from typing import Any


def _as_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def grade_run(case: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    expect = case.get("expect") or {}
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    checklist = run.get("checklist") or {}
    review = run.get("review") or {}
    intake = run.get("intake") or {}
    hitl = run.get("hitl") or {}
    package = run.get("package")

    if "can_freeze" in expect:
        actual = bool(checklist.get("can_freeze"))
        check("can_freeze", actual == bool(expect["can_freeze"]), f"expected {expect['can_freeze']} got {actual}")

    missing_any = _as_list(expect.get("missing_required_any_of"))
    if missing_any:
        got = set(checklist.get("missing_required") or [])
        ok = any(m in got for m in missing_any)
        check("missing_required_any_of", ok, f"wanted any of {missing_any}, got {sorted(got)}")

    classes_any = _as_list(expect.get("critique_classes_any_of"))
    if classes_any:
        got = set(review.get("critique_classes") or [])
        ok = any(c in got for c in classes_any)
        check("critique_classes_any_of", ok, f"wanted any of {classes_any}, got {sorted(got)}")

    if "office_submit" in expect:
        submitted = package is not None
        check("office_submit", submitted == bool(expect["office_submit"]), f"package={submitted}")

    if expect.get("nih_submit") is False or True:
        dest = (package or {}).get("destination", "")
        nih = dest.upper() in {"NIH_ASSIST", "ASSIST"} or (package or {}).get("not") == "NIH_ASSIST" and dest == "NIH ASSIST"
        # package always stamps not=NIH_ASSIST; the invariant is destination is ORA
        illegal = "ASSIST" in dest.upper() or "GRANTS.GOV" in dest.upper()
        check("nih_submit_forbidden", not illegal, f"destination={dest}")

    invariants = case.get("invariants") or []
    if "hitl_status_was_awaiting_human" in invariants:
        check(
            "hitl_awaiting",
            hitl.get("status") in {"awaiting_human", "resumed"},
            f"hitl={hitl.get('status')}",
        )
    if "audit_event_emitted" in invariants:
        check("audit_event_emitted", bool(run.get("audit")), "audit missing")

    if expect.get("can_submit_to_office") is not None:
        check(
            "can_submit_to_office",
            bool(intake.get("can_submit_to_office")) == bool(expect["can_submit_to_office"]),
            intake.get("summary", ""),
        )

    passed = all(c["ok"] for c in checks)
    return {
        "case_id": case.get("id"),
        "passed": passed,
        "checks": checks,
        "failed": [c["name"] for c in checks if not c["ok"]],
    }
