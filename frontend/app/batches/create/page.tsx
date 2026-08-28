'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, Check, CloudUpload, Sparkles, Loader2, X, Plus, Trash2, Image as ImageIcon } from 'lucide-react'
import PageIntro from '../../../components/common/PageIntro'
import { apiRequest } from '../../../lib/apiClient'
import { API_CONFIG } from '../../../config/api.config'

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function CreateBatchPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [name, setName] = useState('')
  const [block, setBlock] = useState('North Block')
  const [date, setDate] = useState('2024-07-18')
  const [notes, setNotes] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [filePreviews, setFilePreviews] = useState<{ file: File; url: string; id: string }[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const previews = files.map(file => ({
      file,
      url: URL.createObjectURL(file),
      id: `${file.name}-${file.size}-${file.lastModified}`
    }))
    setFilePreviews(previews)

    return () => {
      previews.forEach(p => URL.revokeObjectURL(p.url))
    }
  }, [files])

  const handleDropzoneClick = () => {
    fileInputRef.current?.click()
  }

  const addFiles = (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles).filter(f => f.type.startsWith('image/'))
    if (fileArray.length === 0) return

    setFiles(prev => {
      const existingKeys = new Set(prev.map(f => `${f.name}-${f.size}`))
      const uniqueNew = fileArray.filter(f => !existingKeys.has(`${f.name}-${f.size}`))
      return [...prev, ...uniqueNew]
    })
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(e.target.files)
      e.target.value = ''
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files) {
      addFiles(e.dataTransfer.files)
    }
  }

  const removeFile = (idToRemove: string) => {
    setFiles(prev => prev.filter(f => `${f.name}-${f.size}-${f.lastModified}` !== idToRemove))
  }

  const clearAllFiles = () => {
    setFiles([])
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
      
      // Append every selected image file to FormData
      files.forEach((file) => {
        formData.append('files', file)
      })

      const res = await apiRequest(API_CONFIG.ENDPOINTS.UPLOAD, {
        method: 'POST',
        body: formData,
      })

      const newBatchId = res?.batch_id || res?.id || res?.batch?.batch_id || cleanBatchId
      if (newBatchId) {
        router.push(`/batches/${newBatchId}`)
      } else {
        router.push('/batches')
      }
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
                Uploading {files.length} image{files.length > 1 ? 's' : ''} & analyzing...
              </>
            ) : (
              <>
                Create batch <ArrowUpRight size={16} />
              </>
            )}
          </button>
        </section>

        <section className="panel upload-panel">
          <div className="panel-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3>Batch imagery</h3>
              <p>Upload multiple images for accurate detection.</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className="image-count" style={{ fontWeight: 700, background: 'var(--gold-bg)', padding: '4px 10px', borderRadius: '12px', fontSize: '0.85rem' }}>
                {files.length} {files.length === 1 ? 'image' : 'images'} selected
              </span>
              {files.length > 0 && !loading && (
                <button
                  type="button"
                  onClick={clearAllFiles}
                  style={{ background: 'none', border: 'none', color: '#eb5e28', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Trash2 size={14} /> Clear all
                </button>
              )}
            </div>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
          />

          <div
            className={`dropzone ${files.length > 0 ? 'uploaded' : ''}`}
            onClick={handleDropzoneClick}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              cursor: loading ? 'not-allowed' : 'pointer',
              border: isDragging ? '2px dashed var(--gold)' : undefined,
              backgroundColor: isDragging ? 'rgba(217, 119, 6, 0.05)' : undefined
            }}
          >
            <div className="upload-icon">
              {files.length > 0 ? <Check size={21} /> : <CloudUpload size={21} />}
            </div>
            <b>{files.length > 0 ? 'Add more images or drop files here' : 'Drop images here or browse'}</b>
            <span>JPG, PNG, WEBP — Select multiple files at once</span>
          </div>

          {/* Interactive Image Previews Grid */}
          {filePreviews.length > 0 && (
            <div style={{ marginTop: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <b style={{ fontSize: '0.85rem', color: 'var(--navy)' }}>Selected files preview ({filePreviews.length})</b>
                <button
                  type="button"
                  onClick={handleDropzoneClick}
                  className="secondary-button"
                  disabled={loading}
                  style={{ padding: '4px 10px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Plus size={14} /> Add more
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.75rem', maxHeight: '320px', overflowY: 'auto', paddingRight: '4px' }}>
                {filePreviews.map(({ file, url, id }) => (
                  <div
                    key={id}
                    style={{
                      position: 'relative',
                      borderRadius: '10px',
                      border: '1px solid var(--gold-border)',
                      overflow: 'hidden',
                      background: 'var(--cream)',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    <div style={{ position: 'relative', width: '100%', height: '100px', background: '#fff' }}>
                      <img
                        src={url}
                        alt={file.name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      {!loading && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            removeFile(id)
                          }}
                          style={{
                            position: 'absolute',
                            top: '6px',
                            right: '6px',
                            background: 'rgba(0, 0, 0, 0.65)',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '50%',
                            width: '24px',
                            height: '24px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            transition: 'background 0.2s'
                          }}
                          title="Remove image"
                        >
                          <X size={14} />
                        </button>
                      )}
                    </div>
                    <div style={{ padding: '6px 8px', fontSize: '0.75rem', background: 'var(--panel-bg)' }}>
                      <p style={{ fontWeight: 600, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--navy)' }} title={file.name}>
                        {file.name}
                      </p>
                      <span className="muted-text" style={{ fontSize: '0.7rem' }}>
                        {formatFileSize(file.size)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="upload-tip" style={{ marginTop: '1rem' }}>
            <Sparkles size={15} />
            <span>Select multiple clear images from different angles for best YOLO count accuracy.</span>
          </div>
        </section>
      </form>
    </>
  )
}

