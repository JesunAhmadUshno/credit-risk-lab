import { data } from '../data/results'
import { Reveal } from '../components/ui'

const DOCS = data.research.analysis

export default function Analysis() {
  return (
    <div>
      <Reveal>
        <p className="eyebrow">Analysis · wave 3</p>
        <h2 className="section-title">The analysis pack</h2>
        <p className="section-lede">
          SWOT, PESTEL, a numbered gap register, the audit with its clean-checkout
          reproducibility proof, and three number-grounded case studies. Every claim in
          these documents is tied to evidence in the repository; the summaries below are
          extracted from the documents themselves, and each card links to the full text.
        </p>
      </Reveal>

      <div className="grid two">
        {DOCS.map((d, i) => (
          <Reveal key={d.href} delay={0.05 * (i % 4)}>
            <div className="card">
              <h3>{d.title}</h3>
              <p className="sub">{d.summary}</p>
              <p className="sub" style={{ marginBottom: 0 }}>
                <a href={d.href}>Read the full document</a>
              </p>
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  )
}
