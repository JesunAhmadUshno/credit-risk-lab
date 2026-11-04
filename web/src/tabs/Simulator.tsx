import { useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { data } from '../data/results'
import { ChartTip, Reveal } from '../components/ui'
import { BASELINE, simulate, type SimParams } from '../lib/sim'
import { fmtDelta, fmtInt, fmtNT, fmtNTCompact, fmtPct, GRAY, LINE, MUTED, RED } from '../lib/format'

export default function Simulator() {
  const [params, setParams] = useState<SimParams>({ ...BASELINE })
  const result = useMemo(
    () => simulate(data.simulatorStages, params),
    [params],
  )
  const chartData = result.rows.map((r) => ({
    name: `Stage ${r.stage}`,
    stage: r.stage,
    baseline: Math.round(r.ecl),
    simulated: Math.round(r.simEcl),
  }))
  const atBaseline =
    params.lgd === BASELINE.lgd &&
    params.pdShift === BASELINE.pdShift &&
    params.lifetimeYears === BASELINE.lifetimeYears

  const set = (patch: Partial<SimParams>) => setParams((p) => ({ ...p, ...patch }))

  return (
    <div>
      <Reveal>
        <p className="eyebrow">Simulator</p>
        <h2 className="section-title">Stress the loss number yourself</h2>
        <p className="section-lede">
          Sensitivity simulator on published aggregates. Not a re-run of the model. It recomputes
          ECL by stage in your browser from the exported stage aggregates (accounts, exposure,
          exposure-weighted mean PD, baseline ECL), so the baseline position reproduces the
          pipeline total exactly.
        </p>
      </Reveal>

      <div className="grid" style={{ gridTemplateColumns: '380px 1fr' }}>
        <Reveal>
          <div className="card">
            <h3>Scenario levers</h3>
            <p className="sub">Baseline: LGD 45%, PD shift 1.00x, lifetime horizon 3 years.</p>
            <div className="sliders">
              <div className="slider-row">
                <label>
                  <span>Loss given default (LGD)</span>
                  <span className="val mono">{fmtPct(params.lgd, 0)}</span>
                </label>
                <input
                  type="range" min={10} max={90} step={1}
                  value={Math.round(params.lgd * 100)}
                  onChange={(e) => set({ lgd: Number(e.target.value) / 100 })}
                  aria-label="LGD percent"
                />
                <div className="hint">Share of exposure lost when an account defaults. Scales every stage.</div>
              </div>
              <div className="slider-row">
                <label>
                  <span>PD shift</span>
                  <span className="val mono">{params.pdShift.toFixed(2)}x</span>
                </label>
                <input
                  type="range" min={0.5} max={2} step={0.05}
                  value={params.pdShift}
                  onChange={(e) => set({ pdShift: Number(e.target.value) })}
                  aria-label="PD shift multiplier"
                />
                <div className="hint">A downturn lever: multiply every modelled PD before staging math applies.</div>
              </div>
              <div className="slider-row">
                <label>
                  <span>Lifetime horizon, Stage 2</span>
                  <span className="val mono">{params.lifetimeYears} years</span>
                </label>
                <input
                  type="range" min={1} max={5} step={1}
                  value={params.lifetimeYears}
                  onChange={(e) => set({ lifetimeYears: Number(e.target.value) })}
                  aria-label="Lifetime horizon years"
                />
                <div className="hint">Stage 2 PD converts as 1 - (1 - PD) raised to the horizon. Longer horizon, larger lifetime loss.</div>
              </div>
            </div>
            <div style={{ height: 18 }} />
            <button
              className="switcher"
              style={{ padding: '8px 18px', color: atBaseline ? MUTED : '#f4f1ea', cursor: 'pointer' }}
              onClick={() => setParams({ ...BASELINE })}
              disabled={atBaseline}
            >
              Reset to baseline
            </button>
            <div style={{ height: 14 }} />
            <div className="note-box">
              Stage 1 uses 12-month PD. Stage 2 uses the lifetime conversion on the stage's
              exposure-weighted mean PD, anchored to the published baseline. Stage 3 sits at PD
              1.0 by policy, so only LGD moves it.
            </div>
          </div>
        </Reveal>

        <div>
          <Reveal>
            <div className="card">
              <div className="grid two" style={{ gap: 24 }}>
                <div>
                  <div className="kpi">
                    <div className="label">Baseline ECL (published)</div>
                    <div className="big-total mono" style={{ marginTop: 6 }}>{fmtNT(result.baselineTotal)}</div>
                  </div>
                </div>
                <div>
                  <div className="kpi">
                    <div className="label">Simulated ECL</div>
                    <div className="big-total mono" style={{ marginTop: 6, color: atBaseline ? undefined : RED }}>
                      {fmtNT(result.simTotal)}
                    </div>
                    <div className="note">
                      {atBaseline ? (
                        'At baseline. Move a lever.'
                      ) : (
                        <span className={result.delta > 0 ? 'delta-up' : ''}>
                          {fmtDelta(result.delta)} ({result.delta >= 0 ? '+' : ''}
                          {((result.delta / result.baselineTotal) * 100).toFixed(1)}%)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div style={{ height: 16 }} />
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData} margin={{ top: 6, right: 10, bottom: 0, left: 6 }}>
                  <CartesianGrid stroke={LINE} strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: MUTED, fontSize: 12.5 }} axisLine={{ stroke: LINE }} tickLine={false} />
                  <YAxis tick={{ fill: MUTED, fontSize: 12 }} tickFormatter={(v: number) => fmtNTCompact(v)} axisLine={false} tickLine={false} width={86} />
                  <Tooltip
                    cursor={{ fill: 'rgba(244,241,234,0.05)' }}
                    content={
                      <ChartTip
                        rows={(p: any) => (
                          <>
                            <div className="r"><span>Baseline</span><b className="mono">{fmtNT(p[0]?.payload?.baseline ?? 0)}</b></div>
                            <div className="r"><span>Simulated</span><b className="mono">{fmtNT(p[0]?.payload?.simulated ?? 0)}</b></div>
                          </>
                        )}
                      />
                    }
                  />
                  <Bar dataKey="baseline" fill={GRAY} radius={[4, 4, 0, 0]} name="Baseline" />
                  <Bar dataKey="simulated" radius={[4, 4, 0, 0]} name="Simulated">
                    {chartData.map((d) => (
                      <Cell key={d.stage} fill={RED} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Reveal>

          <div style={{ height: 16 }} />

          <Reveal>
            <div className="card">
              <h3>Stage detail under this scenario</h3>
              <p className="sub">Aggregates are the pipeline's published per-stage figures; simulated ECL is computed live.</p>
              <table className="data">
                <thead>
                  <tr><th>Stage</th><th>Accounts</th><th>EAD</th><th>Mean PD</th><th>Baseline ECL</th><th>Simulated ECL</th><th>Delta</th></tr>
                </thead>
                <tbody>
                  {result.rows.map((r) => (
                    <tr key={r.stage}>
                      <td>Stage {r.stage}</td>
                      <td className="mono">{fmtInt(r.accounts)}</td>
                      <td className="mono">{fmtNTCompact(r.ead)}</td>
                      <td className="mono">{r.stage === 3 ? '1.0000' : r.meanPd.toFixed(4)}</td>
                      <td className="mono">{fmtNT(r.ecl)}</td>
                      <td className="mono" style={{ fontWeight: 700 }}>{fmtNT(r.simEcl)}</td>
                      <td className="mono" style={{ color: r.delta > 0 ? RED : undefined }}>{atBaseline ? '—' : fmtDelta(r.delta)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Reveal>
        </div>
      </div>
    </div>
  )
}
