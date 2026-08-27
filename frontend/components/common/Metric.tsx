import React from 'react'

interface MetricProps {
  label: string
  value: string
  change: string
  icon: React.ComponentType<{ size?: number | string }>
}

export default function Metric({ label, value, change, icon: Icon }: MetricProps) {
  return (
    <div className="metric-card">
      <div className="metric-icon">
        <Icon size={18} />
      </div>
      <p>{label}</p>
      <strong>{value}</strong>
      <span className="metric-change">{change}</span>
    </div>
  )
}
