# Research review: credit-risk-lab

A review of the repo against the standard a PhD committee would apply to an
applied empirical study, written on 2026-11-07 against branch
`site/live-dashboard`. Every figure quoted comes from `results/*.json` or
`HYPOTHESES.md`. Grades: A (publishable as is), B (sound, with named gaps),
C (needs work before the claim holds), D (missing).

**Overall: B+.** The discipline is unusually good for a portfolio study:
hypotheses registered before the runs, a refuted hypothesis kept as
refuted, bootstrap intervals, a 5-seed check, an external population, a
hashed run manifest and an honest gap register. What holds it below A is
calibration of the champion, the absence of any temporal validation, and
fairness measured only as approval-rate gaps.

| Criterion | Grade | Evidence and gap |
|---|---|---|
| Research question | A- | Stated in RESEARCH.md (who a cut-off scorecard turns away, and whether a behavioural second look recovers them). Clear and answerable on the data. |
| Hypotheses | A | H1-H4 with numeric decision rules, registered before the experiment code (commit f5fb365 precedes fee580d). Verdicts: H1 REFUTED, H2 CONFIRMED, H3 INCONCLUSIVE, H4 CONFIRMED. The site's build re-applies the rules and fails if a verdict drifts. |
| Method | B | Standard stratified split, two model families, written IFRS 9 style staging policy. Hyperparameters are fixed in code with no documented tuning or nested CV. Lifetime PD is a constant-hazard 1-(1-PD)^3 approximation; scenario multipliers are flat PD scalars, not macro-linked. |
| Baselines | B+ | Logistic regression is the baseline throughout (AUC 0.7518 vs 0.7810). No paired test (DeLong) on the AUC difference; the bootstrap CI of the champion alone (0.7693-0.7919) does not include 0.7518, which is suggestive but not a paired comparison. |
| Statistics and uncertainty | B+ | 1,000-resample bootstrap CIs on every headline rate, re-running the full cut-off procedure per resample; 5-seed robustness for H3. The creditworthy-reject share 51.0% sits inside its CI (45.9%-55.4%); the earlier skewed 48.2%-77.6% interval came from targeting a 2-dp rounded Stage 1 rate (0.12 instead of 0.1244). No multiple-comparison correction across the four fairness variables. |
| Calibration | C+ | The champion fails Hosmer-Lemeshow (p = 0.004) while the baseline passes (p = 0.0651), and the champion drives staging, ECL and the study (gap G9). Recalibration is defined but not run. |
| Reproducibility | A- | Pinned requirements, one-command rebuild (`src/run_all.py`, 457 s), manifest with input and output SHA-256 and invariants. Defect found and fixed in this review: `pytest tests/` overwrote the published `results/results.json` (see below). |
| Threats to validity | B | No time dimension, so no out-of-time test (G10); LGD fixed at 45%, below the Basel QRRE 50% floor (G7, floor view published); EAD = current bill with no CCF; Taiwan 2005 proxy population (G8). All disclosed. |
| Related work | B+ | RESEARCH.md cites Lessmann et al. 2015, Yeh and Lien 2009, Khandani, Kim and Lo 2010, Dastile et al. 2020, Moscato et al. 2021 and the Basel/IFRS 9 texts, and positions the second look against reject inference. |
| Limitations | A- | Stated on the same page as the numbers in STUDY.md, VALIDATION.md, the model card and the dashboard. |
| Engineering rigor | B+ | 40 tests, CI on Python 3.12, generated (never hand-typed) dashboard data with exactness asserts. The root `web/` app ships one ~812 KB chunk (G14). |

## Fixed in this pass (cheap gaps)

1. **Test suite clobbered published results.** `tests/test_pipeline.py`
   called `credit_risk_lab.main()` at import, which rewrote
   `results/results.json` without the Hosmer-Lemeshow, CSI and AUC-CI
   blocks merged in later by `validation_pack` and `rigor`. `main()` now
   takes an output path and the test writes to a temp file; CI runs
   `git diff --exit-code results/` after pytest so any future test that
   mutates published results fails the build.
2. **Dashboard data only in TypeScript.** `scripts/export_dashboard_data.py`
   now also writes `results/dashboard_data.json` (ROC points, deciles,
   per-stage simulator aggregates). Re-running it reproduced
   `web/src/data/results.ts` byte for byte.
3. **G13 for the new dashboard.** `site/src/model.check.mjs` runs inside
   `npm run build` and asserts: ECL simulator at baseline = NT$187,548,414;
   scenario mixer at recorded weights = 192,303,983.68; the QRRE-floor view
   = 208,387,127.21; score bins sum to 9,000 accounts with defaults equal
   to the decile totals; the study counts lie inside the bin edges; and the
   registered rules reproduce the four verdicts in HYPOTHESES.md. A stale
   or hand-edited results file now breaks the Pages build. (The root `web/`
   app is still unchecked in CI.)
4. **Inconsistent recorded verdict.** `results/behavioural_v2.json` still
   says "v2 beats v1" (single seed, +0.0008). It is not hand-edited (that
   needs a rerun); the README and dashboard now label it superseded by H3
   (INCONCLUSIVE, mean delta -0.0006 over 5 seeds).

## Remaining gaps and exactly what each needs

| Gap | What closes it | Compute / data |
|---|---|---|
| Paired model comparison | DeLong test (or paired bootstrap of the AUC difference on the same resamples) between champion and baseline | CPU only, under a minute: reuse the test-set predictions in `src/rigor.py`. |
| Champion calibration (G9) | Pre-registered recalibration study: isotonic or Platt on a held-out calibration split, then report the movement in every PD, stage count, ECL and study count | CPU, ~1-2 min; requires a three-way split, so it changes the published split and must be registered first. |
| Tuning disclosure | Nested CV over a small grid for gradient boosting, reporting outer-fold AUC | CPU, roughly 5-15 min on 21,000 rows (over the 5-minute limit for this pass). |
| Out-of-time validation (G10) | A dataset with origination dates and performance windows (e.g. Freddie Mac single-family loan-level or a Home Credit style panel) | New public data download and a temporal split; structural for the UCI data. |
| LGD / EAD modelling (G7) | Recovery and workout data for LGD, limit and drawdown history for a CCF | New data; none exists in the UCI source. |
| Forward-looking IFRS 9 | PD term structures and macro-linked scenario multipliers (e.g. a satellite model on unemployment and GDP) | Macro series for the portfolio's country and period, plus a time-indexed default panel. |
| Fairness beyond approval gaps (G8) | Equalised odds, calibration within groups and significance tests with group sizes (Other n = 120 is too small for stable rates), then rerun on Canadian-shaped data | CPU for the metrics (seconds, from existing test predictions); Canadian data for the scope claim. |
| Root dashboard freshness and bundle (G13, G14 for `web/`) | CI step that re-runs the export and diffs `web/src/data/results.ts`; code-split the React app by tab | CI minutes only (export takes ~2-41 s); front-end change in `web/`. |
