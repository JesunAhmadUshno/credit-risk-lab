import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { motion } from 'framer-motion'
import { data } from '../data/results'
import { ChartTip, GradeGauge, MODEL_LABEL, ModelSwitcher, Reveal, type ModelKey } from '../components/ui'
import { GRAY, LINE, MUTED, PAPER, RED } from '../lib/format'

const GROUP_MAX: Record<string, number> = { discrimination: 500, calibration: 300, stability: 200 }
const GROUP_LABEL: Record<string, string> = {
  discrimination: 'Discrimination',
  calibration: 'Calibration',
  stability: 'Stability',
}

function GroupBars({ modelKey, dim }: { modelKey: ModelKey; dim?: boolean }) {
  const g = data.grades.models[modelKey]
  return (
    <div>
      {Object.entries(g.groups).map(([group, points]) => (
        <div className="gbar" key={group}>
          <div className="row">
            <span className="gname">{GROUP_LABEL[group] ?? group}</span>
            <span className="mono">
              {points.toFixed(2)} / {GROUP_MAX[group]}
            </span>
          </div>
          <div className="track">
            <motion.div
              className={`fill${dim ? ' dim' : ''}`}
              initial={{ width: 0 }}
              whileInView={{ width: `${(points / GROUP_MAX[group]) * 100}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.9, ease: 'easeOut' }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function GradeCard({ modelKey, champion }: { modelKey: ModelKey; champion?: boolean }) {
  const g = data.grades.models[modelKey]
  return (
    <div className="card">
      <h3>
        {MODEL_LABEL[modelKey]}
        {champion && <span className="pill" style={{ marginLeft: 10, borderColor: RED, color: RED }}>champion</span>}
      </h3>
      <p className="sub">Scorecard grade from the pipeline run, deductions itemised in the detail panel below.</p>
      <GradeGauge points={g.total_points} band={g.letter_band} size={190} />
      <GroupBars modelKey={modelKey} dim={!champion} />
    </div>
  )
}

export default function Models({
  model,
  setModel,
}: {
  model: ModelKey
  setModel: (m: ModelKey) => void
}) {
  const m = data.models[model]
  const g = data.grades.models[model]
  const metrics: Array<[string, number, number]> = [
    ['AUC', m.auc, 4],
    ['KS', m.ks, 4],
    ['Gini', m.gini, 4],
    ['Brier score', m.brier, 4],
    ['Score PSI', m.score_psi, 4],
  ]
  return (
    <div>
      <Reveal>
        <p className="eyebrow">Models</p>
        <h2 className="section-title">Two models, one scorecard, no rounded corners</h2>
        <p className="section-lede">
          Logistic regression is the scorecard-style baseline. Gradient boosting is the challenger
          that won on AUC and holds the champion slot. Both are graded on the same 1000-point
          scorecard: discrimination 500, calibration 300, stability 200.
        </p>
      </Reveal>

      <div className="grid two">
        <Reveal>
          <GradeCard modelKey="gradient_boosting" champion />
        </Reveal>
        <Reveal delay={0.08}>
          <GradeCard modelKey="logistic_regression" />
        </Reveal>
      </div>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="card">
          <h3>ROC curves, held-out test set</h3>
          <p className="sub">
            Both models on one plot. The dashed line is chance. AUC is printed in the legend from
            the exported run data.
          </p>
          <ResponsiveContainer width="100%" height={340}>
            <LineChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid stroke={LINE} strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="fpr"
                domain={[0, 1]}
                tick={{ fill: MUTED, fontSize: 12 }}
                tickFormatter={(v: number) => v.toFixed(1)}
                label={{ value: 'False positive rate', fill: MUTED, fontSize: 12, position: 'insideBottom', offset: -2 }}
              />
              <YAxis
                type="number"
                domain={[0, 1]}
                tick={{ fill: MUTED, fontSize: 12 }}
                tickFormatter={(v: number) => v.toFixed(1)}
                label={{ value: 'True positive rate', angle: -90, fill: MUTED, fontSize: 12, position: 'insideLeft' }}
              />
              <Tooltip
                content={
                  <ChartTip
                    rows={(p: any) => (
                      <>
                        <div className="r"><span>FPR</span><b className="mono">{p[0]?.payload?.fpr?.toFixed(4)}</b></div>
                        <div className="r"><span>TPR</span><b className="mono">{p[0]?.payload?.tpr?.toFixed(4)}</b></div>
                      </>
                    )}
                  />
                }
              />
              <Line
                data={[{ fpr: 0, tpr: 0 }, { fpr: 1, tpr: 1 }]}
                dataKey="tpr"
                stroke={GRAY}
                strokeDasharray="5 5"
                dot={false}
                isAnimationActive={false}
                name="Chance"
              />
              <Line
                data={[...data.roc.gradient_boosting]}
                dataKey="tpr"
                stroke={RED}
                strokeWidth={2.4}
                dot={false}
                name={`Gradient Boosting (AUC ${data.models.gradient_boosting.auc.toFixed(4)})`}
              />
              <Line
                data={[...data.roc.logistic_regression]}
                dataKey="tpr"
                stroke={PAPER}
                strokeWidth={1.8}
                dot={false}
                name={`Logistic Regression (AUC ${data.models.logistic_regression.auc.toFixed(4)})`}
              />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', gap: 18, fontSize: 12.5, color: MUTED, flexWrap: 'wrap' }}>
            <span><span style={{ color: RED }}>——</span> Gradient Boosting (AUC {data.models.gradient_boosting.auc.toFixed(4)})</span>
            <span><span style={{ color: PAPER }}>——</span> Logistic Regression (AUC {data.models.logistic_regression.auc.toFixed(4)})</span>
            <span><span style={{ color: GRAY }}>- -</span> Chance</span>
          </div>
        </div>
      </Reveal>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h3>Model detail and deductions</h3>
              <p className="sub" style={{ marginBottom: 0 }}>Every point lost, named with its measured value.</p>
            </div>
            <ModelSwitcher value={model} onChange={setModel} />
          </div>
          <div style={{ height: 14 }} />
          <div className="grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
            {metrics.map(([label, v, d]) => (
              <div key={label}>
                <div style={{ color: MUTED, fontSize: 11.5, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700 }}>{label}</div>
                <div className="mono" style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{v.toFixed(d)}</div>
              </div>
            ))}
          </div>
          <ul className="deductions">
            {g.components.map((c) => (
              <li key={c.component}>
                <span>
                  <span className="dname">{c.component}</span>
                  <span className="ddetail">{c.detail}</span>
                </span>
                <span className="dpts mono">-{c.deduction.toFixed(2)} pts</span>
              </li>
            ))}
          </ul>
          <p className="sub" style={{ marginTop: 12, marginBottom: 0 }}>
            {MODEL_LABEL[model]} total: <span className="mono">{g.total_points.toFixed(2)}</span> of
            1000, band {g.letter_band}. Largest single deduction:{' '}
            {g.components.reduce((a, b) => (b.deduction > a.deduction ? b : a)).component} at{' '}
            {g.components.reduce((a, b) => (b.deduction > a.deduction ? b : a)).deduction.toFixed(2)}{' '}
            points. The benchmark is a strong production model, not perfection theatre: the gap is
            the honest distance to it.
          </p>
        </div>
      </Reveal>
    </div>
  )
}
