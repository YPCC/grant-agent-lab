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

from src.control_plane.identity import resolve
from src.control_plane.observability import observe_agent
from src.control_plane.profile import current
from src.control_plane.secrets import redact_event
from src.harness.policies import evaluate

logger = logging.getLogger("grant_agent_lab.control_plane")

_KILL_SWITCH = False
_AUDIT_LOG: list[dict[str, Any]] = []


class PolicyDenied(PermissionError):
    """DENY from the policy stack (e.g. NIH ASSIST)."""


class PolicyAsk(PermissionError):
    """ASK: a human must approve before this action proceeds."""


class AuditError(RuntimeError):
    """Production audit log could not be written."""


def set_kill_switch(value: bool) -> None:
    global _KILL_SWITCH
    _KILL_SWITCH = value
    logger.warning("Kill switch set to %s", value)


def is_kill_switch_active() -> bool:
    return _KILL_SWITCH


def _audit_path() -> Path:
    return Path(current().audit_path)


def _emit_audit(event: dict[str, Any]) -> None:
    p = current()
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    event.setdefault("profile", p.name)
    if p.secrets_redact:
        event = redact_event(event)
    _AUDIT_LOG.append(event)
    try:
        path = _audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:
        logger.debug("Could not write audit file: %s", exc)
        if p.audit_fail_closed or p.audit_required:
            raise AuditError(f"Audit write failed under profile {p.name}: {exc}") from exc


def get_audit_log() -> list[dict[str, Any]]:
    return list(_AUDIT_LOG)


def guard(
    agent_name: str,
    action: str,
    fn: Callable[..., Any],
    *args: Any,
    trust_tier: str = "standard",
    human_approved: bool = False,
    actor: str | None = None,
    role: str | None = None,
    **kwargs: Any,
) -> Any:
    """Mediate a call: identity, kill-switch, ALLOW/DENY/ASK, audit, Langfuse span, then fn."""
    ident = resolve(actor, role)
    meta = {
        "trust_tier": trust_tier,
        "human_approved": human_approved,
        "actor": ident["actor"],
        "role": ident["role"],
        "profile": current().name,
    }
    with observe_agent(agent_name, action, metadata=meta, input={"agent": agent_name, "action": action}) as obs:
        if is_kill_switch_active():
            _emit_audit({
                "agent": agent_name,
                "action": action,
                "result": "blocked",
                "reason": "kill_switch",
                "trust_tier": trust_tier,
                **ident,
            })
            obs["status"] = "blocked"
            obs["level"] = "ERROR"
            obs["output"] = {"reason": "kill_switch"}
            raise RuntimeError(f"Control plane kill-switch active – blocked {agent_name}.{action}")

        event = {
            "type": "tool_call",
            "target": action,
            "data": {
                "name": action,
                "arguments": {
                    "agent": agent_name,
                    "human_approved": human_approved,
                    "actor": ident["actor"],
                    "role": ident["role"],
                },
            },
        }
        verdict = evaluate(event) or {"result": "ALLOW"}
        result = verdict.get("result") or "ALLOW"
        reason = verdict.get("reason") or ""
        obs["verdict"] = result

        if result == "DENY":
            _emit_audit({
                "agent": agent_name,
                "action": action,
                "result": "denied",
                "reason": reason,
                "trust_tier": trust_tier,
                **ident,
            })
            obs["status"] = "denied"
            obs["level"] = "ERROR"
            obs["output"] = {"reason": reason}
            raise PolicyDenied(reason or f"{agent_name}.{action} denied")

        if result == "ASK" and not human_approved:
            _emit_audit({
                "agent": agent_name,
                "action": action,
                "result": "ask",
                "reason": reason,
                "trust_tier": trust_tier,
                **ident,
            })
            obs["status"] = "ask"
            obs["level"] = "WARNING"
            obs["output"] = {"reason": reason}
            raise PolicyAsk(reason or f"{agent_name}.{action} requires HITL")

        _emit_audit({
            "agent": agent_name,
            "action": action,
            "result": "allowed",
            "trust_tier": trust_tier,
            "human_approved": human_approved,
            **ident,
        })

        try:
            out = fn(*args, **kwargs)
            _emit_audit({
                "agent": agent_name,
                "action": action,
                "result": "success",
                "trust_tier": trust_tier,
                **ident,
            })
            obs["status"] = "ok"
            obs["output"] = _safe_out(out)
            return out
        except Exception as exc:
            _emit_audit({
                "agent": agent_name,
                "action": action,
                "result": "error",
                "error": str(exc),
                "trust_tier": trust_tier,
                **ident,
            })
            obs["status"] = "error"
            obs["level"] = "ERROR"
            obs["output"] = {"error": str(exc)}
            raise


def _safe_out(out: Any) -> Any:
    if out is None or isinstance(out, (bool, int, float, str)):
        return out
    if isinstance(out, dict):
        keys = list(out.keys())[:12]
        slim: dict[str, Any] = {"keys": keys}
        for k in ("summary", "can_freeze", "can_submit_to_office", "fatal_or_major", "tracking_number", "destination"):
            if k in out:
                slim[k] = out[k]
        return slim
    return type(out).__name__
