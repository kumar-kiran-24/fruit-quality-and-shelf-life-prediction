'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { Apple, Check, Download, FileText, Sparkles, ChevronDown } from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import Metric from '../../components/common/Metric'
import Status from '../../components/common/Status'
import Sparkline from '../../components/common/Sparkline'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'
import { safeFixed } from '../../lib/utils'

export default function DetectionPage() {
  const [batches, setBatches] = useState<any[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true)
        const data = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)
        const list = Array.isArray(data) ? data : (data.batches || data.items || [])
        setBatches(list)
        if (list.length > 0) {
          setSelectedBatchId(list[0].batch_id || list[0].id)
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch batches.')
      } finally {
        setLoading(false)
      }
    }
    fetchBatches()
  }, [])

  const selectedBatch = useMemo(() => {
    return batches.find(b => b.batch_id === selectedBatchId) || batches[0]
  }, [batches, selectedBatchId])

  const totalApplesDetected = useMemo(() => {
    return batches.reduce((sum, b) => sum + (b.total_apples_detected || 0), 0).toLocaleString()
  }, [batches])

  const totalImagesAnalyzed = useMemo(() => {
    return batches.reduce((sum, b) => sum + (b.number_of_images || 0), 0)
  }, [batches])

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading computer vision telemetry...</b>
        </div>
      </div>
    )
  }

  return (
    <>
      <PageIntro
        eyebrow="Computer vision"
        title="Detection results"
        description="Review apple counts and image quality across your batches."
        action={
          <button className="secondary-button" type="button">
            <Download size={16} />Export report
          </button>
        }
      />

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      <div className="metric-grid compact">
        <Metric label="Total detected" value={totalApplesDetected} change={`Across ${batches.length} batches`} icon={Apple} />
        <Metric label="Avg. confidence" value="94.6%" change="Excellent image quality" icon={Sparkles} />
        <Metric label="Images analyzed" value={String(totalImagesAnalyzed)} change="Cumulative processing count" icon={FileText} />
      </div>

      <section className="panel results-panel">
        <div className="panel-heading">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h3>Image analysis</h3>
            {batches.length > 0 && (
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <select
                  value={selectedBatchId}
                  onChange={(e) => setSelectedBatchId(e.target.value)}
                  style={{
                    appearance: 'none',
                    background: 'var(--cream)',
                    border: '1px solid var(--gold-border)',
                    padding: '4px 28px 4px 12px',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: 'var(--navy)',
                    cursor: 'pointer'
                  }}
                >
                  {batches.map(b => (
                    <option key={b.batch_id} value={b.batch_id}>{b.batch_id} — {b.fruit}</option>
                  ))}
                </select>
                <ChevronDown size={12} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--navy)' }} />
              </div>
            )}
          </div>
          {selectedBatch && <Status>{selectedBatch.batch_status}</Status>}
        </div>

        {selectedBatch ? (
          <div className="detection-preview">
            <div className="orchard-placeholder">
              <Apple size={44} />
              <span>Detection preview</span>
              <small>{selectedBatch.total_apples_detected || 0} apples identified</small>
              <div className="scan-line" />
            </div>
            <div className="detection-stats">
              <div>
                <small>Apples detected</small>
                <b>{selectedBatch.total_apples_detected || 0}</b>
                <Sparkline values={[20, 35, 28, 45, 42, 59, 54]} gold />
              </div>
              <div>
                <small>Confidence score</small>
                <b>{selectedBatch.freshness_confidence !== null && selectedBatch.freshness_confidence !== undefined ? `${safeFixed(selectedBatch.freshness_confidence * 100, 1)}%` : 'PENDING'}</b>
                <div className="confidence">
                  <span style={{ width: selectedBatch.freshness_confidence ? `${selectedBatch.freshness_confidence * 100}%` : '0%' }} />
                </div>
              </div>
              <div>
                <small>Images processed</small>
                <b>{selectedBatch.number_of_images} / {selectedBatch.number_of_images}</b>
                <span className="success-text">
                  <Check size={14} />Complete
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem' }} className="muted-text">
            No active batches to analyze. Visit Create Batch to upload images.
          </div>
        )}
      </section>
    </>
  )
}
