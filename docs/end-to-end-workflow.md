# End-to-end workflow (to Office of Research Aid)

This path **stops at the office database**. It does not submit to NIH ASSIST.

1. **Draft / upload** – PI supplies an R01 DOCX (or the writer drafts Aims).
2. **Knowledge refresh** (optional) – Knowledge Updater pulls FOA / SF424 / RePORTER context.
3. **Mock study section** – Grant Reviewer + scientific-strategic-review-board lens.
4. **Compliance + budget scrutinizer** – NIH norms; presence of a budget element, not invented dollars.
5. **Missing Essentials** – required package items vs `r01_essentials.yaml`.
6. **Office intake form** – grouped Compliance / Formatting / Institutional questions, agent-filled from the document; PI overrides and certifies.
7. **HITL** – freeze / revise until required intake items are answered.
8. **Package creator** – versioned packet under `output/packages/<ORA-…>/`.
9. **Submit to Office of Research Aid** – upload to the office database.
10. **Tracking number** – `ORA-YYYYMMDD-xxxxxx` returned to the PI.

The control plane mediates every critical step and records an audit trail. Official NIH submit, if it happens later, is an office process outside this lab.
