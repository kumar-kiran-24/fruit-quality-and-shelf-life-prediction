'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { Apple } from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import Status from '../../components/common/Status'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

export default function ShelfLifePage() {
  const [batches, setBatches] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true)
        const data = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)
        setBatches(data.batches || [])
      } catch (err: any) {
        setError(err.message || 'Failed to load shelf life data.')
      } finally {
        setLoading(false)
      }
    }
    fetchBatches()
  }, [])

  const activeBatches = useMemo(() => {
    return batches.filter((b) => b.batch_status !== 'DISPATCHED' && b.batch_status !== 'COMPLETED' && b.batch_status !== 'DELIVERED')
  }, [batches])

  const averageShelfLife = useMemo(() => {
    const predictedBatches = activeBatches.filter(b => b.shelf_life_prediction && b.shelf_life_prediction !== 'N/A')
    if (predictedBatches.length === 0) return '0'
    const totalDays = predictedBatches.reduce((sum, b) => {
      // Extract first number or middle number from label like "5-10 days" or "10-14 days"
      const match = b.shelf_life_prediction.match(/(\d+)/)
      const days = match ? parseInt(match[1]) : 7
      return sum + days
    }, 0)
    return (totalDays / predictedBatches.length).toFixed(1)
  }, [activeBatches])

  const averageQuality = useMemo(() => {
    if (activeBatches.length === 0) return 0
    const totalScore = activeBatches.reduce((sum, b) => sum + (b.freshness_confidence ? Math.round(b.freshness_confidence * 100) : 75), 0)
    return Math.round(totalScore / activeBatches.length)
  }, [activeBatches])

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Calculating freshness models...</b>
        </div>
      </div>
    )
  }

  return (
    <>
      <PageIntro
        eyebrow="Freshness intelligence"
        title="Shelf life"
        description="Predictive insights to help you move every batch at its best."
      />

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      <div className="shelf-hero">
        <div>
          <div className="eyebrow gold-text">Average across active harvests</div>
          <strong>
            {averageShelfLife} <small>days (min)</small>
          </strong>
          <p>
            Healthy freshness outlook · <b>{activeBatches.length} active</b> batches tracked
          </p>
        </div>
        <div className="freshness-ring">
          <div>
            <b>{averageQuality}</b>
            <span>quality</span>
          </div>
        </div>
      </div>

      <div className="shelf-grid">
        {activeBatches.map((b) => {
          const formattedName = `${b.fruit.charAt(0).toUpperCase() + b.fruit.slice(1)} · ${b.origin}`
          const score = b.freshness_confidence ? Math.round(b.freshness_confidence * 100) : 75
          
          return (
            <div className="panel shelf-card" key={b.batch_id}>
              <div className="shelf-card-top">
                <div className="batch-thumb">
                  <Apple size={19} />
                </div>
                <Status>{b.batch_status}</Status>
              </div>
              <h3>{formattedName}</h3>
              <div className="days">
                <b>{b.shelf_life_prediction || 'PENDING'}</b>
                <span>predicted span</span>
              </div>
              <div className="shelf-bar">
                <span style={{ width: `${score}%` }} />
              </div>
              <small>Quality score {score}/100</small>
            </div>
          )
        })}
        {activeBatches.length === 0 && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }} className="panel muted-text">
            No active batches. Go to Create Batch to upload files.
          </div>
        )}
      </div>
    </>
  )
}
