'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { CheckCircle2, AlertCircle } from 'lucide-react'
import { authService } from '../../services/authService'

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [streetAddress, setStreetAddress] = useState('')
  const [pincode, setPincode] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const formatErrorMessage = (err: any): string => {
    if (!err) return 'An unexpected error occurred. Please try again.'
    const raw = err.message || String(err)
    const lower = raw.toLowerCase()
    if (lower.includes('already exists') || lower.includes('registered') || raw.includes('409') || raw.includes('400')) {
      if (lower.includes('email')) {
        return 'An account with this email address already exists. Please sign in instead.'
      }
    }
    if (raw.includes('422') || lower.includes('validation')) {
      return 'Please check that all fields are filled out correctly.'
    }
    if (raw.includes('500') || lower.includes('server')) {
      return 'Unable to process registration at this time. Please try again later.'
    }
    return raw
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    // Client-side validations
    if (!name.trim() || name.trim().length < 2) {
      setError('Please enter your full name (at least 2 characters).')
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!email.trim() || !emailRegex.test(email.trim())) {
      setError('Please enter a valid email address.')
      return
    }

    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please check your password.')
      return
    }

    if (!streetAddress.trim()) {
      setError('Please enter your street address.')
      return
    }

    if (!pincode.trim() || pincode.trim().length < 3) {
      setError('Please enter a valid PIN / Postal Code.')
      return
    }

    setLoading(true)

    try {
      await authService.registerUser({
        name: name.trim(),
        email: email.trim(),
        password,
        address: streetAddress.trim(),
        pincode: pincode.trim(),
      })

      setSuccess('Account created successfully! Redirecting to login...')
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } catch (err: any) {
      setError(formatErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--cream)', padding: '2rem 1rem' }}>
      <form onSubmit={handleRegister} className="panel" style={{ width: '100%', maxWidth: '460px', padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}>
        <div style={{ textAlign: 'center', marginBottom: '0.75rem' }}>
          <img
            src="/major-project.png"
            alt="Application Logo"
            style={{ height: '52px', maxWidth: '240px', objectFit: 'contain', margin: '0 auto 0.75rem', display: 'block' }}
          />
          <h2 style={{ color: 'var(--navy)', fontWeight: 800, fontSize: '1.4rem', margin: '0.25rem 0' }}>Create an Account</h2>
          <p className="muted-text" style={{ fontSize: '0.9rem' }}>Sign up to manage your fruit operations</p>
        </div>

        {error && (
          <div style={{ color: '#eb5e28', background: 'rgba(235, 94, 40, 0.1)', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{ color: '#2b9348', background: 'rgba(43, 147, 72, 0.1)', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
            <span>{success}</span>
          </div>
        )}

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.85rem' }}>
          Full Name *
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Jamie Davis"
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

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.85rem' }}>
          Email Address *
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

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.85rem' }}>
            Password *
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

          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.85rem' }}>
            Confirm Password *
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
        </div>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.85rem' }}>
          Street Address *
          <input
            type="text"
            value={streetAddress}
            onChange={(e) => setStreetAddress(e.target.value)}
            placeholder="e.g. 123 Farm Road"
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

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontWeight: 600, color: 'var(--navy)', fontSize: '0.85rem' }}>
          PIN / Postal Code *
          <input
            type="text"
            value={pincode}
            onChange={(e) => setPincode(e.target.value)}
            placeholder="e.g. 97031 or 560001"
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
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>

        <div style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--navy-muted)', marginTop: '0.5rem' }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: 'var(--navy)', fontWeight: 700, textDecoration: 'underline' }}>
            Sign in
          </Link>
        </div>
      </form>
    </div>
  )
}
