# Architecture Discovery Questions

Questions to ask **before** selecting components for a multi-agent system. Use them in EA interviews, design reviews, and the [selection framework](architecture-selection-framework.md) (gates + scoring).

How to use:

- Ask in this order: mission → users/UX → agents → data → NFR → security/compliance → audit → control plane/governance → cost/ops.
- Mark each answer as **constraint** (must), **preference**, or **unknown**.
- Any **unknown** on a gate topic (security, compliance, audit, Office of Research Aid authority) blocks a production decision.
- Record answers next to the component decision record in the selection framework.

Context for *this* lab: MCC / GCP, Office of Research Aid–mediated grants, HITL, Cloud SQL + BigQuery already present. The list is written so it also works for other multi-agent platforms.

---

## 0. Mission and scope

1. What job must the system finish that a single chatbot cannot (e.g. draft → review → compliance → HITL → package)?
2. What is explicitly **out of scope** for v1 (e.g. official eRA submission, budget *planning*, clinical PHI)?
3. Who is the institutional authority that must remain in the loop (Office of Research Aid, IRB, sponsored programs)?
4. What does “done” mean (readiness score only vs versioned package ready for institutional review)?
5. Which funding mechanisms and sponsors are in scope (R01, R21, K, NSF, foundations)?
6. Is this a pilot, limited production, or enterprise service—and what changes at each stage?
7. What existing systems of record must we **not** replace (MIRIS, Cloud SQL, BigQuery, SSO)?

---

## 1. Users, journeys, and UI/UX

8. Who are the actors (PI, RA/Navigator, Office of Research Aid reviewer, Admin, auditor) and what is each allowed to *see* vs *do*?
9. What is the primary surface: web portal, chat, both, API-only for some roles?
10. How many distinct UIs are justified (Intake, Reviewer, Navigator, Admin) vs one app with role views?
11. Where must a human stop the agent (approve aims, waive a finding, approve package)?
12. What does the user need on screen to trust a finding (rule citation, excerpt, severity, suggested fix)?
13. How should competing agent outputs be shown (single merged report vs per-agent panels)?
14. What is the expected time-to-first-result vs time-to-final-package?
15. Do we need accessibility, offline drafts, or mobile review for Office of Research Aid?
16. How are errors and “agent uncertain” states presented so users do not treat drafts as submitted truth?
17. Who owns UX copy when the agent is wrong—product, Office of Research Aid, or scientific lead?

---

## 2. Functional capabilities (what agents and tools must do)

18. Which capabilities are mandatory in v1 (map to C1–C16 in the selection framework)?
19. Which work is **deterministic rules** vs **LLM judgment** (page limits and modular ceiling vs critique quality)?
20. Do we generate text, only validate text, or both—and for which sections?
21. Must the Budget component *plan* numbers or only *scrutinize* an existing budget?
22. How does knowledge stay current (FOA, SF424, salary cap, RePORTER)—scheduled, on-demand, or both?
23. What inputs arrive as files vs structured fields vs links?
24. What outputs must be durable (package folder, evidence JSON, MIRIS-ready bundle)?
25. How many revision loops are allowed before we force HITL stop?
26. Do agents need tools (RePORTER, Document AI, SQL, email) or only prompts?
27. Is citation/reference integrity in scope (bib-audit) for v1?
28. Multi-proposal / multi-PI in v1, or single proposal thread only?

---

## 3. Multi-agent design

29. What is the unit of agency (one orchestrator + specialists vs peer agents)?
30. What is the **shared contract** between agents (`ProposalState` fields, events, artifacts)?
31. Which agent is allowed to mutate which fields (writer vs compliance vs package)?
32. How are conflicts resolved when Reviewer and Compliance disagree?
33. Synchronous graph vs event-driven mesh vs mixed?
34. Where is LangGraph required (loops, reducers, checkpoints) vs where a single `LlmAgent` is enough?
35. How is ADK used (identity, deploy, A2A) vs inner graph (science loop)?
36. Can a new agent be added without rewriting the orchestrator (see how-to-add-agent)?
37. What happens if one specialist fails—retry, skip, or halt the package?
38. Do agents call each other directly or only through the orchestrator / control plane?
39. Is there an agent marketplace / skill versioning requirement?

---

## 4. Data, state, and integration

40. What data already exists (Cloud SQL, BigQuery, GCS, MIRIS) and who owns it?
41. What is system of record vs cache vs analytics vs checkpoint?
42. How long must drafts, packages, and checkpoints be retained?
43. What is the maximum document size and page count we must parse?
44. Do we need a semantic index (FOA, guidelines, similar grants) in v1?
45. Which external APIs are required (RePORTER, eRA, SSO, email, MIRIS)?
46. What is the integration style (sync API, Pub/Sub, batch file drop)?
47. How do we version a package so Office of Research Aid can see “what was approved”?
48. Can we reconstruct a run from state + artifacts alone (time-travel)?

---

## 5. Non-functional (reliability, scale, UX performance)

49. Concurrent users and concurrent agent graphs at pilot vs year-1?
50. Latency budget for interactive chat vs overnight package build?
51. Availability target for portals vs for the orchestrator?
52. What is the failure domain if Vertex, Cloud SQL, or RePORTER is down?
53. Do we need multi-region or is a single approved region mandatory?
54. Scale-to-zero on FE vs min instances for reviewer SLA?
55. Token and iteration caps per proposal so cost and latency stay bounded?
56. Accessibility, localization, or branding constraints from the institution?

---

## 6. Security

57. What is the data classification of proposal text, biosketches, Other Support, and budgets?
58. Is any PHI or other regulated clinical data in scope? If yes, stop and re-scope.
59. Which identity system is mandatory (institutional SSO / IAP)?
60. How are roles mapped to IAM (PI vs Navigator vs Office of Research Aid vs Admin vs auditor)?
61. Service-to-service identity: workload identity or long-lived keys?
62. Where do model and API secrets live (Secret Manager only)?
63. Network: VPC, private SQL/Redis, restricted egress allow-list?
64. Encryption: CMEK required? In transit and at rest for GCS, SQL, traces?
65. Prompt injection and tool-abuse: what can an agent *not* call even if the model asks?
66. Can agents write to production MIRIS / eRA, or only to a staging handoff?
67. DLP on logs, traces, and eval sets?
68. Who can export a full package out of the org?

---

## 7. Compliance

69. Which frameworks apply (HIPAA pathway, HITRUST, institutional research-admin policy, NIH GPS)?
70. Is a BAA (or equivalent) required for every vendor that sees prompt text?
71. Data residency: which region / org is allowed? Cross-region training use forbidden?
72. Must we honor Office of Research Aid **internal** deadlines as the hard stop (not the NIH due date)?
73. Which NIH rules must be machine-checkable in v1 (page limits, modular ceiling, PI effort, DMS plan present)?
74. How do we update rules when NOT-OD notices change without a code freeze?
75. COI / Other Support / Common Forms: generate, validate, or only remind?
76. Are we allowed to use proposal text to evaluate or fine-tune models?
77. Retention and legal hold for packages and audit logs?
78. What evidence does sponsored programs need at institutional review?

---

## 8. Auditability

79. What must be reconstructable after the fact: inputs, prompts, tool calls, model ids, outputs, human overrides?
80. Is the audit log append-only and tamper-evident?
81. Do we store full prompts or hashes + pointers (G9 hygiene)?
82. Can an auditor filter by proposal, agent, user, and rule id?
83. Are HITL approve / waive / reject first-class audit events?
84. Is every compliance flag tied to a **cited rule source** (NIH GPS, FOA, institutional SOP)?
85. Do packages include an evidence bundle (`critiques`, `compliance_issues`, `audit_log`)?
86. How long are traces retained vs operational logs vs package artifacts?
87. Who is allowed to replay a run, and does replay use the same model version?

---

## 9. Control plane and multi-agent governance

88. Is there a single **control plane** distinct from the execution plane (policy, identity, kill-switch, audit)?
89. Does every agent and tool call pass through `guard()` (or equivalent) before side effects?
90. What privilege rings exist (read-only retrieve vs write package vs call external submit)?
91. Who can flip the kill-switch, and does it halt in-flight graphs safely?
92. How is an agent identified (name, version, skill hash, trust tier)?
93. Can we disable one agent (e.g. Writer) without taking down Compliance?
94. What is the policy engine (static YAML, Rego, LiteGovernor, ADK policy)—and who edits it?
95. Are there rate limits and budget limits per agent and per tenant?
96. How do we prevent recursive or runaway agent-to-agent calls?
97. Is A2A / agent mesh in scope, and what trust model applies between agents?
98. How are new agents onboarded (review, fingerprint, least privilege, test suite)?
99. How are skills/prompts versioned and rolled back if quality or a policy regresses?
100. Who is accountable when an agent output is used in an official submission packet—the PI, Office of Research Aid, or the platform owner?
101. What is the incident response path for a bad agent action (revoke package tag, notify Office of Research Aid, freeze skill)?
102. Do we need separation of duties (the person who edits rules cannot approve production rollout alone)?

---

## 10. Observability, evaluation, and quality governance

103. What traces must exist per node (Langfuse / Cloud Trace / both)?
104. How do we evaluate Writer vs Reviewer vs Compliance separately?
105. What golden set (public Aims, Summary Statements) gates a release?
106. Who signs off that a new prompt is fit for Office of Research Aid-facing use?
107. How is model drift detected after a Vertex model upgrade?
108. Are eval datasets allowed to contain real proposals?

---

## 11. Cost, tokens, and operability

109. Expected packages per month and tokens per package (draft + review + loops)?
110. Which jobs may use a frontier model vs a small/flash model vs **no model** (rules)?
111. What is the iteration cap and the user-visible cost-to-date?
112. Who pays (research IT, department, grant)? Chargeback needed?
113. What is the on-call model for Cloud Run, SQL, Vertex, and the graph?
114. How many people-hours per month to maintain FOA rules and skills?
115. What is the exit plan if ADK, LangGraph, or the model vendor changes terms?

---

## 12. Decision questions (close the workshop)

116. Which options **failed a gate** and are off the table?
117. What is the recommended runtime (Part A / B / C) and why in one sentence?
118. What is the system of record for metadata, files, checkpoints, and analytics?
119. What will we explicitly **not** build in v1?
120. What is the review date or trigger to re-ask these questions (volume ×3, new NIH notice, new model)?

---

## Mapping to the selection framework

| Question block | Framework use |
|----------------|---------------|
| 0–2 Mission, UX, function | Capability map C1–C16 |
| 3 Multi-agent design | Runtime matrix (ADK / LangGraph / hybrid) |
| 4 Data | Data-store matrix; keep Cloud SQL + BigQuery |
| 5 NFRs | Cloud Run FE vs BE; scale and SLA |
| 6–7 Security & compliance | Gates G1–G10 (pass/fail) |
| 8–9 Audit, control plane, governance | Control plane + AGT-style guard; evidence bundle |
| 10 Eval | Quality gate before production prompts |
| 11 Cost | TCO = Infra + Tokens + People + Risk |
| 12 Close | Decision record template |

---

## Related

- [Architecture component selection framework](architecture-selection-framework.md)
- [Architecture considerations](README.md)
- [Control plane](../control-plane-integration.md)
- [How to add an agent](../guides/how-to-add-agent.md)
