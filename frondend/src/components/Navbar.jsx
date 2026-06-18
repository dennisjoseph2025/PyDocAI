import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import { getUnreadCount, getNotifications, markNotificationRead, deleteNotification, clearAllNotifications } from '../api'
import { MODES } from '../config/themes'

export default function Navbar() {
  const { isAuthenticated, logout, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [notifOpen, setNotifOpen] = useState(false)
  const [genOpen, setGenOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [notifs, setNotifs] = useState([])
  const notifRef = useRef(null)
  const genRef = useRef(null)

  const isActive = (path) => location.pathname === path

  const fetchUnread = useCallback(async () => {
    try {
      const res = await getUnreadCount()
      setUnread(res.data.unread_count)
    } catch { }
  }, [])

  const openDropdown = async () => {
    setNotifOpen(true)
    try {
      const res = await getNotifications({ limit: 10 })
      setNotifs(res.data)
    } catch { }
  }

  useEffect(() => {
    if (!isAuthenticated) return
    fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => clearInterval(interval)
  }, [isAuthenticated, fetchUnread])

  useEffect(() => {
    const handleClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false)
      }
      if (genRef.current && !genRef.current.contains(e.target)) {
        setGenOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleNotifClick = async (n) => {
    if (!n.is_read) {
      try { await markNotificationRead(n.id) } catch { }
      setUnread((u) => Math.max(0, u - 1))
    }
    setNotifOpen(false)
    if (n.project_slug && n.comment?.id) {
      navigate(`/public/${n.project_slug}#comment-${n.comment.id}`)
    } else if (n.comment?.project) {
      navigate(`/output/${n.comment.project}`)
    }
  }

  const handleDeleteNotif = async (e, id) => {
    e.stopPropagation()
    try {
      await deleteNotification(id)
      setNotifs((prev) => prev.filter((n) => n.id !== id))
      setUnread((u) => Math.max(0, u - 1))
    } catch { }
  }

  const handleClearAll = async () => {
    try {
      await clearAllNotifications()
      setNotifs([])
      setUnread(0)
    } catch { }
  }

  return (
    <nav id="navbar" className="sticky top-0 z-50 bg-bg-surface border-b border-border shadow-sm">
      <div className="max-w-[1400px] mx-auto px-6 flex items-center justify-between h-14">

        <div className="flex items-center gap-8">
          {/* Logo */}
          <Link to="/" className="font-display font-bold text-xl flex items-center gap-0.5 tracking-tight">
            <span className="text-accent-blue">Py</span>
            <span className="text-accent">Doc</span>
            <span className="text-ink-primary">AI</span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            <Link
              to={isAuthenticated ? "/dashboard" : "/"}
              className={`text-sm px-3 py-1.5 rounded-md transition-colors font-medium ${isActive('/') || isActive('/dashboard') ? 'bg-bg-elevated text-ink-primary' : 'text-ink-secondary hover:bg-bg-primary hover:text-ink-primary'}`}
            >
              Dashboard
            </Link>
            {isAuthenticated && (
              <div className="relative" ref={genRef}>
                <button
                  onClick={() => setGenOpen((g) => !g)}
                  className={`text-sm px-3 py-1.5 rounded-md transition-colors font-medium flex items-center gap-1.5 ${genOpen ? 'bg-bg-elevated text-ink-primary' : 'text-ink-secondary hover:bg-bg-primary hover:text-ink-primary'}`}
                >
                  Generate
                  <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${genOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Slide-down menu */}
                <div
                  className={`absolute left-0 mt-2 w-72 overflow-hidden transition-all duration-300 ease-out origin-top ${genOpen ? 'opacity-100 scale-y-100 max-h-96' : 'opacity-0 scale-y-0 max-h-0 pointer-events-none'}`}
                >
                  <div className="bg-bg-surface border border-border rounded-xl shadow-xl p-2 space-y-1">
                    {Object.values(MODES).map((m) => {
                      const Icon = m.icon
                      return (
                        <Link
                          key={m.id}
                          to={`/input/${m.id}`}
                          onClick={() => setGenOpen(false)}
                          className={`group flex items-start gap-3 rounded-lg p-3 transition-all duration-200 hover:bg-bg-elevated ${m.border} hover:border`}
                        >
                          <div className={`w-10 h-10 rounded-lg ${m.accentBgSoft} ${m.border} flex items-center justify-center ${m.accent} shrink-0`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div className="min-w-0">
                            <div className="text-sm font-display font-bold text-ink-primary">{m.label}</div>
                            <div className="text-[10px] font-mono text-ink-muted uppercase tracking-wider mt-0.5">{m.tagline}</div>
                            <p className="text-xs text-ink-secondary/80 mt-1 leading-relaxed">{m.desc}</p>
                          </div>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}
            <Link
              to="/published"
              className={`text-sm px-3 py-1.5 rounded-md transition-colors font-medium ${isActive('/published') ? 'bg-bg-elevated text-ink-primary' : 'text-ink-secondary hover:bg-bg-primary hover:text-ink-primary'}`}
            >
              Published
            </Link>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              {/* Notification Bell */}
              <div className="relative" ref={notifRef}>
                <button
                  onClick={notifOpen ? () => setNotifOpen(false) : openDropdown}
                  className="relative p-1.5 rounded-md text-ink-muted hover:text-ink-primary hover:bg-bg-primary transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {unread > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-danger text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                      {unread > 9 ? '9+' : unread}
                    </span>
                  )}
                </button>
                {notifOpen && (
                  <div className="absolute right-0 mt-2 w-80 bg-bg-surface border border-border rounded-xl shadow-lg overflow-hidden">
                    {notifs.length > 0 && (
                      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
                        <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest">
                          Notifications
                        </span>
                        <button
                          onClick={handleClearAll}
                          className="text-[10px] font-mono text-ink-muted hover:text-danger transition-colors"
                        >
                          Clear all
                        </button>
                      </div>
                    )}
                    <div className="max-h-80 overflow-y-auto">
                      {notifs.length === 0 ? (
                        <p className="text-sm text-ink-muted text-center py-6">No notifications</p>
                      ) : (
                        notifs.map((n) => (
                          <button
                            key={n.id}
                            onClick={() => handleNotifClick(n)}
                            className={`w-full text-left px-4 py-3 text-sm border-b border-border last:border-0 hover:bg-bg-primary transition-colors group ${!n.is_read ? 'bg-accent-blue/5' : ''}`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0 flex-1">
                                <p className={`${!n.is_read ? 'font-medium text-ink-primary' : 'text-ink-secondary'}`}>
                                  {n.message}
                                </p>
                                <p className="text-xs text-ink-muted mt-0.5">
                                  {new Date(n.created_at).toLocaleDateString()}
                                </p>
                              </div>
                              <button
                                onClick={(e) => handleDeleteNotif(e, n.id)}
                                className="shrink-0 text-ink-muted hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity p-0.5"
                                title="Delete"
                              >
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

              <Link to="/profile" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                 <div className="w-7 h-7 rounded-md bg-accent-blue/20 border border-accent-blue/50 flex items-center justify-center text-accent-blue font-bold text-xs">
                    {(user?.name || user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                 </div>
                 <span className="text-sm font-mono text-ink-secondary hidden sm:block">
                   {user?.username || user?.name || user?.email}
                 </span>
              </Link>
              <div className="w-px h-5 bg-border mx-1"></div>
              <button onClick={logout} className="text-sm font-mono text-ink-muted hover:text-danger transition-colors">
                [Logout]
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-mono text-ink-secondary hover:text-ink-primary transition-colors">
                [Login]
              </Link>
              <Link to="/register" className="btn-accent text-sm !px-4 !py-1.5">
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
