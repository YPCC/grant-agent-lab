# Eval harness (in-lab feature)

The eval cage lives **in this repo**, not in a sibling package.

- Cases: `data/harness/cases/`
- Knowledge packs: `config/checklists/` + `config/policies/` + `data/harness/packs/`
- Runner / MCP / CLI: `src/harness/`
- Omnigent-compatible policies: `src/harness/policies.py` (ALLOW / DENY / ASK)
- Optional driver: `agents/grant-navigator.yaml`

```bash
PYTHONPATH=. python3 -m src.harness list-cases
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 -m src.harness mcp
```

Copilot / Cursor / Claude: copy `plugin/vscode/mcp.json`. Destination is Office of Research Aid only.

The archived sibling [YPCC/grant-agent-harness](https://github.com/YPCC/grant-agent-harness) points here.
