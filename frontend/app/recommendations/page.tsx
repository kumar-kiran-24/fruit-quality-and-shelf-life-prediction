'use client'

import React, { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import {
  Apple, ArrowUpRight, Calendar, ChevronDown, Clock3, AlertTriangle, MapPin,
  Package, RefreshCw, Sparkles, Truck, Loader2, Target, Zap
} from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'
import { RouteOption, RoutingResponse } from '../../services/recommendationService'
import {
  parseRemainingDays,
  deriveFefoPriority,
  getDispatchWindow,
  getFefoActionMsg,
  DESTINATION_CATALOG,
  matchDestinationsForBatch,
  DISPATCH_WINDOW_LABELS,
  PRIORITY_LEVELS,
  type DispatchWindow,
  type FefoPriority,
  type DestinationCatalog,
  safeNumeric,
} from '../../config/fefo.config'

// ============================================================
// DISPATCH PLAN ENTRY
// ============================================================

interface DispatchPlanEntry {
  batch: any
  days: number | null
  priority: FefoPriority
  window: DispatchWindow
  recommendedDestination: (DestinationCatalog & { dispatchFit: string; fitPriority: number }) | null
  actionMsg: string
}

// ============================================================
// HELPER: BUILD FEFO DISPATCH PLAN
// ============================================================

function buildFefoDispatchPlan(batches: any[]): DispatchPlanEntry[] {
  // Filter out dispatched/completed/delivered batches
  const eligible = batches.filter((b: any) => {
    const status = (b.batch_status || '').toUpperCase()
    return status !== 'DISPATCHED' && status !== 'COMPLETED' && status !== 'DELIVERED'
  })

  const plan: DispatchPlanEntry[] = eligible.map((batch: any) => {
    const days = parseRemainingDays(batch.shelf_life_prediction)
    const priority = deriveFefoPriority(days)
    const window = getDispatchWindow(days)
    const destinations = matchDestinationsForBatch(days, batch.origin)
    const recommendedDestination = destinations.length > 0 ? destinations[0] : null
    const actionMsg = getFefoActionMsg(priority.label, days)

    return { batch, days, priority, window, recommendedDestination, actionMsg }
  })

  // Sort: lowest remaining days first, then by priority sort order
  plan.sort((a, b) => {
    if (a.days !== null && b.days !== null) return a.days - b.days
    if (a.days === null && b.days === null) return a.priority.sortOrder - b.priority.sortOrder
    if (a.days === null) return 1
    return -1
  })

  return plan
}

// ============================================================
// HELPER: GROUP BY DISPATCH WINDOW
// ============================================================

function groupByWindow(plan: DispatchPlanEntry[]): Record<DispatchWindow, DispatchPlanEntry[]> {
  const groups: Record<DispatchWindow, DispatchPlanEntry[]> = {
    today: [],
    tomorrow: [],
    upcoming: [],
    pending: [],
  }
  for (const entry of plan) {
    groups[entry.window].push(entry)
  }
  return groups
}

// ============================================================
// COMPONENT
// ============================================================

export default function RecommendationsPage() {
  const [batches, setBatches] = useState<any[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState('')
  const [recommendation, setRecommendation] = useState<RoutingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [recLoading, setRecLoading] = useState(false)
  const [error, setError] = useState('')

  // ============================================================
  // DATA FETCHING
  // ============================================================

  const fetchBatches = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)
      const list = Array.isArray(data) ? data : (data.batches || data.items || [])
      setBatches(list)
      if (list.length > 0 && !selectedBatchId) {
        setSelectedBatchId(list[0].batch_id || list[0].id)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch batches.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBatches()
  }, [])

  const selectedBatch = useMemo(() => {
    return batches.find((b: any) => (b.batch_id || b.id) === selectedBatchId)
  }, [batches, selectedBatchId])

  const fetchRecommendations = async (id: string) => {
    try {
      setRecLoading(true)
      setError('')
      const recs = await apiRequest(API_CONFIG.ENDPOINTS.RECOMMENDATIONS(id))
      setRecommendation(recs)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch recommendations for this batch.')
      setRecommendation(null)
    } finally {
      setRecLoading(false)
    }
  }

  useEffect(() => {
    if (selectedBatchId) {
      fetchRecommendations(selectedBatchId)
    }
  }, [selectedBatchId])

  const handleRunAnalysis = async () => {
    if (!selectedBatchId) return
    fetchRecommendations(selectedBatchId)
  }

  // ============================================================
  // FEFO DISPATCH PLAN (computed from all batches)
  // ============================================================

  const dispatchPlan = useMemo(() => buildFefoDispatchPlan(batches), [batches])
  const windowGroups = useMemo(() => groupByWindow(dispatchPlan), [dispatchPlan])

  // ============================================================
  // MATCHES for selected batch
  // ============================================================

  const rawMatches = recommendation?.options || recommendation?.recommendations || recommendation?.matches || []
  const matches: RouteOption[] = Array.isArray(rawMatches) ? rawMatches : []
  const explanation = recommendation?.optimization_summary || recommendation?.reason || 'Analysis recommends nearby grocers for immediate stock placement.'

  // ============================================================
  // DISPLAY HELPERS
  // ============================================================

  const getScoreText = (m: any): string => {
    const scoreVal = m?.total_score ?? m?.score ?? m?.matchScore
    if (scoreVal === undefined || scoreVal === null) return 'Awaiting match analysis'

    if (typeof scoreVal === 'number') {
      if (scoreVal >= 0 && scoreVal <= 1) {
        return `${(scoreVal * 100).toFixed(0)}%`
      }
      return `${scoreVal.toFixed(0)}%`
    }

    if (typeof scoreVal === 'string') {
      if (scoreVal.includes('%')) return scoreVal
      const parsed = parseFloat(scoreVal)
      if (!isNaN(parsed)) {
        return parsed >= 0 && parsed <= 1 ? `${(parsed * 100).toFixed(0)}%` : `${parsed.toFixed(0)}%`
      }
      return scoreVal
    }

    return 'Awaiting match analysis'
  }

  const getDistanceText = (m: any): string => {
    const dist = m?.distance_km ?? m?.distance
    if (dist === undefined || dist === null) return 'Distance being calculated'
    if (typeof dist === 'number') {
      if (dist === 0) return 'Local'
      return `${dist.toFixed(1)} km`
    }
    return String(dist)
  }

  const getDispatchFitLabel = (m: any, days: number | null): string => {
    const window = getDispatchWindow(days)
    if (window === 'today') return 'Best for: Send Today'
    if (window === 'tomorrow') return 'Best for: Send Tomorrow'
    return 'Best for: Schedule'
  }

  // ============================================================
  // LOADING STATE
  // ============================================================

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading logistics router...</b>
        </div>
      </div>
    )
  }

  // ============================================================
  // COMPUTED SUMMARY STATS
  // ============================================================

  const todayCount = windowGroups.today.length
  const tomorrowCount = windowGroups.tomorrow.length
  const upcomingCount = windowGroups.upcoming.length
  const pendingCount = windowGroups.pending.length
  const urgentCount = dispatchPlan.filter(e => e.priority.label === 'URGENT').length
  const highCount = dispatchPlan.filter(e => e.priority.label === 'HIGH').length

  return (
    <>
      <PageIntro
        eyebrow="FEFO dispatch planning"
        title="Recommendations"
        description="Plan which batches to dispatch first based on remaining shelf life, and find the best destinations."
        action={
          <button className="primary-button" type="button" onClick={handleRunAnalysis} disabled={recLoading}>
            {recLoading ? (
              <>
                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Analyzing...
              </>
            ) : (
              <>
                <Sparkles size={16} />Run analysis
              </>
            )}
          </button>
        }
      />

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 600 }}>
          {error}
        </div>
      )}

      {/* ============================================================
          SECTION 1: TODAY / TOMORROW / UPCOMING DISTRIBUTION VIEW
          ============================================================ */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '1.5rem',
      }}>
        {(['today', 'tomorrow', 'upcoming', 'pending'] as DispatchWindow[]).map(win => {
          const config = DISPATCH_WINDOW_LABELS[win]
          const count = windowGroups[win].length
          const urgentInWindow = windowGroups[win].filter(e => e.priority.label === 'URGENT').length
          const highInWindow = windowGroups[win].filter(e => e.priority.label === 'HIGH').length

          return (
            <div
              key={win}
              className="metric-card"
              style={{
                borderTop: win === 'today' ? '3px solid #b91c1c'
                  : win === 'tomorrow' ? '3px solid #c2410c'
                  : win === 'pending' ? '3px solid #71808a'
                  : '3px solid #166534',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <p style={{ margin: 0, fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                  {config.icon} {config.title}
                </p>
                {win === 'today' && urgentCount > 0 && (
                  <span style={{
                    background: '#fee2e2', color: '#b91c1c', padding: '2px 8px',
                    borderRadius: '10px', fontSize: '0.7rem', fontWeight: 800,
                  }}>
                    <Zap size={10} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '2px' }} />
                    {urgentCount}
                  </span>
                )}
              </div>
              <strong style={{ fontSize: '28px', color: 'var(--navy)', display: 'block' }}>{count}</strong>
              <span className="metric-change" style={{
                color: win === 'today' ? '#b91c1c' : win === 'tomorrow' ? '#c2410c' : 'var(--green)',
              }}>
                {count === 1 ? 'batch' : 'batches'}
                {urgentInWindow > 0 && ` · ${urgentInWindow} urgent`}
                {highInWindow > 0 && ` · ${highInWindow} high`}
                {count === 0 && win !== 'pending' && ' — clear'}
              </span>
            </div>
          )
        })}
      </div>

      {/* ============================================================
          SECTION 2: FEFO DISPATCH PLAN
          ============================================================ */}
      <div className="section-heading">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock3 size={20} /> FEFO Dispatch Plan
          </h2>
          <p>Batches grouped by dispatch urgency — send the most urgent first.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {urgentCount > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              background: '#fee2e2', color: '#b91c1c', padding: '4px 10px',
              borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700,
            }}>
              <Zap size={12} /> {urgentCount} urgent
            </span>
          )}
          {highCount > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              background: '#ffedd5', color: '#c2410c', padding: '4px 10px',
              borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700,
            }}>
              <AlertTriangle size={12} /> {highCount} high
            </span>
          )}
        </div>
      </div>

      {/* Dispatch Plan Cards by Window */}
      {(['today', 'tomorrow', 'upcoming', 'pending'] as DispatchWindow[]).map(win => {
        const entries = windowGroups[win]
        if (entries.length === 0) return null
        const config = DISPATCH_WINDOW_LABELS[win]

        return (
          <div key={win} style={{ marginBottom: '1.25rem' }}>
            {/* Window Header */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px',
              padding: '8px 14px', borderRadius: '10px',
              background: win === 'today' ? 'rgba(185, 28, 28, 0.06)'
                : win === 'tomorrow' ? 'rgba(194, 65, 12, 0.06)'
                : win === 'pending' ? 'rgba(113, 128, 138, 0.06)'
                : 'rgba(22, 101, 52, 0.06)',
            }}>
              <span style={{ fontSize: '1.1rem' }}>{config.icon}</span>
              <div>
                <b style={{ fontSize: '0.9rem', color: 'var(--navy)' }}>{config.title}</b>
                <span className="muted-text" style={{ display: 'block', fontSize: '0.75rem' }}>{config.subtitle}</span>
              </div>
              <span style={{
                marginLeft: 'auto', fontSize: '0.8rem', fontWeight: 800, color: 'var(--navy)',
                background: 'var(--card)', padding: '3px 10px', borderRadius: '8px',
                border: '1px solid var(--line)',
              }}>
                {entries.length} {entries.length === 1 ? 'batch' : 'batches'}
              </span>
            </div>

            {/* Batch Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {entries.map(({ batch, days, priority, recommendedDestination, actionMsg }) => {
                const fruitName = batch.fruit ? (batch.fruit.charAt(0).toUpperCase() + batch.fruit.slice(1)) : 'Apple'
                const daysText = days !== null ? `${days}d remaining` : 'Awaiting prediction'
                const freshnessText = batch.freshness_prediction || 'Pending'
                const imageCount = batch.number_of_images || 0
                const appleCount = batch.total_apples_detected || 0

                return (
                  <Link
                    href={`/batches/${batch.batch_id || batch.id}`}
                    key={batch.batch_id || batch.id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '14px',
                      background: 'var(--card)', border: '1px solid var(--line)',
                      borderLeft: `4px solid ${priority.color}`,
                      borderRadius: '11px', padding: '12px 16px',
                      color: 'var(--foreground)', textDecoration: 'none', width: '100%',
                      transition: 'border-color 0.15s',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = '#cbb56f' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)' }}
                  >
                    {/* Priority Badge + Days */}
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px',
                      minWidth: '48px',
                    }}>
                      {days !== null ? (
                        <span style={{
                          fontSize: '1.1rem', fontWeight: 800, color: priority.color, lineHeight: 1,
                        }}>
                          {days}
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>—</span>
                      )}
                      <span style={{ fontSize: '0.6rem', color: 'var(--muted)' }}>days</span>
                    </div>

                    {/* Batch Info */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                        <b style={{ fontSize: '0.85rem' }}>{batch.batch_id || batch.id}</b>
                        <span style={{
                          fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase',
                          letterSpacing: '0.06em', color: priority.color,
                          background: priority.bgColor, padding: '2px 7px', borderRadius: '6px',
                        }}>
                          {priority.label}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                        {fruitName} · {batch.origin || 'Harvest'} · {freshnessText}
                        {imageCount > 0 && ` · ${imageCount} images`}
                        {appleCount > 0 && ` · ${appleCount} apples`}
                      </span>
                    </div>

                    {/* Recommended Destination */}
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px',
                      minWidth: '160px',
                    }}>
                      {recommendedDestination ? (
                        <>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--navy)' }}>
                            <MapPin size={11} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '3px' }} />
                            {recommendedDestination.name}
                          </span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                            {recommendedDestination.city} · {recommendedDestination.distance_km > 0 ? `${recommendedDestination.distance_km} km` : 'Local'}
                          </span>
                        </>
                      ) : (
                        <span style={{ fontSize: '0.7rem', color: 'var(--muted)', fontStyle: 'italic' }}>
                          Awaiting destination match
                        </span>
                      )}
                    </div>

                    {/* Action */}
                    <div style={{
                      maxWidth: '140px', textAlign: 'right', fontSize: '0.65rem',
                      color: 'var(--muted)', lineHeight: '1.3',
                    }}>
                      {actionMsg}
                    </div>

                    <ArrowUpRight size={16} style={{ color: '#8d9995', flexShrink: 0 }} />
                  </Link>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* Empty state */}
      {dispatchPlan.length === 0 && (
        <div className="panel" style={{ padding: '2.5rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          <Clock3 size={28} style={{ color: 'var(--gold)', margin: '0 auto 0.75rem', opacity: 0.6 }} />
          <b>No batches in dispatch plan</b>
          <p className="muted-text" style={{ margin: '0.5rem 0 1rem' }}>
            Create a batch and run detection to see FEFO dispatch priorities.
          </p>
          <Link href="/batches/create" className="primary-button" style={{ display: 'inline-flex' }}>
            <Package size={15} /> Create Batch
          </Link>
        </div>
      )}

      {/* ============================================================
          SECTION 3: BATCH SELECTOR + RECOMMENDATION MATCHES
          ============================================================ */}
      <div className="section-heading" style={{ marginTop: '1rem' }}>
        <div>
          <h2>Destination matching</h2>
          <p>Select a batch to see ranked destination recommendations and dispatch windows.</p>
        </div>
      </div>

      <div className="recommend-layout">
        {/* Left: Selected Batch Info */}
        <section className="panel selected-batch">
          <div className="panel-heading">
            <div>
              <h3>Selected batch</h3>
              <p>Choose a batch to see its best matches.</p>
            </div>
            {batches.length > 0 && (
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <select
                  value={selectedBatchId}
                  onChange={(e) => setSelectedBatchId(e.target.value)}
                  style={{
                    appearance: 'none',
                    background: 'var(--cream)',
                    border: '1px solid var(--gold-border)',
                    padding: '6px 28px 6px 12px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: 'var(--navy)',
                    cursor: 'pointer',
                  }}
                  disabled={recLoading}
                >
                  {batches.map((b: any) => {
                    const bId = b.batch_id || b.id
                    const fruit = b.fruit ? (b.fruit.charAt(0).toUpperCase() + b.fruit.slice(1)) : 'Batch'
                    const days = parseRemainingDays(b.shelf_life_prediction)
                    const p = deriveFefoPriority(days)
                    return (
                      <option key={bId} value={bId}>
                        {bId} — {fruit} {days !== null ? `(${days}d)` : ''} [{p.label}]
                      </option>
                    )
                  })}
                </select>
                <ChevronDown
                  size={12}
                  style={{
                    position: 'absolute', right: '10px', top: '50%',
                    transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--navy)',
                  }}
                />
              </div>
            )}
          </div>

          {selectedBatch ? (
            <div className="selected-info">
              <div className="batch-thumb large">
                <Apple size={28} />
              </div>
              <div>
                <b>
                  {selectedBatch.fruit ? (selectedBatch.fruit.charAt(0).toUpperCase() + selectedBatch.fruit.slice(1)) : 'Apple'} · {selectedBatch.origin || 'Harvest'}
                </b>
                <span>
                  {selectedBatch.total_apples_detected || 0} apples · {selectedBatch.shelf_life_prediction || 'N/A'} shelf life
                </span>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '1rem' }} className="muted-text">
              No batches selected.
            </div>
          )}

          {selectedBatch && (
            <div className="recommend-explain">
              <Sparkles size={17} />
              <div>
                <b>Freshness window analysis</b>
                <p>{explanation}</p>
              </div>
            </div>
          )}

          {/* Selected batch FEFO summary */}
          {selectedBatch && (() => {
            const days = parseRemainingDays(selectedBatch.shelf_life_prediction)
            const priority = deriveFefoPriority(days)
            const window = getDispatchWindow(days)
            const windowConfig = DISPATCH_WINDOW_LABELS[window]

            return (
              <div style={{
                marginTop: '12px', padding: '12px', borderRadius: '10px',
                background: priority.bgColor, border: `1px solid ${priority.color}22`,
                display: 'flex', alignItems: 'center', gap: '10px',
              }}>
                <span style={{
                  fontSize: '0.75rem', fontWeight: 800, color: priority.color,
                  background: `${priority.color}15`, padding: '3px 8px', borderRadius: '6px',
                }}>
                  {priority.label}
                </span>
                <div style={{ flex: 1 }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--navy)' }}>
                    {windowConfig.icon} {windowConfig.title}
                  </span>
                  <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--muted)' }}>
                    {days !== null ? `${days} days remaining` : 'Awaiting prediction'} · {priority.actionLabel}
                  </span>
                </div>
                {days !== null && (
                  <span style={{ fontSize: '1.3rem', fontWeight: 800, color: priority.color, lineHeight: 1 }}>
                    {days}d
                  </span>
                )}
              </div>
            )
          })()}
        </section>

        {/* Right: Destination Matches */}
        <section className="panel matches">
          <div className="panel-heading">
            <div>
              <h3>Ranked destinations</h3>
              <p>Ordered by distance suitability and dispatch window.</p>
            </div>
          </div>
          {recLoading ? (
            <div style={{ display: 'flex', minHeight: '150px', alignItems: 'center', justifyContent: 'center' }}>
              <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--gold)' }} />
            </div>
          ) : matches.length > 0 ? (
            (() => {
              const days = selectedBatch ? parseRemainingDays(selectedBatch.shelf_life_prediction) : null
              return matches.map((m: any, idx: number) => {
                const destName = m.destination_name || m.name || 'Destination'
                const destAddr = m.destination_address || m.address || m.location || ''
                const destCity = destAddr.split(',')[0] || destAddr || 'Location'
                const scoreDisplay = getScoreText(m)
                const distanceDisplay = getDistanceText(m)
                const dispatchFit = getDispatchFitLabel(m, days)

                return (
                  <div className={`match-row ${idx === 0 ? 'best' : ''}`} key={m.destination_id || m.id || idx}>
                    <div className="match-rank">{idx + 1}</div>
                    <div className="match-copy">
                      <b>
                        {destName}{' '}
                        {idx === 0 && <span className="recommended-label">Recommended</span>}
                      </b>
                      <span>
                        <MapPin size={13} />
                        {destCity} · {distanceDisplay}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#628368', fontWeight: 600 }}>
                        {dispatchFit}
                      </span>
                    </div>
                    <strong>{scoreDisplay}</strong>
                    <ArrowUpRight size={16} />
                  </div>
                )
              })
            })()
          ) : selectedBatch ? (
            <div style={{ textAlign: 'center', padding: '3rem' }} className="muted-text">
              <Target size={28} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
              <b style={{ display: 'block', fontSize: '0.9rem', color: 'var(--navy)', marginBottom: '0.5rem' }}>
                No routing recommendations yet
              </b>
              <p style={{ margin: 0, fontSize: '0.8rem' }}>
                Run analysis to compute optimal routes and destination matches.
              </p>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem' }} className="muted-text">
              <Package size={28} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
              <b style={{ display: 'block', fontSize: '0.9rem', color: 'var(--navy)', marginBottom: '0.5rem' }}>
                Select a batch to view matches
              </b>
              <p style={{ margin: 0, fontSize: '0.8rem' }}>
                Choose a batch from the dropdown to see recommended destinations.
              </p>
            </div>
          )}
        </section>
      </div>

      {/* ============================================================
          SECTION 4: DESTINATION NETWORK OVERVIEW
          ============================================================ */}
      <div className="section-heading" style={{ marginTop: '1.5rem' }}>
        <div>
          <h2>Destination network</h2>
          <p>All available buyer destinations in the Karnataka region.</p>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
          {DESTINATION_CATALOG.length} locations
        </span>
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px',
        marginBottom: '2rem',
      }}>
        {DESTINATION_CATALOG.map(dest => (
          <div
            key={dest.id}
            className="panel"
            style={{
              padding: '14px', display: 'flex', flexDirection: 'column', gap: '6px',
              cursor: 'default',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <b style={{ fontSize: '0.85rem' }}>{dest.name}</b>
              <span style={{
                fontSize: '0.6rem', fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.05em', color: 'var(--muted)', background: 'var(--cream)',
                padding: '2px 6px', borderRadius: '4px',
              }}>
                {dest.destination_type}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <MapPin size={11} />
              {dest.city}, {dest.state}
              {dest.distance_km > 0 && ` · ${dest.distance_km} km`}
              {dest.distance_km === 0 && ' · Local'}
            </span>
          </div>
        ))}
      </div>
    </>
  )
}
