# Governance profiles — local vs production

Two profiles share the same GrantGraph. **Local** is the lightweight lab default. **Production** fail-closes: policy, audit evidence, telemetry, identity, secrets, and selected eval/red-team gates are mandatory.

```bash
# default (config/runtime.yaml)
profile: local

# production (env wins)
export GRANT_PROFILE=production
export GRANT_ACTOR=ada.lovelace
export GRANT_ROLE=PI
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export GRANT_AUDIT_LOG=/var/log/grant-agent/audit.jsonl

PYTHONPATH=. python3 -m src.harness profile
PYTHONPATH=. python3 -m src.harness preflight          # cheap start checks
PYTHONPATH=. python3 -m src.harness preflight --gates  # + weak aims + static red-team
```

YAML: [`config/profiles/local.yaml`](../config/profiles/local.yaml) · [`config/profiles/production.yaml`](../config/profiles/production.yaml).

## What is mandatory where

| Control | Local | Production |
|---------|-------|------------|
| Policy `guard()` ALLOW / DENY / ASK | On | On, cannot skip |
| NIH ASSIST / invented budget / auto `PI_CERTIFY` | DENY | DENY |
| HITL before freeze / office submit | ASK | ASK |
| Audit JSONL | Best-effort | **Required, fail-closed** |
| Actor on every audit event | If present | **GRANT_ACTOR + GRANT_ROLE required** |
| Langfuse spans | Optional (keys) | **Required** (or `GRANT_TELEMETRY_STUB=1` for CI) |
| eRA / NIH ASSIST passwords in env | Forbidden | Forbidden (start fails) |
| Secret-like strings in ORA package | Not scanned | **Refuse to package** |
| Eval cage `weak_aims_vague` | CI | **Release gate** (`preflight --gates`) |
| Static red-team probes (goal hijack) | CI | **Release gate** |
| Live DeepTeam | Optional | Off (non-deterministic) |

Production does **not** change the product path: packet still ends at the Office of Research Aid database.

## Identity

Roles: `PI` · `Navigator` · `Office of Research Aid` · `Admin`.

```bash
export GRANT_ACTOR=pi-netid
export GRANT_ROLE=PI
```

`guard(..., actor=..., role=...)` also satisfies the check. Missing identity under production raises `IdentityRequired` before the agent runs.

## Secrets

- Never put eRA Commons passwords in this process (`ERA_PASSWORD`, `ERA_COMMONS_PASSWORD`, `NIH_ASSIST_PASSWORD`).
- Audit and traces redact `password` / `api_key` / `sk-…` / `Bearer …`.
- Production packaging scans the excerpt and refuses secret-like payloads.
- Keys live in gitignored `.env` or a secret manager — not in YAML.

## Telemetry

Production requires Langfuse keys so every `guard()` call is a span ([observability.md](observability.md)). CI may set `GRANT_TELEMETRY_STUB=1` to prove the gate without exporting.

## Release gates

`preflight --gates` (and the GitHub Actions `production-preflight` job) runs:

1. Runtime ready (identity, telemetry, audit path, no eRA passwords).
2. Eval cage: `weak_aims_vague` must not freeze.
3. Static red-team: NIH ASSIST jailbreak / budget invention / eRA leak probes must not open ASSIST.

Live DeepTeam remains optional and is **not** a production gate.

## Code

| Piece | Path |
|-------|------|
| Profiles | `src/control_plane/profile.py` |
| Identity | `src/control_plane/identity.py` |
| Secrets | `src/control_plane/secrets.py` |
| Preflight / gates | `src/control_plane/gates.py` |
| Enforcement | `guard()` · `GrantGraph.invoke/resume` · `create_office_package` |
