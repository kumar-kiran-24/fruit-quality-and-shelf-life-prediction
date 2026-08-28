'use client'

import React, { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import {
  Apple, ArrowUpRight, ChevronDown, Clock3, Filter, Package, Plus, Search, SortAsc
} from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import Status from '../../components/common/Status'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

// ============================================================
// FEFO SHELF-LIFE PARSING
// (Same thresholds as dashboard — centralized for easy replacement)
// ============================================================

const SHELF_LIFE_DAYS_MAP: Record<string, number> = {
  '1-5 days': 3,
  '5-10 days': 7,
  '10-14 days': 12,
}

function parseRemainingDays(label: string | null | undefined): number | null {
  if (!label || typeof label !== 'string') return null
  if (SHELF_LIFE_DAYS_MAP[label] !== undefined) return SHELF_LIFE_DAYS_MAP[label]
  const match = label.match(/(\d+)/)
  if (match) return parseInt(match[1], 10)
  return null
}

type SortMode = 'newest' | 'fefo'

export default function BatchesPage() {
  const [batches, setBatches] = useState<any[]>([])
  const [query, setQuery] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('fefo')
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

  const filteredAndSortedBatches = useMemo(() => {
    const filtered = batches.filter((b) =>
      `${b.batch_id} ${b.fruit} ${b.origin} ${b.batch_status}`.toLowerCase().includes(query.toLowerCase())
    )

    if (sortMode === 'fefo') {
      // Separate analyzed batches (with shelf-life) from pending ones
      const analyzed: { batch: any; days: number }[] = []
      const pending: { batch: any }[] = []

      for (const batch of filtered) {
        const days = parseRemainingDays(batch.shelf_life_prediction)
        if (days !== null && batch.shelf_life_prediction && batch.shelf_life_prediction !== 'N/A') {
          analyzed.push({ batch, days })
        } else {
          pending.push({ batch })
        }
      }

      // Sort analyzed batches: shortest remaining shelf life first
      analyzed.sort((a, b) => a.days - b.days)

      return [
        ...analyzed.map(a => a.batch),
        ...pending.map(p => p.batch),
      ]
    }

    // Default: newest first
    return [...filtered].sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime()
      const dateB = new Date(b.created_at || 0).getTime()
      return dateB - dateA
    })
  }, [batches, query, sortMode])

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
        {/* Sort by FEFO / Newest toggle */}
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <button
            className="filter-button"
            onClick={() => setSortMode(prev => prev === 'fefo' ? 'newest' : 'fefo')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <SortAsc size={15} />
            {sortMode === 'fefo' ? 'FEFO order' : 'Newest first'}
            <ChevronDown size={14} />
          </button>
        </div>
      </div>

      {/* FEFO legend */}
      {sortMode === 'fefo' && (
        <div style={{
          display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem',
          fontSize: '0.75rem', color: 'var(--muted)', flexWrap: 'wrap',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock3 size={13} /> Sorted by remaining shelf life (shortest first)
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#b91c1c', display: 'inline-block' }} />
            URGENT
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#c2410c', display: 'inline-block' }} />
            HIGH
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#92400e', display: 'inline-block' }} />
            MEDIUM
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#166534', display: 'inline-block' }} />
            NORMAL
          </span>
        </div>
      )}

      <div className="panel table-panel">
        <div className="table-head">
          <span>Batch</span>
          <span>Created</span>
          <span>Volume</span>
          <span>Shelf life</span>
          <span>Status</span>
          <span />
        </div>
        {filteredAndSortedBatches.map((b) => {
          const formattedName = `${b.fruit.charAt(0).toUpperCase() + b.fruit.slice(1)} · ${b.origin}`
          const formattedDate = new Date(b.created_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
          })
          const days = parseRemainingDays(b.shelf_life_prediction)
          const hasShelfLife = days !== null && b.shelf_life_prediction && b.shelf_life_prediction !== 'N/A'

          return (
            <Link href={`/batches/${b.batch_id}`} className="table-row" key={b.batch_id}>
              <div className="batch-main">
                <b>{formattedName}</b>
                <span>{b.batch_id}</span>
              </div>
              <span>{formattedDate}</span>
              <span>
                {b.number_of_images || 0} images · {b.total_apples_detected || 0} apples
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {hasShelfLife ? (
                  <>
                    <span style={{
                      display: 'inline-block', width: '7px', height: '7px', borderRadius: '50%',
                      background: days! <= 4 ? '#b91c1c' : days! <= 7 ? '#c2410c' : days! <= 12 ? '#92400e' : '#166534',
                    }} />
                    {b.shelf_life_prediction}
                  </>
                ) : (
                  <span style={{ color: 'var(--muted)', fontStyle: 'italic' }}>Awaiting prediction</span>
                )}
              </span>
              <Status>{b.batch_status}</Status>
              <ArrowUpRight size={16} />
            </Link>
          )
        })}
        {filteredAndSortedBatches.length === 0 && (
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
