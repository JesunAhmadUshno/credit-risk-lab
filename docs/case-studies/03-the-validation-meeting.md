# Case study 3: The validation meeting

*An E-23 style review of this lab, conducted with its own artifacts.
The pack under review is VALIDATION.md; the figures are from
results/results.json, results/model_grades.json and
results/rigor.json.*

## The room

A model risk reviewer working to OSFI Guideline E-23 (effective
May 1, 2027, AI/ML explicitly in scope) and SR 11-7 habits opens the
validation pack. The developer's job in this meeting is not to defend
the model; it is to make the reviewer's challenges cheap to raise and
expensive to dodge. What follows is the meeting this lab's documents
are built to survive, including where they do not.

## What passes

- **Inventory and provenance.** Dataset, split, seed, target
  definition, and downstream uses are stated in one table, and every
  run parameter lives in config.json rather than in code.
- **Discrimination with a benchmark, not a boast.** Champion AUC
  0.7810 (bootstrap 95% CI in results/rigor.json) is presented beside
  the published ceiling for the same dataset (0.7878 to 0.7880,
  RESEARCH.md) and the scorecard grade's named deductions (808.73 of
  1000, band B; the AUC shortfall against a 0.90 reference costs
  74.38 points and says so).
- **Reproducibility.** One command (src/run_all.py) rebuilds the lab
  and asserts the headline invariants; the clean-checkout audit in
  docs/analysis/AUDIT.md records a fresh-venv reproduction of the
  published numbers.
- **Stability machinery.** Score PSI and per-feature CSI are computed
  and monitored under stated triggers (MONITORING.md), with the
  Yurdakul and Naranjo caveat attached: the zones are conventions,
  not error-controlled tests.
- **Limitations volunteered.** No out-of-time split exists, LGD is
  assumed, and the fairness scope is Taiwan 2005: all printed in the
  pack before the reviewer has to ask.

## What gets challenged

1. **The Hosmer-Lemeshow flag comes first, as it should.** The
   champion's calibration test statistic is 22.540 (dof 8), p =
   0.0040: a rejection. The logistic baseline passes at p = 0.0651.
   The pack reports both, with the defence that at 9,000 test accounts
   the test rejects on minor miscalibration and the bin table tracks
   closely (worst bin: predicted 0.711 vs observed 0.691). A strict
   reviewer accepts the transparency and still logs a finding:
   a champion that needs a sample-size argument has a calibration
   question, and the remediation (an explicit recalibration layer,
   pre-registered so its effect on staging is measured before it is
   adopted) belongs on the record. It is gap G9 in the register.
2. **Random-split evidence.** Every stability and performance number
   is train-vs-random-test. There is no temporal holdout because the
   dataset has none; the reviewer notes the published decay pattern
   (in-sample ~0.82 to ~0.70 out-of-time) and caps the reliance that
   can be placed on point estimates accordingly. Gap G10.
3. **LGD is a policy value.** 45% flat, below the Basel QRRE floor of
   50%, with the floor view shown beside it. Defensible as a labelled
   assumption with sensitivity (the dashboard simulator recomputes
   ECL across LGD 10-90%); not defensible as a measurement. It is
   presented as the former. Gap G7.
4. **The cut-off is set and audited on the same test set.** The study
   states the rule and applies it once, openly, and the bootstrap in
   rigor.py re-runs the whole procedure per resample to price that
   choice. A production study fixes appetite on a validation sample
   first. The reviewer accepts the disclosure, notes the method debt.
5. **Fairness scope.** Group findings are a Taiwan 2005 method
   demonstration. The reviewer confirms the audit machinery (sizes
   beside rates, gaps computed, monitoring trigger defined) and
   rejects any reading of the group numbers as Canadian evidence -
   which is what STUDY.md itself says. Gap G8.

## The remediation list the meeting would sign

| # | Finding | Action | Owner artefact |
| --- | --- | --- | --- |
| 1 | Champion calibration flagged by Hosmer-Lemeshow | Pre-register and evaluate a recalibration layer; adopt only if staging and ECL effects are measured and published | GAP G9 |
| 2 | No out-of-time evidence | Obtain or construct a time-ordered dataset before any durability claim; until then, quote CIs and the decay literature | GAP G10 |
| 3 | LGD assumed, below Basel floor | Model LGD when recovery data exists; until then keep the floor view beside every ECL | GAP G7 |
| 4 | Cut-off set on the audited sample | Split-sample appetite setting in the next study iteration | STUDY.md limits |
| 5 | Fairness scope is a proxy population | Re-run the audit machinery on any future Canadian-shaped data before drawing population conclusions | GAP G8 |

## The verdict the pack earns

Effective challenge is the product. This lab's validation pack does
not argue the model is production-grade; it argues the work is
auditable, and it hands the reviewer the five findings above in its
own pages. Under E-23 that posture - inventory, evidence, named
limits, dated remediations - is what a validation function is for.
The model is a teaching-dataset PD model with ceiling-level
discrimination and a flagged calibration test. The documentation is
the deliverable that would survive the meeting.
