"""Optional Langfuse traces for each guarded agent.

Always keeps a small in-memory span log (workbench + tests).
Exports to Langfuse Cloud / self-host only when keys are set
and the `langfuse` package is installed.

  pip install -e ".[observability]"
  export LANGFUSE_PUBLIC_KEY=...
  export LANGFUSE_SECRET_KEY=...
  export LANGFUSE_BASE_URL=https://cloud.langfuse.com   # optional

Missing SDK or keys → no-op. The eval cage does not require Langfuse.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

_SPANS: list[dict[str, Any]] = []
_MAX = 80
_current: ContextVar[str | None] = ContextVar("grant_obs_run", default=None)
_client: Any = None
_kind: str | None = None  # "otel" | "v2" | "none"
_tried = False

_DEFAULT_HOST = "https://cloud.langfuse.com"


def _host() -> str:
    return (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or _DEFAULT_HOST
    ).rstrip("/")


def enabled() -> bool:
    if os.environ.get("LANGFUSE_ENABLED", "").lower() in ("0", "false", "no"):
        return False
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def _clip(value: Any, limit: int = 1800) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        try:
            text = json.dumps(value, default=str)
        except Exception:
            text = str(value)
    else:
        text = str(value)
    if len(text) > limit:
        return text[:limit] + "…"
    if isinstance(value, (dict, list)):
        return value
    return text


def _sdk():
    global _client, _kind, _tried
    if _tried:
        return _client
    _tried = True
    if not enabled():
        _kind = "none"
        return None
    os.environ.setdefault("LANGFUSE_HOST", _host())
    os.environ.setdefault("LANGFUSE_BASE_URL", _host())
    try:
        from langfuse import get_client  # v3 / v4

        _client = get_client()
        _kind = "otel" if hasattr(_client, "start_as_current_observation") else "v2"
        return _client
    except Exception:
        pass
    try:
        from langfuse import Langfuse  # v2

        _client = Langfuse()
        _kind = "v2"
        return _client
    except Exception:
        _kind = "none"
        _client = None
        return None


def reset_spans() -> None:
    _SPANS.clear()


def get_spans() -> list[dict[str, Any]]:
    return list(_SPANS)


def status() -> dict[str, Any]:
    if enabled():
        _sdk()
    return {
        "langfuse": {
            "enabled": enabled() and _kind not in (None, "none"),
            "configured": enabled(),
            "sdk": _kind or ("pending" if enabled() else "none"),
            "host": _host(),
        },
        "run_id": _current.get(),
        "spans": get_spans()[-12:],
    }


def flush() -> None:
    client = _client
    if not client:
        return
    try:
        client.flush()
    except Exception:
        pass


def _record(name: str, **fields: Any) -> dict[str, Any]:
    rec = {"name": name, **fields, "ts": time.time()}
    _SPANS.append(rec)
    if len(_SPANS) > _MAX:
        del _SPANS[: len(_SPANS) - _MAX]
    return rec


def _start_remote(name: str, *, metadata: dict | None, input: Any):
    client = _sdk()
    if not client or _kind in (None, "none"):
        return None, None
    meta = dict(metadata or {})
    try:
        if _kind == "otel":
            cm = client.start_as_current_observation(as_type="span", name=name)
            span = cm.__enter__()
            try:
                span.update(input=_clip(input), metadata=meta)
            except Exception:
                pass
            return cm, span
        if _kind == "v2":
            span = client.span(name=name, input=_clip(input), metadata=meta)
            return None, span
    except Exception:
        return None, None
    return None, None


def _end_remote(cm, span, *, output: Any, level: str, metadata: dict | None) -> None:
    try:
        if span is None:
            return
        if _kind == "otel":
            payload: dict[str, Any] = {"output": _clip(output)}
            if level and level != "DEFAULT":
                payload["level"] = level
            if metadata:
                payload["metadata"] = metadata
            try:
                span.update(**payload)
            except Exception:
                pass
            if cm is not None:
                cm.__exit__(None, None, None)
        elif _kind == "v2":
            kwargs: dict[str, Any] = {"output": _clip(output)}
            if level == "ERROR":
                kwargs["level"] = "ERROR"
            span.end(**kwargs)
    except Exception:
        pass


@contextmanager
def trace_run(
    name: str = "grant-pipeline",
    *,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Parent observation for one invoke / resume / harness case."""
    meta = {
        "session_id": session_id,
        "tags": tags or ["grant-agent-lab"],
        **(metadata or {}),
    }
    rec = _record(name, kind="run", metadata=meta, status="running")
    token = _current.set(session_id or name)
    cm, span = _start_remote(name, metadata=meta, input={"session_id": session_id})
    t0 = time.perf_counter()
    try:
        yield rec
        rec["status"] = "ok"
        rec["ms"] = round((time.perf_counter() - t0) * 1000)
        _end_remote(cm, span, output={"status": "ok"}, level="DEFAULT", metadata=meta)
    except Exception as exc:
        rec["status"] = "error"
        rec["error"] = str(exc)
        rec["ms"] = round((time.perf_counter() - t0) * 1000)
        _end_remote(cm, span, output={"error": str(exc)}, level="ERROR", metadata=meta)
        raise
    finally:
        _current.reset(token)
        flush()


@contextmanager
def observe_agent(
    agent_name: str,
    action: str,
    *,
    metadata: dict[str, Any] | None = None,
    input: Any = None,
) -> Iterator[dict[str, Any]]:
    """One span per control-plane guard() call (each agent)."""
    name = f"{agent_name}.{action}"
    meta = {"agent": agent_name, "action": action, "run": _current.get(), **(metadata or {})}
    rec = _record(name, kind="agent", agent=agent_name, action=action, metadata=meta)
    cm, span = _start_remote(name, metadata=meta, input=input)
    t0 = time.perf_counter()
    try:
        yield rec
        rec["ms"] = round((time.perf_counter() - t0) * 1000)
        rec.setdefault("status", "ok")
        level = rec.get("level") or "DEFAULT"
        _end_remote(cm, span, output=rec.get("output"), level=level, metadata=meta)
    except Exception as exc:
        rec["ms"] = round((time.perf_counter() - t0) * 1000)
        rec.setdefault("status", "error")
        rec.setdefault("level", "ERROR")
        rec.setdefault("error", str(exc))
        rec.setdefault("output", {"error": str(exc)})
        _end_remote(cm, span, output=rec.get("output"), level=rec.get("level") or "ERROR", metadata=meta)
        raise


def score_case(grade: dict[str, Any] | None) -> None:
    """Attach harness pass/fail to the current Langfuse trace (best-effort)."""
    if not grade:
        return
    _record(
        "harness.grade",
        kind="score",
        passed=grade.get("passed"),
        failed=grade.get("failed"),
        status="ok" if not grade.get("failed") else "fail",
    )
    client = _sdk()
    if not client:
        return
    passed = not grade.get("failed")
    try:
        if hasattr(client, "create_score"):
            client.create_score(name="harness_passed", value=1 if passed else 0, comment=str(grade.get("failed") or "ok"))
        elif hasattr(client, "score"):
            client.score(name="harness_passed", value=1 if passed else 0)
    except Exception:
        pass
