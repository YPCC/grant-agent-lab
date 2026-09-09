# Architecture (Mermaid)

GitHub renders these diagrams on the repo. Editable draw.io files live in [architecture-considerations](architecture-considerations/README.md).

## System context

Who talks to the lab. Official NIH submit stays with Office of Research Aid / AOR.

```mermaid
flowchart LR
  subgraph People
    PI[PI]
    RA[Navigator / RA]
    ORA["Office of Research Aid / AOR"]
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
    ASSIST[ASSIST / Grants.gov]
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
  ORA -.->|human SSO / MFA| ASSIST
```

## Agent graph (Part B default)

Deterministic scientific loop with HITL **before** freeze. Missing Essentials is a first-class node.

```mermaid
flowchart TD
  IN[Intake: idea / FOA / DOCX] --> KU[Knowledge Updater]
  KU --> WR[Grant Writer]
  WR --> RV[Grant Reviewer]
  RV --> CC[Compliance Checker]
  CC --> BS[Budget Scrutinizer]
  BS --> ME[Missing Essentials checklist]
  ME --> HITL{HITL interrupt<br/>PI / Office of Research Aid}

  HITL -->|revise| WR
  HITL -->|waive optional| HITL
  HITL -->|approve and checklist clear| PK[Package Creator]
  HITL -->|approve but required missing| WR

  PK --> READY[Institutional package ready]
  READY -.->|Office of Research Aid only| SA[Submission assistant<br/>AOR present]
  SA -.-> ASSIST[ASSIST tracking #]

  CP[Control plane] -.-> RV
  CP -.-> CC
  CP -.-> HITL
  CP -.-> SA
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

```mermaid
flowchart LR
  WB[Workbench] --> ROOM[Proposal room]
  ROOM --> DOCS[Document tree]
  ROOM --> RAIL[Agent rail + Copilot chat]
  ROOM --> CL[Checklist]
  ROOM --> HITL[HITL freeze]

  PI[Role PI] -->|edit / run agents / freeze| ROOM
  PI -.->|Submit disabled| X[No official NIH submit]
  ORA["Role Office of Research Aid"] -->|waive / approve transmit| ROOM
  ORA -->|Submit enabled demo| SA[Submission assistant]
```

## Shared state (conceptual)

```mermaid
classDiagram
  class ProposalState {
    +text
    +documents[]
    +findings[]
    +checklist
    +hitl
    +package_ready
    +decision
  }
  class ChecklistItem {
    +id
    +label
    +required
    +status
  }
  ProposalState "1" --> "*" ChecklistItem : missing_essentials
```

Color legend used in draw.io (same meaning as README): blue = ADK / UI, green = LangGraph nodes, yellow = knowledge, rose = HITL, purple = shared state.
