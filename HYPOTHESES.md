# credit-risk-lab: pre-registered hypotheses (wave 3)

Written and committed BEFORE any wave 3 experiment code runs. Each
hypothesis is falsifiable: a claim, a metric, and the threshold that
confirms or refutes it. Verdicts are appended after the runs, with the
measured numbers, and never edited retroactively.

All Taiwan-dataset experiments use the published pipeline: the champion
gradient boosting model, the study cut-off rule (approve at every PD up
to the threshold where the approved book's observed default rate matches
the Stage 1 observed rate, 12.44%), the stratified 70/30 split, seed 42,
unless a hypothesis says otherwise.

## H1: the Second-Look Recovery Policy recovers creditworthy rejects at a bounded cost

Claim: a two-stage policy (stage 1: the study cut-off on the champion
model; stage 2: stage-1 rejects whose thin-file behavioural PD is at or
below the median thin-file PD of stage-1 approved applicants are
approved on second look) recovers a material share of the creditworthy
rejects identified in the fair access study, while barely moving the
approved book's risk.

Metrics (held-out test set, 9,000 accounts):
- recovery rate = creditworthy rejects recovered / all creditworthy
  rejects at stage 1.
- cost = observed default rate of the post-policy approved book minus
  the stage-1-only approved book's observed default rate, in percentage
  points. Additional admitted defaults are also counted directly.

Thresholds: CONFIRMED if recovery rate >= 15% AND cost <= 1.00
percentage point. REFUTED if recovery rate < 15% OR cost > 1.00 point.
A result inside one bound and outside the other is reported as stated,
with the verdict following the failed bound.

## H2: the thin-file behavioural model stays close to the full model

Claim: a model using behavioural features only (the study's thin-file
feature set, bureau-style fields excluded) discriminates nearly as well
as the full champion on the same split.

Metric: thin-file AUC minus full-model AUC on the test set.

Thresholds: CONFIRMED if the gap is no worse than -0.03 (thin-file AUC
within 0.03 of the full model). REFUTED if the gap is worse than -0.03.

## H3: behavioural v2 is at least as good as v1 across seeds, not just on seed 42

Claim: the wave 2 result (v2 marginally ahead on seed 42) is not a
single-split artefact: across 5 seeds (42, 7, 123, 2024, 31337; each
seed drives its own stratified split and its own model seed), the mean
test AUC of behavioural v2 (v1 features plus the four transition
features) is at least the mean test AUC of v1.

Metric: mean AUC over the 5 seeds for v1 and v2, and the difference of
means.

Thresholds: CONFIRMED if mean(v2) >= mean(v1). REFUTED if
mean(v2) < mean(v1) - 0.002. Between the two, INCONCLUSIVE.

## H4: the modelling approach transports to a second population (German Credit)

Claim: the same approach (logistic regression and gradient boosting,
behavioural-style features where the schema allows, stratified split,
fixed seed) reaches useful discrimination on the UCI Statlog German
Credit dataset (dataset 144), a different population (Germany, 1990s,
1,000 accounts) from the Taiwan 2005 portfolio.

Metrics: test AUC for both models on German Credit, against the Taiwan
champion AUC of 0.7810.

Thresholds: CONFIRMED if the German gradient boosting AUC >= 0.65 AND
the German logistic regression AUC >= 0.60. REFUTED if either bound
fails. The transportability gap (Taiwan champion AUC minus German
champion AUC) is reported either way; German Credit is a different
population and era, and its numbers must never be quoted as Taiwan
numbers.

## Verdicts (appended after the runs)

- **H1: REFUTED.** Recovery rate 0.8% (10 of 1,218 creditworthy
  rejects; band threshold 0.1170, the median thin-file PD of approved
  applicants), far below the 15% bound. The cost bound was met
  easily: +0.02 percentage points (approved-book default rate 12.44%
  to 12.46%; 3 additional defaults admitted on 13 recoveries), inside
  the 1.00 point bound. Per the rule registered above, a result
  outside one bound takes the verdict of the failed bound. The
  finding is the refutation itself: a second look that demands
  behavioural evidence as strong as the typical approved applicant's
  is nearly empty among rejects, because thin-file and champion
  scores are correlated; the policy's price is negligible precisely
  because its volume is. A useful second look needs a looser band,
  and pricing that band is future work, not a silent retune of this
  experiment. Source: results/second_look.json, STUDY.md section 4.
- **H2: CONFIRMED.** Thin-file AUC 0.7687 vs full-model AUC 0.7810:
  gap -0.0123, inside the -0.03 bound. Source: results/study.json.
- **H3: INCONCLUSIVE.** Across seeds 42, 7, 123, 2024, 31337: mean
  AUC v1 0.7830 (std 0.0069), v2 0.7824 (std 0.0066), mean delta
  -0.0006. That is inside the registered inconclusive band (v2 is not
  at or above v1, and not below v1 by more than 0.002). Per-seed
  deltas: +0.0008 (seed 42, the wave-2 split), -0.0007, -0.0014,
  -0.0012, -0.0005: the single-seed edge does not survive reseeding,
  and the honest summary is that the transition features make no
  measurable difference on this dataset. Source: results/rigor.json.
- **H4: CONFIRMED.** German Credit (different population and era):
  gradient boosting AUC 0.7848 (95% CI 0.7203 to 0.8437), above the
  0.65 bound; logistic regression AUC 0.8022 (95% CI 0.7391 to
  0.8560), above the 0.60 bound; logistic is the German champion.
  Transportability gap on the gradient boosting model trained both
  places: -0.0038. The intervals are wide, as 300 test accounts
  deserve. Source: results/external_validation.json,
  results/rigor.json.
