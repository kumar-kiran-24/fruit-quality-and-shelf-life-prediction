'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Apple } from 'lucide-react'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const data = await apiRequest(API_CONFIG.ENDPOINTS.LOGIN, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })

      // Store JWT token and user info
      localStorage.setItem('orchard_token', data.access_token)
      localStorage.setItem('orchard_user', JSON.stringify({
        id: data.user_id,
        name: data.name,
        email: data.email,
        role: data.role
      }))

      // Redirect to dashboard overview
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--cream)', padding: '1rem' }}>
      <form onSubmit={handleLogin} className="panel" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}>
        <div style={{ textAlign: 'center', marginBottom: '0.5rem' }}>
          <div className="brand-mark" style={{ display: 'inline-flex', marginBottom: '0.75rem', padding: '10px', background: 'var(--navy)', color: 'var(--gold)', borderRadius: '12px' }}>
            <Apple size={24} fill="currentColor" />
          </div>
          <h2 style={{ color: 'var(--navy)', fontWeight: 800, fontSize: '1.5rem', margin: '0.25rem 0' }}>Welcome to orchardOS</h2>
          <p className="muted-text" style={{ fontSize: '0.9rem' }}>Sign in to manage your harvests</p>
        </div>

        {error && (
          <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.85rem', textAlign: 'center', fontWeight: 600 }}>
            {error}
          </div>
        )}

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.9rem' }}>
          Email Address
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="e.g. farmer@test.com"
            style={{
              padding: '0.75rem',
              borderRadius: '8px',
              border: '1px solid var(--gold-border)',
              background: 'var(--cream)',
              color: 'var(--navy)',
              fontSize: '0.95rem'
            }}
            required
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.9rem' }}>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            style={{
              padding: '0.75rem',
              borderRadius: '8px',
              border: '1px solid var(--gold-border)',
              background: 'var(--cream)',
              color: 'var(--navy)',
              fontSize: '0.95rem'
            }}
            required
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="primary-button"
          style={{
            justifyContent: 'center',
            height: '44px',
            marginTop: '0.5rem',
            fontWeight: 700
          }}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>

        <div style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--navy-muted)', marginTop: '0.5rem' }}>
          Test credentials: <b>farmer@test.com</b> / <b>pass123</b>
        </div>
      </form>
    </div>
  )
}
