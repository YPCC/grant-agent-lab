# Grok Build / Grok Desktop — Grant Agent driver

This is a **plugin-shaped driver**, not a second graph. The governed pipeline stays in this repo.

1. Install the CLI (pipx is the Python analog of `npx`):

   ```bash
   pipx install 'grant-agent-lab @ git+https://github.com/YPCC/grant-agent-lab.git'
   ```

2. Copy `.mcp.json` into the Grok plugin (or merge with `~/.grok` MCP config).

3. Keep [`skills/grant-agent-harness/SKILL.md`](../../skills/grant-agent-harness/SKILL.md) on the skill path.

Institutional install: point MCP at the Cloud Run BE instead of local `grant-harness`. See [packaging-and-deploy.md](../../docs/packaging-and-deploy.md).
