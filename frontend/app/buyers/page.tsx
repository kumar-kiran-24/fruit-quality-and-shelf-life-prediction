'use client'

import React, { useEffect, useState } from 'react'
import { Ellipsis, MapPin, Plus, Apple } from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

export default function BuyersPage() {
  const [buyers, setBuyers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBuyers = async () => {
      try {
        setLoading(true)
        const data = await apiRequest(API_CONFIG.ENDPOINTS.DESTINATIONS)
        setBuyers(data || [])
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve buyers.')
      } finally {
        setLoading(false)
      }
    }
    fetchBuyers()
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading buyers network...</b>
        </div>
      </div>
    )
  }

  return (
    <>
      <PageIntro
        eyebrow="Your network"
        title="Buyers"
        description="Manage destinations and see who is ready for your harvest."
        action={
          <button className="primary-button" type="button">
            <Plus size={17} />Add buyer
          </button>
        }
      />

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      <div className="buyer-grid">
        {buyers.map((buyer) => {
          const avatar = buyer.name
            .split(' ')
            .map((x: string) => x[0])
            .join('')
            .slice(0, 2)

          return (
            <section className="panel buyer-card" key={buyer.destination_id}>
              <div className="buyer-head">
                <div className="buyer-avatar">{avatar}</div>
                <button className="more-button" type="button">
                  <Ellipsis size={17} />
                </button>
              </div>
              <h3>{buyer.name}</h3>
              <span className="location">
                <MapPin size={14} />
                {buyer.address}
              </span>
              <div className="buyer-foot">
                <span>{buyer.destination_type}</span>
                <b>Cap: {buyer.available_capacity_kg.toLocaleString()} kg</b>
              </div>
            </section>
          )
        })}
        {buyers.length === 0 && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }} className="panel muted-text">
            No active buyer destinations registered.
          </div>
        )}
      </div>
    </>
  )
}
