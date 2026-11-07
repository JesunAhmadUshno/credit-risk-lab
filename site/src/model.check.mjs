// Known-answer self-check, run by `npm run build` before vite: node src/model.check.mjs
// Reproduces recorded numbers from results/*.json with the same functions the page runs.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { cutoff, simulateEcl, mixScenarios, verdicts, parseVerdicts, parseGaps, BASELINE } from './model.js';

const root = new URL('../../', import.meta.url);
const json = (p) => JSON.parse(readFileSync(new URL(p, root), 'utf8'));
const results = json('results/results.json');
const dash = json('results/dashboard_data.json');
const scen = json('results/scenarios.json');
const study = json('results/study.json');
const secondLook = json('results/second_look.json');
const rigor = json('results/rigor.json');
const external = json('results/external_validation.json');
const manifest = json('results/run_manifest.json');

// 1. ECL simulator at baseline reproduces the published total ECL (to the NT$).
const sim = simulateEcl(dash.simulatorStages, BASELINE);
assert.equal(Math.round(sim.total), Math.round(results.staging.total_ecl), `ECL ${sim.total} vs ${results.staging.total_ecl}`);
sim.rows.forEach((r, i) => assert.ok(Math.abs(r.sim - results.staging.by_stage[i].ecl) < 0.01, `stage ${r.stage} ECL ${r.sim}`));
// Stage 1 as baseline-anchored equals meanPd x LGD x EAD up to meanPd's rounding.
const s1 = dash.simulatorStages[0];
assert.ok(Math.abs(s1.meanPd * BASELINE.lgd * s1.ead - s1.ecl) < 1, 'stage 1 identity');
assert.deepEqual(dash.simulatorStages.map((s) => s.accounts), results.staging.by_stage.map((s) => s.accounts));

// 2. Scenario mixer at the recorded weights reproduces weighted_ecl; the floor view reproduces the Basel figure.
const mix = mixScenarios(scen, scen.weights, false);
assert.ok(Math.abs(mix.weighted - scen.weighted_ecl) < 0.01, `weighted ${mix.weighted} vs ${scen.weighted_ecl}`);
const floorBase = mixScenarios(scen, { base: 1, upside: 0, downside: 0 }, true).weighted;
assert.ok(Math.abs(floorBase - scen.basel_floor.ecl_at_qrre_lgd_floor) < 0.01, `floor ${floorBase}`);
assert.equal(manifest.invariants_verified.weighted_ecl, scen.weighted_ecl);

// 3. Score-distribution bins sum to the test set; the study cut-off lies inside the bins it claims.
const bins = results.validation.score_distribution;
const all = cutoff(bins, 1);
assert.equal(all.approved, results.dataset.test_rows);
assert.equal(bins.reduce((a, b) => a + b.default, 0), dash.deciles.reduce((a, d) => a + d.defaults, 0), 'bin defaults = decile defaults');
const cr = study.creditworthy_rejects;
assert.equal(cr.approved + cr.rejected, results.dataset.test_rows);
const lo = cutoff(bins, 0.2), hi = cutoff(bins, 0.25);
assert.ok(lo.approved <= cr.approved && cr.approved <= hi.approved, 'study approvals bracketed by the 0.20/0.25 bin edges');
assert.ok(hi.creditworthyRejects <= cr.creditworthy_rejects && cr.creditworthy_rejects <= lo.creditworthyRejects, 'creditworthy rejects bracketed');
assert.equal(Math.round(cr.creditworthy_rejects / cr.rejected * 10000) / 10000, cr.creditworthy_share_of_rejected);
assert.equal(secondLook.headline.creditworthy_rejects_stage1, cr.creditworthy_rejects);

// 4. Registered decision rules applied to the results give the verdicts recorded in HYPOTHESES.md.
const recorded = parseVerdicts(readFileSync(new URL('HYPOTHESES.md', root), 'utf8'));
assert.deepEqual(verdicts({ secondLook, study, rigor, external }), recorded);
assert.ok(Math.abs(rigor.multi_seed.per_seed.reduce((a, s) => a + s.delta, 0) / 5 - rigor.multi_seed.mean_delta) < 1e-4);

// 5. The gap register parses with the ids the page shows.
const gaps = parseGaps(readFileSync(new URL('docs/analysis/GAP_ANALYSIS.md', root), 'utf8'));
for (const id of ['G7', 'G8', 'G9', 'G10', 'G13', 'G14']) assert.ok(gaps.find((g) => g.id === id && g.status), id);

console.log('model ok', { ecl: Math.round(sim.total), weighted: +mix.weighted.toFixed(2), floor: +floorBase.toFixed(2), testRows: all.approved, verdicts: recorded });
