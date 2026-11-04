/**
 * ECL sensitivity simulator math.
 *
 * Works only on the published per-stage aggregates exported from the
 * pipeline (accounts, EAD, exposure-weighted mean PD, baseline ECL).
 * It is a sensitivity calculation on aggregates, not a model re-run.
 *
 * Stage 1: ECL = meanPD x pdShift x LGD x EAD (exact at baseline).
 * Stage 3: ECL = 1.0 x LGD x EAD (exact at baseline).
 * Stage 2: lifetime PD = 1 - (1 - PD)^years, applied to the stage's
 *   exposure-weighted mean PD and anchored to the published baseline ECL,
 *   so the baseline position (LGD 45%, shift 1.0, 3 years) reproduces the
 *   pipeline's ECL exactly for every stage.
 */

export interface StageAggregate {
  stage: number
  accounts: number
  ead: number
  ecl: number
  meanPd: number
  meanPdApplied: number
  observedDefaultRate: number
}

export interface SimParams {
  /** LGD as a fraction, 0.10 to 0.90. */
  lgd: number
  /** PD shift multiplier, 0.5 to 2.0. */
  pdShift: number
  /** Lifetime horizon in years for Stage 2, 1 to 5. */
  lifetimeYears: number
}

export interface SimStageResult extends StageAggregate {
  simEcl: number
  delta: number
}

export const BASELINE: SimParams = { lgd: 0.45, pdShift: 1.0, lifetimeYears: 3 }

const lifetimePd = (pd: number, years: number) => 1 - Math.pow(1 - pd, years)

export function simulateStage(stage: StageAggregate, p: SimParams): SimStageResult {
  const lgdRatio = p.lgd / BASELINE.lgd
  let simEcl: number
  if (stage.stage === 3) {
    // PD applied is 1.0 by policy: only LGD moves the number.
    simEcl = 1.0 * p.lgd * stage.ead
  } else if (stage.stage === 2) {
    const shifted = Math.min(stage.meanPd * p.pdShift, 1)
    const baseShifted = Math.min(stage.meanPd * BASELINE.pdShift, 1)
    const ratio =
      lifetimePd(shifted, p.lifetimeYears) /
      lifetimePd(baseShifted, BASELINE.lifetimeYears)
    simEcl = stage.ecl * ratio * lgdRatio
  } else {
    simEcl = stage.meanPd * p.pdShift * p.lgd * stage.ead
  }
  return { ...stage, simEcl, delta: simEcl - stage.ecl }
}

export function simulate(stages: readonly StageAggregate[], p: SimParams) {
  const rows = stages.map((s) => simulateStage(s, p))
  const baselineTotal = rows.reduce((a, r) => a + r.ecl, 0)
  const simTotal = rows.reduce((a, r) => a + r.simEcl, 0)
  return { rows, baselineTotal, simTotal, delta: simTotal - baselineTotal }
}
