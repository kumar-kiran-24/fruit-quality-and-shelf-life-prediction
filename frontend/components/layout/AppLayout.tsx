'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Apple, Bell, ChevronDown, CircleHelp, Clock3, Ellipsis,
  LayoutDashboard, Leaf, Menu, Package, Plus, Settings2, Sparkles, Sprout, Users, X
} from 'lucide-react'
import { apiRequest } from '../../lib/apiClient'
import { API_CONFIG } from '../../config/api.config'

const nav = [
  ['Overview', LayoutDashboard, '/dashboard'],
  ['Batches', Package, '/batches'],
  ['Create Batch', Plus, '/batches/create'],
  ['Detection', Sparkles, '/detection'],
  ['Shelf Life', Clock3, '/shelf-life'],
  ['Recommendations', Sprout, '/recommendations'],
  ['Buyers', Users, '/buyers'],
  ['Profile', Settings2, '/profile'],
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [mobileNav, setMobileNav] = useState(false)
  const [user, setUser] = useState<{ name: string; role: string; email: string } | null>(null)

  useEffect(() => {
    if (pathname === '/login') return

    const token = localStorage.getItem('orchard_token')
    if (!token) {
      router.push('/login')
      return
    }

    const storedUser = localStorage.getItem('orchard_user')
    if (storedUser) {
      setUser(JSON.parse(storedUser))
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
        localStorage.removeItem('orchard_token')
        localStorage.removeItem('orchard_user')
        router.push('/login')
      }
    }

    syncProfile()
  }, [pathname, router])

  // Skip rendering navigation layout for the login screen
  if (pathname === '/login') {
    return <>{children}</>
  }

  // Map route pathname to active navigation label
  const getActiveLabel = (path: string): string => {
    if (path === '/dashboard') return 'Overview'
    if (path === '/batches/create') return 'Create Batch'
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
    if (pathname === '/dashboard') {
      return <b>Overview</b>
    }
    if (pathname === '/batches/create') {
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
    if (pathname === '/batches') {
      return <b>Batches</b>
    }
    if (pathname === '/detection') {
      return <b>Detection</b>
    }
    if (pathname === '/shelf-life') {
      return <b>Shelf Life</b>
    }
    if (pathname === '/recommendations') {
      return <b>Recommendations</b>
    }
    if (pathname === '/buyers') {
      return <b>Buyers</b>
    }
    if (pathname === '/profile') {
      return <b>Profile</b>
    }
    return <b>Overview</b>
  }

  const handleLogout = () => {
    localStorage.removeItem('orchard_token')
    localStorage.removeItem('orchard_user')
    router.push('/login')
  }

  const userInitials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'JD'

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Apple size={19} fill="currentColor" />
          </div>
          <span>
            orchard<span>OS</span>
          </span>
          <button className="mobile-close" onClick={() => setMobileNav(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>
        <div className="workspace">
          <div className="workspace-avatar">HN</div>
          <div>
            <b>Hawthorne Orchards</b>
            <small>Operations workspace</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <nav>
          <p className="nav-label">Workspace</p>
          {nav.map(([label, Icon, path]) => (
            <Link
              key={label as string}
              href={path as string}
              onClick={() => setMobileNav(false)}
              className={activeLabel === label ? 'nav-item active' : 'nav-item'}
            >
              <Icon size={17} />
              <span>{label as string}</span>
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
          <div className="user-chip" onClick={handleLogout} style={{ cursor: 'pointer' }} title="Click to log out">
            <div className="user-avatar">{userInitials}</div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <b style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', display: 'block' }}>
                {user?.name || 'Jamie Davis'}
              </b>
              <small>{user?.role === 'USER' ? 'Farm manager' : user?.role || 'Farm manager'}</small>
            </div>
            <Ellipsis size={17} />
          </div>
        </div>
      </aside>
      {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open navigation">
            <Menu size={21} />
          </button>
          <div className="crumb">
            <span>Workspace</span>
            <span>/</span>
            {renderBreadcrumbs()}
          </div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Notifications">
              <Bell size={18} />
              <i />
            </button>
            <div className="top-avatar">{userInitials}</div>
          </div>
        </header>
        <div className="page-wrap">{children}</div>
      </main>
    </div>
  )
}
