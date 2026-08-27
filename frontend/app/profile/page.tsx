'use client'

import React, { useEffect, useState } from 'react'
import { Apple } from 'lucide-react'
import PageIntro from '../../components/common/PageIntro'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true)
        const data = await apiRequest(API_CONFIG.ENDPOINTS.ME)
        setProfile(data)
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve profile.')
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '60vh', alignItems: 'center', justifyContent: 'center', color: 'var(--navy)' }}>
        <div style={{ textAlign: 'center' }}>
          <Apple size={48} className="scan-line" style={{ animation: 'bounce 1s infinite', color: 'var(--gold)', margin: '0 auto 1rem' }} />
          <b>Loading profile settings...</b>
        </div>
      </div>
    )
  }

  const initials = profile?.name
    ? profile.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'JD'

  const formattedDate = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
      })
    : 'March 2024'

  return (
    <>
      <PageIntro
        eyebrow="Workspace settings"
        title="Your profile"
        description="Manage your account and orchard workspace preferences."
      />

      {error && (
        <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {profile && (
        <section className="panel profile-panel">
          <div className="profile-head">
            <div className="profile-avatar">{initials}</div>
            <div>
              <h2>{profile.name}</h2>
              <p>{profile.role === 'USER' ? 'Farm manager' : profile.role} · Hawthorne Orchards</p>
            </div>
            <button className="secondary-button" type="button">Edit profile</button>
          </div>
          <div className="profile-fields">
            <div>
              <small>Email address</small>
              <b>{profile.email}</b>
            </div>
            <div>
              <small>Location</small>
              <b>{profile.address ? `${profile.address}, ${profile.city}, ${profile.state}` : 'Hood River, Oregon'}</b>
            </div>
            <div>
              <small>Member since</small>
              <b>{formattedDate}</b>
            </div>
          </div>
        </section>
      )}
    </>
  )
}
