'use client'

import React, { useEffect, useState, useMemo } from 'react'
import Link from 'next/link'
import {
  Apple, ArrowUpRight, Check, Clock3, Ellipsis, Leaf, Package, Plus, Sparkles, Truck, RefreshCw, AlertTriangle, Zap
} from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import Metric from '../../components/common/Metric'
import Status from '../../components/common/Status'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'
import { authService } from '../../services/authService'

// ============================================================
// FEFO SHELF-LIFE PARSING & PRIORITY DERIVATION
//
// These thresholds are centralized here so they can be
// easily replaced with backend-provided thresholds in the future.
// ============================================================

/** Estimated days remaining by shelf-life label from the backend model */
const SHELF_LIFE_DAYS_MAP: Record<string, number> = {
  '1-5 days': 3,
  '5-10 days': 7,
  '10-14 days': 12,
}

/** Parse a shelf-life label into estimated remaining days (nullable) */
function parseRemainingDays(label: string | null | undefined): number | null {
  if (!label || typeof label !== 'string') return null
  if (SHELF_LIFE_DAYS_MAP[label] !== undefined) return SHELF_LIFE_DAYS_MAP[label]
  // Fallback: try to extract the first number from the label
  const match = label.match(/(\d+)/)
  if (match) return parseInt(match[1], 10)
  return null
}

/** FEFO priority thresholds (in days) — easy to replace later */
const FEFO_THRESHOLDS = {
  URGENT: 4,  // <= 4 days remaining
  HIGH: 7,    // <= 7 days remaining
  MEDIUM: 12, // <= 12 days remaining
  // Above 12 days → NORMAL
}

/** Derive FEFO display priority from remaining days */
function deriveFefoPriority(days: number | null): {
  label: string
  color: string
  bgColor: string
  sortOrder: number
} {
  if (days === null) return { label: 'PENDING', color: '#71808a', bgColor: '#eeeDE8', sortOrder: 999 }
  if (days <= FEFO_THRESHOLDS.URGENT) return { label: 'URGENT', color: '#b91c1c', bgColor: '#fee2e2', sortOrder: 1 }
  if (days <= FEFO_THRESHOLDS.HIGH) return { label: 'HIGH', color: '#c2410c', bgColor: '#ffedd5', sortOrder: 2 }
  if (days <= FEFO_THRESHOLDS.MEDIUM) return { label: 'MEDIUM', color: '#92400e', bgColor: '#fef3c7', sortOrder: 3 }
  return { label: 'NORMAL', color: '#166534', bgColor: '#dcfce7', sortOrder: 4 }
}

/** Generate a recommended action message based on FEFO priority */
function getFefoActionMsg(priority: string, days: number | null): string {
  if (days === null) return 'Awaiting analysis'
  switch (priority) {
    case 'URGENT': return 'Prioritize dispatch — immediate action required'
    case 'HIGH': return 'Find a buyer immediately'
    case 'MEDIUM': return 'Route to the nearest suitable buyer'
    case 'NORMAL': return 'This batch can remain in storage'
    default: return 'Process this batch soon'
  }
}

const activities = [
  ['Detection completed', 'Latest batch analysis processed successfully', '8 min ago', 'scan'],
  ['New recommendation', 'Routing matchmaking optimized for active harvests', '42 min ago', 'spark'],
  ['Logistics dispatch', 'FEFO delivery paths activated', '2 hr ago', 'truck'],
]

export default function DashboardPage() {
  const [stats, setStats] = useState({ total: 0, active: 0, apples: 0, ready: 0 })
  const [statusSummary, setStatusSummary] = useState<Record<string, number>>({})
  const [recentBatches, setRecentBatches] = useState<any[]>([])
  const [allBatches, setAllBatches] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [userName, setUserName] = useState('')

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError('')

      // Retrieve logged in user info for greeting
      const user = authService.getStoredUser()
      if (user?.name) {
        setUserName(user.name.split(' ')[0])
      }

      let summary: any = null
      let batchesData: any = null
      let summaryError: string | null = null
      let batchesError: string | null = null

      try {
        summary = await apiRequest(API_CONFIG.ENDPOINTS.SUMMARY)
      } catch (err: any) {
        summaryError = err.message || 'Failed to fetch summary statistics'
      }

      try {
        batchesData = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)
      } catch (err: any) {
        batchesError = err.message || 'Failed to fetch batches list'
      }

      // If both API calls failed, throw error to display diagnostic error state
      if (summaryError && batchesError) {
        throw new Error(summaryError || batchesError || 'Failed to connect to backend server.')
      }

      // Handle both array response formats and object response envelopes
      let batchList: any[] = []
      if (Array.isArray(batchesData)) {
        batchList = batchesData
      } else if (batchesData && Array.isArray(batchesData.batches)) {
        batchList = batchesData.batches
      } else if (batchesData && Array.isArray(batchesData.items)) {
        batchList = batchesData.items
      }

      // Calculate total batches and apples detected
      const total = summary?.total_batches ?? summary?.total ?? batchList.length ?? 0
      const apples = summary?.total_apples_detected ?? summary?.apples ?? batchList.reduce((sum: number, b: any) => sum + (b.total_apples_detected || b.apples || 0), 0)

      // Calculate status summary map
      let statusMap: Record<string, number> = summary?.status_summary || {}

      if (Object.keys(statusMap).length === 0 && batchList.length > 0) {
        batchList.forEach((b: any) => {
          const st = (b.batch_status || b.status || 'CREATED').toUpperCase().replace(/ /g, '_')
          statusMap[st] = (statusMap[st] || 0) + 1
        })
      }

      setStatusSummary(statusMap)

      // Active batches = total - completed/delivered/dispatched
      const active = Math.max(0, total - (statusMap.DISPATCHED || 0) - (statusMap.COMPLETED || 0) - (statusMap.DELIVERED || 0))
      const ready = (statusMap.READY_FOR_DISPATCH || 0) + (statusMap.ASSIGNED_TO_BUYER || 0)

      setStats({ total, active, apples, ready })

      setAllBatches(batchList)

      // Recent batches = newest first (top 3)
      const sortedBatches = [...batchList].sort((a: any, b: any) => {
        const dateA = new Date(a.created_at || a.inspection_date || a.date || 0).getTime()
        const dateB = new Date(b.created_at || b.inspection_date || b.date || 0).getTime()
        return dateB - dateA
      })

      setRecentBatches(sortedBatches.slice(0, 3))
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  // ============================================================
  // FEFO PRIORITY QUEUE
  //
  // Filter eligible batches (with shelf-life predictions) and sort
  // by ascending remaining shelf life (lowest = highest priority).
  // Batches with no prediction appear separately at the end.
  // ============================================================

  const fefoQueue = useMemo(() => {
    const eligible: { batch: any; days: number | null; priority: ReturnType<typeof deriveFefoPriority> }[] = []
    const pending: { batch: any; days: number | null; priority: ReturnType<typeof deriveFefoPriority> }[] = []

    for (const batch of allBatches) {
      const days = parseRemainingDays(batch.shelf_life_prediction)
      const priority = deriveFefoPriority(days)

      // Skip dispatched/completed/delivered batches from FEFO queue
      const status = (batch.batch_status || '').toUpperCase()
      if (status === 'DISPATCHED' || status === 'COMPLETED' || status === 'DELIVERED') continue

      if (days !== null && batch.shelf_life_prediction && batch.shelf_life_prediction !== 'N/A') {
        eligible.push({ batch, days, priority })
      } else {
        pending.push({ batch, days: null, priority })
      }
    }

    // Sort eligible batches: lowest remaining days first
    eligible.sort((a, b) => a.days! - b.days! || a.priority.sortOrder - b.priority.sortOrder)

    return [...eligible, ...pending]
  }, [allBatches])

  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading operations dashboard...</b>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="panel" style={{ padding: '3rem', textAlign: 'center', border: '1px solid rgba(235,94,40,0.2)' }}>
        <h3 style={{ color: '#eb5e28', marginBottom: '0.75rem', fontWeight: 800 }}>Dashboard Loading Failed</h3>
        <p className="muted-text" style={{ marginBottom: '2rem', maxWidth: '500px', margin: '0 auto 2rem' }}>{error}</p>
        <button onClick={loadDashboardData} className="primary-button" style={{ display: 'inline-flex', gap: '0.5rem', margin: '0 auto' }}>
          <RefreshCw size={16} />
          Retry Connection
        </button>
      </div>
    )
  }

  const readyCount = (statusSummary.READY_FOR_DISPATCH || 0) + (statusSummary.ASSIGNED_TO_BUYER || 0)
  const processingCount = (statusSummary.DETECTED || 0) + (statusSummary.SHELF_LIFE_PREDICTED || 0) + (statusSummary.RECOMMENDED || 0)
  const dispatchedCount = (statusSummary.DISPATCHED || 0) + (statusSummary.IN_TRANSIT || 0) + (statusSummary.DELIVERED || 0) + (statusSummary.COMPLETED || 0)
  const draftCount = statusSummary.CREATED || 0

  // Count urgent items for the metric card
  const urgentCount = fefoQueue.filter(item => item.priority.label === 'URGENT').length
  const highCount = fefoQueue.filter(item => item.priority.label === 'HIGH').length

  return (
    <>
      <PageIntro
        eyebrow={formattedDate}
        title={`Good morning, ${userName || 'Farmer'}.`}
        description="Here's what's happening across your orchard operations today."
        action={
          <Link href="/batches/create" className="primary-button">
            <Plus size={17} />Create batch
          </Link>
        }
      />

      <div className="metric-grid">
        <Metric label="Total batches" value={String(stats.total)} change="+12% this season" icon={Package} />
        <Metric label="Active batches" value={String(stats.active)} change="Needs routing review" icon={Leaf} />
        <Metric label="Apples detected" value={stats.apples.toLocaleString()} change="+8.4% this week" icon={Apple} />
        <Metric label="Ready for dispatch" value={String(stats.ready)} change="Awaiting transit confirmation" icon={Truck} />
      </div>

      {/* ============================================================
          FEFO PRIORITY QUEUE SECTION
          ============================================================ */}
      <div className="section-heading">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock3 size={20} /> FEFO Priority Queue
          </h2>
          <p>Batches sorted by urgency — shortest remaining shelf life first.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {urgentCount > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              background: '#fee2e2', color: '#b91c1c', padding: '4px 10px',
              borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700
            }}>
              <Zap size={12} /> {urgentCount} urgent
            </span>
          )}
          {highCount > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              background: '#ffedd5', color: '#c2410c', padding: '4px 10px',
              borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700
            }}>
              <AlertTriangle size={12} /> {highCount} high
            </span>
          )}
        </div>
      </div>

      {fefoQueue.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '1.5rem' }}>
          {fefoQueue.map(({ batch, days, priority }) => {
            const fruitName = batch.fruit ? (batch.fruit.charAt(0).toUpperCase() + batch.fruit.slice(1)) : 'Apple Batch'
            const formattedName = `${fruitName} · ${batch.origin || 'Harvest'}`
            const daysText = days !== null ? `${days}d remaining` : 'Awaiting prediction'
            const freshnessText = batch.freshness_prediction || 'Pending'
            const actionMsg = getFefoActionMsg(priority.label, days)

            return (
              <Link
                href={`/batches/${batch.batch_id || batch.id}`}
                className="batch-row"
                key={batch.batch_id || batch.id}
                style={{
                  borderLeft: `4px solid ${priority.color}`,
                  background: days !== null && days <= FEFO_THRESHOLDS.URGENT
                    ? 'rgba(254, 226, 226, 0.4)'
                    : days !== null && days <= FEFO_THRESHOLDS.HIGH
                      ? 'rgba(255, 237, 213, 0.3)'
                      : undefined,
                }}
              >
                <div className="batch-thumb" style={{
                  background: priority.bgColor,
                  color: priority.color,
                }}>
                  {days !== null ? (
                    <span style={{ fontSize: '14px', fontWeight: 800 }}>{days}</span>
                  ) : (
                    <Apple size={19} />
                  )}
                </div>
                <div className="batch-main">
                  <b>{formattedName}</b>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {batch.batch_id || batch.id} · {freshnessText}
                  </span>
                </div>
                <div className="batch-meta" style={{ flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    fontSize: '0.85rem', fontWeight: 800, color: priority.color,
                  }}>
                    <span style={{
                      display: 'inline-block', width: '8px', height: '8px',
                      borderRadius: '50%', background: priority.color,
                    }} />
                    {priority.label}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                    {daysText}
                  </span>
                </div>
                <div style={{
                  marginLeft: '8px', maxWidth: '160px', textAlign: 'right',
                  fontSize: '0.7rem', color: 'var(--muted)', lineHeight: '1.3',
                }}>
                  {actionMsg}
                </div>
                <ArrowUpRight className="row-arrow" size={17} />
              </Link>
            )
          })}
        </div>
      ) : (
        <div className="panel" style={{ padding: '2rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          <Clock3 size={24} style={{ color: 'var(--gold)', margin: '0 auto 0.75rem', opacity: 0.6 }} />
          <b>No batches in FEFO queue</b>
          <p className="muted-text" style={{ margin: '0.5rem 0 0' }}>Create a batch and run detection to see FEFO priorities.</p>
        </div>
      )}



      {/* ============================================================
          FEFO-PRIORITIZED RECOMMENDATIONS
          ============================================================ */}
      <div className="section-heading">
        <div>
          <h2>Recommended actions</h2>
          <p>Prioritized by FEFO urgency — handle the most critical batches first.</p>
        </div>
        <Link href="/recommendations" className="text-button">
          View all <ArrowUpRight size={15} />
        </Link>
      </div>

      <div className="activity-strip" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: fefoQueue.length > 0 ? 'repeat(3, 1fr)' : '1fr', gap: '16px' }}>
          {fefoQueue.length > 0 ? (
            fefoQueue.slice(0, 3).map(({ batch, days, priority }, idx) => {
              const fruitName = batch.fruit ? (batch.fruit.charAt(0).toUpperCase() + batch.fruit.slice(1)) : 'Apple Batch'
              const actionMsg = getFefoActionMsg(priority.label, days)
              return (
                <Link
                  href={`/batches/${batch.batch_id || batch.id}`}
                  key={batch.batch_id || batch.id}
                  style={{
                    display: 'flex', flexDirection: 'column', gap: '8px',
                    padding: '16px', borderRadius: '12px',
                    background: 'rgba(255,255,255,0.06)', color: '#fff',
                    textDecoration: 'none', border: `1px solid ${priority.color}33`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{
                      fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase',
                      letterSpacing: '0.08em', color: priority.color,
                    }}>
                      {priority.label}
                    </span>
                    {days !== null && (
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--gold)' }}>
                        {days}d left
                      </span>
                    )}
                  </div>
                  <b style={{ fontSize: '0.9rem', color: '#fffdf8' }}>
                    {fruitName} · {batch.origin || 'Harvest'}
                  </b>
                  <span style={{ fontSize: '0.75rem', color: '#afc0bd', lineHeight: '1.3' }}>
                    {actionMsg}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#7e9b9b', marginTop: 'auto' }}>
                    {batch.batch_id || batch.id} · {batch.freshness_prediction || 'Pending'}
                  </span>
                </Link>
              )
            })
          ) : (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '1.5rem', color: '#afc0bd' }}>
              <Clock3 size={20} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
              <span style={{ fontSize: '0.85rem' }}>No FEFO-prioritized batches yet. Create a batch to get started.</span>
            </div>
          )}
        </div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Recent batches</h2>
          <p>Keep an eye on your latest harvest data.</p>
        </div>
        <Link href="/batches" className="text-button">
          View all batches <ArrowUpRight size={15} />
        </Link>
      </div>

      <div className="batch-list">
        {recentBatches.map((batch) => {
          const fruitName = batch.fruit ? (batch.fruit.charAt(0).toUpperCase() + batch.fruit.slice(1)) : 'Apple Batch'
          const formattedName = `${fruitName} · ${batch.origin || 'Harvest'}`
          const imageCount = batch.number_of_images || batch.images || 0
          const appleCount = batch.total_apples_detected || batch.apples || 0
          
          return (
            <Link href={`/batches/${batch.batch_id || batch.id}`} className="batch-row" key={batch.batch_id || batch.id}>
              <div className="batch-thumb">
                <Apple size={21} />
              </div>
              <div className="batch-main">
                <b>{formattedName}</b>
                <span>
                  {batch.batch_id || batch.id} · {imageCount} images · {appleCount} apples detected
                </span>
              </div>
              <div className="batch-meta">
                <span>{batch.shelf_life_prediction || batch.shelf || 'N/A'} shelf life</span>
                <Status>{batch.batch_status || batch.status || 'CREATED'}</Status>
              </div>
              <ArrowUpRight className="row-arrow" size={17} />
            </Link>
          )
        })}
        {recentBatches.length === 0 && (
          <div className="empty-state" style={{ padding: '2rem' }}>
            <Package size={24} />
            <b>No recent batches found</b>
            <p>Go to Create Batch to analyze your first harvest.</p>
          </div>
        )}
      </div>

      <div className="activity-strip">
        <div className="section-heading">
          <div>
            <h2>Recent activity</h2>
            <p>Updates from across your workspace.</p>
          </div>
          <button className="more-button">
            <Ellipsis size={18} />
          </button>
        </div>
        <div className="activity-grid">
          {activities.map(([title, detail, time, icon]) => (
            <div className="activity-item" key={title}>
              <div className="activity-icon">
                {icon === 'truck' ? <Truck size={16} /> : icon === 'spark' ? <Sparkles size={16} /> : <Check size={16} />}
              </div>
              <div>
                <b>{title}</b>
                <p>{detail}</p>
                <small>{time}</small>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
