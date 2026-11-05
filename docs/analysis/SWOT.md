# SWOT: credit-risk-lab

Every point is tied to evidence in this repo or in RESEARCH.md. Two
lenses, as the lab is two things at once: a risk-modelling tool and a
career artifact.

## (a) As a risk-modelling tool

### Strengths
- Discrimination at the published ceiling for its dataset: champion
  AUC 0.7810 against the strongest published leakage-safe result of
  0.7878 to 0.7880 on the same data (RESEARCH.md, benchmark section).
- A complete, internally consistent chain: features, two model classes,
  calibration table, score PSI, staging policy, scenario-weighted ECL,
  and a grading scorecard whose deductions are computed, not asserted
  (results/model_grades.json: champion 808.73/1000, band B).
- Validation is adversarial, not decorative: the Hosmer-Lemeshow test
  is published even where it flags the champion (p = 0.0040,
  VALIDATION.md section 4), and limitations get their own section in
  every generated document.
- Reproducibility is enforced by machinery: config-driven parameters,
  pinned requirements, a one-command rebuild (src/run_all.py) that
  asserts the headline invariants and refuses to write a manifest when
  they break, plus a clean-checkout audit (docs/analysis/AUDIT.md).

### Weaknesses
- One development population until this wave, and it is Taiwan 2005.
  The German external validation (results/external_validation.json)
  narrows but does not close this: two old public datasets are still
  not a Canadian portfolio.
- LGD is a fixed 45 percent assumption and the lifetime PD is a
  3-year power approximation. The machinery prices PD properly and
  LGD not at all (docs/analysis/GAP_ANALYSIS.md, G7).
- No out-of-time evidence exists, because the dataset has no time
  dimension; every stability number is train-vs-random-test, which
  verifies machinery rather than durability (VALIDATION.md section 8).
- The champion fails a strict read of the Hosmer-Lemeshow test at this
  sample size. Recalibration is deliberately not applied silently: it
  would move every downstream PD, stage and ECL figure (GAP G9).

### Opportunities
- The method transfers: on German Credit, a population 30x smaller
  with no payment panel, the same approach reaches AUC 0.78 to 0.80
  (results/external_validation.json), which is the empirical version
  of "this generalises".
- The second-look policy (src/second_look.py) is a decision layer, not
  just a model: it converts the fairness study from diagnosis into an
  intervention whose cost is measured in admitted defaults.
- Scenario weighting plus a queryable database (data/credit.db,
  sql/queries.sql) makes the lab extensible: new macro scenarios,
  segments, or cut-offs are configuration and SQL, not new code paths.

### Threats
- Concept drift is guaranteed and unobservable here: a 2005
  cross-section cannot show how the relationships decay, and the
  literature says they do (in-sample AUC ~0.82 decaying to ~0.70
  out-of-time, per RESEARCH.md).
- Public datasets are the field's shared toy: results on them are
  necessary evidence of method and near-zero evidence about any real
  book. Any reader who mistakes the lab's numbers for portfolio
  performance has been failed by the framing, which is why every
  document repeats the limits on the same page as the numbers.
- Regulatory expectations are rising (OSFI E-23, effective May 2027,
  explicitly covers AI/ML models): a lab that documents like this
  meets the spirit; one that only posts AUCs would not.

## (b) As a career artifact

### Strengths
- It demonstrates the exact duty list of a risk-modelling posting end
  to end (model development, validation, behavioural data, IFRS 9),
  with receipts a hiring panel can re-run: one command rebuilds the
  whole lab and verifies its own headline numbers.
- It contains a named, formalized contribution (the Second-Look
  Recovery Policy) with pre-registered hypotheses (HYPOTHESES.md,
  committed before the experiment code) - the working style of a
  researcher, shown in git history rather than claimed in prose.
- Honesty is load-bearing and visible: a marginal v2 result reported
  as marginal, a failed calibration test published, assumptions
  labelled in every artifact including the dashboard footer.

### Weaknesses
- It is not employment experience in credit risk, and says so
  everywhere. It evidences method and judgement, not institutional
  tenure; no artifact can close that gap, only employment can.
- The development data is a famous teaching dataset. A specialist
  reader will discount it accordingly; the German transportability
  result and the study design carry the counterweight.
- Depth is concentrated in PD. LGD and EAD are policy values here,
  not models, and a validation panel will find that seam quickly
  (it is mapped openly in the gap register).

### Opportunities
- The pursuit map in RESEARCH.md is live market evidence: Canadian
  lenders are hiring model development and validation roles whose
  postings name IFRS 9, PD/LGD/EAD, PSI/KS and E-23 - the lab's own
  vocabulary, demonstrated rather than listed.
- The fair-access thesis gives the work a defensible point of view in
  an interview: not "I built a model" but "here is a measured problem
  in Canadian credit, here is a policy that trades recovery against
  admitted defaults, and here is its price".
- The dashboard is a public, interactive surface (GitHub Pages): a
  recruiter can move the ECL simulator and read the deductions
  without cloning anything.

### Threats
- Artifact inflation is a real failure mode: each wave makes the lab
  broader, and breadth can read as sprawl. The gap register and the
  hypothesis discipline are the countermeasures; if they lapse, the
  artifact becomes a portfolio of demos.
- Numbers age. Delinquency context in RESEARCH.md is dated
  (2026-11-04) and will stale; the lab's defence is that its own
  results are reproducible while its market framing is timestamped
  as reporting, not fact for all time.
