import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminListUsers } from '../api'
import useAuth from '../hooks/useAuth'
import AdminLayout from '../components/AdminLayout'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import { IconRefresh, IconCheck, IconX, IconUser, IconMail, IconFile, IconCalendar, IconSearch } from '../components/Icons'

const PAGE_SIZE = 10

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

  if (isLoading) return <AdminLayout><div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div></AdminLayout>
  if (!user || user.role !== 'admin') return null

  return (
    <AdminLayout>
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
                    <th className="text-center text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Docs</th>
                    <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-4">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-t border-border hover:bg-bg-elevated/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white ${u.role === 'admin' ? 'bg-accent' : 'bg-bg-surface'}`}>
                            <IconUser className="w-4 h-4" />
                          </div>
                          <span className="text-sm font-medium text-ink-primary">{u.name || '—'}</span>
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
                        <span className="text-sm text-ink-primary flex items-center justify-center gap-1">
                          <IconFile className="w-3.5 h-3.5 text-ink-muted" />
                          {u.project_count ?? '—'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-ink-secondary flex items-center gap-1">
                          <IconCalendar className="w-3.5 h-3.5" />
                          {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                        </span>
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
    </AdminLayout>
  )
}
