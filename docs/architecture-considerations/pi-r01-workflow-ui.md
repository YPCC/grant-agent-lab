# PI Workflow UI — NIH R01 (before implementation)

How a real PI works an R01, how the multi-agent system shows up in the UI, how **multiple documents** live in one proposal, how **RBAC** is visible, and how **submission** should work without a bot logging in unsupervised.

This is a product/UX spec. It is not an implementation.

---

## 1. Real-life R01 journey (what the UI must mirror)

An NIH R01 is not “open a chat and generate a grant.” In practice the PI moves through stages that last weeks to months, with other people and an institutional office in the loop.

| Stage | What happens on the ground | Who is in the room | What the product should show |
|-------|----------------------------|--------------------|------------------------------|
| **0. Signal** | Idea, preliminary data, FOA/NOSI, talk to colleagues / PO | PI | New proposal from FOA # + mechanism R01 |
| **1. Notify institution** | PI tells OSPA / SPS; gets **internal deadline** (earlier than NIH due date) | PI, OSPA | Internal deadline as the hard date; OSPA assigned |
| **2. Aims first** | Circulate a 1-page Specific Aims; iterate before writing 12 pages | PI, mentors, RA | Aims document + Writer + Reviewer agents |
| **3. Team & compliance early** | Co-Is, effort, COI, human subjects / animals flags | PI, dept admin | Checklist, not buried in chat |
| **4. Science draft** | Significance, Innovation, Approach; figures, pitfalls | PI, RA | Multi-doc workspace; section status |
| **5. Budget (parallel)** | Modular vs detailed; personnel months; justification tied to aims | PI + OSPA/admin | Budget **scrutinizer** (validate), not a silent planner |
| **6. Forms pack** | Biosketches, Other Support, Facilities, Resource Sharing, DMS | PI, RA, OSPA | Required-docs grid with missing flags |
| **7. Internal review** | Lab / department / mock study section | Reviewer role | Agent critique + human comments side by side |
| **8. Institutional routing** | OSPA package review, F&A, signatures | OSPA | Reviewer portal; PI cannot “submit NIH” yet |
| **9. Official submission** | **AOR / OSPA** submits via ASSIST / Grants.gov | OSPA (AOR) | Staged submit; human authenticates |
| **10. After** | Validations, JIT, summary statement, resubmission | PI, OSPA | Status timeline; new version of same proposal |

The UI should feel like a **proposal workbench with a live agency layer**, not a chatbot that owns the grant.

---

## 2. Recommended product shape

**One web app, four role views** (same proposal, different permissions):

| View | Primary user | Job |
|------|----------------|-----|
| **Workbench** | Everyone | List of proposals I can see |
| **Proposal room** | PI / RA | Documents + agents + readiness |
| **Review queue** | Internal reviewer / OSPA | Findings, overrides, sign-off |
| **Admin / control plane** | Platform admin | Roles, kill-switch, audit |

Chat is a **pane inside the proposal room**, not the home screen. Grounding (“what FOA, what due date, what we know”) lives in a header the PI always sees.

---

## 3. Screens that show the real PI workflow

### 3.1 Workbench (home)

- Cards/rows: **multiple proposals** (e.g. “R01 auditory learning — Feb cycle”, “R21 pilot — June”).
- Each card: mechanism, FOA, NIH due date, **internal OSPA date**, readiness %, blockers, last agent run, my role.
- Actions: New proposal · Clone as resubmission · Open room.
- Filters: Mine / Shared with me / Awaiting my approval.

This is how a PI actually lives: more than one document set at a time.

### 3.2 New proposal (grounding)

Short form, not a blank chat:

- Mechanism = R01  
- FOA / NOSI number  
- Institute/Center (if known)  
- NIH due date + **OSPA internal deadline**  
- Working title + 3–5 sentence idea  
- Central hypothesis (optional at start)  
- Assign Navigator / OSPA specialist if known  

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
- Buttons (RBAC-gated): Run review · Run compliance · Freeze for OSPA

**Bottom or tab: activity**

- Immutable timeline: who/what/when (human and agent).  
- This *is* the audit preview the PI can understand.

### 3.4 Compliance & readiness

Not a wall of logs. A scorecard:

- Blockers (cannot package)  
- Majors (OSPA will bounce)  
- Warnings  
- Each row cites **rule source** (SF424, modular budget, institutional SOP)

PI can request a waiver; only OSPA (or Admin policy) can grant it.

### 3.5 Budget tab

- Shows declared lines / effort / modular flag  
- Budget Scrutinizer results only (no silent invented dollars)  
- Links each line to an aim when present  

### 3.6 Package & submit (staged)

States the PI sees:

1. **Drafting** — agents may run  
2. **Ready for PI freeze** — PI locks science  
3. **Ready for OSPA** — package built (version tag)  
4. **In institutional review**  
5. **Approved to transmit**  
6. **Submitted** (ASSIST / Grants.gov tracking #)  
7. **Post-submit** (errors / JIT)

The “submit” button is **not** a single red button for the PI on an R01 in an OSPA institution.

---

## 4. Role-based access control (what to showcase)

Showcase RBAC by making it **visible in the chrome** (“You are PI”) and by disabling actions, not by hiding the whole app.

| Action | PI | RA / Navigator | Co-I | Internal reviewer | OSPA / AOR | Admin |
|--------|----|----------------|------|-------------------|------------|-------|
| Create proposal | Yes | If delegated | No | No | Yes | Yes |
| Edit science docs | Yes | Yes (if granted) | Own biosketch only | Comment only | Comment / request change | Break-glass |
| Run Writer / Reviewer | Yes | Yes | No | No | No | Yes |
| Run Compliance / Budget scrutinizer | Yes | Yes | No | Yes | Yes | Yes |
| Waive a blocker | Request | Request | No | No | **Yes** | Policy only |
| Freeze science / create package version | Yes | No | No | No | Yes | Yes |
| Mark “approved for institutional submit” | No | No | No | No | **Yes** | No |
| Transmit to ASSIST / Grants.gov | No* | No | No | No | **Yes (AOR)** | No |
| View full audit | Own proposal | Own proposal | Limited | Assigned | Assigned + office | All |
| Kill-switch / disable an agent | No | No | No | No | No | **Yes** |
| Manage roles on a proposal | Yes (invite) | No | No | No | Yes | Yes |

\*Some institutions allow PI-as-AOR in rare setups. Default for MCC/OSPA: **No**.

**UI patterns that make RBAC real:**

- Role chip in the header.  
- Disabled Submit with tooltip: “OSPA AOR submits after institutional approval.”  
- Share dialog: add person + role (PI, Co-I, Navigator, Reviewer, OSPA).  
- “Why can’t I click this?” always answers with role + policy, not a blank control.

---

## 5. How agents appear in the PI’s day (not a black box)

| Agent | When the PI sees it | What they do with it |
|-------|---------------------|----------------------|
| Knowledge Updater | Briefing panel on open / refresh | Read FOA + similar funded work; not auto-rewrite science |
| Writer | “Draft / revise this section” | Accept, edit, or reject hunks |
| Reviewer | After a section is stable | Treat like a mock study section; decide what to fix |
| Compliance | Continuous + on Freeze | Fix blockers before bothering OSPA |
| Budget Scrutinizer | Budget tab | Fix effort / modular / aim linkage |
| Package Creator | After PI freeze + no blockers | Produces versioned packet + evidence |
| Submission assistant | Only after OSPA approval | See section 6 |

Agent runs should be **jobs on a document**, with progress and a diff—not a hidden background rewrite of the only copy.

---

## 6. Submission agent — design it so it is real and safe

**Do not** ship “the agent logs into eRA with stored PI passwords and clicks Submit.”

Reasons: AOR authority, credential policy, MFA, audit, and irreversible sponsor actions.

### Recommended pattern (showcase-able and honest)

```
Package Creator
    → versioned packet in GCS + Cloud SQL manifest
    → OSPA reviews in Review queue
    → AOR authenticates to ASSIST / Grants.gov (human SSO / MFA)
    → Submission assistant pre-fills forms and attachments
    → AOR confirms a Submit checklist
    → System records tracking number + timestamp + actor
```

Call the component a **Submission assistant**, not an autonomous submitter.

What it *may* do after approval:

- Map package files to ASSIST attachment slots  
- Validate file names, page counts, and required forms  
- Open a guided checklist beside the official site  
- Optionally use a **browser automation session the AOR has already logged into** (user-present), never a vaulted password replay  
- Write back status (accepted / validation errors / tracking ID)

What it must not do in v1:

- Store NIH/eRA passwords  
- Submit without an identified AOR action in the audit log  
- Bypass OSPA because the PI is in a hurry  

If a demo needs theater: show a **simulated ASSIST** screen in the lab with a fake tracking number, labeled **demo only**, and the same RBAC rules.

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
2. Sets NIH date and earlier OSPA date.  
3. Invites RA (Navigator) and OSPA specialist.  
4. Pastes idea; Knowledge Updater fills Briefing.  
5. Writer drafts Aims; PI edits.  
6. Reviewer returns one major (aims not independent). PI accepts a revise.  
7. PI uploads a budget justification; Scrutinizer flags missing PI person-months.  
8. Compliance still open: DMS plan missing. RA adds a stub; flag clears.  
9. PI clicks **Freeze for OSPA**. Package v1 appears. Submit stays disabled for PI.  
10. OSPA role logs in, sees Review queue, waives nothing, **Approves to transmit**.  
11. AOR starts Submission assistant → checklist → (demo) tracking #.  
12. Activity log shows every agent + the AOR submit event.

That path is the story. Build screens in that order.

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
