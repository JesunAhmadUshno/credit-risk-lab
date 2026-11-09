import { useMemo, useState, useEffect, useId } from 'react';
import results from '../../results/results.json';
import dash from '../../results/dashboard_data.json';
import grades from '../../results/model_grades.json';
import scen from '../../results/scenarios.json';
import study from '../../results/study.json';
import secondLook from '../../results/second_look.json';
import rigor from '../../results/rigor.json';
import external from '../../results/external_validation.json';
import manifest from '../../results/run_manifest.json';
import behav from '../../results/behavioural_v2.json';
// Named imports let the bundler drop reason_codes.json's per-applicant rows.
import { label as reasonLabel, reason_frequencies as reasonFreq, rejected_applicants as reasonRejected, cutoff_pd as reasonCutoff } from '../../results/reason_codes.json';
import hypMd from '../../HYPOTHESES.md?raw';
import gapMd from '../../docs/analysis/GAP_ANALYSIS.md?raw';
import { cutoff, simulateEcl, mixScenarios, parseVerdicts, parseGaps, BASELINE } from './model.js';

const REPO = 'https://github.com/JesunAhmadUshno/credit-risk-lab';
const ROOT_DASHBOARD = 'https://jesunahmadushno.github.io/credit-risk-lab/';
const blob = (p) => `${REPO}/blob/main/${p}`;
const pct = (x, d = 1) => `${(x * 100).toFixed(d)}%`;
const fmt = (n) => Math.round(n).toLocaleString('en-US');
const ntm = (x, d = 1) => `NT$${(x / 1e6).toFixed(d)}M`;
const MODEL = { logistic_regression: 'Logistic regression', gradient_boosting: 'Gradient boosting' };
const champ = results.champion;
const cr = study.creditworthy_rejects;
const recorded = parseVerdicts(hypMd);
const gaps = parseGaps(gapMd);

const SECTIONS = [['top', 'Overview', '◎'], ['models', 'Models', '▥'], ['calibration', 'Calibration', '◔'], ['appetite', 'Risk appetite', '⇅'], ['ifrs9', 'IFRS 9 and ECL', '§'], ['fairness', 'Fair access', '⚖'], ['second', 'Second look', '↻'], ['hypotheses', 'Hypotheses', '✓'], ['external', 'External', '⇄'], ['reasons', 'Reason codes', '≡'], ['reproduce', 'Reproduce', '❯_']];

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

function MenuBar() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 30000); return () => clearInterval(t); }, []);
  return (
    <div className="menubar" role="banner">
      <span className="apple" aria-hidden="true">◆</span>
      <a className="app" href="#top">Credit Risk Lab</a>
      <a className="m" href={blob('HYPOTHESES.md')}>Hypotheses</a>
      <a className="m" href={blob('VALIDATION.md')}>Validation</a>
      <a className="m" href={blob('STUDY.md')}>Study</a>
      <a className="m" href={ROOT_DASHBOARD}>App dashboard</a>
      <span className="spacer" />
      <span className="status"><i /> {manifest.complete ? 'Run manifest complete' : 'Run incomplete'}</span>
      <a href={REPO}>GitHub ↗</a>
      <span className="clock">{now.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</span>
    </div>
  );
}

function Dock() {
  const [active, setActive] = useState('top');
  useEffect(() => {
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)), { rootMargin: '-45% 0px -50% 0px' });
    SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);
  return (
    <nav className="dock" aria-label="Sections">
      {SECTIONS.map(([id, label, icon]) => (
        <a key={id} href={`#${id}`} className={active === id ? 'on' : ''} aria-current={active === id ? 'true' : undefined} aria-label={label}>
          <span className="ico" aria-hidden="true">{icon}</span><span className="lbl">{label}</span>
        </a>
      ))}
    </nav>
  );
}

function Range({ label, value, min, max, step, onChange, show }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label} <span>{show}</span></label>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} />
    </div>
  );
}

const Verdict = ({ v }) => <span className={`pill ${v === 'CONFIRMED' ? 'good' : v === 'REFUTED' ? 'bad' : 'warn'}`}>● {v}</span>;

export default function App() {
  useReveal();
  return (
    <div className="wrap">
      <MenuBar />
      <div className="glow" aria-hidden="true" />
      <Hero />
      <Models />
      <Calibration />
      <Appetite />
      <Ifrs9 />
      <Fairness />
      <SecondLook />
      <Hypotheses />
      <External />
      <Reasons />
      <Reproduce />
      <Dock />
      <footer>
        Data: UCI Default of Credit Card Clients (Yeh and Lien, 2009) and UCI Statlog German Credit. Every number on this page is read from <code>results/</code>, <code>HYPOTHESES.md</code> or the gap register at build time; the calculators run in your browser on those recorded figures.
      </footer>
    </div>
  );
}

function Hero() {
  const g = grades.models[grades.champion];
  const ci = rigor.taiwan.champion_auc;
  return (
    <header className="card hero window" id="top" data-title="credit-risk-lab — README">
      <div className="head">
        <p className="eyebrow">PD models · IFRS 9 · pre-registered fair access study</p>
        <span className="pill info">● Public data, not a production system</span>
      </div>
      <h1>A gradient-boosting default model ranks {fmt(results.dataset.rows)} Taiwan card accounts at AUC {results.models.gradient_boosting.auc.toFixed(3)}, yet {pct(cr.creditworthy_share_of_rejected)} of the applicants it rejects at a {pct(cr.risk_appetite.target_approved_default_rate, 0)} risk appetite <em>never default</em>.</h1>
      <p className="sub">
        Probability-of-default models, a validation pack, IFRS 9 style staging and expected credit loss, and a study of who a cut-off scorecard turns away, all on the public UCI credit card dataset (Taiwan, 2005).
        Rejects are counted on {fmt(cr.test_accounts)} held-out accounts whose outcomes are known, which a real lender never sees. The four hypotheses were registered before the experiments ran, and one was refuted.
      </p>
      <div className="actions">
        <a className="btn primary" href="#appetite">Move the risk appetite</a>
        <a className="btn ghost" href={blob('HYPOTHESES.md')}>Read the hypotheses</a>
        <span className="hint">Scope: Taiwan 2005 proxy population, LGD assumed, no time dimension.</span>
      </div>
      <div className="tiles">
        <div className="tile"><div className="num">{fmt(results.dataset.rows)}</div><div className="cap">accounts, {pct(results.dataset.default_rate, 2)} default within a month</div></div>
        <div className="tile"><div className="num">{results.models[champ].auc.toFixed(3)}</div><div className="cap">champion AUC, bootstrap 95% CI {ci.lo95.toFixed(4)} to {ci.hi95.toFixed(4)}</div></div>
        <div className="tile"><div className="num">{ntm(results.staging.total_ecl)}</div><div className="cap">total ECL at the {pct(results.staging.lgd_assumption, 0)} LGD assumption</div></div>
        <div className="tile"><div className="num">{g.total_points}</div><div className="cap">of 1,000 grading points, band {g.letter_band}</div></div>
      </div>
    </header>
  );
}

function interp(pts, f) {
  for (let i = 1; i < pts.length; i++) if (pts[i].fpr >= f) {
    const a = pts[i - 1], b = pts[i], t = b.fpr === a.fpr ? 1 : (f - a.fpr) / (b.fpr - a.fpr);
    return a.tpr + t * (b.tpr - a.tpr);
  }
  return 1;
}

function Models() {
  const [fpr, setFpr] = useState(0.2);
  const [view, setView] = useState(champ);
  const W = 420, H = 340, pad = { l: 40, r: 10, t: 10, b: 32 };
  const sx = (v) => pad.l + v * (W - pad.l - pad.r), sy = (v) => pad.t + (1 - v) * (H - pad.t - pad.b);
  const colors = { logistic_regression: 'var(--warn)', gradient_boosting: 'var(--primary)' };
  const g = grades.models[view];
  const metrics = [['AUC', 'auc'], ['KS', 'ks'], ['Gini', 'gini'], ['Brier (lower is better)', 'brier']];
  return (
    <section id="models" className="card window reveal" data-title="pd_models.py — logistic vs gradient boosting">
      <p className="eyebrow">Discrimination</p>
      <h2>Gradient boosting beats the logistic baseline on all four metrics.</h2>
      <p className="sub">Both models train on {fmt(results.dataset.train_rows)} accounts and are scored on the same {fmt(results.dataset.test_rows)}-account test split (seed {results.config.seed}). ROC points and deciles are recorded from the pipeline run, not recomputed here.</p>
      <div style={{ overflowX: 'auto', marginTop: 16 }}>
        <table>
          <thead><tr><th>Model</th>{metrics.map(([l]) => <th key={l}>{l}</th>)}<th>Score PSI train vs test</th></tr></thead>
          <tbody>
            {Object.keys(MODEL).map((m) => (
              <tr key={m}><td>{MODEL[m]}{m === champ && <> <span className="pill info">champion</span></>}</td>{metrics.map(([, k]) => <td key={k}>{results.models[m][k].toFixed(4)}</td>)}<td>{results.models[m].score_psi.toFixed(4)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid2" style={{ marginTop: 20 }}>
        <div>
          <h3>ROC explorer <span className="pill info">recorded</span></h3>
          <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="ROC curves for logistic regression and gradient boosting on the test set" style={{ marginTop: 8 }}>
            {[0, 0.25, 0.5, 0.75, 1].map((t) => <g key={t}><line className="axis" x1={sx(0)} x2={sx(1)} y1={sy(t)} y2={sy(t)} /><text x={pad.l - 6} y={sy(t) + 4} textAnchor="end">{t}</text><text x={sx(t)} y={H - 16} textAnchor="middle">{t}</text></g>)}
            <line x1={sx(0)} y1={sy(0)} x2={sx(1)} y2={sy(1)} stroke="var(--muted)" strokeDasharray="4 4" />
            {Object.keys(MODEL).map((m) => <polyline key={m} fill="none" stroke={colors[m]} strokeWidth="2.5" points={dash.roc[m].map((p) => `${sx(p.fpr)},${sy(p.tpr)}`).join(' ')} />)}
            <line x1={sx(fpr)} x2={sx(fpr)} y1={sy(0)} y2={sy(1)} stroke="var(--text)" strokeOpacity=".4" />
            {Object.keys(MODEL).map((m) => <circle key={m} cx={sx(fpr)} cy={sy(interp(dash.roc[m], fpr))} r="5" fill={colors[m]} stroke="var(--surface-strong)" strokeWidth="2" />)}
            <text x={sx(0.5)} y={H - 2} textAnchor="middle">false-positive rate</text>
          </svg>
          <div className="legend"><span><i style={{ background: colors.gradient_boosting }} />Gradient boosting</span><span><i style={{ background: colors.logistic_regression }} />Logistic regression</span></div>
          <Range label="False-positive rate (good accounts flagged)" value={fpr} min={0} max={1} step={0.01} onChange={setFpr} show={pct(fpr, 0)} />
          <div className="tip" aria-live="polite">At {pct(fpr, 0)} of good accounts flagged, gradient boosting catches {pct(interp(dash.roc.gradient_boosting, fpr))} of defaulters and logistic regression {pct(interp(dash.roc.logistic_regression, fpr))} (interpolated between recorded points).</div>
        </div>
        <div>
          <h3>Champion gains by risk decile <span className="pill info">recorded</span></h3>
          <div style={{ overflowX: 'auto', marginTop: 8 }}>
            <table>
              <thead><tr><th>Decile</th><th>Default rate</th><th>Lift</th><th>Defaults captured</th></tr></thead>
              <tbody>{dash.deciles.map((d) => <tr key={d.decile}><td>{d.decile}{d.decile === 1 ? ' (riskiest)' : ''}</td><td>{pct(d.defaultRate)}</td><td>{d.lift.toFixed(2)}×</td><td>{pct(d.cumulativeCapture)}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      </div>
      <div className="head" style={{ marginTop: 24, marginBottom: 8 }}>
        <div><h3>1,000-point grading scorecard</h3><p className="hint" style={{ margin: '4px 0 0' }}>{grades.scorecard}</p></div>
        <div className="seg" role="group" aria-label="Choose model for the scorecard">
          {Object.keys(MODEL).map((m) => <button key={m} aria-pressed={view === m} onClick={() => setView(m)}>{MODEL[m]}</button>)}
        </div>
      </div>
      <p style={{ marginTop: 0, marginBottom: 10 }}><b style={{ fontSize: 20 }}>{g.total_points}</b> points, band <b>{g.letter_band}</b></p>
      <div className="bars">
        {g.components.map((c) => (
          <div className="bar-row" key={c.component}>
            <div className="lab"><span>{c.component} <span className="hint">· {c.detail}</span></span><b>{c.points} / {c.max_points} (−{c.deduction})</b></div>
            <div className="track"><div className="fill" style={{ width: `${(c.points / c.max_points) * 100}%`, background: 'var(--primary)' }} /></div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Calibration() {
  const hl = results.validation.hosmer_lemeshow;
  const [view, setView] = useState(champ);
  const cal = results.models[view].calibration;
  const max = Math.ceil(Math.max(...Object.values(results.models).flatMap((m) => m.calibration.flatMap((c) => [c.pred, c.obs]))) * 10) / 10;
  const W = 460, H = 320, pad = { l: 44, r: 10, t: 10, b: 32 };
  const sx = (v) => pad.l + (v / max) * (W - pad.l - pad.r), sy = (v) => pad.t + (1 - v / max) * (H - pad.t - pad.b);
  const ticks = Array.from({ length: Math.round(max / 0.2) + 1 }, (_, i) => +(i * 0.2).toFixed(1));
  return (
    <section id="calibration" className="card window reveal" data-title="validation_pack.py — calibration">
      <p className="eyebrow">Calibration · open gap G9</p>
      <h2>The champion ranks better but fails a strict calibration test. The baseline passes.</h2>
      <p className="sub">Test accounts are split into ten bins of predicted PD; each point compares the mean predicted PD with the observed default rate. Hosmer-Lemeshow with {hl[champ].dof} degrees of freedom: a small p-value says the predicted probabilities are off somewhere. Silent recalibration was rejected because it would move every published PD, stage and ECL figure.</p>
      <div className="grid2" style={{ marginTop: 16 }}>
        <div>
          <div className="seg" role="group" aria-label="Choose model for the calibration chart" style={{ marginBottom: 8 }}>
            {Object.keys(MODEL).map((m) => <button key={m} aria-pressed={view === m} onClick={() => setView(m)}>{MODEL[m]}</button>)}
          </div>
          <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Predicted versus observed default rate in ten bins for ${MODEL[view]}`}>
            {ticks.map((t) => <g key={t}><line className="axis" x1={sx(0)} x2={sx(max)} y1={sy(t)} y2={sy(t)} /><text x={pad.l - 6} y={sy(t) + 4} textAnchor="end">{t}</text><text x={sx(t)} y={H - 16} textAnchor="middle">{t}</text></g>)}
            <line x1={sx(0)} y1={sy(0)} x2={sx(max)} y2={sy(max)} stroke="var(--muted)" strokeDasharray="4 4" />
            <polyline fill="none" stroke="var(--primary)" strokeWidth="2" points={cal.map((c) => `${sx(c.pred)},${sy(c.obs)}`).join(' ')} />
            {cal.map((c, i) => <circle key={i} cx={sx(c.pred)} cy={sy(c.obs)} r="5" fill="var(--primary)" stroke="var(--surface-strong)" strokeWidth="2"><title>{`predicted ${c.pred}, observed ${c.obs}, n ${c.n}`}</title></circle>)}
            <text x={sx(max / 2)} y={H - 2} textAnchor="middle">mean predicted PD (dashed line = perfect calibration)</text>
          </svg>
        </div>
        <div className="bars" style={{ alignContent: 'start' }}>
          {Object.keys(MODEL).map((m) => (
            <div className="tile" key={m}>
              <div className="head" style={{ marginBottom: 4 }}><h3>{MODEL[m]}</h3><span className={`pill ${hl[m].p_value < 0.05 ? 'bad' : 'good'}`}>{hl[m].p_value < 0.05 ? 'Fails at 5%' : 'Passes at 5%'}</span></div>
              <div className="num sm">p = {hl[m].p_value}</div>
              <div className="cap">HL statistic {hl[m].statistic}, {hl[m].groups} groups · calibration MAE {grades.models[m].inputs.calibration_mae}</div>
            </div>
          ))}
          <p className="note">In the safest bin the champion predicts {pct(results.models[champ].calibration[0].pred)} and observes {pct(results.models[champ].calibration[0].obs)}. Staging, ECL and the study all use the champion, so this flag travels with every figure below.</p>
        </div>
      </div>
    </section>
  );
}

function Appetite() {
  const bins = results.validation.score_distribution;
  const edges = bins.map((b) => b.bin_end).filter((e) => e < 1);
  const [i, setI] = useState(edges.findIndex((e) => e >= cr.cutoff_pd));
  const edge = edges[i];
  const r = cutoff(bins, edge);
  const maxN = Math.max(...bins.map((b) => b.default + b.non_default));
  const W = 960, H = 260, pad = { l: 44, r: 10, t: 16, b: 30 };
  const bw = (W - pad.l - pad.r) / bins.length;
  const sx = (v) => pad.l + v * (W - pad.l - pad.r), sy = (n) => pad.t + (1 - n / maxN) * (H - pad.t - pad.b);
  return (
    <section id="appetite" className="card window reveal" data-title="cutoff_explorer.app — live">
      <div className="head">
        <div>
          <p className="eyebrow">Live calculator · risk appetite</p>
          <h2>Tighten the cut-off and the rejected pile fills with people who would have paid.</h2>
          <p className="sub">Approve every test account whose champion PD is at or below the cut-off. The page recounts the recorded 20-bin score distribution of the {fmt(r.total)} test accounts in your browser. It is exact at the 0.05 bin edges only, so the study's own cut-off ({cr.cutoff_pd}) appears as a separate recorded marker.</p>
        </div>
        <span className="pill info">computed live</span>
      </div>
      <div className="controls" style={{ gridTemplateColumns: '1fr' }}>
        <Range label="Approve if PD is at or below" value={i} min={0} max={edges.length - 1} step={1} onChange={setI} show={edge.toFixed(2)} />
      </div>
      <div className="tiles" style={{ marginTop: 0 }}>
        <div className="tile"><div className="num">{fmt(r.approved)}</div><div className="cap">approved, {pct(r.approvalRate)} of applicants</div></div>
        <div className="tile"><div className="num">{pct(r.approvedDefaultRate)}</div><div className="cap">default rate of the approved book</div></div>
        <div className="tile"><div className="num">{fmt(r.rejected)}</div><div className="cap">rejected</div></div>
        <div className="tile"><div className="num">{pct(r.creditworthyShare)}</div><div className="cap">of rejects never default ({fmt(r.creditworthyRejects)} accounts)</div></div>
      </div>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Stacked histogram of champion PD for defaulters and non-defaulters with the chosen cut-off" style={{ marginTop: 16 }}>
        {[0, 500, 1000, 1500, 2000].filter((t) => t <= maxN).map((t) => <g key={t}><line className="axis" x1={pad.l} x2={W - pad.r} y1={sy(t)} y2={sy(t)} /><text x={pad.l - 6} y={sy(t) + 4} textAnchor="end">{fmt(t)}</text></g>)}
        {bins.map((b) => {
          const on = b.bin_end <= edge + 1e-9, x = sx(b.bin_start) + 1;
          return (
            <g key={b.bin_start} opacity={on ? 1 : 0.35}>
              <rect x={x} width={bw - 2} y={sy(b.non_default)} height={sy(0) - sy(b.non_default)} fill="var(--good)" rx="2" />
              <rect x={x} width={bw - 2} y={sy(b.non_default + b.default)} height={sy(0) - sy(b.default)} fill="var(--bad)" rx="2" />
            </g>
          );
        })}
        <line x1={sx(edge)} x2={sx(edge)} y1={pad.t - 6} y2={sy(0)} stroke="var(--text)" strokeWidth="2" />
        <text x={sx(edge) + 6} y={pad.t + 4} style={{ fill: 'var(--text)', fontWeight: 600 }}>cut-off {edge.toFixed(2)}</text>
        <line x1={sx(cr.cutoff_pd)} x2={sx(cr.cutoff_pd)} y1={pad.t + 20} y2={sy(0)} stroke="var(--primary)" strokeDasharray="4 3" strokeWidth="2" />
        <text x={sx(cr.cutoff_pd) + 6} y={pad.t + 32} style={{ fill: 'var(--primary)' }}>study {cr.cutoff_pd} (recorded)</text>
        {[0, 0.2, 0.4, 0.6, 0.8, 1].map((t) => <text key={t} x={sx(t)} y={H - 10} textAnchor="middle">{t}</text>)}
      </svg>
      <div className="legend"><span><i style={{ background: 'var(--good)' }} />Did not default</span><span><i style={{ background: 'var(--bad)' }} />Defaulted</span><span>Faded bars are rejected.</span></div>
      <p className="note info" style={{ marginTop: 14 }}>Recorded study point: cut-off {cr.cutoff_pd} approves {fmt(cr.approved)} ({pct(cr.approval_rate)}) at an approved-book default rate of {pct(cr.achieved_approved_default_rate)}, matching the Stage 1 rate, and rejects {fmt(cr.rejected)}, of whom {fmt(cr.creditworthy_rejects)} ({pct(cr.creditworthy_share_of_rejected)}) never default. Bootstrap 95% CI for that share: {pct(rigor.taiwan.creditworthy_reject_share.lo95)} to {pct(rigor.taiwan.creditworthy_reject_share.hi95)}. Each resample re-selects its own cut-off, so the interval prices the whole procedure.</p>
    </section>
  );
}

function Ifrs9() {
  const [lgd, setLgd] = useState(BASELINE.lgd);
  const [shift, setShift] = useState(BASELINE.pdShift);
  const [years, setYears] = useState(BASELINE.years);
  const sim = simulateEcl(dash.simulatorStages, { lgd, pdShift: shift, years });
  const [w, setW] = useState(scen.weights);
  const [floor, setFloor] = useState(false);
  const mix = mixScenarios(scen, w, floor);
  const isBase = lgd === BASELINE.lgd && shift === BASELINE.pdShift && years === BASELINE.years;
  const maxEcl = Math.max(...sim.rows.flatMap((r) => [r.sim, r.base]));
  const d = sim.total - sim.baseTotal;
  return (
    <section id="ifrs9" className="card window reveal" data-title="ifrs9_staging.py — staging · ECL · scenarios">
      <p className="eyebrow">IFRS 9 style staging and expected credit loss</p>
      <h2>Stage 2 holds a quarter of the accounts and most of the loss allowance.</h2>
      <p className="sub">Champion PDs are refit on all {fmt(results.dataset.rows)} accounts and staged by the written policy below. ECL = applied PD × LGD × EAD, where LGD is an assumed {pct(results.staging.lgd_assumption, 0)} and EAD is the current bill.</p>
      <div className="tiles three">
        {results.staging.by_stage.map((s) => (
          <div className="tile" key={s.stage}>
            <div className="head" style={{ marginBottom: 2 }}><h3>Stage {s.stage}</h3><span className={`pill ${s.stage === 1 ? 'good' : s.stage === 2 ? 'warn' : 'bad'}`}>{pct(s.observed_default_rate, 0)} defaulted</span></div>
            <div className="num sm">{fmt(s.accounts)}</div>
            <div className="cap">accounts · ECL {ntm(s.ecl)} on EAD {ntm(s.ead, 0)}</div>
          </div>
        ))}
      </div>
      <p className="hint" style={{ marginTop: 10 }}><b>Policy:</b> {results.staging.policy}</p>

      <div className="head" style={{ marginTop: 28, marginBottom: 8 }}>
        <div><h3>ECL sensitivity simulator</h3><p className="hint" style={{ margin: '4px 0 0' }}>A sensitivity calculation on the published per-stage aggregates, not a model re-run. Stage 2 uses lifetime PD = 1 − (1 − PD)^years.</p></div>
        <span className="pill info">computed live</span>
      </div>
      <div className="controls">
        <Range label="Loss given default" value={lgd} min={0.1} max={0.9} step={0.01} onChange={setLgd} show={pct(lgd, 0)} />
        <Range label="PD multiplier" value={shift} min={0.5} max={2} step={0.05} onChange={setShift} show={`${shift.toFixed(2)}×`} />
        <Range label="Stage 2 lifetime (years)" value={years} min={1} max={5} step={1} onChange={setYears} show={years} />
      </div>
      <div className="grid2">
        <div className="tile">
          <div className="num">NT${fmt(sim.total)}</div>
          <div className="delta" style={{ color: d > 0.5 ? 'var(--bad)' : d < -0.5 ? 'var(--good)' : 'var(--muted)' }}>{isBase ? 'Baseline: matches the published total exactly' : `${d > 0 ? '+' : '−'}${ntm(Math.abs(d))} vs published ${ntm(sim.baseTotal)}`}</div>
          <div className="actions" style={{ marginTop: 12 }}><button className="btn ghost" onClick={() => { setLgd(BASELINE.lgd); setShift(BASELINE.pdShift); setYears(BASELINE.years); }} disabled={isBase}>Reset to published baseline</button></div>
        </div>
        <div className="bars">
          {sim.rows.map((r) => (
            <div className="bar-row" key={r.stage}>
              <div className="lab"><span>Stage {r.stage}</span><b>{ntm(r.sim)}</b></div>
              <div className="track"><div className="fill" style={{ width: `${(r.sim / maxEcl) * 100}%`, background: r.stage === 1 ? 'var(--good)' : r.stage === 2 ? 'var(--warn)' : 'var(--bad)' }} /><div className="ref" style={{ left: `${(r.base / maxEcl) * 100}%` }} title={`Published ${ntm(r.base)}`} /></div>
            </div>
          ))}
          <p className="hint" style={{ margin: 0 }}>Black ticks mark the published ECL per stage.</p>
        </div>
      </div>

      <div className="head" style={{ marginTop: 28, marginBottom: 8 }}>
        <div><h3>Scenario-weight mixer</h3><p className="hint" style={{ margin: '4px 0 0' }}>Weights are normalised to sum to 1. Scenario totals and PD multipliers are recorded in <a href={blob('results/scenarios.json')}>scenarios.json</a>; the weights and multipliers are stated lab assumptions, not macro forecasts.</p></div>
        <span className="pill info">computed live</span>
      </div>
      <div className="controls">
        {['upside', 'base', 'downside'].map((n) => <Range key={n} label={`${n[0].toUpperCase() + n.slice(1)} weight (PD × ${scen.pd_multipliers[n]})`} value={w[n]} min={0} max={1} step={0.05} onChange={(v) => setW({ ...w, [n]: v })} show={pct(mix.parts.find((p) => p.name === n).weight, 0)} />)}
      </div>
      <div className="grid2">
        <div className="tile">
          <div className="num">NT${fmt(mix.weighted)}</div>
          <div className="cap">probability-weighted ECL{floor ? ` at the Basel QRRE ${pct(scen.basel_floor.qrre_lgd_floor, 0)} LGD floor` : ` at ${pct(scen.lgd, 0)} LGD`}. Recorded at {Object.entries(scen.weights).map(([k, v]) => `${k} ${v}`).join(', ')}: NT${fmt(scen.weighted_ecl)}.</div>
          <div className="actions" style={{ marginTop: 12 }}>
            <label className="check"><input type="checkbox" checked={floor} onChange={(e) => setFloor(e.target.checked)} /> Apply Basel QRRE LGD floor</label>
            <button className="btn ghost" onClick={() => setW(scen.weights)}>Reset weights</button>
          </div>
        </div>
        <div className="bars">
          {mix.parts.map((p) => (
            <div className="bar-row" key={p.name}>
              <div className="lab"><span style={{ textTransform: 'capitalize' }}>{p.name}</span><b>{ntm(p.total)} × {p.weight.toFixed(2)}</b></div>
              <div className="track"><div className="fill" style={{ width: `${(p.total / (scen.scenarios.downside.total_ecl * scen.basel_floor.qrre_lgd_floor / scen.basel_floor.lgd_assumption)) * 100}%`, background: 'var(--primary)', opacity: 0.4 + p.weight * 0.6 }} /></div>
            </div>
          ))}
          <p className="hint" style={{ margin: 0 }}>{scen.basel_floor.note}</p>
        </div>
      </div>
    </section>
  );
}

function Fairness() {
  const vars = Object.keys(study.fairness.by_variable);
  const [v, setV] = useState(study.fairness.largest_gap.variable);
  const groups = study.fairness.by_variable[v].groups;
  const sl = Object.fromEntries((secondLook.fairness[v] || []).map((g) => [g.group, g]));
  const id = useId();
  const tf = study.thin_file;
  return (
    <section id="fairness" className="card window reveal" data-title="study.py — fair access">
      <p className="eyebrow">Fair access study</p>
      <h2>{fmt(cr.creditworthy_rejects)} of {fmt(cr.rejected)} rejects never default, and a model without bureau-style fields nearly keeps up.</h2>
      <p className="sub">The thin-file model uses behavioural payment features only ({tf.features.length} of them; limit, age, sex, education, marriage, bills and payment amounts excluded). It reaches AUC {tf.auc} against the full model's {tf.full_model_auc}, a gap of {tf.auc_gap_vs_full} (bootstrap 95% CI for thin-file AUC {rigor.taiwan.thin_file_auc.lo95} to {rigor.taiwan.thin_file_auc.hi95}).</p>
      <div className="head" style={{ marginTop: 20, marginBottom: 8 }}>
        <h3>Fairness explorer <span className="pill info">recorded</span></h3>
        <div className="field" style={{ minWidth: 200 }}><label htmlFor={id}>Protected variable</label>
          <select id={id} value={v} onChange={(e) => setV(e.target.value)}>{vars.map((k) => <option key={k} value={k}>{k}</option>)}</select>
        </div>
      </div>
      <div className="bars">
        {groups.map((g) => (
          <div className="bar-row" key={g.group}>
            <div className="lab"><span>{g.group} <span className="hint">· n = {fmt(g.n)}{g.n < 200 ? ' (small group)' : ''}</span></span><b>{pct(g.approval_rate)} approved</b></div>
            <div className="track"><div className="fill" style={{ width: `${g.approval_rate * 100}%`, background: 'var(--primary)' }} /></div>
          </div>
        ))}
      </div>
      <div style={{ overflowX: 'auto', marginTop: 16 }}>
        <table>
          <thead><tr><th>Group</th><th>n</th><th>Approval rate</th><th>Default rate</th><th>AUC</th><th>Rejected</th><th>Creditworthy rejects</th><th>Recovered on second look</th></tr></thead>
          <tbody>{groups.map((g) => <tr key={g.group}><td>{g.group}</td><td>{fmt(g.n)}</td><td>{pct(g.approval_rate)}</td><td>{pct(g.default_rate)}</td><td>{g.auc.toFixed(4)}</td><td>{sl[g.group] ? fmt(sl[g.group].rejected) : 'n/a'}</td><td>{sl[g.group] ? fmt(sl[g.group].creditworthy_rejects) : 'n/a'}</td><td>{sl[g.group] ? `${sl[g.group].recovered_creditworthy} (${pct(sl[g.group].recovery_rate_of_creditworthy)})` : 'n/a'}</td></tr>)}</tbody>
        </table>
      </div>
      <p className="note" style={{ marginTop: 14 }}>Approval-rate gap for {v}: {pct(study.fairness.by_variable[v].approval_rate_gap)}. These are raw gaps on a Taiwan 2005 proxy population (open gap G8), with no significance test or equalised-odds measure; groups under a few hundred accounts give noisy rates. Differences in default rate between groups mean an approval gap is not by itself evidence of bias.</p>
    </section>
  );
}

function SecondLook() {
  const h = secondLook.headline, ci = secondLook.bootstrap_ci95.recovery_rate_of_creditworthy;
  const steps = [['Test accounts', h.test_accounts], ['Rejected at stage 1', h.stage1_rejected], ['Of whom never default', h.creditworthy_rejects_stage1], ['Recovered on second look (creditworthy)', h.recovered_creditworthy]];
  return (
    <section id="second" className="card window reveal" data-title="second_look.py — Second-Look Recovery Policy">
      <p className="eyebrow">Pre-registered policy test · H1</p>
      <h2>A second look by the thin-file model recovers almost no one.</h2>
      <p className="sub">{secondLook.policy.stage2} {secondLook.policy.band_rule} (threshold {secondLook.policy.band_threshold_thin_pd}).</p>
      <div className="funnel" style={{ marginTop: 18 }}>
        {steps.map(([k, n]) => (
          <div className="row" key={k}><span>{k}</span><div className="bar-wrap"><div className="bar" style={{ width: `${(n / h.test_accounts) * 100}%` }} /></div><b>{fmt(n)}</b></div>
        ))}
      </div>
      <div className="tiles three">
        <div className="tile"><div className="num sm">{pct(h.recovery_rate_of_creditworthy)}</div><div className="cap">recovery rate, bootstrap 95% CI {pct(ci.lo95, 2)} to {pct(ci.hi95, 2)}; the registered bar was 15%</div></div>
        <div className="tile"><div className="num sm">{h.admitted_defaults}</div><div className="cap">defaults admitted among {h.recovered_total} recoveries</div></div>
        <div className="tile"><div className="num sm">+{h.cost_default_rate_pp.toFixed(2)} pts</div><div className="cap">approved-book default rate, {pct(h.approved_book_default_rate_stage1, 2)} to {pct(h.approved_book_default_rate_after, 2)}</div></div>
      </div>
      <p className="hint" style={{ marginTop: 12 }}>The cost is negligible because the volume is: thin-file and champion scores are correlated, so few rejects look as safe as a typical approved applicant. Recovery by group is in the fairness table above.</p>
    </section>
  );
}

function Hypotheses() {
  const ms = rigor.multi_seed, h = secondLook.headline, tf = study.thin_file, m = external.models;
  const W = 460, H = 150, pad = { l: 16, r: 16 }, lo = -0.003, hi = 0.002;
  const sx = (v) => pad.l + ((v - lo) / (hi - lo)) * (W - pad.l - pad.r);
  const cards = [
    ['H1', 'Second look recovers creditworthy rejects at a bounded cost', `Recovery ${pct(h.recovery_rate_of_creditworthy)} of creditworthy rejects (bar: at least 15%); cost +${h.cost_default_rate_pp.toFixed(2)} points (bar: at most 1.00).`],
    ['H2', 'Thin-file model stays within 0.03 AUC of the full model', `Thin-file AUC ${tf.auc} vs ${tf.full_model_auc}: gap ${tf.auc_gap_vs_full}.`],
    ['H3', 'Behavioural v2 is at least as good as v1 across seeds', `Mean AUC over ${ms.seeds.length} seeds: v1 ${ms.v1.mean_auc} (sd ${ms.v1.std_auc}), v2 ${ms.v2.mean_auc} (sd ${ms.v2.std_auc}); mean delta ${ms.mean_delta}, inside the inconclusive band.`],
    ['H4', 'The approach transports to German Credit', `German AUC: gradient boosting ${m.gradient_boosting.auc} (bar 0.65), logistic ${m.logistic_regression.auc} (bar 0.60).`],
  ];
  return (
    <section id="hypotheses" className="card window reveal" data-title="HYPOTHESES.md — registered before the runs">
      <p className="eyebrow">Pre-registered hypotheses · verdicts as recorded</p>
      <h2>Four hypotheses, thresholds written first. One refuted, one inconclusive.</h2>
      <p className="sub">Verdicts are read from <a href={blob('HYPOTHESES.md')}>HYPOTHESES.md</a>. The build re-applies each registered rule to the results files and fails if it disagrees with the recorded verdict.</p>
      <div className="grid2" style={{ marginTop: 16, alignItems: 'start' }}>
        {cards.map(([k, t, d]) => (
          <div className="tile" key={k}>
            <div className="head" style={{ marginBottom: 6 }}><h3>{k}: {t}</h3><Verdict v={recorded[k]} /></div>
            <p className="hint" style={{ margin: 0, fontSize: 13 }}>{d}</p>
            {k === 'H3' && (
              <>
                <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Per-seed AUC change from behavioural v1 to v2 across five seeds" style={{ marginTop: 10 }}>
                  <rect x={sx(-0.002)} width={sx(0) - sx(-0.002)} y={20} height={80} fill="var(--warn)" opacity=".12" />
                  <line x1={sx(0)} x2={sx(0)} y1={14} y2={106} stroke="var(--text)" strokeOpacity=".5" />
                  <line x1={sx(-0.002)} x2={sx(-0.002)} y1={14} y2={106} stroke="var(--bad)" strokeDasharray="4 3" />
                  {ms.per_seed.map((s, i) => <g key={s.seed}><circle cx={sx(s.delta)} cy={30 + i * 16} r="5" fill={s.delta >= 0 ? 'var(--good)' : 'var(--bad)'} /><text x={sx(s.delta) + 9} y={34 + i * 16}>seed {s.seed}: {s.delta > 0 ? '+' : ''}{s.delta}</text></g>)}
                  <line x1={sx(ms.mean_delta)} x2={sx(ms.mean_delta)} y1={20} y2={100} stroke="var(--primary)" strokeWidth="3" />
                  {[-0.003, -0.002, -0.001, 0, 0.001, 0.002].map((t) => <text key={t} x={sx(t)} y={124} textAnchor="middle">{t > 0 ? '+' : ''}{t}</text>)}
                  <text x={W / 2} y={144} textAnchor="middle">AUC v2 − v1 per seed (blue: mean; shaded: inconclusive band)</text>
                </svg>
                <p className="note" style={{ marginTop: 8 }}>Superseded: <span className="mono">behavioural_v2.json</span> still records "{behav.verdict}" from the single seed-{ms.per_seed[0].seed} run (+{behav.delta_auc}). The multi-seed test above replaces it.</p>
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function External() {
  const t = rigor.taiwan.champion_auc;
  const rows = [
    { k: 'German · logistic regression', m: external.models.logistic_regression, ci: rigor.german.logistic_regression, c: 'var(--warn)' },
    { k: 'German · gradient boosting', m: external.models.gradient_boosting, ci: rigor.german.gradient_boosting, c: 'var(--warn)' },
    { k: 'Taiwan · gradient boosting (champion)', m: results.models[champ], ci: t, c: 'var(--primary)', sep: true },
  ];
  const W = 960, rowH = 46, H = rows.length * rowH + 50, l = 300, r = 20, lo = 0.65, hi = 0.9;
  const x = (v) => l + ((v - lo) / (hi - lo)) * (W - l - r);
  return (
    <section id="external" className="card window reveal" data-title="german_credit.py — external validation">
      <p className="eyebrow">External validation · H4</p>
      <h2>The same recipe reaches similar AUC on a different population, with intervals five times wider.</h2>
      <p className="note" style={{ marginTop: 12 }}>{external.dataset.population_note}</p>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="AUC with bootstrap 95% intervals for German Credit models and the Taiwan champion" style={{ marginTop: 14 }}>
        {[0.65, 0.7, 0.75, 0.8, 0.85, 0.9].map((v) => <g key={v}><line className="axis" x1={x(v)} x2={x(v)} y1={0} y2={H - 24} /><text x={x(v)} y={H - 8} textAnchor="middle">{v}</text></g>)}
        {rows.map((row, i) => {
          const y = i * rowH + 26 + (row.sep ? 14 : 0);
          return (
            <g key={row.k}>
              {row.sep && <line x1={0} x2={W} y1={y - 26} y2={y - 26} stroke="var(--border)" strokeDasharray="6 4" />}
              <text x={0} y={y + 4} style={{ fill: 'var(--text)', fontSize: 13 }}>{row.k}</text>
              <line x1={x(row.ci.lo95)} x2={x(row.ci.hi95)} y1={y} y2={y} stroke={row.c} strokeWidth="3" strokeLinecap="round" opacity=".6" />
              <circle cx={x(row.m.auc)} cy={y} r="6" fill={row.c} />
              <text x={x(row.m.auc)} y={y - 10} textAnchor="middle" style={{ fill: 'var(--text)' }}>{row.m.auc.toFixed(4)}</text>
            </g>
          );
        })}
      </svg>
      <p className="sub">{external.dataset.rows} German accounts ({external.dataset.test_rows} in test, {pct(external.dataset.bad_rate, 0)} bad) against {fmt(results.dataset.test_rows)} Taiwan test accounts. Like-for-like gap (gradient boosting both places): {external.transportability.gap_like_for_like}. {external.transportability.reading}</p>
    </section>
  );
}

function Reasons() {
  const max = reasonFreq[0].count;
  return (
    <section id="reasons" className="card window reveal" data-title="reason_codes.py — principal reasons">
      <p className="eyebrow">Reason codes</p>
      <h2>Recent payment delay is the most common principal reason for rejection.</h2>
      <p className="sub">Up to three reasons for each of the {fmt(reasonRejected)} applicants rejected at cut-off {reasonCutoff}, from permutation importance on the champion. Share of rejects that carry each reason:</p>
      <div className="bars" style={{ marginTop: 16 }}>
        {reasonFreq.map((f) => (
          <div className="bar-row" key={f.feature}>
            <div className="lab"><span>{f.reason}</span><b>{fmt(f.count)} · {pct(f.share_of_rejected)}</b></div>
            <div className="track"><div className="fill" style={{ width: `${(f.count / max) * 100}%`, background: 'var(--primary)' }} /></div>
          </div>
        ))}
      </div>
      <p className="note" style={{ marginTop: 14 }}>{reasonLabel}</p>
    </section>
  );
}

function Reproduce() {
  const steps = manifest.steps.filter((s) => s.seconds > 0);
  const max = Math.max(...steps.map((s) => s.seconds));
  const inv = manifest.invariants_verified;
  const shown = gaps.filter((g) => ['G7', 'G8', 'G9', 'G10', 'G13', 'G14'].includes(g.id));
  const docs = [
    ['HYPOTHESES.md', 'Hypotheses', 'Registered rules and verdicts'],
    ['VALIDATION.md', 'Validation pack', 'SR 11-7 / E-23 style review'],
    ['MODEL_CARD.md', 'Model card', 'Intended use and limits'],
    ['STUDY.md', 'Fair access study', 'Creditworthy rejects, thin file'],
    ['docs/analysis/GAP_ANALYSIS.md', 'Gap register', 'Open and closed gaps'],
    ['REPORT.md', 'Report', 'Results, misses, threats, review notes'],
  ];
  return (
    <section id="reproduce" className="card window reveal" data-title="Terminal — python src/run_all.py">
      <p className="eyebrow">Reproduce it · limits</p>
      <h2>One command rebuilds every results file and checks its invariants.</h2>
      <ol className="steps" style={{ marginTop: 16 }}>
        <li><span className="n">1</span><div><b>Install the pinned environment and run</b><div className="hint"><code>pip install -r requirements.txt && python src/run_all.py</code></div></div></li>
        <li><span className="n">2</span><div><b>Manifest</b><div className="hint">Commit <span className="mono">{manifest.git_commit.slice(0, 7)}</span>, {manifest.total_seconds} s in total, invariants verified: logistic AUC {inv.logistic_auc}, champion AUC {inv.champion_auc}, staging {inv.staging_counts.map(fmt).join(' / ')}, ECL NT${fmt(inv.baseline_ecl)}.</div></div></li>
        <li><span className="n">3</span><div><b>Input hashes (SHA-256)</b><div className="hint">{Object.entries(manifest.dataset_sha256).map(([f, h]) => <div key={f} className="wrapall"><span className="mono">{f.replace('data/', '')}</span>: <span className="mono wrapall">{h}</span></div>)}</div></div></li>
      </ol>
      <h3 style={{ marginTop: 22 }}>Step durations</h3>
      <div className="bars" style={{ marginTop: 10 }}>
        {steps.map((s) => (
          <div className="bar-row" key={s.step}>
            <div className="lab"><span className="mono">{s.step}</span><b>{s.seconds} s</b></div>
            <div className="track"><div className="fill" style={{ width: `${(s.seconds / max) * 100}%`, background: 'var(--primary)' }} /></div>
          </div>
        ))}
      </div>
      <h3 style={{ marginTop: 22 }}>Open gaps that limit what this shows</h3>
      <div className="gaps" style={{ marginTop: 10 }}>
        {shown.map((g) => <div key={g.id}><b>{g.id}</b>{g.title} <span className={`pill ${g.status === 'OPEN' ? 'warn' : 'good'}`}>{g.status}{g.severity ? ` · ${g.severity}` : ''}</span></div>)}
      </div>
      <p className="hint" style={{ marginTop: 10 }}>Also not modelled: LGD and EAD (EAD is the current bill, no undrawn limits); scenario multipliers are flat PD scalars, not linked to macro variables. The full app dashboard with drift and data-quality views stays at <a href={ROOT_DASHBOARD}>the Pages root</a>.</p>
      <div className="docs" style={{ marginTop: 20 }}>
        {docs.map(([p, t, dsc]) => <a key={p} href={blob(p)}><b>{t}</b><small>{dsc}</small></a>)}
      </div>
    </section>
  );
}
