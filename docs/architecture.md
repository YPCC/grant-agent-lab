# Architecture (Mermaid)

GitHub renders these diagrams on the repo.

- **C4 infographics (posters + SVG):** [architecture-considerations/c4-infographics](architecture-considerations/c4-infographics/README.md)
- **Editable draw.io:** [architecture-considerations](architecture-considerations/README.md)

This lab’s submit path ends at the **Office of Research Aid database**. NIH ASSIST / Grants.gov is **out of band** (office staff, not the agents). **Harness cases, the workbench, and MCP all invoke the same Part B `GrantGraph`.**

## C4 infographics

Canonical system context for this lab (updated SVG — one pipeline + guard + MCP):

![C4 system context — unified](architecture-considerations/c4-infographics/c4-system-context-unified.svg)

![C4 containers — one pipeline](architecture-considerations/c4-infographics/c4-containers-one-pipeline.svg)

Office-handoff JPG (still valid for the submit contract):

![C4 system context — office handoff](architecture-considerations/c4-infographics/c4-system-context-office-handoff.jpg)

Level 1–3 posters (generic grant-platform vocabulary, mapped in the infographics README):

- [C4 L1–L3 — grant-seeker](architecture-considerations/c4-infographics/c4-levels-1-2-3-grant-seeker.jpg)
- [C4 L1–L3 — researchers](architecture-considerations/c4-infographics/c4-levels-1-2-3-researchers.jpg)

## C4 — system context (Mermaid)

Actors, the lab, stores, and the **office database** (NIH ASSIST is not a lab actor).

```mermaid
flowchart LR
  subgraph People
    PI[PI]
    RA[Navigator / RA]
    ORA["Office of Research Aid"]
    ADM[Platform admin]
  end

  subgraph Lab["Grant Agent Lab"]
    UI[Workbench :8080<br/>CopilotKit · Harness tab]
    MCP[MCP stdio<br/>python -m src.harness mcp]
    CP[Control plane<br/>ALLOW / DENY / ASK]
    G[Part B GrantGraph<br/>one pipeline]
  end

  subgraph Data
    SQL[(Cloud SQL)]
    BQ[(BigQuery)]
    GCS[Package store]
    CAT[Catalogs<br/>r01_essentials · ora_intake]
  end

  subgraph External
    NIH[NIH RePORTER / FOA<br/>read only]
    ODB[Office of Research Aid database]
    ASSIST[NIH ASSIST / Grants.gov<br/>OUT OF BAND]
  end

  PI --> UI
  RA --> UI
  PI --> MCP
  ORA --> UI
  ADM --> CP
  UI --> CP
  MCP --> CP
  CP --> G
  G --> SQL
  G --> BQ
  G --> GCS
  G --> CAT
  G --> NIH
  PI -->|complete intake + HITL approve| ODB
  ODB -->|tracking number| PI
  CP -.->|DENY| ASSIST
```

## C4 — containers (one pipeline)

```mermaid
flowchart TB
  PI[PI / Navigator] --> WB[Workbench :8080]
  PI --> MCP[MCP / Copilot / Cursor / Claude]
  WB --> G
  MCP --> G

  subgraph G["GrantGraph — src/part_b_langgraph"]
    KU[Knowledge]
    RV[Reviewer GPA+SSRB]
    ME[Missing Essentials]
    IN[ORA intake]
    HITL{HITL freeze}
    PK[Package creator]
    KU --> RV --> ME --> IN --> HITL
    HITL -->|revise| RV
    HITL -->|approve + complete| PK
  end

  CP[guard.py + policies.py] -.-> G
  CAT[config/checklists] -.-> ME
  CAT -.-> IN
  HARNESS[data/harness/cases] -->|run_case| G
  CI[GitHub Actions eval-cage] -.-> HARNESS
  PK --> ODB[Office of Research Aid database]
  CP -->|DENY| ASSIST[NIH ASSIST]
```

## Agent graph (Part B default — source of truth)

```mermaid
flowchart TD
  IN[DOCX / text / case YAML] --> KU[Knowledge Updater]
  KU --> RV[Grant Reviewer]
  RV --> ME[Missing Essentials]
  ME --> IF[Intake form<br/>Compliance · Formatting · Institutional]
  IF --> HITL{HITL interrupt}

  HITL -->|revise| RV
  HITL -->|PI certify + required answered| PK[Package Creator]
  HITL -->|unknowns remain| IF

  PK --> ODB[Office of Research Aid database]
  ODB --> TRACK[Tracking number → PI]

  CP[Control plane<br/>DENY ASSIST · ASK freeze] -.-> RV
  CP -.-> ME
  CP -.-> HITL
  CP -.-> PK
```

Writer / compliance / budget scrutinizer remain available on paths A and C. Path B default is the cage the CI gates.

## Runtime paths

Same catalogs and control plane; different outer runtime. Switch with `path:` in [`config/runtime.yaml`](../config/runtime.yaml). **Eval harness currently drives Part B `GrantGraph`.**

```mermaid
flowchart TB
  subgraph A["Part A — pure ADK 2.0"]
    ADK[ADK Workflow / LlmAgent]
  end
  subgraph B["Part B — pure LangGraph — CI default"]
    LG[GrantGraph invoke / resume]
  end
  subgraph C["Part C — hybrid"]
    ADK2[ADK outer]
    LG2[LangGraph inner loop]
    ADK2 --> LG2
  end

  CFG[config/runtime.yaml] --> A
  CFG --> B
  CFG --> C
  H[Harness / workbench / MCP] --> B
```

## UI and RBAC

PI **can** submit the packet to the office. Nobody in this lab submits to NIH.

```mermaid
flowchart LR
  WB[Workbench] --> ROOM[Proposal room]
  ROOM --> DOCS[Document tree]
  ROOM --> RAIL[Agent rail + Copilot chat]
  ROOM --> FORM[Intake form]
  ROOM --> HITL[HITL freeze]
  ROOM --> HARNESS[Harness tab]

  PI[Role PI] -->|edit / run agents / complete intake| ROOM
  PI -->|Submit to Office of Research Aid| ODB[Office database]
  ODB -->|tracking #| PI
  ORA["Role Office of Research Aid"] -->|review queue / waive| ROOM
```

## Shared state (conceptual)

```mermaid
classDiagram
  class ProposalState {
    +text
    +documents[]
    +findings[]
    +review
    +checklist
    +intake
    +hitl
    +package_ready
    +package
    +decision
  }
  class IntakeItem {
    +id
    +group
    +value
    +source agent|human
    +complete
  }
  ProposalState "1" --> "*" IntakeItem : ora_intake
```

Intake catalog: [`config/checklists/ora_intake.yaml`](../config/checklists/ora_intake.yaml). Narrative: [intake and office submit](intake-and-office-submit.md). Harness: [harness.md](harness.md). Guard: [control-plane-integration.md](control-plane-integration.md).

Color legend used in draw.io and SVG (same meaning as README): blue = UI / MCP, green = LangGraph nodes, yellow = knowledge / policy, rose = HITL, purple = shared catalogs.
