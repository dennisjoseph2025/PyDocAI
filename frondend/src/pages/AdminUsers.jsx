import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { adminListUsers, adminGetUserProjects, adminDeleteUser, adminBlockUser } from '../api'
import useAuth from '../hooks/useAuth'
import AdminLayout from '../components/AdminLayout'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import { IconRefresh, IconCheck, IconX, IconUser, IconMail, IconFile, IconCalendar, IconSearch, IconGlobe, IconGithub } from '../components/Icons'

const PAGE_SIZE = 50

export default function AdminUsers() {
  const { user, isLoading, addToast } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterRole, setFilterRole] = useState('')
  const [filterVerified, setFilterVerified] = useState('')

  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleteReason, setDeleteReason] = useState('')
  const [deleting, setDeleting] = useState(false)

  const [blockTarget, setBlockTarget] = useState(null)
  const [blocking, setBlocking] = useState(false)

  const [selectedUser, setSelectedUser] = useState(null)
  const [userProjects, setUserProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(false)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 500)
    return () => clearTimeout(handler)
  }, [search])

  useEffect(() => {
    if (isLoading) return
    if (!user || user.role !== 'admin') {
      navigate('/', { replace: true })
      return
    }
    fetchUsers()
  }, [user, isLoading, navigate, debouncedSearch, filterRole, filterVerified, page])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (debouncedSearch) params.search = debouncedSearch
      if (filterRole) params.role = filterRole
      if (filterVerified) params.is_verified = filterVerified

      const res = await adminListUsers(params)
      const data = res.data || {}
      setUsers(data.results || [])
      setTotalCount(data.count || 0)
      setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE) || 1)
    } catch (error) {
      addToast('Failed to load users', 'error')
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
      addToast('Failed to load published projects', 'error')
    } finally {
      setProjectsLoading(false)
    }
  }

  const handleConfirmBlock = async () => {
    if (!blockTarget) return
    setBlocking(true)
    try {
      const res = await adminBlockUser(blockTarget.id)
      setUsers((prev) => prev.map((x) => x.id === blockTarget.id ? { ...x, is_active: res.data.is_active } : x))
      addToast(`User ${res.data.is_active ? 'unblocked' : 'blocked'}`, 'success')
      setBlockTarget(null)
    } catch {
      addToast('Failed to update user', 'error')
    } finally {
      setBlocking(false)
    }
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await adminDeleteUser(deleteTarget.id, deleteReason)
      setUsers((prev) => prev.filter((u) => u.id !== deleteTarget.id))
      setTotalCount((c) => c - 1)
      addToast(`User ${deleteTarget.email} deleted`, 'success')
      setDeleteTarget(null)
      setDeleteReason('')
    } catch {
      addToast('Failed to delete user', 'error')
    } finally {
      setDeleting(false)
    }
  }

  if (isLoading) return <AdminLayout><div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div></AdminLayout>
  if (!user || user.role !== 'admin') return null

  const formatDate = (d) => d ? new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : ''

  return (
    <AdminLayout>
      <Helmet>
        <title>Admin Users — PyDocAI</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>

      {selectedUser ? (
        <>
          <div className="mb-6">
            <button
              onClick={() => { setSelectedUser(null); setUserProjects([]) }}
              className="flex items-center gap-1 text-sm text-ink-muted hover:text-ink-primary transition-colors mb-4"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg> Back to users
            </button>

            <div className="glass-card p-6 mb-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center text-accent-blue font-bold font-display text-xl">
                    {(selectedUser.name || selectedUser.email || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h1 className="text-2xl font-display font-bold text-ink-primary">{selectedUser.name || 'Unnamed'}</h1>
                    <p className="text-sm text-ink-muted flex items-center gap-1">
                      <IconMail className="w-3.5 h-3.5" /> {selectedUser.email}
                    </p>
                    {selectedUser.github_connected && selectedUser.username && (
                      <a
                        href={`https://github.com/${selectedUser.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-ink-muted hover:text-accent mt-1 transition-colors"
                      >
                        <IconGithub className="w-3.5 h-3.5" /> @{selectedUser.username}
                      </a>
                    )}
                    <p className="flex items-center gap-1 text-xs text-ink-muted mt-1">
                      <IconCalendar className="w-3.5 h-3.5" /> Joined {formatDate(selectedUser.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2.5 py-1 rounded-full ${
                    selectedUser.role === 'admin' ? 'bg-accent/10 text-accent' : 'bg-bg-surface text-ink-secondary'
                  }`}>
                    {selectedUser.role}
                  </span>
                  {selectedUser.is_verified
                    ? <span className="text-xs px-2.5 py-1 rounded-full bg-success/10 text-success">Verified</span>
                    : <span className="text-xs px-2.5 py-1 rounded-full bg-ink-muted/10 text-ink-muted">Unverified</span>
                  }
                  {selectedUser.is_active === false && (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-danger/10 text-danger">Blocked</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 mb-6">
              <button
                onClick={() => setBlockTarget(selectedUser)}
                className={`text-xs px-4 py-2 rounded-lg font-mono transition-colors ${
                  selectedUser.is_active === false
                    ? 'bg-accent/10 border border-accent/20 text-accent hover:bg-accent/20'
                    : 'bg-warning/10 border border-warning/20 text-warning hover:bg-warning/20'
                }`}
              >
                {selectedUser.is_active === false ? 'Unblock User' : 'Block User'}
              </button>
              <button
                onClick={() => { setDeleteTarget(selectedUser); setDeleteReason('') }}
                className="text-xs px-4 py-2 rounded-lg font-mono bg-danger/10 border border-danger/20 text-danger hover:bg-danger/20 transition-colors"
              >
                Delete User
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="glass-card p-5 text-center">
                <p className="text-3xl font-bold text-ink-primary font-display">{selectedUser.project_count ?? 0}</p>
                <p className="text-xs text-ink-muted mt-1 font-mono">Total Documents</p>
              </div>
              <div className="glass-card p-5 text-center">
                <p className="text-3xl font-bold text-accent font-display">{selectedUser.published_count ?? 0}</p>
                <p className="text-xs text-ink-muted mt-1 font-mono">Published</p>
              </div>
            </div>

            <div className="mb-4">
              <h2 className="text-lg font-display font-bold text-ink-primary">Published Projects</h2>
              <p className="text-xs text-ink-muted mt-0.5">{userProjects.length} of {selectedUser.published_count} published</p>
            </div>

            {projectsLoading ? (
              <div className="flex items-center justify-center py-16"><LoadingSpinner size="lg" className="text-accent" /></div>
            ) : userProjects.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <IconGlobe className="w-12 h-12 text-ink-muted/20 mx-auto mb-3" />
                <p className="text-ink-muted">No published projects</p>
              </div>
            ) : (
              <div className="space-y-3">
                {userProjects.map((p) => (
                  <div key={p.id} className="glass-card p-5 hover:border-accent/50 transition-border duration-300">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-display font-bold text-lg text-ink-primary mb-1">{p.name || 'Untitled'}</h3>
                        <p className="text-sm text-ink-secondary line-clamp-2">{p.description || 'No description'}</p>
                      </div>
                      <a
                        href={`/public/${p.public_slug}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 border border-accent/20 text-accent hover:bg-accent/20 text-xs font-mono transition-colors shrink-0 ml-4"
                      >
                        <IconGlobe className="w-3.5 h-3.5" /> Open
                      </a>
                    </div>
                    <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border text-xs text-ink-muted">
                      <span className="flex items-center gap-1">
                        <IconFile className="w-3.5 h-3.5" /> {p.file_count || 0} files
                      </span>
                      <span className="flex items-center gap-1">
                        <IconCalendar className="w-3.5 h-3.5" /> {formatDate(p.updated_at)}
                      </span>
                      <span className="flex items-center gap-1 ml-auto">
                        <IconGlobe className="w-3.5 h-3.5 text-accent" /> Published
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-display font-bold text-ink-primary">Users</h1>
              <p className="text-ink-secondary mt-1">{totalCount} registered users</p>
            </div>
            <button onClick={() => { setPage(1); fetchUsers() }} className="btn-ghost text-sm !px-4 !py-2 flex items-center gap-2">
              <IconRefresh className="w-4 h-4" /> Refresh
            </button>
          </div>

          <div className="glass-card p-4 mb-6 flex flex-wrap gap-4 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
                <IconSearch className="w-4 h-4" />
              </span>
              <input
                type="text"
                placeholder="Search by name, email or username..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input-field pl-10 pr-4 py-2 text-sm w-full"
              />
            </div>
            <select value={filterRole} onChange={e => { setFilterRole(e.target.value); setPage(1) }}
              className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="user">User</option>
            </select>
            <select value={filterVerified} onChange={e => { setFilterVerified(e.target.value); setPage(1) }}
              className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
              <option value="">All Verified</option>
              <option value="true">Verified</option>
              <option value="false">Unverified</option>
            </select>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div>
          ) : users.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <p className="text-ink-muted text-lg">No users found</p>
            </div>
          ) : (
            <>
              <div className="glass-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-bg-elevated">
                        <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">User</th>
                        <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Email</th>
                        <th className="text-center text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Role</th>
                        <th className="text-center text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Verified</th>
                        <th className="text-center text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Published</th>
                        <th className="text-center text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map(u => (
                        <tr key={u.id} onClick={() => handleSelectUser(u)} className="border-t border-border hover:bg-bg-elevated/50 transition-colors cursor-pointer">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white ${u.role === 'admin' ? 'bg-accent' : 'bg-bg-surface'}`}>
                                <IconUser className="w-4 h-4" />
                              </div>
                              <div>
                                <span className="text-sm font-medium text-ink-primary">{u.name || '—'}</span>
                                {u.github_connected && u.username && (
                                  <a
                                    href={`https://github.com/${u.username}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="flex items-center gap-1 text-xs text-ink-muted hover:text-accent mt-0.5 transition-colors"
                                  >
                                    <IconGithub className="w-3 h-3" /> @{u.username}
                                  </a>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2 text-sm text-ink-secondary">
                              <IconMail className="w-3.5 h-3.5" />
                              {u.email}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              u.role === 'admin' ? 'bg-accent/10 text-accent' : 'bg-bg-surface text-ink-secondary'
                            }`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            {u.is_verified
                              ? <IconCheck className="w-4 h-4 text-success mx-auto" />
                              : <IconX className="w-4 h-4 text-ink-muted mx-auto" />
                            }
                          </td>
                          <td className="px-6 py-4 text-center">
                            <button
                              onClick={(e) => { e.stopPropagation(); handleSelectUser(u) }}
                              disabled={(u.published_count ?? 0) === 0}
                              className={`text-sm font-bold font-display flex items-center justify-center gap-1 mx-auto transition-colors ${
                                (u.published_count ?? 0) > 0
                                  ? 'text-accent hover:text-accent/80 cursor-pointer'
                                  : 'text-ink-muted cursor-default'
                              }`}
                              title={(u.published_count ?? 0) > 0 ? 'View published projects' : 'No published projects'}
                            >
                              <IconGlobe className="w-3.5 h-3.5" />
                              {u.published_count ?? 0}
                            </button>
                          </td>
                          <td className="px-6 py-4 text-center">
                            {u.is_active === false ? (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-danger/10 text-danger border border-danger/20">Blocked</span>
                            ) : (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-success/10 text-success">Active</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <Pagination
                page={page}
                totalPages={totalPages}
                totalCount={totalCount}
                onPageChange={setPage}
              />
            </>
          )}
        </>
      )}

      {blockTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-elevated border border-border rounded-2xl shadow-2xl max-w-sm w-full mx-4 p-8 space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-warning/20 border border-warning/30 flex items-center justify-center text-warning text-lg font-bold">!</div>
              <div>
                <h3 className="text-base font-display font-bold text-ink-primary">
                  {blockTarget.is_active === false ? 'Unblock' : 'Block'} User
                </h3>
                <p className="text-[11px] text-ink-muted font-mono">
                  Are you sure you want to {blockTarget.is_active === false ? 'unblock' : 'block'} <strong className="text-ink-primary">{blockTarget.email}</strong>?
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setBlockTarget(null)}
                className="flex-1 py-2.5 px-4 rounded-xl border border-border bg-bg-surface hover:bg-bg-primary text-ink-primary text-xs font-mono transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmBlock}
                disabled={blocking}
                className={`flex-1 py-2.5 px-4 rounded-xl text-white text-xs font-mono transition-all disabled:opacity-50 ${
                  blockTarget.is_active === false
                    ? 'bg-accent hover:bg-accent/80'
                    : 'bg-warning hover:bg-warning/80'
                }`}
              >
                {blocking ? 'Processing...' : blockTarget.is_active === false ? 'Unblock' : 'Block'}
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-elevated border border-border rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8 space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-danger/20 border border-danger/30 flex items-center justify-center text-danger text-lg font-bold">!</div>
              <div>
                <h3 className="text-base font-display font-bold text-ink-primary">Delete User</h3>
                <p className="text-[11px] text-ink-muted font-mono">
                  This will permanently delete <strong className="text-ink-primary">{deleteTarget.email}</strong> and all their projects.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-xs text-ink-muted font-mono mb-1.5">Reason for deletion (sent via email):</label>
              <textarea
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                placeholder="e.g. Violation of terms of service..."
                rows={3}
                className="input-field p-3 text-sm w-full resize-none"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 py-2.5 px-4 rounded-xl border border-border bg-bg-surface hover:bg-bg-primary text-ink-primary text-xs font-mono transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="flex-1 py-2.5 px-4 rounded-xl bg-danger hover:bg-danger/80 text-white text-xs font-mono transition-all disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete User'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}