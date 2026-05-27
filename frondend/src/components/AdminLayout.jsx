import { Link, useLocation } from 'react-router-dom'
import Navbar from './Navbar'
import { IconChartIncreasing, IconUsers, IconBook } from './Icons'

const NAV_ITEMS = [
  { path: '/admin/stats',    label: 'Dashboard', icon: IconChartIncreasing },
  { path: '/admin/feedback', label: 'Feedback',   icon: IconBook },
  { path: '/admin/users',    label: 'Users',      icon: IconUsers },
]

export default function AdminLayout({ children }) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-bg-primary">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-8 flex gap-8">
        <aside className="w-56 flex-shrink-0">
          <nav className="glass-card p-2 space-y-1 sticky top-24">
            {NAV_ITEMS.map(item => {
              const active = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    active
                      ? 'bg-accent text-white shadow-glow'
                      : 'text-ink-secondary hover:text-ink-primary hover:bg-bg-surface'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </Link>
              )
            })}
            <div className="pt-2 mt-2 border-t border-border">
              <Link
                to="/dashboard"
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-ink-secondary hover:text-ink-primary hover:bg-bg-surface transition-all duration-200"
              >
                ← Back to App
              </Link>
            </div>
          </nav>
        </aside>
        <main className="flex-1 min-w-0">
          {children}
        </main>
      </div>
    </div>
  )
}
