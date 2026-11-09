# Report: credit-risk-lab

Status 2026-11-08. Verdict: **Functional, not pre-registered** (see
section 7 and README). Every number below is read from a file in
`results/`; section 6 says which command regenerates it, and section 7
says which numbers are not yet re-derived by a clean rebuild of the
current commit.

## 1. Current state

The question (PROPOSAL.md): at a cut-off that holds the approved book
at the performing-book default rate, how many rejected applicants
were creditworthy, and does a behavioural second look recover them at
a bounded cost?

Answer on the held-out Taiwan test set (9,000 accounts): 1,218 of
2,386 rejects (51.0%, 95% bootstrap CI 45.9% to 55.4%) did not default
(`results/study.json`, `results/rigor.json`). The registered second
look recovered only 10 of them (0.8%), so H1 is REFUTED; the thin-file
model stays within 0.03 AUC of the full model (H2 CONFIRMED); the
behavioural v2 edge does not survive reseeding (H3 INCONCLUSIVE); the
method transports to German Credit (H4 CONFIRMED).

| Hypothesis | Pass line (HYPOTHESES.md) | Measured | Verdict | Evidence |
| --- | --- | --- | --- | --- |
| H1 second look | recovery >= 15% and cost <= 1.00 pt | recovery 0.8% (10 of 1,218), cost +0.02 pt | REFUTED (miss) | results/second_look.json |
| H2 thin file | gap no worse than -0.03 AUC | 0.7687 vs 0.7810, gap -0.0123 | CONFIRMED | results/study.json |
| H3 v2 across seeds | mean(v2) >= mean(v1) | 0.7820 vs 0.7830, delta -0.0010 | INCONCLUSIVE (miss) | results/rigor.json |
| H4 German Credit | GBM >= 0.65 and LR >= 0.60 | GBM 0.7848, LR 0.8022 | CONFIRMED | results/external_validation.json |

The site build (`site/src/model.check.mjs`) re-applies each registered
rule to the results files and fails if a verdict disagrees with
HYPOTHESES.md.

## 2. Background


Risk-modelling roles ask for four things: develop models, validate models,
work with behavioural data, and speak IFRS 9. This lab does all four on real
(though public) data, with the method written down and the results table
generated from the run, not typed in.


**Live dashboard: https://jesunahmadushno.github.io/credit-risk-lab/lab/**
(Lab OS research dashboard in `site/`: a live risk-appetite cut-off explorer,
ECL sensitivity simulator and scenario-weight mixer, the fairness explorer,
hypothesis verdicts and the gap register, all read from `results/*.json` at
build time and checked by `npm run build`.)

**App dashboard: https://jesunahmadushno.github.io/credit-risk-lab/**
(React app in `web/`: model grades, ROC curves, staging, calibration, gains,
drift, and an ECL sensitivity simulator. An offline single-file fallback,
`dashboard.html`, is described below.)

Note: `results/behavioural_v2.json` once recorded the single-seed wave 2
verdict ("v2 beats v1"); it was superseded by the pre-registered
multi-seed test H3, which is INCONCLUSIVE (`results/rigor.json`,
`HYPOTHESES.md`). Correction 2026-11-08: the published behavioural v2 numbers did not
reproduce under the pinned environment (section 7); the regenerated
files are now committed.

**Research: [RESEARCH.md](RESEARCH.md)** — the fair access thesis behind
this lab (creditworthy rejects, thin-file applicants, fairness), the Canada
context, the literature, and the published benchmarks this work is graded
against. The measured study itself is [STUDY.md](STUDY.md); the validation
pack is [VALIDATION.md](VALIDATION.md).


## 3. Data, provenance and licence


UCI "default of credit card clients" (Taiwan, 2005), dataset 350 at
archive.ics.uci.edu: 30,000 accounts with credit limits, demographics, six
months of payment history (PAY_0..PAY_6), bill and payment amounts, and a
default-next-month target. Observed default rate: 22.12 percent.


Second population: UCI Statlog (German Credit Data), dataset 144,
1,000 accounts, `data/german.data` with its original description
`data/german.doc` (source: Prof. Dr. Hans Hofmann, Universitat
Hamburg). Both raw files are committed unchanged and treated as
immutable; their SHA-256 checksums are recorded in
`results/run_manifest.json` and match the committed files. This repo
redistributes them only as the unchanged UCI files, with attribution.
Licence: UCI publishes both for research use; the licence text on each
UCI dataset page is not copied into this repo and was not re-checked
during the 2026-11-08 migration, so the exact licence is an open item
(CHANGELOG, Unreleased).

## 4. Method


- Behavioural features on top of the raw fields: utilization, payment ratio,
  delinquency mean and max, bill trend, days-past-due proxy.
- Two PD models: logistic regression (scorecard-style baseline) and gradient
  boosting (challenger), stratified 70/30 split, fixed seed.
- Validation pack: AUC, KS, Gini, Brier score, a 10-bin calibration table,
  and score PSI between train and test.
- IFRS 9 style staging with a written policy (see below), then ECL per
  account as PD x LGD x EAD, summed by stage and for the portfolio.
- A grading scorecard (`src/grading.py`): every model graded 0 to 1000 with
  letter bands, computed from the run outputs, every deduction named.
- A self-contained dashboard (`dashboard.html`, generated by
  `src/dashboard.py`): model grades, staging, calibration, and score
  distribution charts as inline SVG. No server, no JavaScript, no CDN.
- A data quality section and a per-feature drift table (PSI, train vs test)
  in `results/results.json`, plus input validation on the loader.
- `MODEL_CARD.md`: intended use, data, metrics, assumptions, and limits.
- All run parameters (LGD, lifetime horizon, staging thresholds, seed, test
  size) live in `config.json`, not in the code.
- A scenario-weighted IFRS 9 engine (`src/scenarios.py`): base, upside and
  downside scenarios (weights and PD multipliers in `config.json`) re-run
  the staging policy, and the probability-weighted ECL is reported beside
  the baseline, with a Basel QRRE LGD floor view.
- An E-23 / SR 11-7 style validation pack (`VALIDATION.md`, generated by
  `src/validation_pack.py`): inventory, conceptual soundness, outcomes
  analysis, a computed Hosmer-Lemeshow calibration test, per-feature CSI,
  benchmarking, a monitoring plan, and honest limitations.
- Behavioural PD v2 (`src/behavioural_v2.py`): transition features from
  the delinquency path (worsening steps, longest delinquent run, DPD
  slope, recent-3-month mean DPD) against v1 on the same split.
- The fair access study (`src/study.py`, written up in `STUDY.md`):
  creditworthy rejects at a stated risk appetite, a behavioural-only
  thin-file model, and a fairness audit by demographic group.
- Wave 3 (see `HYPOTHESES.md`, pre-registered before the code ran):
  - The **Second-Look Recovery Policy** (`src/second_look.py`): stage-1
    rejects are re-scored with the independent thin-file behavioural
    model and approved when their behavioural PD is at or below the
    median approved applicant's. Recovery and cost are measured, not
    assumed (findings: `STUDY.md` section 4).
  - External validation (`src/external_validation.py`): the same
    approach on UCI Statlog German Credit, a different population and
    era, reported with bootstrap intervals.
  - A database layer (`src/build_db.py`, `sql/queries.sql`): the full
    portfolio, both models' scores, staging, and scenario staging in
    SQLite (`data/credit.db`), with a test asserting the SQL staging
    counts and total ECL match the published JSON.
  - Adverse-action reason codes (`src/reason_codes.py`):
    permutation-importance-ranked, plain-language top-3 reasons per
    rejected applicant, labelled model-derived, not causal.
  - Statistical rigor (`src/rigor.py`): bootstrap 95% confidence
    intervals (1,000 resamples) on the headline numbers and a 5-seed
    robustness check for v1 vs v2.
  - `MONITORING.md` (generated): PSI/CSI state, retraining triggers as
    rules, MRM cadence, with the Yurdakul and Naranjo caveat attached.
  - The analysis pack (`docs/analysis/`): SWOT, PESTEL, a numbered gap
    register, and an audit with a clean-checkout reproducibility
    proof; three case studies in `docs/case-studies/`.



- Stage 3: 90+ days past due proxy, PAY_0 at 3 months delayed or worse.
- Stage 2 (significant increase in credit risk): 30+ DPD (PAY_0 at 1 or 2),
  or modelled PD at least twice the portfolio median and above 10 percent.
- Stage 1: everyone else.
- Stage 1 ECL uses the 12-month PD. Stage 2 uses a lifetime approximation,
  PD_lifetime = 1 - (1 - PD)^3. Stage 3 uses PD = 1.
- LGD is fixed at 45 percent. Both the LGD and the lifetime horizon are
  stated assumptions, not measured values.


## 5. Results


| Model | AUC | KS | Gini | Brier |
| --- | --- | --- | --- | --- |
| Logistic regression | 0.7518 | 0.4008 | 0.5036 | 0.1416 |
| Gradient boosting (champion) | 0.7810 | 0.4196 | 0.5621 | 0.1355 |

Score PSI (train vs test): 0.0007, stable. Calibration tracks closely across
all 10 bins (worst bin: predicted 0.711 vs observed 0.691).

Scenario-weighted ECL (`results/scenarios.json`, weights and PD multipliers
are stated assumptions in `config.json`): base (weight 0.50, PD x1.00)
NT$187,548,414; upside (0.20, x0.85) NT$171,347,227; downside (0.30, x1.30)
NT$214,201,104. **Probability-weighted ECL: NT$192,303,984**, against the
single-scenario baseline of NT$187,548,414.

Basel floor view: portfolio EL is **NT$187,548,414** at the lab's 45% LGD
assumption and **NT$208,387,127** at the Basel QRRE foundation LGD floor of
50%, both from the same staging code path (`results/scenarios.json`).

Behavioural PD v2 (`results/behavioural_v2.json`): v2 scores AUC 0.7799
against v1's 0.7810 (delta -0.0011) with KS 0.4173 against 0.4196 and Brier
0.1357 against 0.1355. Verdict, reported as measured: v2 does not beat v1;
the transition features add nothing the level features do not already
carry. (Published until 2026-11-08 as AUC 0.7818, delta +0.0008, "v2 beats
v1"; that file did not reproduce, see section 7.)

Fair access study headlines (`results/study.json`, `STUDY.md`, test set of
9,000): at the cut-off that holds the approved book at the Stage 1 default
rate (cut-off PD 0.2478; 6,614 approved), **1,218 of 2,386 rejected
applicants (51.0%) did not default**: the creditworthy rejects. The
behavioural-only thin-file model scores AUC 0.7687 against the full model's
0.7810. The largest approval-rate gap is within EDUCATION, 26.3 points
between Other (n=120) and High school (n=1,477); group sizes sit next to
every rate in `STUDY.md`, and the dataset is Taiwan 2005, not Canada.

Wave 3 headlines (`HYPOTHESES.md` verdicts H1 to H4: H1 REFUTED, H2
and H4 CONFIRMED, H3 INCONCLUSIVE, each with its measured numbers
recorded there):

- **Intervals** (`results/rigor.json`, 1,000 bootstrap resamples):
  champion AUC 0.7810, 95% CI 0.7693 to 0.7919; thin-file AUC 0.7687,
  CI 0.7567 to 0.7799; creditworthy-reject share 51.0%, CI 45.9% to
  55.4% (each resample re-selects the cut-off, so the interval prices
  the whole procedure). Across 5 seeds, champion AUC
  averages 0.7830 (std 0.0069) and behavioural v2 averages 0.7820
  (std 0.0067), mean delta -0.0010: hypothesis H3 is INCONCLUSIVE
  under its registered rule; v2 is behind v1 on every seed in the
  regenerated run (published until 2026-11-08 as 0.7824, -0.0006).
- **Second look**: at the pre-registered band (a reject's thin-file
  behavioural PD at or below the approved median, 0.1170), the policy
  recovered 10 of the 1,218 creditworthy rejects (0.8%) at the price
  of 3 admitted defaults; the approved book's default rate moved from
  12.44% to 12.46% (+0.02 points). Hypothesis H1 is REFUTED on its
  recovery bound: the strict band is nearly empty because behavioural
  and champion scores are correlated. The refutation, its fairness
  read by group, and the follow-up it defines are in `STUDY.md`
  section 4 and `HYPOTHESES.md`.
- **External validation** (German Credit: 1,000 accounts, Germany,
  1990s - a different population and era from Taiwan 2005): logistic
  regression AUC 0.8022 (CI 0.7391 to 0.8560), gradient boosting AUC
  0.7848 (CI 0.7203 to 0.8437). The method transports; the wide
  intervals on 300 test accounts are part of the result.
- **Reason codes**: across the 2,386 rejected test applicants (7,075
  reason assignments), the most frequent principal reasons are a
  payment delay in the most recent month (1,770 applicants), severe
  past delinquency (1,325), and repeated payment delays across six
  months (1,232). The low-repayment-ratio reason is given only to
  applicants with a positive statement balance. Model-derived explanations, not causal
  findings.


### Model scorecard

The scorecard below is an output of the lab (`src/grading.py` scores
each credit model against stated benchmarks). It rates the PD models,
not this repository.

Scorecard of 1000: discrimination 500 (AUC 250, KS 150, Gini 100),
calibration 300 (Brier 150, calibration MAE 150), stability 200 (score PSI).
Bands: A 900+, B 800+, C 700+, D 600+, F below 600.

| Model | Points | Band | Discrimination | Calibration | Stability |
| --- | --- | --- | --- | --- | --- |
| Gradient boosting (champion) | 808.73 | B | 350.78/500 | 258.65/300 | 199.30/200 |
| Logistic regression | 772.18 | C | 320.53/500 | 253.05/300 | 198.60/200 |

The biggest deductions are in discrimination: AUC 0.7810 against the 0.90
benchmark costs the champion 74.38 of its 250 AUC points. Every deduction,
with its number and reason, is listed in `results/model_grades.json` and on
the dashboard.

## 6. Evidence and reproduction


Run parameters live in `config.json` at the repo root: LGD, lifetime years,
staging thresholds, seed, test size, bin counts. Edit the file and rerun;
the code holds no hardcoded copies.

**The single reproduction command** rebuilds the entire lab end to end
(pipeline, grading, dashboards, scenarios, behavioural v2, study, second
look, reason codes, external validation, validation pack, monitoring,
database, rigor, dashboard data export), then asserts the headline
invariants (baseline AUCs, KS, staging counts, baseline and weighted ECL)
and writes `results/run_manifest.json` with per-step durations, the git
commit, dataset SHA256 checksums, and output hashes. It exits nonzero if
any invariant breaks:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python src/run_all.py
    .venv/bin/python -m pytest tests/ -q

The individual steps remain runnable one by one (for example
`src/credit_risk_lab.py`, `src/grading.py`, `src/study.py`,
`src/run_all.py` lists the full order in code).

45 tests pass (2026-11-08, including tests/test_layout.py for the
portfolio standard): pipeline checks (dataset shape, AUC floors, exact staging
partition, positive ECL with stage-ordered risk, calibration bins, data
quality, feature drift, config applied, per-model validation), unit tests
(staging policy on synthetic rows including the SICR rule, grading band
boundaries, config loading and overrides, loader validation, dashboard
smoke test), wave-2 tests (scenario weights sum to one and the base
scenario reproduces the published ECL, Basel floor scaling, study counts
partition the test set, the cut-off holds the Stage 1 risk appetite,
thin-file AUC in range, fairness groups cover the test set, transition
features on synthetic delinquency paths), and wave-3 tests (German
champion AUC above its floor with intervals bracketing the estimates, the
SQLite staging counts and total ECL matching the published JSON, reason
codes drawn only from the documented mapping with at least one per
rejected applicant, the second-look partition closing on the study
counts, multi-seed results reported for all 5 seeds). CI runs the same
suite on every push (`.github/workflows/ci.yml`).


Headline numbers and the files they come from:

    python3 -c "import json; s=json.load(open('results/study.json'))['creditworthy_rejects']; print(s['creditworthy_rejects'], s['rejected'], s['creditworthy_share_of_rejected'])"
    python3 -c "import json; r=json.load(open('results/rigor.json'))['taiwan']; print(r['creditworthy_reject_share'], r['champion_auc'])"

To regenerate them from the raw data: `python src/run_all.py` (full
rebuild in dependency order, 19 s on the development machine and 36 s
on the CI runner on 2026-11-08; the 2026-11-05 manifest recorded 457 s
on a loaded machine). The steps share state through `results/results.json`, so
running one step alone can leave that file without the blocks later
steps merge in (gap G11); use the full rebuild.

## 7. Threats to validity

**Not pre-registered.** The first code and results (commit d083dad,
2026-11-04) came with SPEC.md, a build plan without hypotheses or pass
lines. Waves 1 and 2 produced results before any hypothesis was
written. H1 to H4 were committed in HYPOTHESES.md at f5fb365 before the
wave 3 code (fee580d), which is a real per-wave registration, but
(a) it was written after the wave 1 and 2 results were seen, and (b)
commit d12cccb later edited the registered text, changing the stated
Stage 1 target from 12.00% to 12.44% when a rounding bug was fixed.
The fix is correct and documented in its commit, but it changed a
registered parameter after results existed. Under METHOD section 7
the repo is therefore labelled "not pre-registered", no proposal tag
is applied, and the verdict is capped at Functional.

**Results that did not reproduce (corrected 2026-11-08).** Until this
migration `results/run_manifest.json` was the receipt of the full
rebuild at fee580d, and commits f2d1da1 and d12cccb had regenerated five
results files without re-running `run_all.py`. The new CI job
"reproduce" runs the full rebuild on every pull request and fails if any
committed output differs. Its first run showed that every file
reproduced exactly except the behavioural v2 numbers: under the pinned
requirements, v2 AUC on seed 42 is 0.7799, not the published 0.7818, and
the 5-seed v2 mean is 0.7820, not 0.7824 (mean delta -0.0010, not
-0.0006). The regenerated value is the same at commit fee580d, on 1, 2
and 8 threads, on the development machine and on a GitHub arm64 runner,
so the published file most likely came from a library version before
the pins were frozen. The regenerated `behavioural_v2.json`,
`rigor.json`, `web/src/data/results.ts` and a fresh `run_manifest.json`
are committed. H3 stays INCONCLUSIVE (the REFUTED line is -0.002);
the single-seed "v2 beats v1" claim is withdrawn. HYPOTHESES.md keeps
its appended verdict text and gains a dated amendment below it.

**Single split, no time dimension.** See the review notes below (G9,
G10) and `docs/analysis/GAP_ANALYSIS.md`.


This is a public-data lab, not a production system and not employment
experience in credit risk. It demonstrates the method end to end: data,
features, model development, validation, staging, and loss estimation, with
receipts. EAD is the current bill amount from the dataset; the currency is
NT$ as recorded there.


## 8. Review notes (2026-11-07)

A review of the repo against the standard applied to an applied
empirical study, written on 2026-11-07 against branch
`site/live-dashboard` (moved here from docs/research-review.md; its
letter grades are kept out of public files under the portfolio
standard). Every figure quoted comes from `results/*.json` or
`HYPOTHESES.md`.

What the review found strong: hypotheses registered before the wave 3
runs, a refuted hypothesis kept as refuted, bootstrap intervals, a
5-seed check, an external population, a hashed run manifest and an
honest gap register. What it found limiting: calibration of the
champion, the absence of any temporal validation, and fairness
measured only as approval-rate gaps.

| Criterion | Evidence and gap |
|---|---|
| Research question | Stated in RESEARCH.md (who a cut-off scorecard turns away, and whether a behavioural second look recovers them). Clear and answerable on the data. |
| Hypotheses | H1-H4 with numeric decision rules, registered before the experiment code (commit f5fb365 precedes fee580d). Verdicts: H1 REFUTED, H2 CONFIRMED, H3 INCONCLUSIVE, H4 CONFIRMED. The site's build re-applies the rules and fails if a verdict drifts. |
| Method | Standard stratified split, two model families, written IFRS 9 style staging policy. Hyperparameters are fixed in code with no documented tuning or nested CV. Lifetime PD is a constant-hazard 1-(1-PD)^3 approximation; scenario multipliers are flat PD scalars, not macro-linked. |
| Baselines | Logistic regression is the baseline throughout (AUC 0.7518 vs 0.7810). No paired test (DeLong) on the AUC difference; the bootstrap CI of the champion alone (0.7693-0.7919) does not include 0.7518, which is suggestive but not a paired comparison. |
| Statistics and uncertainty | 1,000-resample bootstrap CIs on every headline rate, re-running the full cut-off procedure per resample; 5-seed robustness for H3. The creditworthy-reject share 51.0% sits inside its CI (45.9%-55.4%); the earlier skewed 48.2%-77.6% interval came from targeting a 2-dp rounded Stage 1 rate (0.12 instead of 0.1244). No multiple-comparison correction across the four fairness variables. |
| Calibration | The champion fails Hosmer-Lemeshow (p = 0.004) while the baseline passes (p = 0.0651), and the champion drives staging, ECL and the study (gap G9). Recalibration is defined but not run. |
| Reproducibility | Pinned requirements, one-command rebuild (`src/run_all.py`, 457 s), manifest with input and output SHA-256 and invariants. Defect found and fixed in this review: `pytest tests/` overwrote the published `results/results.json` (see below). |
| Threats to validity | No time dimension, so no out-of-time test (G10); LGD fixed at 45%, below the Basel QRRE 50% floor (G7, floor view published); EAD = current bill with no CCF; Taiwan 2005 proxy population (G8). All disclosed. |
| Related work | RESEARCH.md cites Lessmann et al. 2015, Yeh and Lien 2009, Khandani, Kim and Lo 2010, Dastile et al. 2020, Moscato et al. 2021 and the Basel/IFRS 9 texts, and positions the second look against reject inference. |
| Limitations | Stated on the same page as the numbers in STUDY.md, VALIDATION.md, the model card and the dashboard. |
| Engineering rigor | 40 tests, CI on Python 3.12, generated (never hand-typed) dashboard data with exactness asserts. The root `web/` app ships one ~812 KB chunk (G14). |

### Fixed in that pass (cheap gaps)

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
   (INCONCLUSIVE, mean delta -0.0006 over 5 seeds). Resolved 2026-11-08:
   the rerun gives -0.0011 and "v2 does not beat v1" (section 7).

### Remaining gaps and exactly what each needs


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

## 9. Dashboards


**Live (GitHub Pages): https://jesunahmadushno.github.io/credit-risk-lab/**

The React dashboard (`web/`, deployed by `.github/workflows/pages.yml`)
has seven tabs: Overview (KPIs and the champion grade gauge), Models
(scorecard grades, group bars, named deductions, ROC curves for both
models), Portfolio (clickable stage cards, accounts / ECL / default-rate
charts), Validation (per-model calibration, gains and lift with a sortable
decile table, score distribution, feature drift), Simulator (LGD, PD
shift, and lifetime-horizon sliders that recompute ECL by stage live from
the published aggregates; a sensitivity calculation, not a model re-run),
Research (the fair access thesis, scenario-weighted ECL against the
baseline, the v1 vs v2 comparison, the study headlines, German external
validation with intervals, the Second-Look Recovery Policy, adverse-action
reason codes, and the dataset limits stated), and Analysis (the wave-3
analysis pack: SWOT, PESTEL, gap register, audit, and the three case
studies, with summaries extracted from the documents).
Its data file is generated, never hand-typed:
`.venv/bin/python scripts/export_dashboard_data.py` (see `web/README.md`).

Offline fallback: open `dashboard.html` in any browser (double-click works,
it is a single file with inline SVG charts and no JavaScript): model
comparison with grades and named deductions, accounts and ECL by stage, the
champion's calibration chart, and the test-set score distribution by
outcome. Regenerate it any time with `src/dashboard.py` after a run.

| Stage | Accounts | Observed default rate | EAD (NT$) | ECL (NT$) |
| --- | --- | --- | --- | --- |
| 1 | 22,099 | 12.0% | 1,224,621,954 | 63,068,436 |
| 2 | 7,438 | 48.0% | 288,778,113 | 113,688,443 |
| 3 | 463 | 72.1% | 23,981,190 | 10,791,536 |
| Total | 30,000 | 22.1% | 1,537,381,257 | 187,548,414 |


## 10. Conclusion

The fair access finding holds with its interval: about half of the
applicants a risk-appetite cut-off rejects did not default. The
pre-registered remedy (a strict behavioural second look) does not
recover them, because behavioural and champion scores are correlated;
a looser band is future work and must be registered before it runs.
