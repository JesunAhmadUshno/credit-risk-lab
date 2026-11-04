import { useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { data } from '../data/results'
import { ChartTip, MODEL_LABEL, ModelSwitcher, Reveal, type ModelKey } from '../components/ui'
import { fmtPct, GRAY, LINE, MUTED, PAPER, RED } from '../lib/format'

const driftRows = Object.entries(data.featureDrift)
  .map(([feature, psi]) => ({ feature, psi }))
  .sort((a, b) => b.psi - a.psi)

type DecileKey = 'decile' | 'accounts' | 'defaults' | 'defaultRate' | 'lift' | 'cumulativeCapture'

export default function Validation({
  model,
  setModel,
}: {
  model: ModelKey
  setModel: (m: ModelKey) => void
}) {
  const calib = useMemo(
    () =>
      data.models[model].calibration.map((b, i) => ({
        bin: i + 1,
        pred: b.pred,
        obs: b.obs,
        diag: b.pred,
        n: b.n,
      })),
    [model],
  )
  const scoreDist = data.validation.score_distribution.map((b) => ({
    ...b,
    label: `${b.bin_start.toFixed(2)}`,
  }))
  const gains = data.deciles.map((d) => ({
    ...d,
    diagonal: d.cumulativeShare,
    label: `D${d.decile}`,
  }))
  const [sortKey, setSortKey] = useState<DecileKey>('decile')
  const [sortAsc, setSortAsc] = useState(true)
  const decileRows = useMemo(() => {
    const rows = [...data.deciles]
    rows.sort((a, b) => (sortAsc ? a[sortKey] - b[sortKey] : b[sortKey] - a[sortKey]))
    return rows
  }, [sortKey, sortAsc])
  const sortBy = (k: DecileKey) => {
    if (k === sortKey) setSortAsc((v) => !v)
    else {
      setSortKey(k)
      setSortAsc(true)
    }
  }
  const arrow = (k: DecileKey) => (sortKey === k ? (sortAsc ? ' ↑' : ' ↓') : '')

  return (
    <div>
      <Reveal>
        <p className="eyebrow">Validation</p>
        <h2 className="section-title">Calibration, gains, drift: the evidence pack</h2>
        <p className="section-lede">
          A model that ranks well can still price risk wrong. This tab holds the checks that catch
          that: predicted vs observed default rates, the gains curve, the score distribution, and
          train-to-test drift on every feature.
        </p>
      </Reveal>

      <Reveal>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h3>Calibration: predicted vs observed</h3>
              <p className="sub" style={{ marginBottom: 0 }}>
                Ten bins on the test set for {MODEL_LABEL[model]}. On the dashed diagonal,
                predicted risk equals observed risk.
              </p>
            </div>
            <ModelSwitcher value={model} onChange={setModel} />
          </div>
          <div style={{ height: 12 }} />
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={calib} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid stroke={LINE} strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="pred"
                domain={[0, 'dataMax']}
                tick={{ fill: MUTED, fontSize: 12 }}
                tickFormatter={(v: number) => v.toFixed(2)}
                label={{ value: 'Mean predicted PD', fill: MUTED, fontSize: 12, position: 'insideBottom', offset: -2 }}
              />
              <YAxis
                type="number"
                domain={[0, 'dataMax']}
                tick={{ fill: MUTED, fontSize: 12 }}
                tickFormatter={(v: number) => v.toFixed(2)}
                label={{ value: 'Observed default rate', angle: -90, fill: MUTED, fontSize: 12, position: 'insideLeft' }}
              />
              <Tooltip
                content={
                  <ChartTip
                    rows={(p: any) => {
                      const d = p[0]?.payload
                      if (!d) return null
                      return (
                        <>
                          <div className="t">Bin {d.bin} · {d.n} accounts</div>
                          <div className="r"><span>Predicted</span><b className="mono">{d.pred.toFixed(4)}</b></div>
                          <div className="r"><span>Observed</span><b className="mono">{d.obs.toFixed(4)}</b></div>
                        </>
                      )
                    }}
                  />
                }
              />
              <Line dataKey="diag" stroke={GRAY} strokeDasharray="5 5" dot={false} isAnimationActive={false} name="Perfect calibration" />
              <Line dataKey="obs" stroke={RED} strokeWidth={2.4} dot={{ r: 3.5, fill: RED }} name="Observed" />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="sub" style={{ marginBottom: 0 }}>
            Mean absolute calibration error for the champion:{' '}
            {data.grades.models[data.champion].components.find((c) => c.component === 'Calibration MAE')?.detail ?? ''}
          </p>
        </div>
      </Reveal>

      <div style={{ height: 16 }} />

      <div className="grid two">
        <Reveal>
          <div className="card">
            <h3>Gains and lift, champion model</h3>
            <p className="sub">
              Test accounts ranked riskiest first, in deciles. The curve shows the share of all
              defaults captured as more of the book is reviewed.
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={gains} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid stroke={LINE} strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fill: MUTED, fontSize: 12 }} axisLine={{ stroke: LINE }} tickLine={false} />
                <YAxis yAxisId="left" domain={[0, 1]} tick={{ fill: MUTED, fontSize: 12 }} tickFormatter={(v: number) => fmtPct(v, 0)} axisLine={false} tickLine={false} width={48} />
                <YAxis yAxisId="right" orientation="right" domain={[0, 'dataMax']} tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} width={36} />
                <Tooltip
                  content={
                    <ChartTip
                      rows={(p: any) => {
                        const d = p[0]?.payload
                        if (!d) return null
                        return (
                          <>
                            <div className="t">Through decile {d.decile}</div>
                            <div className="r"><span>Defaults captured</span><b className="mono">{fmtPct(d.cumulativeCapture)}</b></div>
                            <div className="r"><span>Book reviewed</span><b className="mono">{fmtPct(d.cumulativeShare)}</b></div>
                            <div className="r"><span>Decile lift</span><b className="mono">{d.lift.toFixed(2)}x</b></div>
                          </>
                        )
                      }}
                    />
                  }
                />
                <Bar yAxisId="right" dataKey="lift" fill={GRAY} radius={[4, 4, 0, 0]} name="Lift" />
                <Line yAxisId="left" dataKey="diagonal" stroke={GRAY} strokeDasharray="5 5" dot={false} isAnimationActive={false} name="Random" />
                <Line yAxisId="left" dataKey="cumulativeCapture" stroke={RED} strokeWidth={2.4} dot={{ r: 3, fill: RED }} name="Cumulative capture" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="card">
            <h3>Score distribution by outcome, champion</h3>
            <p className="sub">
              Test-set predicted PD in 0.05 bins. Defaults (Signal Red) concentrate at high scores;
              non-defaults (grey) at low scores. That separation is what the KS statistic measures.
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={scoreDist} margin={{ top: 6, right: 8, bottom: 0, left: 6 }} barCategoryGap="12%">
                <CartesianGrid stroke={LINE} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: MUTED, fontSize: 10.5 }} interval={1} axisLine={{ stroke: LINE }} tickLine={false} />
                <YAxis tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} width={52} />
                <Tooltip
                  cursor={{ fill: 'rgba(244,241,234,0.05)' }}
                  content={
                    <ChartTip
                      rows={(p: any) => {
                        const d = p[0]?.payload
                        if (!d) return null
                        return (
                          <>
                            <div className="t">PD {d.bin_start.toFixed(2)} to {d.bin_end.toFixed(2)}</div>
                            <div className="r"><span>Non-default</span><b className="mono">{d.non_default}</b></div>
                            <div className="r"><span>Default</span><b className="mono">{d.default}</b></div>
                          </>
                        )
                      }}
                    />
                  }
                />
                <Bar dataKey="non_default" stackId="a" fill={GRAY} name="Non-default" />
                <Bar dataKey="default" stackId="a" fill={RED} radius={[4, 4, 0, 0]} name="Default" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Reveal>
      </div>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="card">
          <h3>Decile table, champion (sortable)</h3>
          <p className="sub">Click a column header to sort. Decile 1 is the riskiest tenth of the test book.</p>
          <div style={{ overflowX: 'auto' }}>
            <table className="data">
              <thead>
                <tr>
                  <th className="sortable" onClick={() => sortBy('decile')}>Decile{arrow('decile')}</th>
                  <th className="sortable" onClick={() => sortBy('accounts')}>Accounts{arrow('accounts')}</th>
                  <th className="sortable" onClick={() => sortBy('defaults')}>Defaults{arrow('defaults')}</th>
                  <th className="sortable" onClick={() => sortBy('defaultRate')}>Default rate{arrow('defaultRate')}</th>
                  <th className="sortable" onClick={() => sortBy('lift')}>Lift{arrow('lift')}</th>
                  <th className="sortable" onClick={() => sortBy('cumulativeCapture')}>Cum. capture{arrow('cumulativeCapture')}</th>
                </tr>
              </thead>
              <tbody>
                {decileRows.map((d) => (
                  <tr key={d.decile} className={d.decile === 1 ? 'hl' : ''}>
                    <td className="mono">{d.decile}</td>
                    <td className="mono">{d.accounts}</td>
                    <td className="mono">{d.defaults}</td>
                    <td className="mono">{fmtPct(d.defaultRate)}</td>
                    <td className="mono">{d.lift.toFixed(2)}x</td>
                    <td className="mono">{fmtPct(d.cumulativeCapture)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Reveal>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="card">
          <h3>Feature drift, train vs test (PSI)</h3>
          <p className="sub">
            Population Stability Index per feature. Under 0.10 reads as no meaningful shift. Every
            feature here is far under it, which is why the stability grade is near full marks.
          </p>
          <table className="data">
            <thead>
              <tr><th>Feature</th><th style={{ width: '45%' }}>PSI bar</th><th>PSI</th><th>Read</th></tr>
            </thead>
            <tbody>
              {driftRows.map((r) => (
                <tr key={r.feature}>
                  <td className="mono" style={{ fontSize: 12.5 }}>{r.feature}</td>
                  <td>
                    <div style={{ height: 7, background: '#101012', borderRadius: 99, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.min((r.psi / 0.1) * 100, 100)}%`, background: r.psi >= 0.1 ? RED : PAPER }} />
                    </div>
                  </td>
                  <td className="mono">{r.psi.toFixed(4)}</td>
                  <td>{r.psi < 0.1 ? 'Stable' : r.psi < 0.25 ? 'Watch' : 'Shift'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="sub" style={{ marginTop: 12, marginBottom: 0 }}>
            Champion score PSI overall: {data.validation.score_psi_train_vs_test}.
          </p>
        </div>
      </Reveal>
    </div>
  )
}
