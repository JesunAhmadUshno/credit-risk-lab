# PESTEL: Canadian credit risk, as it bears on this lab

Sources are the figures and documents cited in RESEARCH.md (researched
2026-11-04); inline notes point at the section there. This analysis is
context for a public-data lab, written to be read beside its limits.

## Political / regulatory

- OSFI Guideline E-23 (final September 2025, effective May 1, 2027)
  brings model risk management, explicitly including AI/ML models,
  into force for Canadian federally regulated lenders. Validation
  stops being a courtesy and becomes a dated obligation. This lab's
  VALIDATION.md is structured in E-23's image for exactly that
  reason. (RESEARCH.md, "Regulation".)
- IFRS 9 in Canada runs under OSFI's guideline (2016, revised April
  2022), which adopts the BCBS expected-credit-loss principles,
  including model validation (Principle 5) and forward-looking
  macroeconomic judgment. The scenario-weighted ECL engine in
  src/scenarios.py exists because the standard demands
  probability-weighted, forward-looking estimates, not a single
  point forecast.
- Political attention follows household debt: with credit-market debt
  at 179.6% of disposable income (Statistics Canada, Q1 2026, via
  secondary reporting), consumer-credit policy (affordability tests,
  rate caps debates, open banking) stays on the federal agenda, and
  each proposal changes what lenders must model and document.

## Economic

- The cycle is late and strained: Equifax Canada reports total
  consumer debt of $2.68T in Q2 2026 (+4.18% year over year),
  non-mortgage 90+ delinquency at 1.76%, and credit card 90+
  delinquency at 4.19%; 1.5 million Canadians missed a payment in
  Q1 2026 and insolvencies rose 18.8% year over year.
  (RESEARCH.md, "Canada first".)
- The Bank of Canada's Financial Stability Report 2026 puts 12% of
  mortgages renewing within 12 months at roughly 15% higher payments,
  with refinance failure near 4% nationally and 9% in Toronto.
  Renewal shock transmits into unsecured performance through household
  cash flow, which is precisely the channel behavioural PD features
  (utilization, payment ratio, delinquency path) are built to see
  early.
- TransUnion Canada (Q4 2025) notes tighter credit supply alongside
  plateauing headline delinquency (1.83% total 90+): lenders are
  already pulling the lever this lab studies - the cut-off.

## Social

- Newcomer credit invisibility is the lab's thesis (RESEARCH.md):
  people arrive creditworthy with no Canadian file, and a cut-off
  scorecard reads "no file" as "no". Canada admits hundreds of
  thousands of newcomers a year into exactly this wall. The thin-file
  study (AUC 0.7687 on behavioural data alone) is the quantitative
  version of the argument that the wall is a data problem before it
  is a risk problem.
- An aging population shifts the risk pool and the fairness surface:
  older borrowers show different delinquency paths and thinner digital
  footprints, and any approval model audited only in aggregate will
  miss group-level effects. The study's audit-by-group machinery is
  the habit that catches it.
- Financial stress is unevenly distributed: arrears concentrate in
  non-mortgage households and in younger cohorts (Equifax reports the
  26-35 band worst on non-mortgage delinquency). Models that price
  the average borrower misprice both tails.

## Technological

- ML is now inside the regulatory perimeter (E-23 names AI/ML), which
  moves the bottleneck from "can we build it" to "can we validate,
  monitor, and explain it". The lab's grading scorecard, monitoring
  plan (MONITORING.md) and reason codes (src/reason_codes.py) are
  built to that bottleneck.
- Monitoring technology is commoditizing: PSI/CSI dashboards are
  table stakes, while the literature (Yurdakul and Naranjo 2020)
  warns their thresholds are conventions. The durable skill is
  knowing which number is evidence and which is alarm wiring.
- Alternative data (rent, utilities, cash-flow underwriting under
  open banking) is the technological frontier for thin files; it
  strengthens exactly the behavioural channel this lab measures, and
  it raises the consent and fairness questions the study's audit is
  designed to answer.

## Environmental

- OSFI Guideline B-15 (revised March 2025) puts climate risk inside
  prudential expectations. For credit models the transmission is
  physical (property-secured exposures, regional concentration) and
  transitional (sector cash flows). RESEARCH.md scores climate credit
  risk as BUILD FIRST for a Toronto practitioner: the regulation is
  real today, the dedicated data-science postings were not yet there
  at research time.
- This lab models unsecured consumer credit on 2005 data; it has no
  climate channel and claims none. The honest PESTEL entry is that
  the framework (scenario weighting) is the same machinery a climate
  scenario would plug into, and that is a direction, not a result.

## Legal

- Adverse-action expectations: declined applicants are owed the
  principal reasons in several regimes (US ECOA/Reg B is the strict
  template; Canadian expectations run through fair-lending practice,
  human-rights law, and PIPEDA's accuracy and access principles).
  Reason codes (src/reason_codes.py) are the lab's implementation:
  model-derived, plain-language, and labelled as explanations of the
  score rather than causal findings or legal notices.
- Protected-ground discrimination law binds model outcomes, not just
  model inputs: a model that never sees a protected attribute can
  still produce group-skewed approvals through proxies. That is why
  the fairness audit measures outcomes by group while the reason-code
  vocabulary deliberately excludes demographic attributes.
- PIPEDA and provincial privacy law govern the data side: consent,
  purpose limitation, and accuracy obligations apply to behavioural
  data with the same force as to bureau data. A thin-file product
  built on payment behaviour is a privacy artifact as much as a
  modelling one.
