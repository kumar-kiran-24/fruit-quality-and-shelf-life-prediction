import React from 'react'

export default function Status({ children }: { children: string }) {
  const tone = children === 'Ready for dispatch' ? 'gold' : children === 'Dispatched' ? 'navy' : children === 'Buyer recommended' ? 'green' : 'muted'
  return (
    <span className={`status status-${tone}`}>
      <span className="status-dot" />
      {children}
    </span>
  )
}
