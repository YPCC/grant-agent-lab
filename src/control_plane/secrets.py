"""Secrets handling: redact audit/traces, forbid eRA passwords, scan packets."""
from __future__ import annotations

import os
import re
from typing import Any

ERA_ENV = (
    "ERA_PASSWORD",
    "ERA_COMMONS_PASSWORD",
    "NIH_ASSIST_PASSWORD",
    "ERA_COMMONS_SECRET",
)

_SECRET_KEY = re.compile(
    r"(password|secret|api[_-]?key|token|authorization|passwd|private[_-]?key|era_commons)",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(?i)(sk-[a-z0-9]{8,}|api[_-]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+|bearer\s+[a-z0-9\-._]+)"
)

REDACTED = "***REDACTED***"


class SecretsError(PermissionError):
    """Production secrets invariant violated."""


def redact_value(key: str, value: Any) -> Any:
    if _SECRET_KEY.search(str(key)):
        return REDACTED
    if isinstance(value, str) and _SECRET_VALUE.search(value):
        return _SECRET_VALUE.sub(REDACTED, value)
    return value


def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in event.items():
        if isinstance(v, dict):
            out[k] = redact_event(v)
        elif isinstance(v, list):
            out[k] = [redact_event(x) if isinstance(x, dict) else redact_value(str(k), x) for x in v]
        else:
            out[k] = redact_value(k, v)
    return out


def forbid_era_passwords() -> None:
    present = [k for k in ERA_ENV if os.environ.get(k)]
    if present:
        raise SecretsError(
            "eRA / NIH ASSIST passwords must not be loaded into this process: " + ", ".join(present)
        )


def scan_text(text: str) -> list[str]:
    hits = []
    if not text:
        return hits
    if _SECRET_VALUE.search(text):
        hits.append("secret_like_value")
    low = text.lower()
    if "era commons password" in low or "era_password" in low:
        hits.append("era_password_mention")
    return hits


def assert_package_clean(text_excerpt: str) -> None:
    hits = scan_text(text_excerpt or "")
    if hits:
        raise SecretsError("Refusing to package: " + ", ".join(hits))
