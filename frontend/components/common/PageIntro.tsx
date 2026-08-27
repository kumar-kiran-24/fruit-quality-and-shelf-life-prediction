import React from 'react'

interface PageIntroProps {
  eyebrow: string
  title: string
  description: string
  action?: React.ReactNode
}

export default function PageIntro({ eyebrow, title, description, action }: PageIntroProps) {
  return (
    <div className="page-intro">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  )
}
