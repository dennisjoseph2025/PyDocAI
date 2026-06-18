import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getAdminStats, adminGetUserProjects } from '../api'
import useAuth from '../hooks/useAuth'
import AdminLayout from '../components/AdminLayout'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  IconUser, IconUsers, IconGlobe, IconBook, IconClock, IconGithub,
  IconDatabase, IconCheck, IconWarning, IconBolt, IconRefresh,
  IconFile, IconCalendar, IconChartIncreasing, IconSearch
} from '../components/Icons'

export default function AdminProjects() {
  const { user, isLoading, addToast } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const [selectedUser, setSelectedUser] = useState(null)
  const [userProjects, setUserProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(false)

  useEffect(() => {
    if (isLoading) return
    if (!user || !(user.role === 'admin' || user.is_staff)) {
      navigate('/', { replace: true })
      return
    }
    fetchStats()
  }, [user, isLoading, navigate])

  const fetchStats = async () => {
    setLoading(true)
    try {
      const res = await getAdminStats()
      setStats(res.data)
    } catch {
      addToast('Failed to load stats', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectUser = async (u) => {
    setSelectedUser(u)
    setProjectsLoading(true)
    setUserProjects([])
    try {
      const res = await adminGetUserProjects(u.id)
      setUserProjects(res.data?.results ?? (Array.isArray(res.data) ? res.data : []))
    } catch {
      addToast('Failed to load user projects', 'error')
    } finally {
      setProjectsLoading(false)
    }
  }

  if (isLoading) return <AdminLayout><div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div></AdminLayout>
  if (!user || !(user.role === 'admin' || user.is_staff)) return null

  const formatDate = (d) => d ? new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : ''

  return (
    <AdminLayout>
      <Helmet>
        <title>Dashboard — PyDocAI</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>

      {selectedUser ? (
        <>
          <div className="mb-6">
            <button
              onClick={() => { setSelectedUser(null); setUserProjects([]) }}
              className="flex items-center gap-1 text-sm text-ink-muted hover:text-ink-primary transition-colors mb-4"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg> Back to dashboard
            </button>
            <h1 className="text-3xl font-display font-bold text-ink-primary">
              {selectedUser.name || selectedUser.email}
            </h1>
            <p className="text-ink-secondary mt-1">
              Published projects ({userProjects.length} of {selectedUser.published_count})
            </p>
          </div>

          {projectsLoading ? (
            <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div>
          ) : userProjects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <IconGlobe className="w-16 h-16 text-ink-muted/20 mb-4" />
              <h3 className="text-xl font-bold text-ink-primary mb-2">No published projects</h3>
              <p className="text-ink-secondary text-center max-w-md">This user hasn't published any projects yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {userProjects.map((p) => (
                <div key={p.id} className="glass-card p-5 hover:border-accent/50 transition-border duration-300">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-display font-bold text-xl text-ink-primary mb-1 truncate">
                        {p.name || 'Untitled'}
                      </h3>
                      <p className="text-sm text-ink-secondary line-clamp-2">
                        {p.description || 'No description'}
                      </p>
                    </div>
                    <Link
                      to={`/public/${p.public_slug}`}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 border border-accent/20 text-accent hover:bg-accent/20 text-xs font-mono transition-colors shrink-0 ml-4"
                    >
                      <IconGlobe className="w-3.5 h-3.5" /> View
                    </Link>
                  </div>
                  <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border text-xs text-ink-muted">
                    <span className="flex items-center gap-1">
                      <IconBook className="w-3.5 h-3.5" /> {p.file_count || 0} files
                    </span>
                    <span className="flex items-center gap-1">
                      <IconClock className="w-3.5 h-3.5" /> {formatDate(p.updated_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-display font-bold text-ink-primary">Dashboard</h1>
              <p className="text-ink-secondary mt-1">Platform overview and statistics</p>
            </div>
            <button onClick={() => { fetchStats() }} className="btn-ghost text-sm !px-4 !py-2 flex items-center gap-2">
              <IconRefresh className="w-4 h-4" /> Refresh
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div>
          ) : !stats ? (
            <div className="flex flex-col items-center justify-center py-20">
              <IconChartIncreasing className="w-16 h-16 text-ink-muted/20 mb-4" />
              <h3 className="text-xl font-bold text-ink-primary mb-2">No data available</h3>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Users section */}
              <div>
                <h2 className="text-lg font-display font-bold text-ink-primary mb-4 flex items-center gap-2">
                  <IconUsers className="w-5 h-5 text-accent" /> Users
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-ink-primary font-display">{stats.users.total}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">Total</p>
                  </div>
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-success font-display">{stats.users.verified}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">Verified</p>
                  </div>
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-ink-primary font-display">{stats.users.github_connected}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono flex items-center justify-center gap-1">
                      <IconGithub className="w-3 h-3" /> GitHub
                    </p>
                  </div>
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-accent font-display">{stats.users.new_this_week}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">New this week</p>
                  </div>
                </div>
              </div>

              {/* Projects section */}
              <div>
                <h2 className="text-lg font-display font-bold text-ink-primary mb-4 flex items-center gap-2">
                  <IconDatabase className="w-5 h-5 text-accent" /> Projects
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-ink-primary font-display">{stats.projects.total}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">Total</p>
                  </div>
                  <div className="glass-card p-5 text-center border border-success/20">
                    <p className="text-3xl font-bold text-success font-display">{stats.projects.done}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono flex items-center justify-center gap-1">
                      <IconCheck className="w-3 h-3 text-success" /> Done
                    </p>
                  </div>
                  <div className="glass-card p-5 text-center border border-warning/20">
                    <p className="text-3xl font-bold text-warning font-display">{stats.projects.processing}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono flex items-center justify-center gap-1">
                      <IconBolt className="w-3 h-3 text-warning" /> Processing
                    </p>
                  </div>
                  <div className="glass-card p-5 text-center border border-danger/20">
                    <p className="text-3xl font-bold text-danger font-display">{stats.projects.failed}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono flex items-center justify-center gap-1">
                      <IconWarning className="w-3 h-3 text-danger" /> Failed
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-ink-muted font-display">{stats.projects.pending}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">Pending</p>
                  </div>
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-accent font-display">{stats.projects.new_this_week}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">New this week</p>
                  </div>
                  <div className="glass-card p-5 text-center">
                    <p className="text-3xl font-bold text-accent font-display">{stats.projects.new_this_month}</p>
                    <p className="text-xs text-ink-muted mt-1 font-mono">New this month</p>
                  </div>
                </div>
              </div>

              {/* Source breakdown */}
              {stats.projects.by_source?.length > 0 && (
                <div>
                  <h2 className="text-lg font-display font-bold text-ink-primary mb-4 flex items-center gap-2">
                    <IconFile className="w-5 h-5 text-accent" /> By Source
                  </h2>
                  <div className="glass-card overflow-hidden">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-bg-elevated">
                          <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Source</th>
                          <th className="text-right text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Count</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.projects.by_source.map((s, i) => (
                          <tr key={i} className="border-t border-border">
                            <td className="px-6 py-4 text-sm text-ink-primary capitalize">{s.source_type}</td>
                            <td className="px-6 py-4 text-right text-sm font-bold text-ink-primary font-mono">{s.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Top users */}
              {stats.top_users?.length > 0 && (
                <div>
                  <h2 className="text-lg font-display font-bold text-ink-primary mb-4 flex items-center gap-2">
                    <IconUser className="w-5 h-5 text-accent" /> Top Users
                  </h2>
                  <div className="glass-card overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-bg-elevated">
                            <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">#</th>
                            <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">User</th>
                            <th className="text-right text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Projects</th>
                          </tr>
                        </thead>
                        <tbody>
                          {stats.top_users.map((u, i) => (
                            <tr key={i} className="border-t border-border">
                              <td className="px-6 py-4 text-sm text-ink-muted font-mono">{i + 1}</td>
                              <td className="px-6 py-4">
                                <button
                                  onClick={() => handleSelectUser(u)}
                                  className="text-sm text-ink-primary hover:text-accent transition-colors text-left"
                                >
                                  {u.name || u.email}
                                </button>
                              </td>
                              <td className="px-6 py-4 text-right text-sm font-bold text-ink-primary font-mono">{u.project_count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </AdminLayout>
  )
}
