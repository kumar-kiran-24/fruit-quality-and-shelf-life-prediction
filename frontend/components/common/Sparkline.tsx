import React from 'react'

export default function Sparkline({ values, gold = false }: { values: number[]; gold?: boolean }) {
  const points = values.map((v, i) => `${(i / (values.length - 1)) * 100},${44 - v * 0.33}`).join(' ')
  return (
    <svg viewBox="0 0 100 48" preserveAspectRatio="none" className="sparkline" aria-hidden="true">
      <polyline
        points={points}
        fill="none"
        stroke={gold ? 'var(--gold)' : 'var(--navy)'}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
