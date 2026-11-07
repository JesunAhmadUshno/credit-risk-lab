// Pure calculations behind the live elements. Every input is a parsed results/*.json
// object (or markdown text) passed in by the caller; nothing here holds a number of its own
// except the registered hypothesis thresholds, which are copied from HYPOTHESES.md and
// checked against its recorded verdicts by model.check.mjs.

/** Risk-appetite cut-off over the recorded 20-bin champion score distribution.
 *  Approve every bin whose upper edge is at or below `edge`. Exact at bin edges only. */
export function cutoff(bins, edge) {
  let appN = 0, appD = 0, rejN = 0, rejD = 0;
  for (const b of bins) {
    if (b.bin_end <= edge + 1e-9) { appN += b.non_default; appD += b.default; }
    else { rejN += b.non_default; rejD += b.default; }
  }
  const approved = appN + appD, rejected = rejN + rejD, total = approved + rejected;
  return {
    approved, rejected, total,
    approvalRate: approved / total,
    approvedDefaultRate: approved ? appD / approved : 0,
    creditworthyRejects: rejN,
    creditworthyShare: rejected ? rejN / rejected : 0,
    rejectedDefaults: rejD,
  };
}

/** ECL sensitivity on published per-stage aggregates (the math of web/src/lib/sim.ts).
 *  Stage 1: meanPD x shift x LGD x EAD, written as baseline ECL x shift x LGD ratio, which is
 *  the same product but avoids the 8-digit rounding of meanPd (worth NT$0.13 at baseline).
 *  Stage 3: 1.0 x LGD x EAD.
 *  Stage 2: baseline ECL scaled by the lifetime-PD ratio 1-(1-PD)^years and the LGD ratio. */
export const BASELINE = { lgd: 0.45, pdShift: 1, years: 3 };
const lifetime = (pd, y) => 1 - Math.pow(1 - pd, y);
export function simulateEcl(stages, { lgd, pdShift, years }, base = BASELINE) {
  const rows = stages.map((s) => {
    let sim;
    if (s.stage === 3) sim = lgd * s.ead;
    else if (s.stage === 2) {
      const ratio = lifetime(Math.min(s.meanPd * pdShift, 1), years) / lifetime(Math.min(s.meanPd * base.pdShift, 1), base.years);
      sim = s.ecl * ratio * (lgd / base.lgd);
    } else sim = s.ecl * (pdShift / base.pdShift) * (lgd / base.lgd);
    return { stage: s.stage, accounts: s.accounts, ead: s.ead, base: s.ecl, sim };
  });
  return { rows, total: rows.reduce((a, r) => a + r.sim, 0), baseTotal: rows.reduce((a, r) => a + r.base, 0) };
}

/** Probability-weighted ECL from the three recorded scenario totals. Weights are normalised.
 *  ECL is linear in LGD (pd_applied x LGD x EAD), so the QRRE floor view scales every
 *  scenario by floor/assumption; the check confirms this reproduces ecl_at_qrre_lgd_floor. */
export function mixScenarios(scen, w, useFloor) {
  const sum = w.base + w.upside + w.downside || 1;
  const k = useFloor ? scen.basel_floor.qrre_lgd_floor / scen.basel_floor.lgd_assumption : 1;
  const parts = ['upside', 'base', 'downside'].map((n) => ({ name: n, weight: w[n] / sum, total: scen.scenarios[n].total_ecl * k, mult: scen.scenarios[n].pd_multiplier }));
  return { parts, weighted: parts.reduce((a, p) => a + p.weight * p.total, 0) };
}

/** Registered decision rules from HYPOTHESES.md, applied to the recorded results. */
export function verdicts({ secondLook, study, rigor, external }) {
  const h = secondLook.headline;
  const h1 = h.recovery_rate_of_creditworthy >= 0.15 && h.cost_default_rate_pp <= 1.0 ? 'CONFIRMED' : 'REFUTED';
  const h2 = study.thin_file.auc_gap_vs_full >= -0.03 ? 'CONFIRMED' : 'REFUTED';
  const v1 = rigor.multi_seed.v1.mean_auc, v2 = rigor.multi_seed.v2.mean_auc;
  const h3 = v2 >= v1 ? 'CONFIRMED' : v2 < v1 - 0.002 ? 'REFUTED' : 'INCONCLUSIVE';
  const m = external.models;
  const h4 = m.gradient_boosting.auc >= 0.65 && m.logistic_regression.auc >= 0.6 ? 'CONFIRMED' : 'REFUTED';
  return { H1: h1, H2: h2, H3: h3, H4: h4 };
}

/** Verdict lines as recorded in HYPOTHESES.md: "- **H1: REFUTED.**" */
export function parseVerdicts(md) {
  return Object.fromEntries([...md.matchAll(/\*\*(H\d): ([A-Z]+)\.\*\*/g)].map((m) => [m[1], m[2]]));
}

/** Gap register entries from GAP_ANALYSIS.md: "**G7. Title.**" plus the Severity and Status lines. */
export function parseGaps(md) {
  return md.split(/\n(?=\*\*G\d+\. )/).filter((b) => /^\*\*G\d+\. /.test(b)).map((b) => {
    const [, id, title] = b.match(/^\*\*(G\d+)\. (.+?)\*\*/);
    const flat = b.replace(/\s+/g, ' ');
    const status = (flat.match(/Status: ([A-Z]+)/) || [])[1] || '';
    const severity = (flat.match(/Severity: (\w+)/) || [])[1] || '';
    return { id, title: title.replace(/\.$/, ''), status, severity };
  });
}
