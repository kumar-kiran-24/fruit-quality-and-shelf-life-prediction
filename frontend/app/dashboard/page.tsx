'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Apple, ArrowUpRight, Check, ChevronDown, Ellipsis, Leaf, Package, Plus, Sparkles, Truck
} from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import Metric from '../../components/common/Metric'
import Status from '../../components/common/Status'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

const activities = [
  ['Detection completed', 'Latest batch analysis processed successfully', '8 min ago', 'scan'],
  ['New recommendation', 'Routing matchmaking optimized for active harvests', '42 min ago', 'spark'],
  ['Logistics dispatch', 'FEFO delivery paths activated', '2 hr ago', 'truck'],
]

export default function DashboardPage() {
  const [stats, setStats] = useState({ total: 0, active: 0, apples: 0, ready: 0 })
  const [statusSummary, setStatusSummary] = useState<Record<string, number>>({})
  const [recentBatches, setRecentBatches] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true)
        const summary = await apiRequest(API_CONFIG.ENDPOINTS.SUMMARY)
        const batchesData = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)

        const total = summary.total_batches || 0
        const apples = summary.total_apples_detected || 0
        const statusMap = summary.status_summary || {}
        setStatusSummary(statusMap)

        // Active means not fully completed/delivered/dispatched
        const active = total - (statusMap.DISPATCHED || 0) - (statusMap.COMPLETED || 0) - (statusMap.DELIVERED || 0)
        const ready = (statusMap.READY_FOR_DISPATCH || 0) + (statusMap.ASSIGNED_TO_BUYER || 0)

        setStats({ total, active, apples, ready })

        // Sort by latest creation date
        const sortedBatches = (batchesData.batches || []).sort(
          (a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        setRecentBatches(sortedBatches.slice(0, 3))
      } catch (err: any) {
        setError(err.message || 'Failed to connect to backend server.')
      } finally {
        setLoading(false)
      }
    }
    loadDashboardData()
  }, [])

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
        <h3 style={{ color: '#eb5e28', marginBottom: '1rem' }}>Dashboard Loading Failed</h3>
        <p className="muted-text" style={{ marginBottom: '2rem' }}>{error}</p>
        <button onClick={() => window.location.reload()} className="secondary-button" style={{ display: 'inline-flex' }}>
          Retry connection
        </button>
      </div>
    )
  }

  const readyCount = (statusSummary.READY_FOR_DISPATCH || 0) + (statusSummary.ASSIGNED_TO_BUYER || 0)
  const processingCount = (statusSummary.DETECTED || 0) + (statusSummary.SHELF_LIFE_PREDICTED || 0) + (statusSummary.RECOMMENDED || 0)
  const dispatchedCount = (statusSummary.DISPATCHED || 0) + (statusSummary.IN_TRANSIT || 0) + (statusSummary.DELIVERED || 0) + (statusSummary.COMPLETED || 0)
  const draftCount = statusSummary.CREATED || 0

  return (
    <>
      <PageIntro
        eyebrow={formattedDate}
        title="Good morning, Jamie."
        description="Here’s what’s happening across Hawthorne Orchards today."
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

      <div className="dashboard-grid">
        <section className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Batch activity</h3>
              <p>Apples processed over the last 30 days</p>
            </div>
            <button className="select-button">
              Last 30 days <ChevronDown size={14} />
            </button>
          </div>
          <div className="chart-area">
            <div className="chart-y">
              <span>800</span>
              <span>600</span>
              <span>400</span>
              <span>200</span>
              <span>0</span>
            </div>
            <div className="bars">
              {[
                34, 42, 38, 53, 48, 66, 58, 72, 63, 78, 70, 88, 81, 74, 92, 84, 96, 87, 75, 90, 80, 94, 86, 98,
                92, 100, 88, 96, 84, 91,
              ].map((v, i) => (
                <div key={i} className="bar-wrap">
                  <div className="bar" style={{ height: `${v}%` }} />
                  <span>{i === 0 ? 'Jun 18' : i === 14 ? 'Jul 2' : i === 29 ? 'Jul 18' : ''}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="panel status-panel">
          <div className="panel-heading">
            <div>
              <h3>Batch status</h3>
              <p>Current lifecycle overview</p>
            </div>
            <button className="more-button" aria-label="More options">
              <Ellipsis size={18} />
            </button>
          </div>
          <div className="donut-wrap">
            <div className="donut">
              <div>
                <b>{stats.total}</b>
                <span>Total</span>
              </div>
            </div>
            <div className="legend">
              <span>
                <i className="dot gold-dot" />Ready <b>{readyCount}</b>
              </span>
              <span>
                <i className="dot navy-dot" />Processing <b>{processingCount}</b>
              </span>
              <span>
                <i className="dot green-dot" />Dispatched <b>{dispatchedCount}</b>
              </span>
              <span>
                <i className="dot gray-dot" />Draft <b>{draftCount}</b>
              </span>
            </div>
          </div>
        </section>
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
          const formattedName = `${batch.fruit.charAt(0).toUpperCase() + batch.fruit.slice(1)} · ${batch.origin}`
          
          return (
            <Link href={`/batches/${batch.batch_id}`} className="batch-row" key={batch.batch_id}>
              <div className="batch-thumb">
                <Apple size={21} />
              </div>
              <div className="batch-main">
                <b>{formattedName}</b>
                <span>
                  {batch.batch_id} · {batch.number_of_images} images · {batch.total_apples_detected} apples detected
                </span>
              </div>
              <div className="batch-meta">
                <span>{batch.shelf_life_prediction || 'N/A'} shelf life</span>
                <Status>{batch.batch_status}</Status>
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
