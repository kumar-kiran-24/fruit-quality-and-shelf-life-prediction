'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Apple, ArrowLeft, ArrowUpRight, Check, MapPin, Sparkles, Loader2
} from 'lucide-react'
import PageIntro from '../../../components/common/PageIntro'
import Status from '../../../components/common/Status'
import Sparkline from '../../../components/common/Sparkline'
import { apiRequest } from '../../../lib/apiClient'
import { API_CONFIG } from '../../../config/api.config'

export default function BatchDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const batchId = params?.batchId as string

  const [data, setData] = useState<any>(null)
  const [validTransitions, setValidTransitions] = useState<string[]>([])
  const [selectedBuyerId, setSelectedBuyerId] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')

  const loadData = async () => {
    try {
      setError('')
      const details = await apiRequest(API_CONFIG.ENDPOINTS.BATCH_DETAIL(batchId))
      setData(details)

      // Fetch next valid status transitions
      const transitionData = await apiRequest(`${API_CONFIG.ENDPOINTS.STATUS_UPDATE(batchId)}/valid-transitions`)
      setValidTransitions(transitionData.valid_next_statuses || [])
      
      // Auto-set the recommended buyer if available
      if (details.recommendations && details.recommendations.length > 0) {
        setSelectedBuyerId(details.recommendations[0].destination_id)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load batch report details.')
    } finally {
      setLoading(false)
      setActionLoading(false)
    }
  }

  useEffect(() => {
    if (batchId) {
      loadData()
    }
  }, [batchId])

  const handlePredictShelfLife = async () => {
    try {
      setActionLoading(true)
      setError('')
      // 1. Run prediction
      await apiRequest(API_CONFIG.ENDPOINTS.PREDICT_SHELF_LIFE(batchId))
      // 2. Transition status
      await apiRequest(API_CONFIG.ENDPOINTS.STATUS_UPDATE(batchId), {
        method: 'PATCH',
        body: JSON.stringify({
          new_status: 'SHELF_LIFE_PREDICTED',
          action: 'AI Shelf-Life model executed'
        })
      })
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to execute prediction.')
      setActionLoading(false)
    }
  }

  const handleRunRecommendations = async () => {
    try {
      setActionLoading(true)
      setError('')
      // 1. Generate matches
      await apiRequest(API_CONFIG.ENDPOINTS.RECOMMENDATIONS(batchId))
      // 2. Transition status
      await apiRequest(API_CONFIG.ENDPOINTS.STATUS_UPDATE(batchId), {
        method: 'PATCH',
        body: JSON.stringify({
          new_status: 'RECOMMENDED',
          action: 'Routing recommendation optimization generated'
        })
      })
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to generate buyer recommendations.')
      setActionLoading(false)
    }
  }

  const handleAssignBuyer = async () => {
    if (!selectedBuyerId) return
    try {
      setActionLoading(true)
      setError('')
      await apiRequest(API_CONFIG.ENDPOINTS.ASSIGN(batchId), {
        method: 'POST',
        body: JSON.stringify({ destination_id: selectedBuyerId })
      })
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to assign buyer.')
      setActionLoading(false)
    }
  }

  const handleGenericTransition = async (nextStatus: string) => {
    try {
      setActionLoading(true)
      setError('')
      await apiRequest(API_CONFIG.ENDPOINTS.STATUS_UPDATE(batchId), {
        method: 'PATCH',
        body: JSON.stringify({
          new_status: nextStatus,
          action: `Logistics state transition to ${nextStatus}`
        })
      })
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to update status.')
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading batch report...</b>
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="panel" style={{ padding: '3rem', textAlign: 'center', border: '1px solid rgba(235,94,40,0.2)' }}>
        <Apple size={44} style={{ color: '#eb5e28', margin: '0 auto 1rem' }} />
        <h3 style={{ color: '#eb5e28', marginBottom: '1rem' }}>Report Retrieval Failed</h3>
        <p className="muted-text" style={{ marginBottom: '2rem' }}>{error}</p>
        <Link href="/batches" className="secondary-button" style={{ display: 'inline-flex' }}>
          Back to batches
        </Link>
      </div>
    )
  }

  const batch = data.batch
  const recommendations = data.recommendations || []
  const dispatch = data.dispatch || {}

  // Determine user friendly date
  const formattedDate = new Date(batch.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })

  return (
    <>
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link href="/batches" className="text-button" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem' }}>
          <ArrowLeft size={15} /> Back to batches
        </Link>

        {/* Dynamic transition action buttons */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {actionLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', color: 'var(--navy-muted)' }}>
              <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Processing...
            </div>
          )}
          
          {!actionLoading && validTransitions.includes('SHELF_LIFE_PREDICTED') && (
            <button className="primary-button" onClick={handlePredictShelfLife}>
              <Sparkles size={15} /> Predict Shelf Life
            </button>
          )}

          {!actionLoading && validTransitions.includes('RECOMMENDED') && (
            <button className="primary-button" onClick={handleRunRecommendations}>
              <Sparkles size={15} /> Run Recommendations
            </button>
          )}

          {!actionLoading && validTransitions.includes('READY_FOR_DISPATCH') && (
            <button className="primary-button" onClick={() => handleGenericTransition('READY_FOR_DISPATCH')}>
              Mark Ready for Dispatch
            </button>
          )}

          {!actionLoading && validTransitions.includes('DISPATCHED') && (
            <button className="primary-button" onClick={() => handleGenericTransition('DISPATCHED')}>
              Confirm Dispatch
            </button>
          )}

          {!actionLoading && validTransitions.includes('DELIVERED') && (
            <button className="primary-button" onClick={() => handleGenericTransition('DELIVERED')}>
              Mark Delivered
            </button>
          )}

          {!actionLoading && validTransitions.includes('COMPLETED') && (
            <button className="primary-button" onClick={() => handleGenericTransition('COMPLETED')}>
              Complete Batch
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 600 }}>
          {error}
        </div>
      )}

      <PageIntro
        eyebrow={`Batch identifier: ${batch.batch_id}`}
        title={`${batch.fruit.charAt(0).toUpperCase() + batch.fruit.slice(1)} · ${batch.origin}`}
        description={`Harvested on ${formattedDate}`}
        action={<Status>{batch.batch_status}</Status>}
      />

      <div className="create-layout">
        {/* Left Column: Information and YOLO Computer Vision Results */}
        <section className="panel form-panel">
          <div className="panel-heading">
            <div>
              <h3>Detection results</h3>
              <p>YOLO computer vision analysis overview.</p>
            </div>
            <span>Quality: <b>{batch.quality_status}</b></span>
          </div>

          <div className="detail-grid" style={{ marginBottom: '1.5rem' }}>
            <div>
              <small>Apples detected</small>
              <b>{batch.total_apples_detected || 0}</b>
            </div>
            <div>
              <small>Freshness status</small>
              <b style={{ color: batch.freshness_prediction === 'fresh' ? '#2d6a4f' : 'inherit' }}>
                {batch.freshness_prediction || 'PENDING'}
              </b>
            </div>
            <div>
              <small>Images processed</small>
              <b>{batch.number_of_images || 0} images</b>
            </div>
          </div>

          <div className="detection-preview" style={{ marginBottom: '1.5rem' }}>
            <div className="orchard-placeholder">
              <Apple size={44} />
              <span>Detection preview</span>
              <small>{batch.total_apples_detected || 0} apples identified</small>
              <div className="scan-line" />
            </div>
            <div className="detection-stats">
              <div>
                <small>Confidence rating</small>
                <b>{(batch.freshness_confidence * 100).toFixed(1)}%</b>
                <div className="confidence">
                  <span style={{ width: `${batch.freshness_confidence * 100}%` }} />
                </div>
              </div>
              <div>
                <small>Confidence trace</small>
                <Sparkline values={[20, 35, 28, 45, 42, 59, 54]} gold />
              </div>
            </div>
          </div>

          {batch.ai_summary && (
            <div style={{ marginTop: '1.5rem' }}>
              <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--navy-muted)', marginBottom: '0.5rem' }}>AI Summary Report</h4>
              <p style={{ fontSize: '0.95rem', color: 'var(--navy)', lineHeight: '1.5', background: 'rgba(0,0,0,0.02)', padding: '1rem', borderRadius: '8px' }}>
                {batch.ai_summary}
              </p>
            </div>
          )}
        </section>

        {/* Right Column: Freshness and Destination Routing */}
        <section className="panel upload-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Shelf Life Prediction */}
          <div>
            <div className="panel-heading" style={{ padding: 0, marginBottom: '1rem' }}>
              <div>
                <h3>Shelf-life prediction</h3>
                <p>Freshness degradation intelligence.</p>
              </div>
            </div>
            <div style={{ background: 'var(--cream)', border: '1px solid var(--gold-border)', borderRadius: '12px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span className="gold-text" style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>Remaining span</span>
                <strong style={{ fontSize: '2rem', color: 'var(--navy)', fontWeight: 800 }}>
                  {batch.shelf_life_prediction !== 'N/A' ? batch.shelf_life_prediction : 'Pending'}{' '}
                  {batch.shelf_life_prediction !== 'N/A' && <small style={{ fontSize: '1rem', fontWeight: 500 }}></small>}
                </strong>
              </div>
              <div className="shelf-bar" style={{ height: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <span style={{ display: 'block', height: '100%', width: batch.shelf_life_prediction !== 'N/A' ? '70%' : '0%', background: 'var(--gold)' }} />
              </div>
              <small className="muted-text">Confidence: {(batch.shelf_life_confidence * 100).toFixed(1)}% · Risk: {batch.risk_level}</small>
            </div>
          </div>

          {/* Dispatch Details / Buyer Assignment */}
          <div>
            <div className="panel-heading" style={{ padding: 0, marginBottom: '1rem' }}>
              <div>
                <h3>Destination routing</h3>
                <p>Active routing assignment matches.</p>
              </div>
            </div>

            {batch.batch_status === 'RECOMMENDED' && recommendations.length > 0 && (
              <div style={{ background: 'var(--cream)', border: '1px solid var(--gold-border)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontWeight: 600, fontSize: '0.85rem', color: 'var(--navy)' }}>
                  Select Buyer Destination
                  <select
                    value={selectedBuyerId}
                    onChange={(e) => setSelectedBuyerId(e.target.value)}
                    style={{ padding: '8px', borderRadius: '6px', border: '1px solid var(--gold-border)', background: 'var(--cream)', fontSize: '0.9rem' }}
                  >
                    {recommendations.map((r: any) => (
                      <option key={r.destination_id} value={r.destination_id}>
                        {r.destination_name} (Score: {r.total_score.toFixed(1)})
                      </option>
                    ))}
                  </select>
                </label>
                <button className="primary-button full" onClick={handleAssignBuyer} disabled={actionLoading}>
                  <Check size={16} /> Assign Selected Buyer
                </button>
              </div>
            )}

            {/* Display Dispatch / Assigned Info */}
            {dispatch.dispatch_id ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="recommend-card" style={{ margin: 0 }}>
                  <MapPin size={17} style={{ color: 'var(--gold)' }} />
                  <div>
                    <b>Assigned Destination</b>
                    <p style={{ margin: '2px 0 0', fontWeight: 700 }}>{dispatch.destination_name}</p>
                    <small className="muted-text">{dispatch.destination_address} · {dispatch.distance_km} km</small>
                  </div>
                </div>
                <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.02)', borderRadius: '6px', fontSize: '0.85rem' }}>
                  Transit Status: <b>{dispatch.dispatch_status}</b>
                  {dispatch.dispatched_at && (
                    <div className="muted-text" style={{ fontSize: '0.75rem', marginTop: '4px' }}>
                      Dispatched: {new Date(dispatch.dispatched_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            ) : recommendations.length > 0 ? (
              <div className="matches" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {recommendations.map((m: any, idx: number) => (
                  <div className={`match-row ${idx === 0 ? 'best' : ''}`} key={m.destination_id} style={{ margin: 0 }}>
                    <div className="match-rank">{idx + 1}</div>
                    <div className="match-copy">
                      <b>
                        {m.destination_name} {idx === 0 && <span className="recommended-label">Best Match</span>}
                      </b>
                      <span>
                        <MapPin size={13} /> {m.destination_address} · {m.distance_km.toFixed(1)} km
                      </span>
                    </div>
                    <strong>{(m.total_score).toFixed(0)}%</strong>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', border: '1px dashed var(--gold-border)', borderRadius: '12px' }}>
                <small className="muted-text">
                  {batch.batch_status === 'DETECTED'
                    ? 'Run Shelf-Life prediction first to assess freshness parameters.'
                    : 'Run recommendations analysis to compute routes.'}
                </small>
              </div>
            )}
          </div>
        </section>
      </div>
    </>
  )
}
