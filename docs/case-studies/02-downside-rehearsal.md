# Case study 2: Downside rehearsal

*The scenario engine read as a 2026 Canada stress narrative. Market
figures are from RESEARCH.md (researched 2026-11-04); portfolio figures
are from results/scenarios.json. The portfolio is the lab's Taiwan
2005 book; the narrative is what the machinery is for.*

## The setup a risk committee actually faces

Canada enters the renewal wall with household credit-market debt at
179.6% of disposable income (Statistics Canada, Q1 2026, via secondary
reporting). The Bank of Canada's Financial Stability Report 2026
counts 12% of mortgages renewing within a year at payments roughly 15%
higher, and refinance failure at about 4% nationally, 9% in Toronto.
The unsecured book is already warm: Equifax Canada has non-mortgage
90+ delinquency at 1.76% and credit card 90+ at 4.19% (Q2 2026), with
1.5 million Canadians having missed a payment in Q1 2026 and
insolvencies up 18.8% year over year.

None of that enters a PD model directly. It enters as a question: if
household cash flow tightens by roughly this much, what happens to
expected loss? IFRS 9 (OSFI guideline, BCBS principles) requires the
answer to be probability-weighted across forward-looking scenarios,
not a single forecast defended to the death.

## The rehearsal

The lab's engine (src/scenarios.py) scales every champion PD by a
scenario multiplier and re-runs the unchanged staging policy. Weights
and multipliers are stated assumptions in config.json:

| Scenario | Weight | PD multiplier | Total ECL (NT$) |
| --- | --- | --- | --- |
| Upside | 0.20 | x0.85 | 171,347,227 |
| Base | 0.50 | x1.00 | 187,548,414 |
| Downside | 0.30 | x1.30 | 214,201,104 |
| **Probability-weighted** | | | **192,303,984** |

The base scenario reproduces the published pipeline ECL to the cent -
the engine asserts it in code, so the scenarios hang off a verified
anchor. The staging mix moves as it should: a downside pushes accounts
across the SICR boundary into Stage 2 lifetime ECL, which is where
most of the +NT$26.7M downside increment is born (Stage 2 ECL rises
from NT$113.7M to NT$121.4M, and Stage 1's from NT$63.1M to NT$82.0M
as its members' PDs scale).

## The punchline

**Probability-weighted ECL: NT$192,303,984, against a single-scenario
baseline of NT$187,548,414.** The weighting adds NT$4.76M (+2.5%):
the honest price of admitting the downside is more likely than the
upside, at weights a committee chose and wrote down. Beside it sits
the Basel floor view: at the QRRE foundation LGD floor of 50% instead
of the lab's 45% assumption, the same book carries NT$208,387,127.

That is the whole rehearsal: three numbers a committee can argue
about, each traceable to a stated assumption, a staging policy in
code, and an anchor that reproduces exactly. Argue about the weights,
argue about the multipliers, argue about the LGD floor - the argument
is the governance. What cannot be argued with is a single point
estimate whose assumptions nobody wrote down.

## What would change the rehearsal

- Vintage data. The book here is a 2005 cross-section; a real
  rehearsal re-runs on the current book with current behavioural
  features, which is why the pipeline reads raw data to ECL in one
  command (src/run_all.py).
- Macro-linked multipliers. Today the PD scaling is a flat stated
  assumption; a production engine ties it to unemployment and rate
  paths per segment. The lab labels the seam rather than sewing it
  shut.
- Segment scenarios. Renewal shock lands on mortgage holders first
  and transmits to unsecured; a segmented engine would stress the
  channels separately. The staging and scenario code takes per-account
  PDs, so segmentation is a data problem here, not a design change.
