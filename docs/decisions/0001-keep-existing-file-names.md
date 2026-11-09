# 0001: Keep the existing document names

Date: 2026-11-08. Status: accepted.

Context: the standard names PROPOSAL.md, REPORT.md, experiments/ and
results/. This repo already has HYPOTHESES.md, RESEARCH.md, STUDY.md,
VALIDATION.md, MODEL_CARD.md, MONITORING.md, docs/analysis/ and data/,
and code reads them by name: site/src/model.check.mjs parses
HYPOTHESES.md and docs/analysis/GAP_ANALYSIS.md at build time,
scripts/export_dashboard_data.py parses RESEARCH.md and docs/analysis/,
and the generators write VALIDATION.md, MONITORING.md and STUDY.md
sections.

Decision: keep every one of those names and map each to its role in
the README layout table. Add PROPOSAL.md and REPORT.md as the entry
points. data/ plays the role of experiments/ (raw, immutable inputs,
hashed in results/run_manifest.json), so no experiments/ folder is
created.

Consequence: no parser changes, no broken links; a reader finds the
standard roles through the layout table.
