# Datasets & Validation Resources

We use publicly available NIH (and related) resources for testing, validating, and demonstrating the multi-agent workflow. Full proposal text is used only where investigators have explicitly shared it; otherwise we work with abstracts + structured metadata.

## 1. Full Sample Applications (Gold Standard for Writer + Reviewer)

| Source | Content | Mechanisms | Notes |
|--------|---------|------------|-------|
| [NIAID Sample Applications](https://www.niaid.nih.gov/grants-contracts/sample-applications) | Complete funded applications + Summary Statements | R01, R03, R15, R21, K, F, U01, SBIR… | Best single source. Includes reviewer comments. |
| [NIDCD Sample Grant Applications](https://www.nidcd.nih.gov/funding/sample-grant-applications) | Full applications + Summary Statements | R01 primarily | Excellent Specific Aims examples. |
| [NIH Central Sample Hub](https://grants.nih.gov/grants-process/write-application/samples-applications-and-documents) | Index to institute samples | Multiple | Always start here for current links. |
| [NCI Behavioral / Epidemiology samples](https://cancercontrol.cancer.gov/brp/funding/sample-grant-applications) | ~15 R01/R03/R21 | Behavioral research | Useful for hybrid designs. |

**Usage in this lab**
- `data/samples/` will contain redacted or publicly shared excerpts (Specific Aims pages, selected Research Strategy paragraphs).
- Writer agent is evaluated by how closely its output structure matches successful patterns.
- Reviewer agent is evaluated against real Summary Statement critique styles.

## 2. Large-scale Structured Grant Data (for Knowledge Updater, Compliance, Analytics)

| Dataset | Size / Scope | Access | Primary Use |
|---------|--------------|--------|-------------|
| **NIH RePORTER / ExPORTER** | >1.2 M projects (1985–present) | [API](https://api.reporter.nih.gov) + bulk CSV | Abstracts, activity codes, study sections, funding amounts, PIs |
| NIH RePORTER Grant Dataset (Kaggle, 2017–2022) | Abstracts + metadata | Kaggle | Offline experimentation |
| Harmonised multi-funder grants (Zenodo 2025) | ~1.9 M records (NIH + NSF + UKRI + EC + …) | Zenodo | Cross-agency comparison |
| NIH-MPINet (Hugging Face) | Multi-PI collaboration network on R01-equivalents | HF | Team science features |
| NIH peer-review scoring dataset (Erosheva et al.) | ~5.8 k scored applications | CRAN / paper | Score distribution baselines |

**API tip**: Prefer the official RePORTER v2 API for live queries; respect rate limits (≈1 req/s, off-peak for bulk).

## 3. How we use these datasets inside the lab

1. **Writer evaluation** – Compare generated Specific Aims structure and language patterns against NIAID/NIDCD funded examples.
2. **Reviewer evaluation** – Check that the mock study-section output raises the same classes of issues that appear in real Summary Statements (aim dependency, missing controls, vague innovation, etc.).
3. **Compliance** – Page-limit and required-element rules are taken from current SF424 and FOA language; sample applications serve as positive/negative test cases.
4. **Knowledge Updater** – Periodically pulls new FOAs / NOSIs and abstracts from RePORTER to keep the guideline store fresh.
5. **End-to-end demos** – A small curated set of anonymized or public Specific Aims + Research Strategy excerpts live in `data/samples/` and drive the CI test suite.

## 4. Recommended starting test set (to be populated in `data/samples/`)

- 3–5 NIAID R01 Specific Aims pages (public)
- 2–3 corresponding Summary Statement excerpts (critique language)
- 1–2 R21 / K-series examples for mechanism variation
- Synthetic “intentionally flawed” aims (vague hypothesis, dependent aims) for negative testing

## 5. Legal / Ethical Notes

- Only use material that investigators or NIH institutes have explicitly made public.
- Never redistribute full proprietary proposal text.
- When citing a sample, always credit the original PI and institute page.
- For production institutional use, replace public samples with internal redacted historical proposals under appropriate data-use agreements.
