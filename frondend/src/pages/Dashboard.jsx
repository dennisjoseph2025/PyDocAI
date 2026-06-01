import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getProjects, deleteProject } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import {
  IconFolder, IconSparkles, IconFile, IconTrash,
  IconSearch, IconCode, IconLink, IconClock, IconEdit,
  IconChartIncreasing // Added for the Admin Dashboard button
} from '../components/Icons'

const PAGE_SIZE = 10

export default function Dashboard() {
  const { user, addToast } = useAuth()

  const [projects, setProjects] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterType, setFilterType] = useState('all')

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
    const fetchProjects = async () => {
      setLoading(true)
      try {
        const params = { page, page_size: PAGE_SIZE }
        if (debouncedSearch) params.search = debouncedSearch
        if (filterType !== 'all') params.source_type = filterType

        const res = await getProjects(params)

        if (res.data && res.data.results) {
          setProjects(res.data.results)
          setStats(res.data.stats || null)
          setTotalCount(res.data.count)
          setTotalPages(Math.ceil(res.data.count / PAGE_SIZE) || 1)
        } else if (res.data && res.data.stats) {
          setProjects(res.data.results || [])
          setStats(res.data.stats)
          setTotalCount(res.data.stats.total || 0)
          setTotalPages(1)
        } else {
          setProjects(res.data || [])
          setStats(null)
          setTotalCount((res.data || []).length)
          setTotalPages(1)
        }
      } catch (error) {
        addToast('Failed to load your projects', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [debouncedSearch, filterType, page, addToast])

  const handleFilterChange = (type) => {
    if (filterType !== type) {
      setFilterType(type)
      setPage(1)
    }
  }

  const handleDelete = async (id, e) => {
    e.preventDefault()
    if (!window.confirm('Are you sure you want to delete this project?')) return
    try {
      await deleteProject(id)
      setProjects(prev => prev.filter(p => p.id !== id))
      setTotalCount(prev => prev - 1)
      addToast('Project deleted successfully', 'success')
      if (projects.length === 1 && page > 1) {
        setPage(prev => prev - 1)
      }
    } catch (error) {
      addToast('Failed to delete project', 'error')
    }
  }

  const sourceCounts = {}
  if (stats?.by_source) {
    stats.by_source.forEach(s => { sourceCounts[s.source_type] = s.count })
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-4 gap-8">

        <aside className="lg:col-span-1 space-y-6">
          <div className="glass-card p-6 border-border/80">
            <p className="text-xs font-mono text-ink-muted uppercase tracking-wider mb-4">Workspace Control</p>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center text-accent-blue font-bold font-display">
                {(user?.name || user?.email || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <h3 className="font-display font-bold text-ink-primary truncate">{user?.name || 'Developer'}</h3>
                <p className="text-xs text-ink-muted truncate">{user?.email}</p>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <Link to="/input" className="btn-accent flex items-center justify-center gap-2 !py-2.5 text-sm w-full">
                + New Generation
              </Link>
              <Link to="/profile" className="btn-ghost flex items-center justify-center gap-2 !py-2.5 text-sm w-full">
                <IconEdit className="w-4 h-4" /> Edit Profile
              </Link>
              <Link to="/feedback" className="btn-ghost flex items-center justify-center gap-2 !py-2.5 text-sm w-full">
                <IconEdit className="w-4 h-4" /> Feedback
              </Link>
              <Link to="/my-feedback" className="btn-ghost flex items-center justify-center gap-2 !py-2.5 text-sm w-full">
                <IconEdit className="w-4 h-4" /> My Feedback
              </Link>
              
              {/* ADMIN DASHBOARD BUTTON */}
              {(user?.role === 'admin' || user?.is_staff) && (
                <Link to="/admin/stats" className="btn-ghost !border-accent-blue/30 !text-accent-blue hover:!border-accent-blue hover:!bg-accent-blue/5 flex items-center justify-center gap-2 !py-2.5 text-sm w-full transition-all">
                  <IconChartIncreasing className="w-4 h-4" /> Admin Dashboard
                </Link>
              )}
            </div>
          </div>

          <div className="glass-card p-6 space-y-4">
            <p className="text-xs font-mono text-ink-muted uppercase tracking-wider">Metrics</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-bg-surface p-3 rounded-xl border border-border">
                <span className="text-[10px] text-ink-muted uppercase block">Total Docs</span>
                <span className="text-xl font-bold text-accent-blue font-display">{stats?.total ?? totalCount}</span>
              </div>
              <div className="bg-bg-surface p-3 rounded-xl border border-border">
                <div className="flex items-center gap-1.5">
                  <IconFolder className="w-3 h-3 text-warning" />
                  <span className="text-[10px] text-ink-muted uppercase">Folder</span>
                </div>
                <span className="text-lg font-bold text-warning font-display">{sourceCounts['folder'] ?? 0}</span>
              </div>
              <div className="bg-bg-surface p-3 rounded-xl border border-border">
                <div className="flex items-center gap-1.5">
                  <IconCode className="w-3 h-3 text-accent" />
                  <span className="text-[10px] text-ink-muted uppercase">GitHub</span>
                </div>
                <span className="text-lg font-bold text-accent font-display">{sourceCounts['github'] ?? 0}</span>
              </div>
              <div className="bg-bg-surface p-3 rounded-xl border border-border">
                <div className="flex items-center gap-1.5">
                  <IconFile className="w-3 h-3 text-accent-blue" />
                  <span className="text-[10px] text-ink-muted uppercase">File</span>
                </div>
                <span className="text-lg font-bold text-accent-blue font-display">{sourceCounts['file'] ?? 0}</span>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-3 space-y-6">
          <div className="glass-card p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h1 className="text-2xl font-display font-bold text-ink-primary">Python Workspaces</h1>
                <p className="text-sm text-ink-secondary">Manage and browse generated documentation suites</p>
              </div>

              <div className="flex bg-bg-surface p-1 rounded-lg border border-border text-xs font-mono">
                {['all', 'folder', 'github', 'file'].map(t => (
                  <button
                    key={t}
                    onClick={() => handleFilterChange(t)}
                    className={`px-3 py-1.5 rounded-md capitalize transition-all ${filterType === t ? 'bg-accent text-[#0b1320] font-bold' : 'text-ink-secondary hover:text-ink-primary'}`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="relative mb-6">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-muted">
                <IconSearch className="w-4 h-4" />
              </span>
              <input
                type="text"
                placeholder="Search workspace... "
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input-field pl-10 pr-4 py-2.5 text-sm"
              />
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 bg-bg-surface/10 rounded-xl border border-dashed border-border">
                <LoadingSpinner size="lg" className="text-accent-blue mb-4" />
                <p className="text-sm text-ink-secondary font-mono">Querying backend registry...</p>
              </div>
            ) : projects.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 bg-bg-surface/10 rounded-xl border border-dashed border-border text-center">
                <div className="text-4xl text-ink-muted mb-4"><IconFolder className="w-12 h-12 mx-auto" /></div>
                <h3 className="font-display font-bold text-ink-primary mb-1">No workspaces found</h3>
                <p className="text-sm text-ink-secondary max-w-sm mb-6">
                  {search || filterType !== 'all' ? 'No projects match your current filters.' : 'Get started by compiling documentation for your first Django app.'}
                </p>
                {!search && filterType === 'all' && <Link to="/input" className="btn-accent text-sm py-2">Create Workspace</Link>}
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {projects.map((project) => (
                    <Link
                      to={`/output/${project.id}`}
                      key={project.id}
                      className="group bg-bg-surface hover:bg-bg-elevated border border-border hover:border-accent-blue/40 rounded-xl p-5 transition-all duration-300 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-start justify-between mb-3">
                          <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${
                            project.source_type === 'github' ? 'text-success border-success/30 bg-success/5' :
                            project.source_type === 'folder' ? 'text-warning border-warning/30 bg-warning/5' :
                            'text-accent-blue border-accent-blue/30 bg-accent-blue/5'
                          }`}>
                            {project.source_type || 'files'}
                          </span>

                          <button
                            onClick={(e) => handleDelete(project.id, e)}
                            className="text-ink-muted hover:text-danger p-1 rounded hover:bg-bg-primary transition-colors"
                            title="Delete Workspace"
                          >
                            <IconTrash className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <h3 className="font-display font-bold text-lg text-ink-primary group-hover:text-accent-blue transition-colors truncate mb-1">
                          {project.name || 'Untitled Workspace'}
                        </h3>
                        <p className="text-xs text-ink-secondary line-clamp-2 leading-relaxed mb-4">
                          {project.description || 'No description provided.'}
                        </p>
                      </div>

                      <div className="flex items-center justify-between pt-3 border-t border-border/40 text-xs text-ink-muted">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1 font-mono">
                            <IconCode className="w-3.5 h-3.5 text-accent-blue" />
                            <span>{project.file_count || 0} file{(project.file_count || 0) !== 1 ? 's' : ''}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <IconClock className="w-3.5 h-3.5" />
                          <span>{new Date(project.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                        </div>
                      </div>
                    </Link>
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
          </div>
        </main>
      </div>

      <Footer />
    </div>
  )
}