'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Bell, ChevronDown, CircleHelp, Leaf, LogOut, Menu, X
} from 'lucide-react'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'
import { authService } from '../../services/authService'

const nav = [
  ['Overview', '/dashboard'],
  ['Batches', '/batches'],
  ['Create Batch', '/batches/create'],
  ['Detection', '/detection'],
  ['Shelf Life', '/shelf-life'],
  ['Recommendations', '/recommendations'],
  ['Buyers', '/buyers'],
  ['Profile', '/profile'],
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [mobileNav, setMobileNav] = useState(false)
  const [user, setUser] = useState<{ name: string; role: string; email: string } | null>(null)

  const isPublicRoute = pathname === '/login' || pathname === '/register'

  useEffect(() => {
    if (isPublicRoute) return

    const token = authService.getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }

    const storedUser = authService.getStoredUser()
    if (storedUser) {
      setUser(storedUser as any)
    }

    // Sync profile from backend
    const syncProfile = async () => {
      try {
        const profile = await apiRequest(API_CONFIG.ENDPOINTS.ME)
        const updatedUser = {
          id: profile.user_id,
          name: profile.name,
          email: profile.email,
          role: profile.role
        }
        setUser(updatedUser)
        localStorage.setItem('orchard_user', JSON.stringify(updatedUser))
      } catch (err) {
        // Clear tokens on auth failure (like expired JWT)
        authService.logoutUser()
        router.push('/login')
      }
    }

    syncProfile()
  }, [pathname, router, isPublicRoute])

  // Skip rendering navigation layout for public screens (login & register)
  if (isPublicRoute) {
    return <>{children}</>
  }

  // Map route pathname to active navigation label
  const getActiveLabel = (path: string): string => {
    if (path === '/dashboard') return 'Overview'
    if (path === '/batches/create' || path === '/create-batch') return 'Create Batch'
    if (path.startsWith('/batches')) return 'Batches'
    if (path === '/detection') return 'Detection'
    if (path === '/shelf-life') return 'Shelf Life'
    if (path === '/recommendations') return 'Recommendations'
    if (path === '/buyers') return 'Buyers'
    if (path === '/profile') return 'Profile'
    return 'Overview'
  }

  const activeLabel = getActiveLabel(pathname || '/dashboard')

  // Generate dynamic breadcrumb hierarchy
  const renderBreadcrumbs = () => {
    if (pathname === '/dashboard') return <b>Overview</b>
    if (pathname === '/batches/create' || pathname === '/create-batch') {
      return (
        <>
          <span>Batches</span>
          <span>/</span>
          <b>Create Batch</b>
        </>
      )
    }
    if (pathname && pathname.match(/^\/batches\/[^/]+$/)) {
      const parts = pathname.split('/')
      const batchId = parts[2]
      return (
        <>
          <span>Batches</span>
          <span>/</span>
          <b>{batchId}</b>
        </>
      )
    }
    if (pathname === '/batches') return <b>Batches</b>
    if (pathname === '/detection') return <b>Detection</b>
    if (pathname === '/shelf-life') return <b>Shelf Life</b>
    if (pathname === '/recommendations') return <b>Recommendations</b>
    if (pathname === '/buyers') return <b>Buyers</b>
    if (pathname === '/profile') return <b>Profile</b>
    return <b>Overview</b>
  }

  const handleLogout = () => {
    authService.logoutUser()
    router.push('/login')
  }

  const userInitials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'JD'

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <div className="brand" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 8px 24px' }}>
          <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', textDecoration: 'none', background: '#ffffff', padding: '6px 14px', borderRadius: '12px', boxShadow: '0 4px 14px rgba(0, 0, 0, 0.2)' }}>
            <img
              src="/major-project.png"
              alt="Application Logo"
              style={{ height: '36px', maxWidth: '170px', objectFit: 'contain', display: 'block' }}
            />
          </Link>
          <button className="mobile-close" onClick={() => setMobileNav(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>
        <div className="workspace">
          <div className="workspace-avatar" style={{ background: '#ffffff', padding: '2px', overflow: 'hidden' }}>
            <img src="/major-project.png" alt="Major Project Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          </div>
          <div>
            <b>Hawthorne Orchards</b>
            <small>Operations workspace</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <nav>
          <p className="nav-label">Workspace</p>
          {nav.map(([label, path]) => (
            <Link
              key={label}
              href={path}
              onClick={() => setMobileNav(false)}
              className={activeLabel === label ? 'nav-item active' : 'nav-item'}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                fontSize: '0.85rem',
                fontWeight: activeLabel === label ? 700 : 500,
                letterSpacing: '0.01em',
                borderRadius: '8px',
                transition: 'all 0.15s ease-in-out',
                color: activeLabel === label ? '#fffdf8' : '#a9bec0',
                background: activeLabel === label ? '#294e5d' : 'transparent',
                boxShadow: activeLabel === label ? 'inset 3px 0 var(--gold)' : 'none',
              }}
            >
              <span>{label}</span>
              {label === 'Recommendations' && <i>3</i>}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="season-card">
            <div className="season-top">
              <Leaf size={15} />
              <span>Harvest season</span>
            </div>
            <b>78% complete</b>
            <div className="progress">
              <span style={{ width: '78%' }} />
            </div>
            <small>32 days remaining</small>
          </div>
          <button className="help-link">
            <CircleHelp size={16} />
            Help center
          </button>
          <div className="user-chip" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, overflow: 'hidden' }}>
              <div className="user-avatar">{userInitials}</div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <b style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', display: 'block' }}>
                  {user?.name || 'Jamie Davis'}
                </b>
                <small>{user?.role === 'USER' ? 'Farm manager' : user?.role || 'Farm manager'}</small>
              </div>
            </div>
            <button
              onClick={handleLogout}
              style={{ background: 'none', border: 'none', color: 'var(--navy-muted)', padding: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
              title="Log Out"
              aria-label="Log Out"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open navigation">
            <Menu size={21} />
          </button>
          <div className="crumb" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img
              src="/major-project.png"
              alt="Major Project Icon"
              style={{ height: '22px', width: 'auto', objectFit: 'contain', background: '#ffffff', padding: '2px 6px', borderRadius: '6px', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}
            />
            <span>Workspace</span>
            <span>/</span>
            {renderBreadcrumbs()}
          </div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Notifications">
              <Bell size={18} />
              <i />
            </button>
            <div
              className="top-avatar"
              onClick={handleLogout}
              style={{ cursor: 'pointer' }}
              title="Click to Log Out"
            >
              {userInitials}
            </div>
          </div>
        </header>
        <div className="page-wrap">{children}</div>
      </main>
    </div>
  )
}

