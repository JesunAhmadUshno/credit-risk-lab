# Model Card: credit-risk-lab

## Intended use

A public, reproducible demonstration of the credit-risk modelling method end
to end: probability-of-default (PD) model development, independent-style
validation, IFRS 9 style staging, and expected credit loss (ECL) estimation.
It exists so a reader (for example a hiring manager or a model reviewer) can
inspect exactly how the work is done and verify every number from the run
outputs in `results/`.

Out of scope: any real lending decision, any real portfolio, any production
use. The dataset is a 2005 Taiwan credit-card portfolio published for
research; nothing here is a statement about any actual borrower or lender.

## Status, stated plainly

This is a public-data lab built by Jesun Ahmad Ushno as a portfolio project.
It is **not employment experience in credit risk**, and it does not claim to
be. It demonstrates the method with receipts: code, tests, measured metrics,
a grading scorecard, and a dashboard, all reproducible from this repo.

## Data

- Source: UCI Machine Learning Repository, "default of credit card clients"
  (dataset 350, archive.ics.uci.edu), Taiwan, 2005.
- 30,000 accounts, 25 columns: credit limit, demographics, six months of
  payment status (PAY_0, PAY_2..PAY_6), bill amounts, payment amounts.
- Target: default in the following month. Observed default rate 22.12%.
- Data quality (from the run, `results/results.json`): 0 duplicate IDs,
  missing rate 0.0 in every column of the source file.
- Split: stratified 70/30 train/test from `config.json` (`test_size` 0.30,
  `seed` 42). Feature drift between the splits is negligible: every feature
  PSI is below 0.002 in the current run.

## Features

Raw account and payment-history fields, plus engineered behavioural
features: utilization, payment ratio, delinquency mean, delinquency max,
bill trend, and a days-past-due proxy from PAY_0. Categorical fields (SEX,
EDUCATION, MARRIAGE) are one-hot encoded; numeric fields are median-imputed
and scaled for the regression baseline.

## Models and measured performance (test set)

| Model | AUC | KS | Gini | Brier | Score PSI |
| --- | --- | --- | --- | --- | --- |
| Logistic regression | 0.7518 | 0.4008 | 0.5036 | 0.1416 | 0.0014 |
| Gradient boosting (champion) | 0.7810 | 0.4196 | 0.5621 | 0.1355 | 0.0007 |

Calibration is reported as a 10-bin predicted-vs-observed table per model
in `results/results.json` and charted in `dashboard.html`.

## Model grades (src/grading.py, from the run outputs)

Scorecard of 1000: discrimination 500 (AUC 250, KS 150, Gini 100),
calibration 300 (Brier 150, calibration MAE 150), stability 200 (score PSI).
Bands: A 900+, B 800+, C 700+, D 600+, F below 600. Full component detail,
with every deduction named, is in `results/model_grades.json`.

| Model | Points | Band | Discrimination | Calibration | Stability |
| --- | --- | --- | --- | --- | --- |
| Gradient boosting | 808.73 | B | 350.78/500 | 258.65/300 | 199.30/200 |
| Logistic regression | 772.18 | C | 320.53/500 | 253.05/300 | 198.60/200 |

## Staging and ECL

IFRS 9 style staging policy (thresholds in `config.json`): Stage 3 at 90+
days-past-due proxy (PAY_0 at 3 months or worse); Stage 2 on significant
increase in credit risk (30+ DPD, or modelled PD at least twice the
portfolio median and above 10%); Stage 1 otherwise. Current run: Stage 1
22,099 accounts, Stage 2 7,438, Stage 3 463. Portfolio ECL NT$187,548,414 on
EAD NT$1,537,381,257 (EAD is the current bill amount; currency is NT$ as
recorded in the dataset).

## Assumptions, labelled as assumptions

- **LGD is fixed at 45%** (a Basel-style unsecured benchmark). It is an
  assumption, not a measured value; the dataset carries no recovery data.
- **Lifetime PD** for Stage 2 is approximated as 1 - (1 - PD)^3, a 3-year
  horizon. Also an assumption, set in `config.json`.
- Stage 3 PD is set to 1.0 by policy.
- The DPD proxy reads PAY_0 as months delayed; the source codes -2, -1 and
  0 (no consumption, paid in full, revolving) are treated as 0 months.

## Limits

- One public dataset from 2005, one geography, one product (credit cards).
  Performance will not transfer to a modern portfolio as-is.
- No fairness or protected-group analysis is performed; the demographic
  fields are used as ordinary predictors, which a regulated lender would
  need to review under its own governance before any real use.
- No temporal validation: the split is random, not out-of-time.
- ECL is a method demonstration. Real IFRS 9 ECL needs macroeconomic
  scenarios, measured LGD/EAD models, and governance this lab does not have.

## Reproduce

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python src/credit_risk_lab.py
    .venv/bin/python src/grading.py
    .venv/bin/python src/dashboard.py
    .venv/bin/python -m pytest tests/ -q
