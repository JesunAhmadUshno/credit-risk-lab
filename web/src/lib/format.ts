export const RED = '#e63946'
export const PAPER = '#f4f1ea'
export const DIM = '#b9b4a8'
export const MUTED = '#8a867d'
export const GRAY = '#55534e'
export const LINE = '#26262b'

export const fmtInt = (n: number) => Math.round(n).toLocaleString('en-US')

export const fmtNT = (n: number) =>
  'NT$' + Math.round(n).toLocaleString('en-US')

/** Compact NT$ for tight KPI space: NT$187.5M style. */
export const fmtNTCompact = (n: number) => {
  if (Math.abs(n) >= 1e9) return `NT$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `NT$${(n / 1e6).toFixed(1)}M`
  return fmtNT(n)
}

export const fmtPct = (x: number, digits = 1) => `${(x * 100).toFixed(digits)}%`

export const fmtDelta = (x: number) =>
  `${x >= 0 ? '+' : '-'}NT$${Math.abs(Math.round(x)).toLocaleString('en-US')}`
