import { Link, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth'

export default function Navbar() {
  const { isAuthenticated, logout, user } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

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
              <>
                <Link
                  to="/input"
                  className={`text-sm px-3 py-1.5 rounded-md transition-colors font-medium ${isActive('/input') ? 'bg-bg-elevated text-ink-primary' : 'text-ink-secondary hover:bg-bg-primary hover:text-ink-primary'}`}
                >
                  Generate
                </Link>
              </>
            )}
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
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