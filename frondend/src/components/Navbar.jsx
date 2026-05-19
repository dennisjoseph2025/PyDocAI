import { Link, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth'

export default function Navbar() {
  const { isAuthenticated, logout, user } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <nav id="navbar" className="sticky top-0 z-50 border-b border-border/0 hover:border-border bg-bg-primary/80 backdrop-blur-xl transition-all duration-300">
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <Link to="/" className="font-display font-bold text-xl flex items-center gap-0.5">
          <span className="text-ink-primary">Py</span>
          <span className="text-accent">Doc</span>
          <span className="text-ink-primary">AI</span>
        </Link>

        {/* Nav Links */}
        <div className="hidden md:flex items-center gap-6">
          <Link
            to={isAuthenticated ? "/dashboard" : "/"}
            className={`text-sm transition-colors ${isActive('/') || isActive('/dashboard') ? 'text-ink-primary' : 'text-ink-secondary hover:text-ink-primary'}`}
          >
            Home
          </Link>
          {isAuthenticated && (
            <>
              <Link
                to="/input"
                className={`text-sm transition-colors ${isActive('/input') ? 'text-ink-primary' : 'text-ink-secondary hover:text-ink-primary'}`}
              >
                Generate
              </Link>
              <Link
                to="/profile"
                className={`text-sm transition-colors ${isActive('/profile') ? 'text-ink-primary' : 'text-ink-secondary hover:text-ink-primary'}`}
              >
                Profile
              </Link>
            </>
          )}
        </div>

        {/* CTA Buttons */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <span className="text-sm text-ink-secondary hidden sm:block">
                {user?.name || user?.full_name || user?.email}
              </span>
              <button onClick={logout} className="btn-ghost text-sm !px-4 !py-2">
                Log Out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost text-sm !px-4 !py-2">
                Log In
              </Link>
              <Link to="/register" className="btn-accent text-sm !px-4 !py-2">
                Get Started →
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
