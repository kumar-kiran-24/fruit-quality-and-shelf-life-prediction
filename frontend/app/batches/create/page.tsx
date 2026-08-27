'use client'

import React, { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, Check, CloudUpload, Sparkles, Loader2 } from 'lucide-react'
import PageIntro from '../../../components/common/PageIntro'
import { apiRequest } from '../../../lib/apiClient'
import { API_CONFIG } from '../../../config/api.config'

export default function CreateBatchPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [name, setName] = useState('')
  const [block, setBlock] = useState('North Block')
  const [date, setDate] = useState('2024-07-18')
  const [notes, setNotes] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleDropzoneClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (files.length === 0) {
      setError('Please select at least one apple image file for YOLO detection.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const cleanBatchId = name.trim().toUpperCase().replace(/\s+/g, '-')
      
      const formData = new FormData()
      formData.append('batch_id', cleanBatchId)
      formData.append('origin', block)
      formData.append('current_address', block)
      
      files.forEach((file) => {
        formData.append('files', file)
      })

      await apiRequest(API_CONFIG.ENDPOINTS.UPLOAD, {
        method: 'POST',
        body: formData,
      })

      router.push('/batches')
    } catch (err: any) {
      setError(err.message || 'Failed to submit batch upload.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageIntro
        eyebrow="New batch"
        title="Create a batch"
        description="Add your harvest details and imagery to begin analysis."
        action={
          <button
            className="secondary-button"
            type="button"
            onClick={() => router.push('/batches')}
            disabled={loading}
          >
            Cancel
          </button>
        }
      />

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 600 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="create-layout">
        <section className="panel form-panel">
          <div className="panel-heading">
            <div>
              <h3>Batch information</h3>
              <p>Tell us a little about this harvest.</p>
            </div>
          </div>
          
          <label>
            Batch ID / Name
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. BATCH-2408-01"
              disabled={loading}
              required
            />
          </label>
          
          <div className="form-row">
            <label>
              Orchard block
              <select
                value={block}
                onChange={(e) => setBlock(e.target.value)}
                disabled={loading}
              >
                <option value="North Block">North Block</option>
                <option value="East Orchard">East Orchard</option>
                <option value="Ridge 4">Ridge 4</option>
              </select>
            </label>
            <label>
              Harvest date
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                disabled={loading}
                required
              />
            </label>
          </div>
          
          <label>
            Notes
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this harvest..."
              disabled={loading}
            />
          </label>

          <button type="submit" className="primary-button" disabled={loading} style={{ gap: '8px' }}>
            {loading ? (
              <>
                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                Processing YOLO model...
              </>
            ) : (
              <>
                Create batch <ArrowUpRight size={16} />
              </>
            )}
          </button>
        </section>

        <section className="panel upload-panel">
          <div className="panel-heading">
            <div>
              <h3>Batch imagery</h3>
              <p>Upload multiple images for accurate detection.</p>
            </div>
            <span className="image-count">{files.length} selected</span>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
          />

          <button
            type="button"
            className={`dropzone ${files.length > 0 ? 'uploaded' : ''}`}
            onClick={handleDropzoneClick}
            disabled={loading}
          >
            <div className="upload-icon">
              {files.length > 0 ? <Check size={21} /> : <CloudUpload size={21} />}
            </div>
            <b>{files.length > 0 ? 'Images loaded successfully' : 'Drop images here or browse'}</b>
            <span>
              {files.length > 0
                ? files.map((f) => f.name).join(' · ').slice(0, 80) + (files.length > 3 ? '...' : '')
                : 'PNG, JPG up to 10MB each'}
            </span>
          </button>
          
          <div className="upload-tip">
            <Sparkles size={15} />
            <span>For best results, include clear photos from different angles.</span>
          </div>
        </section>
      </form>
    </>
  )
}
