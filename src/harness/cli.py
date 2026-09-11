"""CLI for Copilot / any LLM tool that shells out instead of MCP."""
from __future__ import annotations

import argparse
import sys

from src.harness import __version__
from src.harness.cases import list_cases, load_case
from src.harness.checklist import evaluate_checklist
from src.harness.intake import fill_intake
from src.harness.knowledge import list_packs, load_pack
from src.harness.review import review_text
from src.harness.runner import dumps, run_case, run_pipeline


def _read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        return open(args.file, encoding="utf-8").read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide --text, --file, or stdin")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="grant-harness",
        description="Grant Agent Lab eval harness — MCP/CLI plugin. Office of Research Aid only.",
    )
    p.add_argument("--version", action="version", version=f"grant-harness {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list-cases")
    sub.add_parser("list-packs")
    sub.add_parser("mcp", help="MCP stdio server for Copilot / Cursor / Claude / Omnigent")

    s = sub.add_parser("run-case")
    s.add_argument("case_id")
    s.add_argument("--package", action="store_true")

    s = sub.add_parser("review")
    s.add_argument("--text")
    s.add_argument("--file")
    s.add_argument("--mechanism", default="R01")

    s = sub.add_parser("checklist")
    s.add_argument("--text")
    s.add_argument("--file")

    s = sub.add_parser("intake")
    s.add_argument("--text")
    s.add_argument("--file")
    s.add_argument("--filename", default="proposal.docx")

    s = sub.add_parser("run")
    s.add_argument("--text")
    s.add_argument("--file")
    s.add_argument("--mechanism", default="R01")
    s.add_argument("--filename", default="proposal.docx")
    s.add_argument("--hitl", default="revise")
    s.add_argument("--package", action="store_true")

    s = sub.add_parser("pack")
    s.add_argument("name")

    s = sub.add_parser("redteam", help="Adversarial probes (static). --live uses DeepTeam if installed.")
    s.add_argument("--live", action="store_true")

    sub.add_parser("desktop", help="Open the desktop workbench (pywebview or browser)")
    sub.add_parser("profile", help="Print current governance profile (local | production)")
    s = sub.add_parser("preflight", help="Governance runtime checks; --gates runs eval cage + static red-team")
    s.add_argument("--gates", action="store_true")

    args = p.parse_args(argv)
    if args.cmd == "mcp":
        from src.harness.mcp_server import serve_stdio

        serve_stdio()
        return 0
    if args.cmd == "list-cases":
        print(dumps(list_cases()))
        return 0
    if args.cmd == "list-packs":
        print(dumps(list_packs()))
        return 0
    if args.cmd == "pack":
        print(dumps(load_pack(args.name)))
        return 0
    if args.cmd == "desktop":
        from src.desktop.app import main as desktop_main

        return desktop_main()
    if args.cmd == "profile":
        from src.control_plane.profile import as_dict

        print(dumps(as_dict()))
        return 0
    if args.cmd == "preflight":
        from src.control_plane.gates import preflight

        report = preflight(gates=args.gates)
        print(dumps(report))
        return 0 if report.get("passed") else 2
    if args.cmd == "redteam":
        from src.harness.redteam import run_deepteam, run_static_probes

        out = run_static_probes()
        if args.live:
            out["deepteam"] = run_deepteam()
        print(dumps(out))
        return 0 if out.get("passed") else 2
    if args.cmd == "run-case":
        result = run_case(load_case(args.case_id), allow_package=args.package or None)
        print(dumps(_public(result)))
        return 0 if result["grade"]["passed"] else 2
    text = _read_text(args)
    if args.cmd == "review":
        print(dumps(review_text(text, mechanism=args.mechanism)))
        return 0
    if args.cmd == "checklist":
        print(dumps(evaluate_checklist(text)))
        return 0
    if args.cmd == "intake":
        print(dumps(fill_intake(text, filename=args.filename)))
        return 0
    if args.cmd == "run":
        result = run_pipeline(
            text,
            mechanism=args.mechanism,
            filename=args.filename,
            hitl_script=[s.strip() for s in args.hitl.split(",") if s.strip()],
            allow_package=args.package,
        )
        print(dumps(_public(result)))
        return 0
    return 1


def _public(result: dict) -> dict:
    out = dict(result)
    if "intake" in out and "groups" in out["intake"]:
        slim = dict(out["intake"])
        slim.pop("groups", None)
        out["intake"] = slim
    return out


if __name__ == "__main__":
    raise SystemExit(main())
