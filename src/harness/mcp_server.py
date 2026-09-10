"""Minimal MCP stdio server for Copilot, Cursor, Claude, and Omnigent MCP tools."""
from __future__ import annotations

import json
import sys
from typing import Any

from src.harness import __version__
from src.harness.cases import list_cases, load_case
from src.harness.checklist import evaluate_checklist
from src.harness.intake import fill_intake
from src.harness.knowledge import list_packs, load_pack
from src.harness.review import review_text
from src.harness.runner import run_case, run_pipeline

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "grant-agent-harness"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "grant_harness_list_cases",
        "description": "List bundled eval cases (good/weak aims, HITL, incomplete package, complete ORA packet).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "grant_harness_run_case",
        "description": "Run a named case and return the grade. Does not submit to NIH.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "allow_package": {"type": "boolean"},
            },
            "required": ["case_id"],
        },
    },
    {
        "name": "grant_harness_review_text",
        "description": "Deterministic mock study-section review (GPA + SSRB issue classes).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "mechanism": {"type": "string", "default": "R01"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "grant_harness_score_checklist",
        "description": "Score Missing Essentials against config/checklists/r01_essentials.yaml.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "grant_harness_fill_intake",
        "description": "Fill Office of Research Aid intake. PI_CERTIFY stays human-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "filename": {"type": "string", "default": "proposal.docx"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "grant_harness_run",
        "description": "Full pipeline: knowledge, review, checklist, intake, HITL. Never NIH ASSIST.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "mechanism": {"type": "string", "default": "R01"},
                "filename": {"type": "string", "default": "proposal.docx"},
                "hitl_script": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["revise", "approve", "waive"]},
                },
                "allow_package": {"type": "boolean", "default": False},
            },
            "required": ["text"],
        },
    },
    {
        "name": "grant_harness_get_knowledge",
        "description": "Return a versioned knowledge pack.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "enum": [
                        "r01_essentials",
                        "ora_intake",
                        "sf424",
                        "gpa_core_questions",
                        "ssrb_issue_classes",
                        "invariants",
                        "reporter_frozen",
                    ],
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "grant_harness_list_packs",
        "description": "List knowledge packs.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _call_tool(name: str, arguments: dict[str, Any] | None) -> Any:
    args = arguments or {}
    if name == "grant_harness_list_cases":
        return list_cases()
    if name == "grant_harness_list_packs":
        return list_packs()
    if name == "grant_harness_run_case":
        result = run_case(load_case(args["case_id"]), allow_package=args.get("allow_package"))
        result.get("intake", {}).pop("groups", None)
        return result
    if name == "grant_harness_review_text":
        return review_text(args["text"], mechanism=args.get("mechanism") or "R01")
    if name == "grant_harness_score_checklist":
        return evaluate_checklist(args["text"])
    if name == "grant_harness_fill_intake":
        form = fill_intake(args["text"], filename=args.get("filename") or "proposal.docx")
        form.pop("groups", None)
        return form
    if name == "grant_harness_run":
        result = run_pipeline(
            args["text"],
            mechanism=args.get("mechanism") or "R01",
            filename=args.get("filename") or "proposal.docx",
            hitl_script=args.get("hitl_script") or ["revise"],
            allow_package=bool(args.get("allow_package")),
        )
        result.get("intake", {}).pop("groups", None)
        return result
    if name == "grant_harness_get_knowledge":
        return load_pack(args["name"])
    raise ValueError(f"Unknown tool: {name}")


def _handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    mid = msg.get("id")
    method = msg.get("method")
    if method is None:
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
                "instructions": (
                    "Grant Agent Lab eval harness. Review/checklist/intake before claiming ready. "
                    "Destination is Office of Research Aid — never NIH ASSIST."
                ),
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        try:
            result = _call_tool(name, params.get("arguments") or {})
            text = json.dumps(result, indent=2, default=str)
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "result": {"content": [{"type": "text", "text": text}], "isError": False},
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                    "isError": True,
                },
            }
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def _read_message(stdin) -> dict[str, Any] | None:
    header = {}
    while True:
        line = stdin.readline()
        if line == "":
            return None
        line = line.decode("utf-8") if isinstance(line, bytes) else line
        if line in ("\r\n", "\n"):
            break
        if ":" in line:
            k, _, v = line.partition(":")
            header[k.strip().lower()] = v.strip()
    n = int(header.get("content-length") or "0")
    if n <= 0:
        return None
    raw = stdin.read(n)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def _write_message(msg: dict[str, Any], stdout) -> None:
    blob = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    stdout.write(f"Content-Length: {len(blob)}\r\n\r\n".encode("utf-8"))
    stdout.write(blob)
    stdout.flush()


def serve_stdio() -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        try:
            msg = _read_message(stdin)
        except Exception:
            break
        if msg is None:
            break
        reply = _handle(msg)
        if reply is not None:
            _write_message(reply, stdout)
