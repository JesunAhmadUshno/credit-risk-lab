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
          note={`${fmtInt(R.study.creditworthyRejects)} of ${fmtInt(R.study.rejected)} rejected test applicants did not default, at a cut-off holding the approved book at the Stage 1 default rate (${fmtPct(R.study.targetRate, 2)}).${R.study.creditworthyShareCi95 ? ` Bootstrap 95% CI for the share: ${fmtPct(R.study.creditworthyShareCi95.lo95, 1)} to ${fmtPct(R.study.creditworthyShareCi95.hi95, 1)}.` : ''}`}
          delay={0}
        />
        <Headline
          label="Thin-file AUC"
          value={R.study.thinFileAuc}
          format={(n) => n.toFixed(4)}
          note={`Behavioural features only, no bureau-style fields. Full model: ${R.study.fullModelAuc.toFixed(4)}.${R.study.thinFileCi95 ? ` Bootstrap 95% CI: ${R.study.thinFileCi95.lo95.toFixed(4)} to ${R.study.thinFileCi95.hi95.toFixed(4)}.` : ''} A thin file is not an empty file when payment behaviour is observable.`}
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

      <div className="grid two">
        <Reveal>
          <div className="card">
            <h3>External validation: German Credit (different population, different era)</h3>
            <p className="sub">{R.externalValidation.populationNote}</p>
            <table className="data">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>AUC</th>
                  <th>AUC 95% CI</th>
                  <th>KS</th>
                  <th>Brier</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(R.externalValidation.models).map(([name, m]) => (
                  <tr key={name}>
                    <td>
                      {name.replaceAll('_', ' ')}
                      {name === R.externalValidation.champion ? ' (champion here)' : ''}
                    </td>
                    <td className="mono">{m.auc.toFixed(4)}</td>
                    <td className="mono">
                      {m.aucCi95 ? `${m.aucCi95.lo95.toFixed(3)} to ${m.aucCi95.hi95.toFixed(3)}` : 'n/a'}
                    </td>
                    <td className="mono">{m.ks.toFixed(4)}</td>
                    <td className="mono">{m.brier.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="sub" style={{ marginTop: 10 }}>
              {R.externalValidation.transportability.note} On 300 German test accounts the
              intervals are wide; that width is part of the result.
            </p>
          </div>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="card">
            <h3>{R.secondLook.name}</h3>
            <p className="sub">
              Stage 1 rejects applicants above the study cut-off. Stage 2 re-scores the
              rejects with the independent thin-file behavioural model: {R.secondLook.bandRule}{' '}
              (band threshold: thin-file PD {R.secondLook.bandThreshold.toFixed(4)}).
            </p>
            <table className="data">
              <tbody>
                <tr>
                  <td>Rejects given a second look</td>
                  <td className="mono">{fmtInt(R.secondLook.stage1_rejected)}</td>
                </tr>
                <tr>
                  <td>Recovered on second look</td>
                  <td className="mono">{fmtInt(R.secondLook.recovered_total)}</td>
                </tr>
                <tr>
                  <td>Creditworthy recovered</td>
                  <td className="mono">
                    {fmtInt(R.secondLook.recovered_creditworthy)} (
                    {fmtPct(R.secondLook.recovery_rate_of_creditworthy, 1)} of creditworthy
                    rejects
                    {R.secondLook.recoveryCi95
                      ? `, 95% CI ${fmtPct(R.secondLook.recoveryCi95.lo95, 1)} to ${fmtPct(R.secondLook.recoveryCi95.hi95, 1)}`
                      : ''}
                    )
                  </td>
                </tr>
                <tr>
                  <td>Additional defaults admitted</td>
                  <td className="mono">{fmtInt(R.secondLook.admitted_defaults)}</td>
                </tr>
                <tr>
                  <td>Approved-book default rate</td>
                  <td className="mono">
                    {fmtPct(R.secondLook.approved_book_default_rate_stage1, 2)} to{' '}
                    {fmtPct(R.secondLook.approved_book_default_rate_after, 2)} (
                    {R.secondLook.cost_default_rate_pp >= 0 ? '+' : ''}
                    {R.secondLook.cost_default_rate_pp.toFixed(2)} pp)
                  </td>
                </tr>
              </tbody>
            </table>
            <p className="sub" style={{ marginTop: 10 }}>
              The policy was pre-registered as hypothesis H1 in HYPOTHESES.md before the
              experiment code ran. Full write-up: STUDY.md, section 4.
            </p>
          </div>
        </Reveal>
      </div>

      <div style={{ height: 16 }} />

      <Reveal>
        <div className="card">
          <h3>Why applicants are declined: adverse-action reason codes</h3>
          <p className="sub">
            For each of the {fmtInt(R.reasonCodes.rejected)} rejected test applicants, the
            lab emits up to three principal reasons from a documented mapping of model
            features to plain language ({fmtInt(R.reasonCodes.totalAssignments)} assignments
            in total). The most frequent:
          </p>
          <table className="data">
            <thead>
              <tr>
                <th>Reason</th>
                <th>Applicants</th>
                <th>Share of rejected</th>
              </tr>
            </thead>
            <tbody>
              {R.reasonCodes.topReasons.map((r) => (
                <tr key={r.reason}>
                  <td>{r.reason}</td>
                  <td className="mono">{fmtInt(r.count)}</td>
                  <td className="mono">{fmtPct(r.count / R.reasonCodes.rejected, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="sub" style={{ marginTop: 10 }}>
            {R.reasonCodes.basis} Reason codes explain the score; they are not causal
            findings and not legal notices.
          </p>
        </div>
      </Reveal>

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
