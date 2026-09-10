# PI Workflow UI — NIH R01 (before implementation)

How a real PI works an R01, how the multi-agent system shows up in the UI, how **multiple documents** live in one proposal, how **RBAC** is visible, and how **submission** should work without a bot logging in unsupervised.

This is a product/UX spec. It is not an implementation.

---

## 1. Real-life R01 journey (what the UI must mirror)

An NIH R01 is not “open a chat and generate a grant.” In practice the PI moves through stages that last weeks to months, with other people and an institutional office in the loop.

| Stage | What happens on the ground | Who is in the room | What the product should show |
|-------|----------------------------|--------------------|------------------------------|
| **0. Signal** | Idea, preliminary data, FOA/NOSI, talk to colleagues / PO | PI | New proposal from FOA # + mechanism R01 |
| **1. Notify institution** | PI tells Office of Research Aid / SPS; gets **internal deadline** (earlier than NIH due date) | PI, Office of Research Aid | Internal deadline as the hard date; Office of Research Aid assigned |
| **2. Aims first** | Circulate a 1-page Specific Aims; iterate before writing 12 pages | PI, mentors, RA | Aims document + Writer + Reviewer agents |
| **3. Team & compliance early** | Co-Is, effort, COI, human subjects / animals flags | PI, dept admin | Checklist, not buried in chat |
| **4. Science draft** | Significance, Innovation, Approach; figures, pitfalls | PI, RA | Multi-doc workspace; section status |
| **5. Budget (parallel)** | Modular vs detailed; personnel months; justification tied to aims | PI + Office of Research Aid/admin | Budget **scrutinizer** (validate), not a silent planner |
| **6. Forms pack** | Biosketches, Other Support, Facilities, Resource Sharing, DMS | PI, RA, Office of Research Aid | Required-docs grid with missing flags |
| **7. Internal review** | Lab / department / mock study section | Reviewer role | Agent critique + human comments side by side |
| **8. Institutional routing** | PI completes office intake form; packaging agent uploads to office database; tracking # returns | PI + Office of Research Aid | Grouped intake; Submit to Office of Research Aid |
| **9. Official NIH submission** | **Out of this lab.** Office staff may later use ASSIST; agents never do. | Office of Research Aid (AOR) | Not implemented here |
| **10. After** | Validations, JIT, summary statement, resubmission | PI, Office of Research Aid | Status timeline; new version of same proposal |

The UI should feel like a **proposal workbench with a live agency layer**, not a chatbot that owns the grant.

---

## 2. Recommended product shape

**One web app, four role views** (same proposal, different permissions):

| View | Primary user | Job |
|------|----------------|-----|
| **Workbench** | Everyone | List of proposals I can see |
| **Proposal room** | PI / RA | Documents + agents + readiness |
| **Review queue** | Internal reviewer / Office of Research Aid | Findings, overrides, sign-off |
| **Admin / control plane** | Platform admin | Roles, kill-switch, audit |

Chat is a **pane inside the proposal room**, not the home screen. Grounding (“what FOA, what due date, what we know”) lives in a header the PI always sees.

---

## 3. Screens that show the real PI workflow

### 3.1 Workbench (home)

- Cards/rows: **multiple proposals** (e.g. “R01 auditory learning — Feb cycle”, “R21 pilot — June”).
- Each card: mechanism, FOA, NIH due date, **internal Office of Research Aid date**, readiness %, blockers, last agent run, my role.
- Actions: New proposal · Clone as resubmission · Open room.
- Filters: Mine / Shared with me / Awaiting my approval.

This is how a PI actually lives: more than one document set at a time.

### 3.2 New proposal (grounding)

Short form, not a blank chat:

- Mechanism = R01  
- FOA / NOSI number  
- Institute/Center (if known)  
- NIH due date + **Office of Research Aid internal deadline**  
- Working title + 3–5 sentence idea  
- Central hypothesis (optional at start)  
- Assign Navigator / Office of Research Aid specialist if known  

On save: Knowledge Updater pulls FOA summary + recent RePORTER context into a **Briefing** panel so the PI starts from ground truth.

### 3.3 Proposal room (the core UI)

Persistent chrome:

```
[R01] Working title                    NIH due  ·  INTERNAL due  ·  Ready 62%
FOA PA-XX-XXX  ·  Modular budget  ·  You are PI
[Documents] [Agents] [Compliance] [Budget] [Package] [Activity]
```

**Left: document tree** (multiple documents, one proposal)

- Specific Aims (v3) — In review  
- Research Strategy / Significance  
- Research Strategy / Innovation  
- Research Strategy / Approach  
- Bibliography  
- Budget justification  
- Biosketch — PI  
- Biosketch — Co-I  
- Other Support  
- Facilities  
- DMS plan  
- Letters / appendix (optional)

Each row: owner, version, status (`draft | agent-running | needs-PI | approved`), last compliance flags.

**Center: the open document**

- Editor or PDF viewer  
- Margin: agent annotations (rule id, severity, suggested fix)  
- Accept / dismiss / “ask writer to revise this span”

**Right: agent rail** (always visible)

- Now running: Reviewer (Approach)  
- Queue: Compliance · Budget scrutinizer  
- Last output: 1 major, 3 warnings  
- Buttons (RBAC-gated): Run review · Run compliance · Freeze for Office of Research Aid

**Bottom or tab: activity**

- Immutable timeline: who/what/when (human and agent).  
- This *is* the audit preview the PI can understand.

### 3.4 Compliance & readiness

Not a wall of logs. A scorecard:

- Blockers (cannot package)  
- Majors (Office of Research Aid will bounce)  
- Warnings  
- Each row cites **rule source** (SF424, modular budget, institutional SOP)

PI can request a waiver; only Office of Research Aid (or Admin policy) can grant it.

### 3.5 Budget tab

- Shows declared lines / effort / modular flag  
- Budget Scrutinizer results only (no silent invented dollars)  
- Links each line to an aim when present  

### 3.6 Package & submit (staged)

States the PI sees:

1. **Drafting** — agents may run  
2. **Ready for PI freeze** — PI locks science  
3. **Intake form** — Compliance / Formatting / Institutional, agent-filled, human override  
4. **Submitted to Office of Research Aid** — packaging agent uploaded the packet  
5. **Tracking number on PI record** (`ORA-…`)  
6. **In office review**  
7. **NIH transmit** — **out of this product**; office process only

The PI **does** click **Submit to Office of Research Aid** after the intake form is complete. There is no Submit to NIH in this UI.

---

## 4. Role-based access control (what to showcase)

Showcase RBAC by making it **visible in the chrome** (“You are PI”) and by disabling actions, not by hiding the whole app.

| Action | PI | RA / Navigator | Co-I | Internal reviewer | Office of Research Aid / AOR | Admin |
|--------|----|----------------|------|-------------------|------------|-------|
| Create proposal | Yes | If delegated | No | No | Yes | Yes |
| Edit science docs | Yes | Yes (if granted) | Own biosketch only | Comment only | Comment / request change | Break-glass |
| Run Writer / Reviewer | Yes | Yes | No | No | No | Yes |
| Run Compliance / Budget scrutinizer | Yes | Yes | No | Yes | Yes | Yes |
| Waive a blocker | Request | Request | No | No | **Yes** | Policy only |
| Freeze science / create package version | Yes | No | No | No | Yes | Yes |
| Complete office intake / override | Yes | Yes | No | No | Yes | Yes |
| Submit packet to Office of Research Aid database | **Yes** | If delegated | No | No | Yes | Yes |
| Transmit to NIH ASSIST / Grants.gov | No | No | No | No | **Out of lab** | No |
| View full audit | Own proposal | Own proposal | Limited | Assigned | Assigned + office | All |
| Kill-switch / disable an agent | No | No | No | No | No | **Yes** |
| Manage roles on a proposal | Yes (invite) | No | No | No | Yes | Yes |

**UI patterns that make RBAC real:**

- Role chip in the header.  
- **Submit to Office of Research Aid** enabled only when required intake items are answered.  
- Disabled NIH language: this lab never offers Submit to NIH.
- Share dialog: add person + role (PI, Co-I, Navigator, Reviewer, Office of Research Aid).  
- “Why can’t I click this?” always answers with role + policy, not a blank control.

---

## 5. How agents appear in the PI’s day (not a black box)

| Agent | When the PI sees it | What they do with it |
|-------|---------------------|----------------------|
| Knowledge Updater | Briefing panel on open / refresh | Read FOA + similar funded work; not auto-rewrite science |
| Writer | “Draft / revise this section” | Accept, edit, or reject hunks |
| Reviewer | After a section is stable | Treat like a mock study section; decide what to fix |
| Compliance | Continuous + on Freeze | Fix blockers before bothering Office of Research Aid |
| Budget Scrutinizer | Budget tab | Fix effort / modular / aim linkage |
| Package Creator | After intake complete | Versioned packet + upload to office database |
| Intake agent | After review | Fills Compliance / Formatting / Institutional form |

Agent runs should be **jobs on a document**, with progress and a diff—not a hidden background rewrite of the only copy.

---

## 6. Office submit — design it so it is real and safe

**Do not** ship “the agent logs into eRA and clicks NIH Submit.”

This lab’s submit is **to the Office of Research Aid database**.

```
Intake agent fills form from the DOCX
    → PI / Navigator overrides unknowns and certifies
    → Package Creator writes output/packages/<ORA-…>/
    → Packet uploaded to Office of Research Aid database
    → Tracking number returned to the PI
```

What it *may* do:

- Assemble MANIFEST, intake JSON, findings, excerpt  
- Require every required intake item to be answered  
- Return `ORA-YYYYMMDD-xxxxxx` onto the PI record  

What it must not do:

- Store NIH/eRA passwords  
- Call ASSIST / Grants.gov  
- Bypass the intake form  

Demo: CopilotKit + workbench show this path. See [intake and office submit](../intake-and-office-submit.md).

---

## 7. Multi-document mental model

One **Proposal** has many **Documents**; agents run on documents or on the whole package.

```
Proposal  PR-2026-014  (R01, FOA PA-XX)
 ├─ Docs[]        versioned, owned, statused
 ├─ Agents[]      runs tied to doc or package
 ├─ Findings[]    compliance + critiques
 ├─ Budget        scrutinizer input/output
 ├─ Package       snapshot + tag when frozen
 └─ Members[]     user + role
```

The workbench lists proposals. The room lists documents. That matches how PIs juggle Aims vs Strategy vs biosketches vs a second grant.

---

## 8. Minimal click-path to demo “real R01 life”

1. PI creates “R01 — synaptic basis of auditory learning.”  
2. Sets NIH date and earlier Office of Research Aid date.  
3. Invites RA (Navigator) and Office of Research Aid specialist.  
4. Pastes idea; Knowledge Updater fills Briefing.  
5. Writer drafts Aims; PI edits.  
6. Reviewer returns one major (aims not independent). PI accepts a revise.  
7. PI uploads a budget justification; Scrutinizer flags missing PI person-months.  
8. Compliance still open: DMS plan missing. RA adds a stub; flag clears.  
9. PI completes the **office intake form** (agent-filled; overrides + PI certify).  
10. PI clicks **Submit to Office of Research Aid**. Packaging agent uploads.  
11. Tracking number `ORA-…` appears on the PI record.  
12. Activity log shows every agent + the office ingest event.

That path is the story. Build screens in that order. NIH ASSIST is not in this click-path.

---

## 9. What not to build first

- A global chat that mixes two grants in one thread  
- Auto-submit to production eRA  
- Budget generator that invents salaries  
- Hidden agent edits with no diff  
- RBAC only in the API (it must be visible in the UI)

---

## Related

- [End-to-end workflow](../end-to-end-workflow.md)
- [Discovery questions](architecture-discovery-questions.md) (users/UX + governance)
- [Selection framework](architecture-selection-framework.md)
- [Control plane](../control-plane-integration.md)
