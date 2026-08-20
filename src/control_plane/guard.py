"""Thin AGT-style control-plane façade.

Every critical agent / tool call should pass through `guard()`.
This keeps policy, identity, kill-switch and audit in one place.
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("grant_agent_lab.control_plane")

# Simple in-memory / file-backed state for the lab
_KILL_SWITCH = False
_AUDIT_LOG: list[Dict[str, Any]] = []
_AUDIT_FILE = Path("output/audit_log.jsonl")


def set_kill_switch(value: bool) -> None:
    global _KILL_SWITCH
    _KILL_SWITCH = value
    logger.warning("Kill switch set to %s", value)


def is_kill_switch_active() -> bool:
    return _KILL_SWITCH


def _emit_audit(event: Dict[str, Any]) -> None:
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    _AUDIT_LOG.append(event)
    try:
        _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_FILE.open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.debug("Could not write audit file: %s", exc)


def guard(
    agent_name: str,
    action: str,
    fn: Callable[..., Any],
    *args: Any,
    trust_tier: str = "standard",
    **kwargs: Any,
) -> Any:
    """
    Mediate a call.

    - Checks kill-switch
    - Records identity / action
    - Emits audit event
    - (Future) can call LiteGovernor / ACS / Rego policies
    """
    if is_kill_switch_active():
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "blocked",
            "reason": "kill_switch",
            "trust_tier": trust_tier,
        })
        raise RuntimeError(f"Control plane kill-switch active – blocked {agent_name}.{action}")

    _emit_audit({
        "agent": agent_name,
        "action": action,
        "result": "allowed",
        "trust_tier": trust_tier,
    })

    try:
        result = fn(*args, **kwargs)
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "success",
            "trust_tier": trust_tier,
        })
        return result
    except Exception as exc:
        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "error",
            "error": str(exc),
            "trust_tier": trust_tier,
        })
        raise


def get_audit_log() -> list[Dict[str, Any]]:
    return list(_AUDIT_LOG)
