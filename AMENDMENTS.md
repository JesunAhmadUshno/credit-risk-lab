# credit-risk-lab: post-registration amendments (paper improvement programme)

These amendments were written and committed on 2026-11-16, BEFORE any
of the computations below ran. They are not part of the frozen wave 3
registration in HYPOTHESES.md and they change no registered hypothesis,
threshold, or verdict. Both are exploratory, post-hoc analyses of the
published test set, run for version 2 of the fair-access preprint
(Zenodo DOI 10.5281/zenodo.24282032), and both will be reported in the
paper as amendments, labelled exploratory, next to the registered
results they extend. The frozen verdicts stand as registered: H1
REFUTED, H2 CONFIRMED, H3 INCONCLUSIVE, H4 CONFIRMED.

## Amendment A1: the second-look recovery-cost curve (band sweep)

Motivation, stated before running: H1 tested one band rule (the
approved median thin-file PD, 0.114442) and was refuted on recovery
(1.2 percent). The paper defines the follow-up question (what recovery
do looser bands buy, at what cost?) but does not price it. This
amendment prices it on the same held-out test set, descriptively.

Specification, frozen before the run:

- Same pipeline, split, and seed as the published run (seed 42,
  stratified 70/30, test set 9,000). Champion and thin-file models
  retrained by the published code paths (src/study.py,
  src/second_look.py).
- Stage 1 is unchanged: the study cut-off (approved book matches the
  Stage 1 observed default rate, 12.00 percent).
- Band grid: the stage-2 band threshold is set at k times the
  registered band (the median thin-file PD of stage-1 approved
  applicants), for k in {1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0}. The
  k = 1.0 row must reproduce the published H1 headline exactly
  (21 recovered, 17 creditworthy, recovery 1.2 percent, cost plus
  0.023 points); if it does not, the amendment run is void and the
  discrepancy is reported instead of the curve.
- For each k: band threshold, recovered total, recovered
  creditworthy, recovery rate of creditworthy rejects, admitted
  defaults, post-policy approved book default rate, and cost in
  percentage points against the stage-1 book.
- Also reported, descriptively: the smallest grid band whose
  recovery reaches the registered 15 percent line, and its cost;
  no interpolation and no new verdict is issued. H1 stays REFUTED:
  this curve prices bands that were not the registered policy.

## Amendment A2: paired bootstrap interval for the thin-file AUC gap

Motivation, stated before running: H2 was judged on the point gap
(thin-file AUC 0.7687 vs full-model 0.7810, gap minus 0.0123) against
the registered minus 0.03 bound. The paper reports each AUC's own
bootstrap interval but no interval for the gap itself. This amendment
adds the paired interval.

Specification, frozen before the run:

- Same models and test set as A1. The two models' test-set scores are
  computed once; the resampling is over test accounts.
- 2,000 bootstrap resamples of the 9,000 test accounts, with
  replacement, seed 20261116. In each resample, both AUCs are
  recomputed on the resampled accounts (paired by construction) and
  the gap (thin-file minus full) is recorded.
- Reported: the point gap (must equal minus 0.0123 as published), the
  bootstrap mean gap, and the 2.5 and 97.5 percentile interval. No
  verdict is issued; H2's registered judgement on the point gap
  stands.

Outputs: results/amendments.json (written by src/amendments.py);
this file gains a results note after the run, appended, never edited
retroactively.

## Results note (appended after the run, 2026-11-16)

A1 ran as specified (src/amendments.py; output
results/amendments.json). The k = 1.0 validation row reproduced the
published H1 headline exactly (21 recovered, 17 creditworthy,
recovery 0.0122, cost plus 0.023 points), so the sweep is valid.
Recovery rises slowly with the band: 2.9 percent at 1.25 times the
registered band, 5.3 at 1.5, 8.7 at 1.75, 16.1 at 2.0 (cost plus
0.637 points, 79 admitted defaults), 36.8 at 2.5 (cost plus 1.562),
57.8 at 3.0 (cost plus 2.914). The first grid band reaching the
registered 15 percent recovery line is 2.0 times the approved
median, and its cost sits inside the registered 1.00 point bound.
That is a descriptive fact about a band that was not the registered
policy; H1 remains REFUTED as registered, and any future test of a
2.0-times band needs fresh data and its own registration.

A2 ran as specified: point gap minus 0.0123 (as published),
bootstrap mean minus 0.0122, 95 percent percentile interval minus
0.0176 to minus 0.0069 (2,000 resamples, seed 20261116). The gap is
distinguishable from zero, and the whole interval lies inside the
registered minus 0.03 bound. No verdict issued; H2 stands CONFIRMED
on its registered point-gap rule.
