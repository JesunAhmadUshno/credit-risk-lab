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
import { ChartTip, CountUp, Reveal } from '../components/ui'
import { fmtInt, fmtNT, fmtNTCompact, fmtPct, LINE, MUTED, RED, GRAY } from '../lib/format'

const R = data.research

const scenChart = [
  ...R.scenarios.rows.map((s) => ({
    name: `${s.name} (w ${s.weight.toFixed(2)}, PD x${s.pdMultiplier.toFixed(2)})`,
    ecl: s.totalEcl,
    kind: 'scenario' as const,
  })),
  { name: 'Probability-weighted', ecl: R.scenarios.weightedEcl, kind: 'weighted' as const },
]

const vCompare = [
  { metric: 'AUC', v1: R.behaviouralV2.v1.auc, v2: R.behaviouralV2.v2.auc },
  { metric: 'KS', v1: R.behaviouralV2.v1.ks, v2: R.behaviouralV2.v2.ks },
  { metric: 'Brier (lower is better)', v1: R.behaviouralV2.v1.brier, v2: R.behaviouralV2.v2.brier },
]

function Headline({
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

export default function Research() {
  const lg = R.study.largestGap
  return (
    <div>
      <Reveal>
        <p className="eyebrow">Research · fair access to credit</p>
        <h2 className="section-title">The study behind the pipeline</h2>
        <p className="section-lede">{R.thesis}</p>
      </Reveal>

      <Reveal>
        <div className="card">
          <h3>The three questions</h3>
          <ol style={{ margin: '6px 0 0', paddingLeft: 20, lineHeight: 1.65 }}>
            {R.thesisQuestions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ol>
          <p className="sub" style={{ marginTop: 12 }}>
            Full text, Canada context, literature and sources:{' '}
            <a href="https://github.com/JesunAhmadUshno/credit-risk-lab/blob/main/RESEARCH.md">
              RESEARCH.md
            </a>{' '}
            · study detail:{' '}
            <a href="https://github.com/JesunAhmadUshno/credit-risk-lab/blob/main/STUDY.md">
              STUDY.md
            </a>{' '}
            · validation pack:{' '}
            <a href="https://github.com/JesunAhmadUshno/credit-risk-lab/blob/main/VALIDATION.md">
              VALIDATION.md
            </a>
          </p>
        </div>
      </Reveal>

      <div style={{ height: 16 }} />

      <div className="grid three">
        <Headline
          label="Creditworthy rejects"
          value={R.study.creditworthyShareOfRejected}
          format={(n) => fmtPct(n, 1)}
          note={`${fmtInt(R.study.creditworthyRejects)} of ${fmtInt(R.study.rejected)} rejected test applicants did not default, at a cut-off holding the approved book at the Stage 1 default rate (${fmtPct(R.study.targetRate, 2)}).`}
          delay={0}
        />
        <Headline
          label="Thin-file AUC"
          value={R.study.thinFileAuc}
          format={(n) => n.toFixed(4)}
          note={`Behavioural features only, no bureau-style fields. Full model: ${R.study.fullModelAuc.toFixed(4)}. A thin file is not an empty file when payment behaviour is observable.`}
          delay={0.05}
        />
        <Headline
          label="Largest fairness gap"
          value={lg.gap}
          format={(n) => fmtPct(n, 1)}
          note={`${lg.variable}: ${lg.higherGroup.group} approved at ${fmtPct(lg.higherGroup.approval_rate)} (n=${fmtInt(lg.higherGroup.n)}) vs ${lg.lowerGroup.group} at ${fmtPct(lg.lowerGroup.approval_rate)} (n=${fmtInt(lg.lowerGroup.n)}).`}
          delay={0.1}
        />
      </div>

      <div style={{ height: 16 }} />

      <div className="grid two">
        <Reveal>
          <div className="card">
            <h3>Scenario-weighted ECL (IFRS 9 style)</h3>
            <p className="sub">
              Three macro scenarios scale the champion PDs and re-run the unchanged staging
              policy. Weights and multipliers are stated assumptions in config.json. The base
              scenario reproduces the published baseline of {fmtNT(R.scenarios.baselineEcl)}{' '}
              exactly. Probability-weighted ECL: <b>{fmtNT(R.scenarios.weightedEcl)}</b>.
            </p>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={scenChart} margin={{ top: 6, right: 10, bottom: 0, left: 6 }}>
                <CartesianGrid stroke={LINE} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: MUTED, fontSize: 11 }} axisLine={{ stroke: LINE }} tickLine={false} interval={0} angle={-18} textAnchor="end" height={64} />
                <YAxis tick={{ fill: MUTED, fontSize: 12 }} tickFormatter={(v: number) => fmtNTCompact(v)} axisLine={false} tickLine={false} width={86} />
                <Tooltip
                  cursor={{ fill: 'rgba(244,241,234,0.05)' }}
                  content={
                    <ChartTip
                      rows={(p: any) => (
                        <div className="r">
                          <span>Total ECL</span>
                          <b className="mono">{fmtNT(p[0]?.value ?? 0)}</b>
                        </div>
                      )}
                    />
                  }
                />
                <Bar dataKey="ecl" radius={[4, 4, 0, 0]}>
                  {scenChart.map((row) => (
                    <Cell key={row.name} fill={row.kind === 'weighted' ? RED : GRAY} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="sub" style={{ marginTop: 10 }}>
              Basel floor view: at the lab LGD assumption of{' '}
              {fmtPct(R.scenarios.baselFloor.lgdAssumption, 0)}, ECL is{' '}
              {fmtNT(R.scenarios.baselFloor.eclAtAssumption)}. At the Basel QRRE foundation LGD
              floor of {fmtPct(R.scenarios.baselFloor.lgdFloor, 0)}, it is{' '}
              {fmtNT(R.scenarios.baselFloor.eclAtFloor)}.
            </p>
          </div>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="card">
            <h3>Behavioural PD v2: transition features</h3>
            <p className="sub">
              v2 adds the path of delinquency, not just its level:{' '}
              {R.behaviouralV2.transitionFeatures.join(', ')}. Same model, same split, same
              seed. Verdict from the run:{' '}
              <b>
                {R.behaviouralV2.beatsV1
                  ? `v2 beats v1 on AUC by ${R.behaviouralV2.deltaAuc.toFixed(4)}, a marginal gain, with KS slightly lower.`
                  : `v2 does not beat v1 on AUC (${R.behaviouralV2.deltaAuc.toFixed(4)}). The transition features add nothing the level features do not already carry.`}
              </b>
            </p>
            <table className="data">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>v1</th>
                  <th>v2</th>
                </tr>
              </thead>
              <tbody>
                {vCompare.map((row) => (
                  <tr key={row.metric}>
                    <td>{row.metric}</td>
                    <td className="mono">{row.v1.toFixed(4)}</td>
                    <td className="mono">{row.v2.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="sub" style={{ marginTop: 12 }}>
              Cut-off for the study: PD {R.study.cutoffPd.toFixed(4)}, approving{' '}
              {fmtInt(R.study.approved)} of {fmtInt(R.study.testAccounts)} test accounts.
            </p>
          </div>
        </Reveal>
      </div>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="card">
          <h3>Dataset limits, on the same page</h3>
          <p className="sub" style={{ marginBottom: 0 }}>
            The dataset is Taiwan, 2005 (UCI dataset 350), not Canada. The fairness audit
            demonstrates the method on that data; it is not evidence about Canadian borrowers or
            any Canadian lender. Outcomes cover a single month, and the cut-off is set on the
            same test set it is audited on. Full limits and the complete group tables are in
            STUDY.md; validation limits (no out-of-time split exists in this data, PSI
            thresholds are rules of thumb, LGD is assumed) are in VALIDATION.md.
          </p>
        </div>
      </Reveal>
    </div>
  )
}
