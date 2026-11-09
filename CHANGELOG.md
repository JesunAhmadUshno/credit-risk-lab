# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning; no release is tagged yet.

## [Unreleased]

### Changed
- 2026-11-08: Restructured to the portfolio standard v2. README is the
  abstract (question, headline with interval, field, job family,
  verdict, reproduce, lifecycle, layout). PROPOSAL.md replaces SPEC.md
  (moved unchanged) and points to HYPOTHESES.md. REPORT.md holds the
  former README body and the 2026-11-07 research review (formerly
  docs/research-review.md; its letter grades left the public repo).
  Verdict: Functional, not pre-registered (docs/decisions/0002).
- 2026-11-08: CI renamed from tests.yml to ci.yml with read-only token
  permissions: the full suite on Python 3.12 (the pinned freeze needs
  3.12), the standard checks on 3.11 (docs/decisions/0003), and a
  "reproduce" job that rebuilds every result from data/ and fails if
  any committed output differs. CodeQL (Python, JavaScript/TypeScript)
  and Dependabot (pip, npm for web/ and site/, GitHub Actions) added.

### Fixed
- 2026-11-08: Behavioural v2 results did not reproduce under the pinned
  requirements (found by the new CI rebuild). Regenerated with
  src/run_all.py: seed-42 v2 AUC 0.7799 (was 0.7818), 5-seed mean delta
  -0.0010 (was -0.0006); H3 stays INCONCLUSIVE, the single-seed "v2
  beats v1" claim is withdrawn. Fresh run_manifest.json; dated amendment
  appended to HYPOTHESES.md; REPORT.md section 7 gives the details.

### Added
- 2026-11-08: CITATION.cff, SECURITY.md, docs/decisions/ (0001 file
  names kept, 0002 not pre-registered, 0003 Python versions in CI),
  tests/test_layout.py (required files exist, no public grade).

### Open
- No LICENSE file: the code licence is the Owner's choice.
- Dataset licence text from the UCI pages is not yet recorded here.

## 2026-11-07
- Study cut-off targets the observed Stage 1 default rate (0.12444),
  not its 2-dp rounding; downstream results regenerated (d12cccb).
- Reason code "Low repayment ratio" only for positive balances (f2d1da1).
- Lab OS dashboard in site/, Pages builds web/ at the root and site/
  under /lab/; tests no longer overwrite results/ (c3f52d7 to c741d50).

## 2026-11-05
- Wave 3: pre-registered H1 to H4 (f5fb365), second-look policy,
  external validation, reason codes, rigor, database, analysis pack,
  one-command rebuild with manifest (fee580d, f3de8af); CI on 3.12.

## 2026-11-04
- First build: PD models, validation, IFRS 9 staging and ECL (d083dad);
  robustness pass, React dashboard, wave 2 (6d6af08 to d1a5024).
