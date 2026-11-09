
# credit-risk-lab: the research

## Thesis

Credit scoring decides who gets access to credit. A standard scorecard
rejects some applicants who would have repaid, and the cost falls hardest on
people with thin files: newcomers who arrive creditworthy and
credit-invisible. This lab studies that gap with measured work, not opinion:

1. How many creditworthy applicants does a cut-off scorecard reject?
2. Can behavioural features alone score a thin-file applicant, and how much
   accuracy does that buy?
3. Does the model treat demographic groups differently, in approvals and in
   errors?

The pipeline (PD models, validation, IFRS 9 style staging, ECL) is the
instrument. The study is the point.

## Canada first: why this matters here, now

- Equifax Canada, Q2 2026: total consumer debt $2.68T, up 4.18% year over
  year. Non-mortgage 90+ day balance delinquency 1.76%. Credit card 90+
  delinquency 4.19%. (Equifax Canada market pulse, reported 2026-08-24.)
- Equifax Canada, Q1 2026: 1.5 million Canadians (1 in 21) missed a payment;
  consumer insolvencies up 18.8% year over year, to levels not seen since
  2009.
- TransUnion Canada, Q4 2025: total 90+ delinquency 1.83%, Alberta highest
  at 2.37%, Quebec lowest at 1.31%; tighter credit supply noted.
- Bank of Canada, Financial Stability Report 2026 (Households): 12% of
  mortgages renew in the next 12 months at roughly 15% higher payments;
  refinance failure about 4% nationally and about 9% in Toronto. Arrears are
  concentrated in non-mortgage households.
- Statistics Canada: household credit-market debt reached 179.6% of
  disposable income in Q1 2026, a sixth straight quarterly rise (secondary
  reporting; primary release to be re-verified before citation in print).

Rising delinquency is the hiring signal: lenders need people who can build,
validate, and explain credit models.

## Regulation the work answers to

- Canada: IFRS 9 expected credit loss under OSFI's guideline (2016, revised
  April 2022), which adopts the BCBS ECL principles, including model
  validation (Principle 5) and forward-looking macroeconomic judgment.
  Stage 1 carries 12-month ECL; a significant increase in credit risk moves
  an exposure to Stage 2 lifetime ECL; Stage 3 is credit-impaired. The
  30-days-past-due SICR presumption is rebuttable.
- Model risk: OSFI Guideline E-23 (final September 2025, effective May 1,
  2027) explicitly covers AI and ML models. Validation demand is regulatory,
  not optional.
- United States: CECL (FASB ASC 326) books lifetime ECL at origination for
  all assets, with no staging. IFRS 9 staging creates a cliff CECL does not
  have.
- Basel framework (BIS CRE32): expected loss = PD x LGD x EAD. Floors
  include a 0.05% PD floor (0.10% for qualifying revolving retail) and a 50%
  LGD floor for QRRE under the foundation approach. The lab's 45% LGD is a
  stated assumption below that floor; v2 adds the floor-aware variant.

## What the literature says

- Lessmann et al. (2015), European Journal of Operational Research
  (DOI 10.1016/j.ejor.2015.05.030): 41 classifiers across 8 credit datasets;
  ensembles lead, but margins over strong baselines are modest.
- Yeh and Lien (2009), Expert Systems with Applications
  (DOI 10.1016/j.eswa.2007.12.020): the source study for this lab's dataset;
  warns that predicted probabilities need calibration care.
- Khandani, Kim and Lo (2010), Journal of Banking and Finance
  (DOI 10.1016/j.jbankfin.2010.06.001): transaction plus bureau data
  materially improves consumer default prediction.
- Dastile, Celik and Potsane (2020), Applied Soft Computing 91:106263:
  survey of 74 studies; ensembles beat single models on average.
- Moscato et al. (2021), Expert Systems with Applications
  (DOI 10.1016/j.eswa.2020.113986): on 877,956 Lending Club loans, sampling
  and evaluation design matter as much as the classifier.
- Alonso and Carbó (2021/2022), Banco de España WP 2105 and International
  Review of Financial Analysis (DOI 10.1016/j.irfa.2022.102372): a
  supervisor-run study; ML over logistic regression translated into 12.4 to
  17 percent capital savings.
- Yurdakul and Naranjo (2020), Journal of Risk Model Validation: the common
  PSI thresholds (0.10 / 0.25) are rules of thumb without a Type I/II error
  basis. The lab reports PSI as a signal, not a pass/fail law.

## Benchmark verdict on this lab's models

Application scorecards in production typically reach AUC 0.70 to 0.80;
behavioural scorecards on existing customers exceed 0.85 because the target
and features are richer. On this exact dataset (30,000 accounts, 22.12%
default), the strongest published leakage-safe results are gradient boosting
at AUC 0.7878 to 0.7880 (Research Square preprint, September 2026, DOI
10.21203/rs.3.rs-10794000/v1) and an optimized CatBoost at AUC 0.7814, KS
0.4324, Brier 0.1350.

This lab: gradient boosting AUC 0.7810, KS 0.4196, Gini 0.5621, Brier
0.1355. That is within 0.007 AUC of the best published number on the same
data, achieved with a plain pipeline and no leakage. Production portfolios
differ for named reasons: prime Canadian default rates near 2% rather than
22%, reject inference on booked-only samples, and out-of-time decay
(published work shows in-sample AUC 0.82 falling to about 0.70 out of time).

## Scope and opportunity verdicts (researched 2026-11-04)

- PURSUE NOW: credit risk model development and model validation roles at
  TD, Scotiabank, CIBC, BMO, RBC; model risk management under OSFI E-23;
  fraud analytics as a second track. Job Bank Canada (updated 2025-11-19)
  puts Toronto data scientists at a $46.33 hourly median, about $96,000 a
  year.
- BUILD FIRST: collections analytics (senior and SAS gated), climate credit
  risk (real regulation, no Toronto postings found yet), BNPL risk through
  point-of-sale lenders, global remote (real but residency gated).
- The lab's next builds, ranked by opportunity value: (1) scenario-weighted
  IFRS 9 staging and ECL engine, (2) an E-23 / SR 11-7 style validation
  pack, (3) behavioural PD v2 with roll-rate and survival views, (4)
  LGD/EAD with Basel floors and capital translation, (5) monitoring and
  SHAP reason codes.

## The v2 study (fair access)

- Creditworthy rejects: at the cut-off that holds portfolio default at the
  observed Stage 1 level, count rejected applicants whose observed outcome
  was repayment, and estimate the same share model-based for the rejected
  region, labelled as estimation.
- Thin-file simulation: retrain on behavioural features only (no limit, no
  demographics), report AUC against the full model. This is the newcomer
  question in miniature.
- Fairness audit: approval rates and error rates by sex, age band,
  education, and marriage, with group sizes printed next to every rate and
  the dataset's limits (Taiwan, 2005) stated on the same page.

Every number in the study comes from a run. Assumptions are labelled.
Unverifiable items in the source research (some Statistics Canada quarters
rest on secondary reporting; one salary summary conflicted and was dropped)
are flagged here rather than smoothed over.

## Wave 3: the second-look policy, external validation, and intervals

**Second look versus reject inference.** Classic reject inference attacks
the selection problem inside a single model: it reweights the booked
sample, augments it with rejected applicants whose labels are imputed
(parceling, fuzzy augmentation), or re-labels the rejected region, so one
scorecard can be trained as if the rejects had been observed. The risk is
that the imputed labels are the model's own beliefs fed back to it. The
Second-Look Recovery Policy (src/second_look.py, pre-registered as H1)
takes a different route: it leaves the champion and its cut-off untouched,
re-scores only the rejects with a second, independent model restricted to
behavioural evidence (the thin-file model), and approves a reject when
that behavioural score is at least as strong as the median approved
applicant's (band threshold: thin-file PD 0.1170). Nothing is re-labelled;
the policy's cost is measured on observed outcomes instead of assumed.
Measured, the pre-registered version of the policy is nearly empty: it
recovered 13 of 2,386 rejects - 10 creditworthy applicants, 0.8% of all
creditworthy rejects - at the price of 3 admitted defaults, moving the
approved book's default rate from 12.44% to 12.46% (+0.02 percentage
points). H1 is therefore REFUTED on its recovery bound (15%), and the
refutation is the finding: behavioural and champion scores are
correlated, so almost no reject carries approved-median behavioural
evidence. A second look that bites needs a band set by an explicit
recovery-versus-cost appetite rather than by the approved median, and
pricing candidate bands is the follow-up experiment this one defines.
Reject inference asks "what would the model have said about everyone?";
the second look asks "what does independent evidence say about the
people the model refused, and what does acting on it cost?". Here the
honest answer is: at the strictest defensible band, almost nothing, at
almost no cost.

**External validation.** The same approach (logistic regression plus
gradient boosting, behavioural-style ratios where the schema allows) was
run on UCI Statlog German Credit (1,000 accounts, German applicants,
collected in the 1990s; results/external_validation.json). Logistic
regression reached AUC 0.8022 (95% CI 0.7391 to 0.8560) and gradient
boosting 0.7848 (0.7203 to 0.8437), against 0.7810 for the champion model
applied at home: the method transports, and on 300 test accounts the
intervals are wide enough to say how little a sample that size proves.
German Credit is a different population and era from Taiwan 2005, and
both are far from a Canadian portfolio; the claim is about the method,
not about any real book.

**Intervals on the headline numbers** (1,000 bootstrap resamples, fixed
seed; results/rigor.json): champion AUC 0.7810, 95% CI 0.7693 to 0.7919;
thin-file AUC 0.7687, CI 0.7567 to 0.7799; creditworthy-reject share
51.0%, CI 45.9% to 55.4% - every resample re-runs the whole procedure
including cut-off selection, so the interval prices the procedure, not
just the proportion. The second-look recovery rate of 0.8% carries
CI 0.0% to 1.8%: small under every resample, which is what makes the H1
refutation solid rather than a knife-edge call. Across five seeds (each
with its own split), champion AUC averaged 0.7830 (std 0.0069) and
behavioural v2 averaged 0.7820 (std 0.0067), mean delta -0.0010: H3 is
INCONCLUSIVE under its registered rule, and the v2 transition features
show no edge. (Corrected 2026-11-08 from 0.7824 and -0.0006, published
before the pinned rebuild; the single-seed edge did not reproduce. See
REPORT.md section 7.)
