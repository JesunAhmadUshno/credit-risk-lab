# Proposal: credit-risk-lab

Status: **not locked.** This file gathers the plan as it was written
over time. Nothing here was committed and tagged before the first
result, so the repo is labelled "not pre-registered" (REPORT.md
section 7, docs/decisions/0002). A future confirmatory cycle (for
example the recalibration study, gap G9) gets its own locked proposal
and tag before it runs.

## Question

At a cut-off that holds the approved book at the performing-book
(Stage 1) default rate, how many rejected applicants were
creditworthy, and does a behavioural second look recover them at a
bounded cost?

## Hypotheses and pass lines

H1 to H4, each with a metric and a CONFIRMED / REFUTED / INCONCLUSIVE
rule, are in HYPOTHESES.md. They were committed at f5fb365, before the
wave 3 code (fee580d) but after the wave 1 and 2 results; commit
d12cccb later corrected the stated Stage 1 target from 12.00% to
12.44% (a rounding fix). HYPOTHESES.md keeps its name because the
dashboard build parses it.

Prior work and the thesis behind the question: RESEARCH.md.

## Original build plan (SPEC.md, commit d083dad, 2026-11-04)

The text below is the first plan, moved here unchanged from SPEC.md.
It was committed together with the first code and results.

### SPEC

#### Purpose
A working credit-risk modelling lab on public data, built to the duties in a
Data Scientist, Risk Modeling posting: develop and validate ML and statistical
risk models for credit decisioning, with IFRS 9 style staging and ECL.

#### Data
UCI "default of credit card clients" (Taiwan, 2005): 30,000 accounts, balances,
payment history (PAY_0..PAY_6), bill and payment amounts, default next month.
Public research dataset. Source: archive.ics.uci.edu, dataset 350.

#### Build
1. Load and clean the XLS (header row offset, EDUCATION/MARRIAGE recodes).
2. Behavioural features: utilization, payment ratio, delinquency mean/max,
   bill trend, on top of the raw account and payment-history fields.
3. Two PD models: logistic regression (scorecard-style baseline) and gradient
   boosting (challenger). Stratified 70/30 split, fixed seed.
4. Validation: AUC, KS, Gini, Brier score, calibration table, score PSI
   between train and test.
5. IFRS 9 style staging with a written policy (DPD proxy from PAY_0 plus a
   SICR rule on modelled PD), then ECL = PD x LGD x EAD by stage.
   LGD fixed at 45 percent and lifetime PD approximated as 1-(1-PD)^3.
   Both are stated lab assumptions, not measured values.
6. Outputs: results/results.json with every measured number, README results
   table generated from that file.

#### Tests
Dataset shape and target rate; champion AUC above 0.65; staging partitions the
portfolio exactly; ECL positive and stage-ordered (Stage 3 ECL rate highest);
calibration table has 10 bins.

#### Non-goals
No production claim. No real portfolio. No claim of employment experience in
credit risk: this is a public-data lab that demonstrates the method.
