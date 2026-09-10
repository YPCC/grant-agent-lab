# Architecture (Mermaid)

GitHub renders these diagrams on the repo.

- **C4 infographics (posters):** [architecture-considerations/c4-infographics](architecture-considerations/c4-infographics/README.md)
- **Editable draw.io:** [architecture-considerations](architecture-considerations/README.md)

This lab’s submit path ends at the **Office of Research Aid database**. NIH ASSIST / Grants.gov is **out of band** (office staff, not the agents).

## C4 infographics

Canonical system context for this lab:

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
    UI[Workbench / CopilotKit UI]
    CP[Control plane<br/>guard · audit · kill-switch]
    ORCH[Orchestration<br/>path A / B / C]
  end

  subgraph Data
    SQL[(Cloud SQL)]
    BQ[(BigQuery)]
    GCS[Package store]
  end

  subgraph External
    NIH[NIH RePORTER / FOA]
    ODB[Office of Research Aid database]
  end

  PI --> UI
  RA --> UI
  ORA --> UI
  ADM --> CP
  UI --> CP
  CP --> ORCH
  ORCH --> SQL
  ORCH --> BQ
  ORCH --> GCS
  ORCH --> NIH
  PI -->|complete intake + submit| ODB
  ODB -->|tracking number| PI
```

## Agent graph (Part B default)

```mermaid
flowchart TD
  IN[DOCX / idea / FOA] --> KU[Knowledge Updater]
  KU --> WR[Grant Writer]
  WR --> RV[Grant Reviewer]
  RV --> CC[Compliance Checker]
  CC --> BS[Budget Scrutinizer]
  BS --> ME[Missing Essentials]
  ME --> IF[Intake form<br/>Compliance · Formatting · Institutional]
  IF --> HITL{HITL interrupt}

  HITL -->|revise| WR
  HITL -->|PI certify + required answered| PK[Package Creator]
  HITL -->|unknowns remain| IF

  PK --> ODB[Office of Research Aid database]
  ODB --> TRACK[Tracking number → PI]

  CP[Control plane] -.-> RV
  CP -.-> CC
  CP -.-> HITL
  CP -.-> PK
```

## Runtime paths

Same agents; different outer runtime. Switch with `path:` in [`config/runtime.yaml`](../config/runtime.yaml).

```mermaid
flowchart TB
  subgraph A["Part A — pure ADK 2.0"]
    ADK[ADK Workflow / LlmAgent]
  end
  subgraph B["Part B — pure LangGraph"]
    LG[StateGraph + MemorySaver<br/>or GrantGraph fallback]
  end
  subgraph C["Part C — hybrid"]
    ADK2[ADK outer]
    LG2[LangGraph inner loop]
    ADK2 --> LG2
  end

  CFG[config/runtime.yaml] --> A
  CFG --> B
  CFG --> C
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
    +checklist
    +intake
    +hitl
    +package_ready
    +tracking_number
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

Intake catalog: [`config/checklists/ora_intake.yaml`](../config/checklists/ora_intake.yaml). Narrative: [intake and office submit](intake-and-office-submit.md).

Color legend used in draw.io (same meaning as README): blue = ADK / UI, green = LangGraph nodes, yellow = knowledge, rose = HITL, purple = shared state.
