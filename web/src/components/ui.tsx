import { useEffect, useRef, useState, type ReactNode } from 'react'
import { animate, motion, useInView } from 'framer-motion'
import { RED } from '../lib/format'

export type ModelKey = 'logistic_regression' | 'gradient_boosting'

export const MODEL_LABEL: Record<ModelKey, string> = {
  logistic_regression: 'Logistic Regression',
  gradient_boosting: 'Gradient Boosting',
}

export const MODEL_KEYS: ModelKey[] = ['logistic_regression', 'gradient_boosting']

/** Scroll-triggered reveal wrapper. */
export function Reveal({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}

/** Animated count-up that starts when scrolled into view. */
export function CountUp({
  value,
  format,
  duration = 1.3,
}: {
  value: number
  format: (n: number) => string
  duration?: number
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  const [display, setDisplay] = useState(() => format(0))
  useEffect(() => {
    if (!inView) return
    const controls = animate(0, value, {
      duration,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(format(v)),
    })
    return () => controls.stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, value])
  return (
    <span ref={ref} className="mono">
      {display}
    </span>
  )
}

/** Animated semicircle gauge for a 0..1000 grade. */
export function GradeGauge({ points, band, size = 210 }: { points: number; band: string; size?: number }) {
  const frac = Math.max(0, Math.min(points / 1000, 1))
  return (
    <div style={{ width: size, margin: '0 auto', textAlign: 'center' }}>
      <svg viewBox="0 0 200 118" width={size} role="img" aria-label={`Grade ${points} of 1000, band ${band}`}>
        <path d="M 16 104 A 84 84 0 0 1 184 104" fill="none" stroke="#26262b" strokeWidth="13" strokeLinecap="round" />
        <motion.path
          d="M 16 104 A 84 84 0 0 1 184 104"
          fill="none"
          stroke={RED}
          strokeWidth="13"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: frac }}
          viewport={{ once: true }}
          transition={{ duration: 1.4, ease: 'easeOut' }}
        />
        <text x="100" y="86" textAnchor="middle" fill="#f4f1ea" fontSize="34" fontWeight="800" className="mono">
          {points.toFixed(0)}
        </text>
        <text x="100" y="106" textAnchor="middle" fill="#8a867d" fontSize="11.5">
          of 1000 · band {band}
        </text>
      </svg>
    </div>
  )
}

/** Pill toggle between the two models. */
export function ModelSwitcher({
  value,
  onChange,
}: {
  value: ModelKey
  onChange: (m: ModelKey) => void
}) {
  return (
    <div className="switcher" role="tablist" aria-label="Model">
      {MODEL_KEYS.map((k) => (
        <button key={k} className={k === value ? 'active' : ''} onClick={() => onChange(k)}>
          {MODEL_LABEL[k]}
        </button>
      ))}
    </div>
  )
}

/** Shared dark tooltip for recharts. */
export function ChartTip({ active, payload, label, rows }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tip">
      {label !== undefined && <div className="t">{label}</div>}
      {rows(payload)}
    </div>
  )
}
