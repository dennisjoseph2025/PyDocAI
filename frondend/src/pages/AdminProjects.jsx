import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getAllProjects } from '../api'
import useAuth from '../hooks/useAuth'
import AdminLayout from '../components/AdminLayout'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import { IconFolder, IconUser, IconCode, IconSearch, IconChartIncreasing } from '../components/Icons'

const PAGE_SIZE = 10

export default function AdminProjects() {
  const { user, isLoading, addToast } = useAuth()
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSource, setFilterSource] = useState('')

  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 500)
    return () => clearTimeout(handler)
  }, [search])

  useEffect(() => {
    if (isLoading) return
    if (!user || !(user.role === 'admin' || user.is_staff)) {
      navigate('/', { replace: true })
      return
    }
    const fetchProjects = async () => {
      try {
        setLoading(true)
        const params = { page, page_size: PAGE_SIZE }
        if (debouncedSearch) params.search = debouncedSearch
        if (filterStatus) params.status = filterStatus
        if (filterSource) params.source_type = filterSource

        const res = await getAllProjects(params)
        const data = res.data || {}
        setStats(data.stats || null)
        setProjects(data.results || [])
        setTotalCount(data.count || 0)
        setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE) || 1)
      } catch (error) {
        console.error('Error fetching admin projects:', error)
        addToast('Failed to load projects', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [user, isLoading, navigate, addToast, debouncedSearch, filterStatus, filterSource, page])

  if (isLoading) return <AdminLayout><div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div></AdminLayout>
  if (!user || !(user.role === 'admin' || user.is_staff)) return null

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-display font-bold text-ink-primary">
          All Projects
        </h1>
        <p className="text-ink-secondary mt-1">
          View all projects across all users
        </p>
      </div>

      {/* Search & Filters */}
      <div className="glass-card p-4 mb-6 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
            <IconSearch className="w-4 h-4" />
          </span>
          <input
            type="text"
            placeholder="Search by name, user email or name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10 pr-4 py-2 text-sm w-full"
          />
        </div>
        <select value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1) }}
          className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
          <option value="">All Status</option>
          <option value="done">Done</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
          <option value="pending">Pending</option>
        </select>
        <select value={filterSource} onChange={e => { setFilterSource(e.target.value); setPage(1) }}
          className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
          <option value="">All Sources</option>
          <option value="folder">Folder</option>
          <option value="github">GitHub</option>
          <option value="file">File</option>
        </select>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-ink-primary">{stats.total}</p>
            <p className="text-xs text-ink-muted mt-1">Total</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-success">{stats.done}</p>
            <p className="text-xs text-ink-muted mt-1">Done</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-danger">{stats.failed}</p>
            <p className="text-xs text-ink-muted mt-1">Failed</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-warning">{stats.processing + stats.pending}</p>
            <p className="text-xs text-ink-muted mt-1">In Progress</p>
          </div>
        </div>
      )}

      {/* Projects List */}
      {loading ? (
        <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="text-6xl mb-6 opacity-20 text-ink-muted"><IconFolder className="w-16 h-16" /></div>
          <h3 className="text-xl font-bold text-ink-primary mb-2">No projects found</h3>
          <p className="text-ink-secondary text-center max-w-md">
            {search || filterStatus || filterSource ? 'No projects match your current filters.' : 'No projects have been created yet by any users.'}
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {projects.map(project => (
              <div key={project.id} className="glass-card p-5 hover:border-accent/50 transition-border duration-300">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl">
                      {project.source_type === 'github' ? <IconCode className="w-5 h-5 text-accent" /> :
                       project.source_type === 'folder' ? <IconFolder className="w-5 h-5 text-warning" /> :
                        <IconChartIncreasing className="w-5 h-5 text-success" />}
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-xl text-ink-primary mb-1 truncate">
                        {project.name || 'Untitled'}
                      </h3>
                      <p className="text-sm text-ink-secondary">
                        {project.description || 'No description provided'}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-ink-muted">By:</span>
                        <span className="font-medium text-ink-primary">{project.user_name || 'Unknown'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="px-2.5 py-0.5 rounded text-xs font-mono">
                      {project.source_type || 'files'}
                    </span>
                    <span className="text-ink-muted">
                      {new Date(project.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-border">
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="text-xs text-ink-muted">Status:</p>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        'done' === project.status ? 'bg-success/20 text-success' :
                        'processing' === project.status ? 'bg-warning/20 text-warning' :
                        'failed' === project.status ? 'bg-danger/20 text-danger' :
                        'bg-border/20 text-ink-secondary'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs text-ink-muted">Files:</p>
                      <span className="font-medium text-ink-primary">{(project.file_count || 0)}</span>
                    </div>
                    <div>
                      <Link to={`/output/${project.id}`} className="p-1.5 rounded-lg hover:bg-bg-elevated text-ink-muted hover:text-ink-primary transition-all">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Pagination
            page={page}
            totalPages={totalPages}
            totalCount={totalCount}
            onPageChange={setPage}
          />
        </>
      )}
    </AdminLayout>
  )
}
