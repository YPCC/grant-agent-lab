# C4 infographics

Presentation-ready C4 views of Grant Agent Lab. Editable draw.io sources remain next to this folder. Mermaid lives in [architecture.md](../../architecture.md).

**Canonical for this lab:** the Office of Research Aid handoff (first image). The two triptychs are Level 1–3 C4 posters in a more generic grant-platform vocabulary (Qdrant / FastAPI / Next.js). Map those containers to this repo as:

| Infographic container | This lab |
|-----------------------|----------|
| Web Application (Next.js) | Workbench (`serve_workbench.py`) + CopilotKit (`ui-copilotkit/`) |
| API / Agent orchestrator | Path A ADK · Path B LangGraph · Path C hybrid + control plane |
| Agents (research / write / review) | Writer, Reviewer, Compliance, Budget scrutinizer, Intake, Package creator |
| Relational DB | Cloud SQL (PostgreSQL) |
| Vector store | Vertex Vector Search (prod) / local index (lab) |
| File storage | Package store (`output/packages/`, GCS in prod) |
| External data | NIH RePORTER / FOA only (read) |
| Official sponsor submit | **Out of band** — NIH ASSIST is office staff after ingest |

NIH ASSIST / Grants.gov is **not** a lab actor. Submit is to the **Office of Research Aid database**; a tracking number returns to the PI.

## Files

| File | C4 level | Use |
|------|----------|-----|
| [c4-system-context-office-handoff.jpg](c4-system-context-office-handoff.jpg) | Context (this lab) | Actors, workbench, control plane, stores, office DB + tracking |
| [c4-levels-1-2-3-grant-seeker.jpg](c4-levels-1-2-3-grant-seeker.jpg) | L1 + L2 + L3 poster | Generic grant-seeker / consultant / admin triptych |
| [c4-levels-1-2-3-researchers.jpg](c4-levels-1-2-3-researchers.jpg) | L1 + L2 + L3 poster | Researchers / grant-writers triptych |

### 1. System context — office handoff (canonical)

![Grant Agent Lab C4 system context](c4-system-context-office-handoff.jpg)

The platform prepares and validates the packet; **it does not submit to NIH**.

### 2. C4 Levels 1–3 — grant-seeker poster

![C4 Levels 1–3 grant-seeker](c4-levels-1-2-3-grant-seeker.jpg)

### 3. C4 Levels 1–3 — researchers poster

![C4 Levels 1–3 researchers](c4-levels-1-2-3-researchers.jpg)

Color meaning matches the lab legend: blue = UI / platform, green = agent runtime, yellow = knowledge, purple = shared state, rose = HITL, gray = external.
