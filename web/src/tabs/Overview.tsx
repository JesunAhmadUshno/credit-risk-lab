import { data } from '../data/results'
import { CountUp, GradeGauge, Reveal } from '../components/ui'
import { fmtInt, fmtNTCompact, fmtPct } from '../lib/format'

const champ = data.models[data.champion]
const champGrade = data.grades.models[data.champion]
const maxMissing = Math.max(...Object.values(data.dataQuality.missing_rate_per_column))

function Kpi({
  label,
  value,
  format,
  note,
  delay,
}: {
  label: string
  value: number
  format: (n: number) => string
  note: string
  delay: number
}) {
  return (
    <Reveal delay={delay}>
      <div className="card kpi">
        <div className="label">{label}</div>
        <div className="value">
          <CountUp value={value} format={format} />
        </div>
        <div className="note">{note}</div>
      </div>
    </Reveal>
  )
}

export default function Overview() {
  return (
    <div>
      <Reveal>
        <p className="eyebrow">Credit risk modelling · measured, not claimed</p>
        <h1 className="section-title" style={{ fontSize: 30 }}>
          Probability-of-default models, graded like a model risk team would grade them.
        </h1>
        <p className="section-lede">
          Two PD models on {fmtInt(data.dataset.rows)} real credit accounts from the public UCI
          dataset: behavioural features, full validation (discrimination, calibration, stability),
          IFRS 9 style staging, and expected credit loss. Every figure on this page is computed by
          the pipeline and exported from its run output. Nothing is typed in by hand.
        </p>
      </Reveal>

      <div className="grid kpis">
        <Kpi label="Champion AUC" value={champ.auc} format={(n) => n.toFixed(4)} note="Gradient boosting, held-out test set" delay={0} />
        <Kpi label="Champion KS" value={champ.ks} format={(n) => n.toFixed(4)} note="Separation between defaults and non-defaults" delay={0.05} />
        <Kpi label="Portfolio ECL" value={data.staging.total_ecl} format={fmtNTCompact} note={`On ${fmtNTCompact(data.staging.total_ead)} exposure at default`} delay={0.1} />
        <Kpi label="Accounts" value={data.dataset.rows} format={fmtInt} note={`${fmtInt(data.dataset.train_rows)} train · ${fmtInt(data.dataset.test_rows)} test`} delay={0.15} />
        <Kpi label="Default rate" value={data.dataset.default_rate} format={(n) => fmtPct(n, 2)} note="Observed across the full portfolio" delay={0.2} />
      </div>

      <div style={{ height: 16 }} />

      <div className="grid two">
        <Reveal>
          <div className="card">
            <h3>Champion model, graded</h3>
            <p className="sub">
              Gradient boosting scores {champGrade.total_points.toFixed(2)} of 1000 on the lab
              scorecard: discrimination 500, calibration 300, stability 200. Deductions are named,
              never rounded away. Full breakdown in the Models tab.
            </p>
            <GradeGauge points={champGrade.total_points} band={champGrade.letter_band} />
          </div>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="card">
            <h3>Portfolio at a glance</h3>
            <p className="sub">{data.staging.policy}</p>
            <table className="data">
              <thead>
                <tr><th>Stage</th><th>Accounts</th><th>Default rate</th><th>ECL</th></tr>
              </thead>
              <tbody>
                {data.staging.by_stage.map((s) => (
                  <tr key={s.stage}>
                    <td>Stage {s.stage}</td>
                    <td className="mono">{fmtInt(s.accounts)}</td>
                    <td className="mono">{fmtPct(s.observed_default_rate)}</td>
                    <td className="mono">{fmtNTCompact(s.ecl)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="sub" style={{ marginTop: 12, marginBottom: 0 }}>
              Stage 2 carries the largest loss share despite holding fewer accounts than Stage 1:
              that is the SICR rule doing its job. Detail and charts in the Portfolio tab.
            </p>
          </div>
        </Reveal>
      </div>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="grid three">
          <div className="card">
            <h3>Data quality</h3>
            <p className="sub" style={{ marginBottom: 0 }}>
              {data.dataQuality.columns} columns · {fmtInt(data.dataQuality.rows)} rows · duplicate
              IDs: {data.dataQuality.duplicate_id_count} · highest missing rate in any column:{' '}
              {fmtPct(maxMissing, 2)}.
            </p>
          </div>
          <div className="card">
            <h3>Stability</h3>
            <p className="sub" style={{ marginBottom: 0 }}>
              Champion score PSI, train vs test: {data.validation.score_psi_train_vs_test}. Well
              under the 0.10 watch level. Per-feature drift is tabled in the Validation tab.
            </p>
          </div>
          <div className="card">
            <h3>Reproduce it</h3>
            <p className="sub mono" style={{ marginBottom: 0, fontSize: 12.5 }}>
              .venv/bin/python src/credit_risk_lab.py
              <br />
              .venv/bin/python -m pytest tests/ -q
            </p>
          </div>
        </div>
      </Reveal>
    </div>
  )
}
