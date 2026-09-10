"""Thin AGT-style control-plane façade.

Every critical agent / tool call should pass through `guard()`.
Policies from `src.harness.policies` (ALLOW / DENY / ASK) run here —
not only in the optional Omnigent YAML.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.harness.policies import evaluate

logger = logging.getLogger("grant_agent_lab.control_plane")

_KILL_SWITCH = False
_AUDIT_LOG: list[dict[str, Any]] = []
_AUDIT_FILE = Path("output/audit_log.jsonl")


class PolicyDenied(PermissionError):
    """DENY from the policy stack (e.g. NIH ASSIST)."""


class PolicyAsk(PermissionError):
    """ASK: a human must approve before this action proceeds."""


def set_kill_switch(value: bool) -> None:
    global _KILL_SWITCH
    _KILL_SWITCH = value
    logger.warning("Kill switch set to %s", value)


def is_kill_switch_active() -> bool:
    return _KILL_SWITCH


def _emit_audit(event: dict[str, Any]) -> None:
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    _AUDIT_LOG.append(event)
    try:
        _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_FILE.open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.debug("Could not write audit file: %s", exc)


def get_audit_log() -> list[dict[str, Any]]:
    return list(_AUDIT_LOG)


def guard(
    agent_name: str,
    action: str,
    fn: Callable[..., Any],
    *args: Any,
    trust_tier: str = "standard",
    human_approved: bool = False,
    **kwargs: Any,
) -> Any:
    """Mediate a call: kill-switch, ALLOW/DENY/ASK, audit, then fn."""
    if is_kill_switch_active():
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "blocked",
            "reason": "kill_switch",
            "trust_tier": trust_tier,
        })
        raise RuntimeError(f"Control plane kill-switch active – blocked {agent_name}.{action}")

    event = {
        "type": "tool_call",
        "target": action,
        "data": {
            "name": action,
            "arguments": {"agent": agent_name, "human_approved": human_approved},
        },
    }
    verdict = evaluate(event) or {"result": "ALLOW"}
    result = verdict.get("result") or "ALLOW"
    reason = verdict.get("reason") or ""

    if result == "DENY":
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "denied",
            "reason": reason,
            "trust_tier": trust_tier,
        })
        raise PolicyDenied(reason or f"{agent_name}.{action} denied")

    if result == "ASK" and not human_approved:
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "ask",
            "reason": reason,
            "trust_tier": trust_tier,
        })
        raise PolicyAsk(reason or f"{agent_name}.{action} requires HITL")

    _emit_audit({
        "agent": agent_name,
        "action": action,
        "result": "allowed",
        "trust_tier": trust_tier,
        "human_approved": human_approved,
    })

    try:
        out = fn(*args, **kwargs)
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "success",
            "trust_tier": trust_tier,
        })
        return out
    except Exception as exc:
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "error",
            "error": str(exc),
            "trust_tier": trust_tier,
        })
        raise
