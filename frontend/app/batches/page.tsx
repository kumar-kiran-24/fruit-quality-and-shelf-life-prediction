'use client'

import React, { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import {
  Apple, ArrowUpRight, ChevronDown, Filter, Package, Plus, Search
} from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import Status from '../../components/common/Status'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

export default function BatchesPage() {
  const [batches, setBatches] = useState<any[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true)
        const data = await apiRequest(API_CONFIG.ENDPOINTS.BATCHES)
        setBatches(data.batches || [])
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve batches.')
      } finally {
        setLoading(false)
      }
    }
    fetchBatches()
  }, [])

  const filteredBatches = useMemo(() => {
    return batches.filter((b) =>
      `${b.batch_id} ${b.fruit} ${b.origin} ${b.batch_status}`.toLowerCase().includes(query.toLowerCase())
    )
  }, [batches, query])

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading batches directory...</b>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="panel" style={{ padding: '3rem', textAlign: 'center', border: '1px solid rgba(235,94,40,0.2)' }}>
        <h3 style={{ color: '#eb5e28', marginBottom: '1rem' }}>Data Fetch Error</h3>
        <p className="muted-text" style={{ marginBottom: '2rem' }}>{error}</p>
        <button onClick={() => window.location.reload()} className="secondary-button" style={{ display: 'inline-flex' }}>
          Retry connection
        </button>
      </div>
    )
  }

  return (
    <>
      <PageIntro
        eyebrow="Operations"
        title="Your batches"
        description="Track every harvest from orchard to destination."
        action={
          <Link href="/batches/create" className="primary-button">
            <Plus size={17} />Create batch
          </Link>
        }
      />

      <div className="toolbar">
        <div className="search-box">
          <Search size={17} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search batches..."
          />
        </div>
        <button className="filter-button">
          <Filter size={16} />Filter
        </button>
        <button className="filter-button">
          All statuses <ChevronDown size={15} />
        </button>
      </div>

      <div className="panel table-panel">
        <div className="table-head">
          <span>Batch</span>
          <span>Created</span>
          <span>Volume</span>
          <span>Shelf life</span>
          <span>Status</span>
          <span />
        </div>
        {filteredBatches.map((b) => {
          const formattedName = `${b.fruit.charAt(0).toUpperCase() + b.fruit.slice(1)} · ${b.origin}`
          const formattedDate = new Date(b.created_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
          })

          return (
            <Link href={`/batches/${b.batch_id}`} className="table-row" key={b.batch_id}>
              <div className="batch-main">
                <b>{formattedName}</b>
                <span>{b.batch_id}</span>
              </div>
              <span>{formattedDate}</span>
              <span>
                {b.number_of_images} images · {b.total_apples_detected} apples
              </span>
              <span>{b.shelf_life_prediction || 'N/A'}</span>
              <Status>{b.batch_status}</Status>
              <ArrowUpRight size={16} />
            </Link>
          )
        })}
        {filteredBatches.length === 0 && (
          <div className="empty-state">
            <Package size={28} />
            <b>No batches found</b>
            <p>Try a different search term.</p>
          </div>
        )}
      </div>
    </>
  )
}
