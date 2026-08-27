'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { Apple, ArrowUpRight, ChevronDown, MapPin, Sparkles, Loader2 } from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

export default function RecommendationsPage() {
  const [batches, setBatches] = useState<any[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState('')
  const [recommendation, setRecommendation] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [recLoading, setRecLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchBatches = async () => {
    try {
      setLoading(true)
      const data = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)
      const list = data.batches || []
      setBatches(list)
      if (list.length > 0) {
        setSelectedBatchId(list[0].batch_id)
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
    return batches.find((b) => b.batch_id === selectedBatchId)
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

  const matches = recommendation?.recommendations || []
  const explanation = recommendation?.optimization_summary || 'Analysis recommends nearby grocers for immediate stock placement.'

  return (
    <>
      <PageIntro
        eyebrow="Smart routing"
        title="Recommendations"
        description="Find the right destination for every batch, before freshness becomes urgency."
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

      <div className="recommend-layout">
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
                    cursor: 'pointer'
                  }}
                  disabled={recLoading}
                >
                  {batches.map((b) => (
                    <option key={b.batch_id} value={b.batch_id}>
                      {b.batch_id} — {b.fruit}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={12}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    pointerEvents: 'none',
                    color: 'var(--navy)'
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
                <b>{selectedBatch.fruit.charAt(0).toUpperCase() + selectedBatch.fruit.slice(1)} · {selectedBatch.origin}</b>
                <span>
                  {selectedBatch.total_apples_detected} apples · {selectedBatch.shelf_life_prediction || 'N/A'} shelf life
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
        </section>

        <section className="panel matches">
          <div className="panel-heading">
            <div>
              <h3>Best matches</h3>
              <p>Ranked by freshness, distance, and buyer demand.</p>
            </div>
          </div>
          {recLoading ? (
            <div style={{ display: 'flex', minHeight: '150px', alignItems: 'center', justifyContent: 'center' }}>
              <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--gold)' }} />
            </div>
          ) : matches.length > 0 ? (
            matches.map((m: any, idx: number) => (
              <div className={`match-row ${idx === 0 ? 'best' : ''}`} key={m.destination_id}>
                <div className="match-rank">{idx + 1}</div>
                <div className="match-copy">
                  <b>
                    {m.destination_name}{' '}
                    {idx === 0 && <span className="recommended-label">Recommended</span>}
                  </b>
                  <span>
                    <MapPin size={13} />
                    {m.destination_address} · {m.distance_km.toFixed(1)} km
                  </span>
                </div>
                <strong>{(m.total_score).toFixed(0)}%</strong>
                <ArrowUpRight size={16} />
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem' }} className="muted-text">
              No routing recommendations found. Make sure the batch status is processed.
            </div>
          )}
        </section>
      </div>
    </>
  )
}
