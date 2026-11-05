# Gap register: credit-risk-lab

Numbered gaps found by audit (wave 3, 2026-11-04), each with a severity,
the fix applied in this wave, or OPEN with the reason it stays open.
Statuses were updated after the wave-3 runs; nothing here is marked
closed on intention alone.

## Seeded gaps (known before the wave)

**G1. Single development dataset.**
Severity: high. The lab's PD evidence rested on one population
(Taiwan, 2005). Fix applied: external validation on UCI Statlog German
Credit (src/external_validation.py: logistic AUC 0.8022, gradient
boosting 0.7848, both with bootstrap intervals), showing the method
transports to a second population and era. Status: PARTIALLY CLOSED.
Two public historical datasets are still not a Canadian portfolio, and
no artifact in this repo claims otherwise.

**G2. No database layer.**
Severity: medium. All outputs were flat JSON; nothing was queryable.
Fix applied: src/build_db.py builds data/credit.db (accounts, scores
for both models, staging, scenario staging, run metadata) and
sql/queries.sql carries four analytics queries; a wave-3 test asserts
the SQL staging counts and total ECL match results.json. Status:
CLOSED.

**G3. No adverse-action reason codes.**
Severity: medium. The lab could decline but could not say why, in the
plain language fair-lending practice expects. Fix applied:
src/reason_codes.py (permutation-importance-ranked drivers, documented
feature-to-reason mapping, top 3 per rejected applicant, demographic
attributes deliberately excluded from the vocabulary), with a contract
test. Labelled model-derived, not causal. Status: CLOSED.

**G4. No case studies.**
Severity: low. Numbers without narratives undersell the method and
hide its judgement calls. Fix applied: three number-grounded studies
in docs/case-studies/ (newcomer file, downside rehearsal, validation
meeting). Status: CLOSED.

**G5. Unpinned requirements.**
Severity: medium. requirements.txt named packages without versions;
results could drift with library releases. Fix applied: pinned to the
exact installed versions from the venv (full freeze). Status: CLOSED.

**G6. No clean-checkout reproducibility proof.**
Severity: high for a repo whose claim is "re-runnable". Fix applied:
src/run_all.py rebuilds the whole lab in one command, asserts the
headline invariants, and writes a hashed run manifest; the audit
(docs/analysis/AUDIT.md) ran that command in a fresh copy with a fresh
venv built from the pinned requirements and compared the outputs.
Status: CLOSED (outcome recorded in AUDIT.md).

**G7. LGD is a fixed 45% assumption.**
Severity: medium. It is also below the Basel QRRE foundation floor of
50%. The dataset carries no recovery or workout data, so LGD cannot be
modelled from it; inventing a fitted LGD would be fabrication. Current
treatment: the assumption is labelled everywhere it is used, the
Basel floor view is published beside it (ECL NT$208,387,127 at 50%),
and the dashboard simulator sweeps LGD 10-90%. Status: OPEN, reason:
no recovery data exists in the source dataset.

**G8. Fairness scope is Taiwan 2005.**
Severity: high for any Canadian reading. The audit machinery
(approval rates by group, sizes beside rates, recovery fairness under
the second-look policy) is demonstrated on a proxy population.
Status: OPEN (structural). It closes only when the machinery runs on
Canadian-shaped data; every artifact states the limit on the same
page as the numbers.

## Gaps found by the wave-3 audit

**G9. The champion fails a strict Hosmer-Lemeshow read.**
Severity: medium. Statistic 22.540 (dof 8), p = 0.0040, while the
logistic baseline passes (p = 0.0651). The pack publishes the flag and
the bin table (worst bin predicted 0.711 vs observed 0.691). The
tempting fix, silent recalibration, is rejected on governance
grounds: it would move every published PD, stage boundary, ECL
figure, cut-off, and study count in the repo. The honest fix is a
pre-registered recalibration study that measures those effects before
adoption. Status: OPEN, with the remediation defined (case study 3).

**G10. No out-of-time evidence.**
Severity: high. The dataset has no time dimension, so no temporal
holdout can exist. Mitigations applied: bootstrap confidence
intervals and a 5-seed robustness check (src/rigor.py), plus the
published decay evidence cited in RESEARCH.md (in-sample AUC ~0.82
decaying to ~0.70 out-of-time in the literature). Status: OPEN
(structural). No durability claim is made anywhere in the repo.

**G11. results.json depended on merge order.**
Severity: low. Running the pipeline alone dropped the validation
blocks that src/validation_pack.py merges in, so the headline JSON's
contents depended on which scripts had run last. Fix applied:
src/run_all.py fixes the order (validation pack after the studies,
rigor last among writers) and the manifest hashes the outputs.
Status: CLOSED.

**G12. Classic reject inference not attempted.**
Severity: low. The lab addresses the rejected region with the
Second-Look Recovery Policy instead: an independent behavioural
re-score with a measured cost, positioned against reweighting and
re-labelling approaches in RESEARCH.md. Status: CLOSED as a
documented alternative; classic reject inference remains available as
future work, not as an unmarked absence.

**G13. CI does not check dashboard-data freshness.**
Severity: low. The web data file is generated by
scripts/export_dashboard_data.py, which asserts the headline metrics
reproduce exactly at generation time, and run_all.py regenerates it
on every full build. A stale export would still pass CI if committed
by hand. Status: OPEN (low): a CI freshness check is the fix; the
published numbers cannot silently diverge because the export itself
asserts them.

**G14. Dashboard ships a single ~812 KB JavaScript chunk.**
Severity: low. First load on a slow connection pays for charts the
visitor may never open. Code-splitting by tab is the fix. Status:
OPEN (low): performance polish, no correctness impact.

**G15. German validation rests on 300 test accounts.**
Severity: noted, not a defect. The intervals say so themselves
(AUC CI widths 0.117 and 0.123). The dataset is fixed at 1,000
accounts by its publisher. Status: OPEN (inherent), disclosed
wherever the German numbers appear.

**G16. The study cut-off is set on the set it is audited on.**
Severity: medium. Disclosed in STUDY.md from wave 2. Wave-3
mitigation: the bootstrap in src/rigor.py re-runs the entire
procedure (cut-off selection, band definition, recovery counting)
inside every resample, so the intervals price that choice instead of
hiding it. The production fix (fix appetite on a validation sample,
audit on a separate one) is recorded in case study 3. Status: OPEN,
mitigated and disclosed.
