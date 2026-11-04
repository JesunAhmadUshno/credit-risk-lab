import { useState } from 'react'
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
import { motion } from 'framer-motion'
import { data } from '../data/results'
import { ChartTip, Reveal } from '../components/ui'
import { fmtInt, fmtNT, fmtNTCompact, fmtPct, LINE, MUTED, PAPER, RED, GRAY } from '../lib/format'

const stages = data.staging.by_stage.map((s) => ({
  ...s,
  name: `Stage ${s.stage}`,
}))

const STAGE_BLURB: Record<number, string> = {
  1: 'Performing. 12-month PD, no significant increase in credit risk.',
  2: 'Underperforming. SICR triggered: 30+ DPD or PD at twice the portfolio median. Lifetime PD applies.',
  3: 'Credit-impaired proxy. 90+ DPD. PD applied at 1.0.',
}

function StageChart({
  title,
  sub,
  dataKey,
  format,
  selected,
}: {
  title: string
  sub: string
  dataKey: 'accounts' | 'ecl' | 'observed_default_rate'
  format: (n: number) => string
  selected: number | null
}) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <p className="sub">{sub}</p>
      <ResponsiveContainer width="100%" height={230}>
        <BarChart data={stages} margin={{ top: 6, right: 10, bottom: 0, left: 6 }}>
          <CartesianGrid stroke={LINE} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: MUTED, fontSize: 12.5 }} axisLine={{ stroke: LINE }} tickLine={false} />
          <YAxis tick={{ fill: MUTED, fontSize: 12 }} tickFormatter={(v: number) => format(v)} axisLine={false} tickLine={false} width={86} />
          <Tooltip
            cursor={{ fill: 'rgba(244,241,234,0.05)' }}
            content={
              <ChartTip
                rows={(p: any) => (
                  <div className="r">
                    <span>{title}</span>
                    <b className="mono">{format(p[0]?.value ?? 0)}</b>
                  </div>
                )}
              />
            }
          />
          <Bar dataKey={dataKey} radius={[5, 5, 0, 0]}>
            {stages.map((s) => (
              <Cell
                key={s.stage}
                fill={s.stage === 3 ? RED : s.stage === 2 ? PAPER : GRAY}
                fillOpacity={selected === null || selected === s.stage ? 1 : 0.3}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Portfolio() {
  const [selected, setSelected] = useState<number | null>(null)
  const toggle = (stage: number) => setSelected((cur) => (cur === stage ? null : stage))
  return (
    <div>
      <Reveal>
        <p className="eyebrow">Portfolio</p>
        <h2 className="section-title">IFRS 9 style staging, with the losses where the risk is</h2>
        <p className="section-lede">
          The champion model is refit on the full portfolio and every account is staged under the
          lab policy. Click a stage card to highlight it across the charts.
        </p>
      </Reveal>

      <div className="grid three">
        {stages.map((s, i) => (
          <Reveal key={s.stage} delay={i * 0.06}>
            <motion.div
              className={`card hoverable${selected === s.stage ? ' selected' : ''}`}
              onClick={() => toggle(s.stage)}
              whileHover={{ y: -4 }}
              transition={{ type: 'spring', stiffness: 320, damping: 22 }}
              role="button"
              aria-pressed={selected === s.stage}
            >
              <h3>
                Stage {s.stage}
                {selected === s.stage && <span className="pill" style={{ marginLeft: 10, borderColor: RED, color: RED }}>highlighted</span>}
              </h3>
              <p className="sub">{STAGE_BLURB[s.stage]}</p>
              <table className="data">
                <tbody>
                  <tr><td>Accounts</td><td className="mono">{fmtInt(s.accounts)}</td></tr>
                  <tr><td>Exposure (EAD)</td><td className="mono">{fmtNT(s.ead)}</td></tr>
                  <tr><td>Observed default rate</td><td className="mono">{fmtPct(s.observed_default_rate)}</td></tr>
                  <tr><td>ECL</td><td className="mono" style={{ color: RED, fontWeight: 700 }}>{fmtNT(s.ecl)}</td></tr>
                </tbody>
              </table>
            </motion.div>
          </Reveal>
        ))}
      </div>

      <div style={{ height: 16 }} />

      <div className="grid two">
        <Reveal>
          <StageChart title="Accounts by stage" sub="Stage 1 holds most accounts. It does not hold most of the loss." dataKey="accounts" format={fmtInt} selected={selected} />
        </Reveal>
        <Reveal delay={0.08}>
          <StageChart title="ECL by stage" sub="Stage 2 is the loss centre: lifetime PD on accounts that already slipped." dataKey="ecl" format={fmtNTCompact} selected={selected} />
        </Reveal>
      </div>

      <div style={{ height: 16 }} />

      <div className="grid two">
        <Reveal>
          <StageChart title="Observed default rate by stage" sub="The staging separates risk in the right order, on outcomes it never trained on directly." dataKey="observed_default_rate" format={(n) => fmtPct(n)} selected={selected} />
        </Reveal>
        <Reveal delay={0.08}>
          <div className="card">
            <h3>Policy and assumptions</h3>
            <p className="sub">{data.staging.policy}</p>
            <p className="sub">
              ECL per account = PD applied x LGD x EAD, with EAD the current bill amount from the
              dataset.
            </p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span className="pill">LGD {fmtPct(data.staging.lgd_assumption, 0)} · assumption</span>
              <span className="pill">Lifetime horizon {data.staging.lifetime_years_assumption} years · assumption</span>
              <span className="pill">Total ECL {fmtNT(data.staging.total_ecl)}</span>
            </div>
            <p className="sub" style={{ marginTop: 12, marginBottom: 0 }}>
              Both pills are stated lab assumptions, not measured values. Move them yourself in the
              Simulator tab and watch the loss move.
            </p>
          </div>
        </Reveal>
      </div>
    </div>
  )
}
