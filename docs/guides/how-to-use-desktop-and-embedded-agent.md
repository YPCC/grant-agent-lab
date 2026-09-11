# How to use the desktop app and the embedded agent

Two ways to run **the same** GrantGraph (review → Missing Essentials → intake → HITL → Office of Research Aid package). Neither submits to NIH ASSIST.

| You want | Start here |
|----------|------------|
| A window on your laptop (PI / Navigator) | [Part 1 — desktop app](#part-1--desktop-app) |
| Grok, Copilot, Cursor, or Claude calling the graph | [Part 2 — embedded agent (MCP + skill)](#part-2--embedded-agent-mcp--skill) |
| Your own Python / notebook | [Part 3 — embed in code](#part-3--embed-in-code) |

Invariants in every path: **ORA only**, no invented budget dollars, HITL before freeze, `PI_CERTIFY` is human-only.

---

## Part 1 — Desktop app

### Install and launch

```bash
cd grant-agent-lab
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[desktop]"
pip install python-docx

python -m src.desktop
# same thing:
grant-harness desktop
```

A native window opens (pywebview). If pywebview is missing, the system browser opens `http://127.0.0.1:<port>/`.

**Vertex Gemini (optional narrative, not the freeze gate):**

```bash
pip install -e ".[desktop,vertex]"
export GOOGLE_CLOUD_PROJECT=your-gcp-project
gcloud auth application-default login
export GRANT_LLM_PROVIDER=vertex
export GRANT_LLM_MODEL=gemini-2.5-flash
python -m src.desktop
```

Or use the in-app **Settings** tab (provider / model / project / location). Keys stay in the environment, not in the form. Details: [desktop-and-llm.md](../desktop-and-llm.md).

### What you should see

Header chips: **You are PI** · **Langfuse off/on** · **LLM none|vertex|…**

Three tabs:

1. **Review & intake** — documents, findings, Missing Essentials, ORA form.
2. **Harness** — eval cases on the same graph (`weak_aims_vague` must not freeze).
3. **Settings** — LLM backend.

### Walkthrough (sample Aims)

1. Leave role on **PI**. Click **Run graph on sample**.
2. Read **Agent findings** (GPA + SSRB) and **Missing essentials**. Weak/sample drafts show gaps; **Submit** stays disabled until required intake is complete.
3. Override any intake row (Compliance / Formatting / Institutional). `PI_CERTIFY` is human-only — the agent will not check it for you.
4. **HITL: approve freeze** when the checklist can freeze. Then **Submit to Office of Research Aid**.
5. A tracking number `ORA-YYYYMMDD-xxxxxx` appears. That is the only submit destination.
6. Open **Harness** → `weak_aims_vague`. Expect `can_freeze: false` and `nih_assist: false`.

Optional: **Upload .docx** instead of the sample. Copilot-style chat rail: “Review this draft” / “NIH ASSIST” (the latter is denied).

### LLM narrative

If Settings → provider is `vertex` (or gemini / openai / xai) and Test connection succeeds, the next **Run graph** may append an **LLM · vertex · gemini-2.5-flash** block under findings. Checklist freeze does **not** change. CI uses `provider: none`.

---

## Part 2 — Embedded agent (MCP + skill)

The graph stays in this repo. Grok / Copilot / Cursor / Claude only **drive** it over MCP (stdio), the same pattern as a Grok skill or `npx` MCP wrapper.

### One-time: run the MCP server

From the repo root (so catalogs resolve):

```bash
cd grant-agent-lab
PYTHONPATH=. python3 -m src.harness mcp
```

Or after `pipx install 'grant-agent-lab @ git+https://github.com/YPCC/grant-agent-lab.git'`:

```bash
grant-harness mcp
```

Leave that process running, or point the host at the command (stdio).

### Copilot / VS Code / Cursor

Merge [`plugin/vscode/mcp.json`](../../plugin/vscode/mcp.json) (Cursor: [`plugin/cursor/mcp.json`](../../plugin/cursor/mcp.json)):

```json
{
  "servers": {
    "grant-agent-harness": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "src.harness", "mcp"]
    }
  }
}
```

Run the IDE from the repo directory (`PYTHONPATH=.`) or switch `command` to `grant-harness` after pipx.

Copilot plugin metadata: [`plugin/github-copilot/plugin.json`](../../plugin/github-copilot/plugin.json).

### Grok Build / Grok Desktop

1. Copy [`plugin/grok/.mcp.json`](../../plugin/grok/.mcp.json) into the Grok MCP config.
2. Put [`skills/grant-agent-harness/SKILL.md`](../../skills/grant-agent-harness/SKILL.md) on the skill path (`~/.grok/skills/` or the project skill folder).
3. Ask Grok: *Review this Specific Aims page with the grant harness. Do not submit to NIH ASSIST.*

The skill is instructions. MCP is the tools. The graph is still Part B.

### Claude Desktop

Snippet: [`plugin/claude-desktop/claude_desktop_config.snippet.json`](../../plugin/claude-desktop/claude_desktop_config.snippet.json). Restart Claude Desktop after merging.

### Tools the host can call

| Tool | Does |
|------|------|
| `grant_harness_list_cases` | Bundled YAML cases |
| `grant_harness_run_case` | Grade a case (e.g. `weak_aims_vague`) |
| `grant_harness_review_text` | GPA + SSRB review |
| `grant_harness_score_checklist` | Missing Essentials |
| `grant_harness_fill_intake` | ORA intake; `PI_CERTIFY` stays human |
| `grant_harness_run` | Full pipeline + scripted HITL. Never NIH ASSIST. |

Try in chat: *Run case weak_aims_vague* → expect cannot freeze. *Review this aims text…* → paste a draft.

### What embedding is not

- Not a second graph in the LLM.
- Not permission to file Grants.gov / ASSIST (`guard()` DENY).
- Not a place to store eRA passwords.
- Production: point MCP at the Cloud Run **backend**, not `python3` on a laptop ([packaging-and-deploy.md](../packaging-and-deploy.md)).

---

## Part 3 — Embed in code

Same nodes as desktop and MCP:

```python
from src.part_b_langgraph.graph import build_graph

g = build_graph()
s = g.invoke(
    {"text": open("data/samples/weak_aims_vague.txt").read(), "filename": "aims.txt"},
    {"configurable": {"thread_id": "demo"}},
)
assert s["hitl"]["status"] == "awaiting_human"
s = g.resume("demo", "revise")
```

CLI (no UI):

```bash
PYTHONPATH=. python3 -m src.harness review --file data/samples/weak_aims_vague.txt
PYTHONPATH=. python3 -m src.harness run-case weak_aims_vague
PYTHONPATH=. python3 -m src.harness preflight
```

---

## If something looks wrong

| Symptom | Check |
|---------|--------|
| Window does not open | `pip install -e ".[desktop]"` or use the printed `http://127.0.0.1:…` URL |
| Submit disabled | Required intake incomplete, or freeze not approved |
| LLM chip says `none` | Settings / `GRANT_LLM_PROVIDER`; Test connection |
| Vertex not ready | `GOOGLE_CLOUD_PROJECT` + `gcloud auth application-default login` |
| MCP tools missing | Host cwd is repo root; `PYTHONPATH=.` or pipx `grant-harness` |
| Case freezes a vague Aims | File an issue — that is a cage failure |

See also: [launch UI](how-to-launch-ui.md) · [desktop / LLM](../desktop-and-llm.md) · [harness](../harness.md) · [governance](../governance.md).
