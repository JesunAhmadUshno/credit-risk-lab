import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { data } from './data/results'
import { MODEL_LABEL, type ModelKey } from './components/ui'
import Overview from './tabs/Overview'
import Models from './tabs/Models'
import Portfolio from './tabs/Portfolio'
import Validation from './tabs/Validation'
import Simulator from './tabs/Simulator'
import { fmtPct } from './lib/format'

const TABS = ['Overview', 'Models', 'Portfolio', 'Validation', 'Simulator'] as const
type Tab = (typeof TABS)[number]

const champGrade = data.grades.models[data.champion]

function Footer() {
  return (
    <footer>
      <div className="wrap">
        <div className="cols">
          <div>
            <strong>Data source</strong>
            <br />
            UCI Machine Learning Repository, dataset 350: default of credit card clients (Taiwan,
            2005). {data.dataset.rows.toLocaleString('en-US')} accounts, observed default rate{' '}
            {fmtPct(data.dataset.default_rate, 2)}. Public research data, used as-is.
          </div>
          <div>
            <strong>Assumptions, labelled</strong>
            <br />
            LGD is fixed at {fmtPct(data.staging.lgd_assumption, 0)} and the Stage 2 lifetime
            horizon at {data.staging.lifetime_years_assumption} years. Both are stated lab
            assumptions, not measured values. Staging thresholds are the lab's written IFRS 9
            style policy, in the Portfolio tab.
          </div>
          <div>
            <strong>What this is</strong>
            <br />
            A public-data lab that demonstrates the method end to end: features, model development,
            validation, grading, staging, loss estimation. It is not a production system and not
            employment experience in credit risk. Code and receipts:{' '}
            <a href="https://github.com/JesunAhmadUshno/credit-risk-lab">github.com/JesunAhmadUshno/credit-risk-lab</a>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('Overview')
  const [model, setModel] = useState<ModelKey>(data.champion as ModelKey)
  return (
    <>
      <header className="site-header">
        <div className="wrap">
          <div className="header-inner">
            <div className="wordmark">
              <span className="dot" />
              <span className="name">credit-risk-lab</span>
              <span className="tag">PD · Validation · IFRS 9 staging · ECL</span>
            </div>
            <div className="header-spacer" />
            <div className="grade-badge" title="Champion model grade from the pipeline scorecard">
              <span className="band">{champGrade.letter_band}</span>
              <span>
                Champion: {MODEL_LABEL[data.champion as ModelKey]} ·{' '}
                <span className="mono">{champGrade.total_points.toFixed(2)}</span> / 1000
              </span>
            </div>
          </div>
          <nav className="tabnav" aria-label="Dashboard sections">
            {TABS.map((t) => (
              <button key={t} className={t === tab ? 'active' : ''} onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="wrap">
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, x: 14 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -14 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            {tab === 'Overview' && <Overview />}
            {tab === 'Models' && <Models model={model} setModel={setModel} />}
            {tab === 'Portfolio' && <Portfolio />}
            {tab === 'Validation' && <Validation model={model} setModel={setModel} />}
            {tab === 'Simulator' && <Simulator />}
          </motion.div>
        </AnimatePresence>
      </main>

      <Footer />
    </>
  )
}
