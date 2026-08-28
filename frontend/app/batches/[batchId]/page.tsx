'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Apple, ArrowLeft, ArrowUpRight, Check, FileText, Loader2, Maximize2, X, ChevronLeft, ChevronRight, RefreshCw, AlertTriangle, MapPin, Sparkles
} from 'lucide-react'
import PageIntro from '../../../components/common/PageIntro'
import Status from '../../../components/common/Status'
import Sparkline from '../../../components/common/Sparkline'
import { apiRequest } from '../../../lib/apiClient'
import { API_CONFIG } from '../../../config/api.config'
import { safeFixed, safeNumber, getImageUrl } from '../../../lib/utils'

export default function BatchDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const batchId = params?.batchId as string

  const [data, setData] = useState<any>(null)
  const [validTransitions, setValidTransitions] = useState<string[]>([])
  const [selectedBuyerId, setSelectedBuyerId] = useState('')
  const [selectedImageIdx, setSelectedImageIdx] = useState(0)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')
  // AI Report state
  const [aiReport, setAiReport] = useState<any>(null)
  const [aiReportLoading, setAiReportLoading] = useState(false)
  const [aiReportError, setAiReportError] = useState('')

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

  // AI Report generation
  const handleGenerateAiReport = async (forceRegenerate = false) => {
    try {
      setAiReportLoading(true)
      setAiReportError('')
      const report = await apiRequest(API_CONFIG.ENDPOINTS.AI_REPORT(batchId), {
        method: 'POST',
      })
      setAiReport(report)
    } catch (err: any) {
      setAiReportError(err.message || 'Failed to generate AI report.')
    } finally {
      setAiReportLoading(false)
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

  // Check if existing AI report data is available on the batch itself
  const hasExistingReport = !!(batch.ai_summary && batch.recommended_action && batch.quality_status && batch.quality_status !== 'PENDING')
  const images = batch.images || []
  const selectedImage = images[selectedImageIdx]

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
      </div>          {error && (
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
              <small>Total apples detected</small>
              <b style={{ color: 'var(--navy)', fontSize: '1.4rem' }}>{batch.total_apples_detected || 0}</b>
            </div>
            <div>
              <small>Freshness status</small>
              <b style={{ color: batch.freshness_prediction === 'fresh' ? '#2d6a4f' : 'inherit' }}>
                {batch.freshness_prediction || 'PENDING'}
              </b>
            </div>
            <div>
              <small>Images processed</small>
              <b>{batch.number_of_images || images.length || 0} images</b>
            </div>
          </div>

          {/* Interactive Batch Image Gallery */}
          <div className="detection-preview" style={{ marginBottom: '1.5rem' }}>
            {(() => {
              const imageUrl = getImageUrl(selectedImage)
              const isAnnotated = selectedImage?.is_annotated || selectedImage?.url?.includes('annotated') || selectedImage?.filename?.includes('annotated')
              
              if (imageUrl) {
                return (
                  <div>
                    {/* Featured Image Display */}
                    <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', background: '#0f172a', border: '1px solid var(--gold-border)', marginBottom: '1rem' }}>
                      <img
                        src={imageUrl}
                        alt={selectedImage?.filename || `Batch image ${selectedImageIdx + 1}`}
                        style={{ width: '100%', height: '360px', objectFit: 'contain', display: 'block', background: '#0f172a' }}
                        onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
                      />
                      
                      {/* Image Type Badge */}
                      <div style={{ position: 'absolute', top: '12px', left: '12px', display: 'flex', gap: '6px' }}>
                        <span style={{ background: isAnnotated ? '#2d6a4f' : 'rgba(15, 23, 42, 0.75)', color: '#fff', padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700, backdropFilter: 'blur(4px)' }}>
                          {isAnnotated ? 'Annotated YOLO Result' : 'Original Upload'}
                        </span>
                        <span style={{ background: 'rgba(15, 23, 42, 0.75)', color: 'var(--gold)', padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700, backdropFilter: 'blur(4px)' }}>
                          Image {selectedImageIdx + 1} of {images.length}
                        </span>
                      </div>

                      {/* Expand Button */}
                      <button
                        onClick={() => setIsModalOpen(true)}
                        style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(15, 23, 42, 0.75)', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600, backdropFilter: 'blur(4px)' }}
                        title="Open Fullscreen Lightbox"
                      >
                        <Maximize2 size={14} /> Fullscreen
                      </button>

                      {/* Bottom Info Bar */}
                      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '0.6rem 0.85rem', background: 'linear-gradient(180deg, transparent, rgba(15, 23, 42, 0.9))', color: 'white', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {selectedImage?.filename || `Image ${selectedImageIdx + 1}`}
                        </span>
                        <b>{batch.total_apples_detected || 0} total apples counted</b>
                      </div>
                    </div>

                    {/* Responsive Gallery Grid */}
                    {images.length > 1 && (
                      <div>
                        <b style={{ fontSize: '0.85rem', color: 'var(--navy)', display: 'block', marginBottom: '0.5rem' }}>
                          Batch Gallery ({images.length} images uploaded)
                        </b>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: '0.5rem' }}>
                          {images.map((img: any, idx: number) => {
                            const thumbUrl = getImageUrl(img)
                            if (!thumbUrl) return null
                            const isSelected = idx === selectedImageIdx
                            return (
                              <div
                                key={img.id || idx}
                                onClick={() => setSelectedImageIdx(idx)}
                                style={{
                                  position: 'relative',
                                  height: '80px',
                                  borderRadius: '8px',
                                  overflow: 'hidden',
                                  cursor: 'pointer',
                                  border: isSelected ? '2px solid var(--gold)' : '1px solid var(--gold-border)',
                                  boxShadow: isSelected ? '0 0 0 2px rgba(217, 119, 6, 0.3)' : 'none',
                                  background: '#fff'
                                }}
                              >
                                <img
                                  src={thumbUrl}
                                  alt={`Thumb ${idx + 1}`}
                                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'rgba(0,0,0,0.6)', color: '#fff', fontSize: '0.65rem', textAlign: 'center', padding: '2px' }}>
                                  #{idx + 1}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )
              } else {
                return (
                  <div className="orchard-placeholder">
                    <Apple size={44} />
                    <span>Detection preview</span>
                    <small>{batch.total_apples_detected || 0} apples identified</small>
                    <div className="scan-line" />
                  </div>
                )
              }
            })()}

            <div className="detection-stats" style={{ marginTop: '1rem' }}>
              <div>
                <small>Confidence rating</small>
                <b>{batch.freshness_confidence !== null && batch.freshness_confidence !== undefined ? `${safeFixed(batch.freshness_confidence * 100, 1)}%` : 'PENDING'}</b>
                <div className="confidence">
                  <span style={{ width: `${safeNumber(batch.freshness_confidence) * 100}%` }} />
                </div>
              </div>
              <div>
                <small>Confidence trace</small>
                <Sparkline values={[20, 35, 28, 45, 42, 59, 54]} gold />
              </div>
            </div>
          </div>

          {/* AI Batch Report Section */}
          <div style={{ marginTop: '1.5rem' }}>
            <div className="panel-heading" style={{ padding: 0, marginBottom: '1rem' }}>
              <div>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={18} /> AI Batch Report
                </h3>
                <p>LLM-generated quality assessment and logistics analysis.</p>
              </div>
            </div>

            {aiReportLoading ? (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '2.5rem',
                background: 'rgba(0,0,0,0.02)',
                borderRadius: '12px',
                border: '1px dashed var(--gold-border)',
                flexDirection: 'column',
                gap: '1rem'
              }}>
                <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--gold)' }} />
                <b style={{ fontSize: '0.9rem', color: 'var(--navy)' }}>Generating AI analysis report...</b>
                <small className="muted-text">This may take a few moments while the LLM processes batch data.</small>
              </div>
            ) : aiReportError ? (
              <div style={{
                padding: '1.5rem',
                background: 'rgba(235, 94, 40, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(235, 94, 40, 0.2)',
                textAlign: 'center'
              }}>
                <AlertTriangle size={24} style={{ color: '#eb5e28', margin: '0 auto 0.75rem' }} />
                <p style={{ color: '#eb5e28', fontSize: '0.9rem', fontWeight: 600, margin: '0 0 0.75rem' }}>{aiReportError}</p>
                <button className="secondary-button" onClick={() => handleGenerateAiReport()} style={{ display: 'inline-flex' }}>
                  <RefreshCw size={14} /> Retry
                </button>
              </div>
            ) : (aiReport || (hasExistingReport && batch.ai_summary)) ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Report Content */}
                <div style={{
                  background: 'var(--cream)',
                  border: '1px solid var(--gold-border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem'
                }}>
                  {/* Quality Status & Risk Level */}
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: '120px' }}>
                      <small style={{ color: 'var(--muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>Quality Status</small>
                      <b style={{ display: 'block', fontSize: '1.1rem', color: 'var(--navy)', marginTop: '4px' }}>
                        {(aiReport?.quality_status || batch.quality_status) || 'N/A'}
                      </b>
                    </div>
                    <div style={{ flex: 1, minWidth: '120px' }}>
                      <small style={{ color: 'var(--muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>Risk Level</small>
                      <b style={{ display: 'block', fontSize: '1.1rem', color: 'var(--navy)', marginTop: '4px' }}>
                        {(aiReport?.risk_level || batch.risk_level) || 'N/A'}
                      </b>
                    </div>
                    {aiReport?.generated_at && (
                      <div style={{ flex: 1, minWidth: '120px' }}>
                        <small style={{ color: 'var(--muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>Generated</small>
                        <b style={{ display: 'block', fontSize: '0.9rem', color: 'var(--navy)', marginTop: '4px' }}>
                          {new Date(aiReport.generated_at).toLocaleString()}
                        </b>
                      </div>
                    )}
                  </div>

                  <hr style={{ border: 'none', borderTop: '1px solid var(--gold-border)', margin: '0.25rem 0' }} />

                  {/* AI Summary */}
                  <div>
                    <small style={{ color: 'var(--muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>AI Summary</small>
                    <p style={{
                      fontSize: '0.9rem',
                      color: 'var(--navy)',
                      lineHeight: '1.6',
                      marginTop: '6px',
                      background: 'rgba(0,0,0,0.02)',
                      padding: '1rem',
                      borderRadius: '8px'
                    }}>
                      {(aiReport?.ai_summary || batch.ai_summary) || 'No summary available.'}
                    </p>
                  </div>

                  {/* Recommended Action */}
                  {(aiReport?.recommended_action || batch.recommended_action) && (
                    <div>
                      <small style={{ color: 'var(--muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>Recommended Action</small>
                      <p style={{
                        fontSize: '0.9rem',
                        color: 'var(--navy)',
                        fontWeight: 600,
                        lineHeight: '1.5',
                        marginTop: '6px',
                        padding: '0.75rem 1rem',
                        background: 'var(--gold-soft)',
                        borderRadius: '8px',
                        border: '1px solid var(--gold-border)'
                      }}>
                        {aiReport?.recommended_action || batch.recommended_action}
                      </p>
                    </div>
                  )}
                </div>

                {/* Regenerate button */}
                <button
                  className="secondary-button"
                  onClick={() => handleGenerateAiReport(true)}
                  style={{ display: 'inline-flex', alignSelf: 'flex-start', gap: '6px' }}
                  disabled={aiReportLoading}
                >
                  <RefreshCw size={14} /> Regenerate Report
                </button>
              </div>
            ) : (
              /* No report yet — show Generate button */
              <div style={{
                textAlign: 'center',
                padding: '2.5rem',
                border: '1px dashed var(--gold-border)',
                borderRadius: '12px',
                background: 'rgba(0,0,0,0.01)'
              }}>
                <FileText size={32} style={{ color: 'var(--gold)', margin: '0 auto 0.75rem', opacity: 0.7 }} />
                <b style={{ display: 'block', fontSize: '0.95rem', color: 'var(--navy)', marginBottom: '0.5rem' }}>No AI report generated yet</b>
                <p className="muted-text" style={{ marginBottom: '1.25rem', maxWidth: '360px', margin: '0 auto 1.25rem' }}>
                  Generate an LLM-powered quality assessment including freshness analysis, risk evaluation, and logistics recommendations.
                </p>
                <button
                  className="primary-button"
                  onClick={() => handleGenerateAiReport()}
                  style={{ display: 'inline-flex' }}
                >
                  <FileText size={15} /> Generate AI Report
                </button>
              </div>
            )}
          </div>
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
                  {batch.shelf_life_prediction && batch.shelf_life_prediction !== 'N/A' ? batch.shelf_life_prediction : 'Pending'}
                </strong>
              </div>
              <div className="shelf-bar" style={{ height: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <span style={{ display: 'block', height: '100%', width: batch.shelf_life_prediction && batch.shelf_life_prediction !== 'N/A' ? '70%' : '0%', background: 'var(--gold)' }} />
              </div>
              <small className="muted-text">
                Confidence: {batch.shelf_life_confidence !== null && batch.shelf_life_confidence !== undefined ? `${safeFixed(batch.shelf_life_confidence * 100, 1)}%` : 'N/A'} · Risk: {batch.risk_level || 'Normal'}
              </small>
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
                        {r.destination_name} (Score: {safeFixed(r.total_score ?? r.score, 1)})
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
                    <small className="muted-text">{dispatch.destination_address} · {dispatch.distance_km ? `${safeFixed(dispatch.distance_km, 1)} km` : 'N/A'}</small>
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
                  <div className={`match-row ${idx === 0 ? 'best' : ''}`} key={m.destination_id || idx} style={{ margin: 0 }}>
                    <div className="match-rank">{idx + 1}</div>
                    <div className="match-copy">
                      <b>
                        {m.destination_name} {idx === 0 && <span className="recommended-label">Best Match</span>}
                      </b>
                      <span>
                        <MapPin size={13} /> {m.destination_address} · {safeFixed(m.distance_km ?? m.distance, 1)} km
                      </span>
                    </div>
                    <strong>{safeFixed(m.total_score ?? m.score, 0)}%</strong>
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

      {/* Fullscreen Image Lightbox Modal */}
      {isModalOpen && selectedImage && (
        <div
          onClick={() => setIsModalOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem'
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'relative',
              maxWidth: '1100px',
              width: '100%',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              background: '#0f172a',
              borderRadius: '16px',
              overflow: 'hidden',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            {/* Modal Header */}
            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#fff' }}>
              <div>
                <b style={{ fontSize: '1rem', display: 'block' }}>
                  {selectedImage?.filename || `Batch Image ${selectedImageIdx + 1}`}
                </b>
                <span style={{ fontSize: '0.8rem', color: 'var(--gold)' }}>
                  Image {selectedImageIdx + 1} of {images.length} · {batch.total_apples_detected || 0} total apples identified
                </span>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                style={{ background: 'rgba(255, 255, 255, 0.1)', border: 'none', color: '#fff', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Image Viewport */}
            <div style={{ position: 'relative', flex: 1, minHeight: '380px', maxHeight: '70vh', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src={getImageUrl(selectedImage) || ''}
                alt={selectedImage?.filename || 'Batch detail preview'}
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
              />

              {images.length > 1 && (
                <>
                  <button
                    onClick={() => setSelectedImageIdx(prev => (prev > 0 ? prev - 1 : images.length - 1))}
                    style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.6)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '50%', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
                  >
                    <ChevronLeft size={24} />
                  </button>
                  <button
                    onClick={() => setSelectedImageIdx(prev => (prev < images.length - 1 ? prev + 1 : 0))}
                    style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.6)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '50%', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
                  >
                    <ChevronRight size={24} />
                  </button>
                </>
              )}
            </div>

            {/* Modal Footer Thumbnails */}
            {images.length > 1 && (
              <div style={{ padding: '0.75rem 1.25rem', background: '#090d16', display: 'flex', gap: '0.5rem', overflowX: 'auto' }}>
                {images.map((img: any, idx: number) => {
                  const thumb = getImageUrl(img)
                  if (!thumb) return null
                  const isSelected = idx === selectedImageIdx
                  return (
                    <img
                      key={img.id || idx}
                      src={thumb}
                      alt={`thumb ${idx + 1}`}
                      onClick={() => setSelectedImageIdx(idx)}
                      style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '6px', cursor: 'pointer', border: isSelected ? '2px solid var(--gold)' : '1px solid transparent', opacity: isSelected ? 1 : 0.6 }}
                    />
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

