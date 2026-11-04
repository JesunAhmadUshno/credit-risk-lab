# credit-risk-lab

Credit risk modelling done in the open: probability-of-default models,
model validation, IFRS 9 style staging, and expected credit loss, built on a
public dataset with every number measured and reproducible.

## Why this exists

Risk-modelling roles ask for four things: develop models, validate models,
work with behavioural data, and speak IFRS 9. This lab does all four on real
(though public) data, with the method written down and the results table
generated from the run, not typed in.

## Data

UCI "default of credit card clients" (Taiwan, 2005), dataset 350 at
archive.ics.uci.edu: 30,000 accounts with credit limits, demographics, six
months of payment history (PAY_0..PAY_6), bill and payment amounts, and a
default-next-month target. Observed default rate: 22.12 percent.

## What is built

- Behavioural features on top of the raw fields: utilization, payment ratio,
  delinquency mean and max, bill trend, days-past-due proxy.
- Two PD models: logistic regression (scorecard-style baseline) and gradient
  boosting (challenger), stratified 70/30 split, fixed seed.
- Validation pack: AUC, KS, Gini, Brier score, a 10-bin calibration table,
  and score PSI between train and test.
- IFRS 9 style staging with a written policy (see below), then ECL per
  account as PD x LGD x EAD, summed by stage and for the portfolio.

## Results (from results/results.json, run 2026-11-04)

| Model | AUC | KS | Gini | Brier |
| --- | --- | --- | --- | --- |
| Logistic regression | 0.7518 | 0.4008 | 0.5036 | 0.1416 |
| Gradient boosting (champion) | 0.7810 | 0.4196 | 0.5621 | 0.1355 |

Score PSI (train vs test): 0.0007, stable. Calibration tracks closely across
all 10 bins (worst bin: predicted 0.711 vs observed 0.691).

| Stage | Accounts | Observed default rate | EAD (NT$) | ECL (NT$) |
| --- | --- | --- | --- | --- |
| 1 | 22,099 | 12.0% | 1,224,621,954 | 63,068,436 |
| 2 | 7,438 | 48.0% | 288,778,113 | 113,688,443 |
| 3 | 463 | 72.1% | 23,981,190 | 10,791,536 |
| Total | 30,000 | 22.1% | 1,537,381,257 | 187,548,414 |

## Staging policy (lab rules)

- Stage 3: 90+ days past due proxy, PAY_0 at 3 months delayed or worse.
- Stage 2 (significant increase in credit risk): 30+ DPD (PAY_0 at 1 or 2),
  or modelled PD at least twice the portfolio median and above 10 percent.
- Stage 1: everyone else.
- Stage 1 ECL uses the 12-month PD. Stage 2 uses a lifetime approximation,
  PD_lifetime = 1 - (1 - PD)^3. Stage 3 uses PD = 1.
- LGD is fixed at 45 percent. Both the LGD and the lifetime horizon are
  stated assumptions, not measured values.

## Run it

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python src/credit_risk_lab.py
    .venv/bin/python -m pytest tests/ -q

Six tests pass: dataset shape, AUC floors, exact staging partition, positive
ECL with stage-ordered risk, calibration bins.

## Limits, stated plainly

This is a public-data lab, not a production system and not employment
experience in credit risk. It demonstrates the method end to end: data,
features, model development, validation, staging, and loss estimation, with
receipts. EAD is the current bill amount from the dataset; the currency is
NT$ as recorded there.
