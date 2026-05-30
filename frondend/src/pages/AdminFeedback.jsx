import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAllFeedback, resolveFeedback, createFeedbackReply } from '../api'
import useAuth from '../hooks/useAuth'
import AdminLayout from '../components/AdminLayout'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import { IconCheck, IconRefresh, IconSearch } from '../components/Icons'

const PAGE_SIZE = 10

const CATEGORIES = [
  { value: '',             label: 'All Categories' },
  { value: 'general',      label: 'General' },
  { value: 'docs_quality', label: 'Docs Quality' },
  { value: 'ui_ux',        label: 'UI / UX' },
  { value: 'performance',  label: 'Performance' },
  { value: 'bug',          label: 'Bug Report' },
  { value: 'feature',      label: 'Feature Request' },
]

export default function AdminFeedback() {
  const { user, isLoading, addToast } = useAuth()
  const navigate = useNavigate()
  const [feedbacks, setFeedbacks] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterCategory, setFilterCategory] = useState('')
  const [filterResolved, setFilterResolved] = useState('')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [replyText, setReplyText] = useState({})
  const [sending, setSending] = useState({})
  const [resolving, setResolving] = useState({})

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
    fetchFeedbacks()
  }, [user, isLoading, navigate, filterCategory, filterResolved, debouncedSearch, page])

  const fetchFeedbacks = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (filterCategory) params.category = filterCategory
      if (filterResolved) params.resolved = filterResolved
      if (debouncedSearch) params.search = debouncedSearch

      const res = await getAllFeedback(params)
      const data = res.data || {}
      setFeedbacks(data.results || [])
      setTotalCount(data.count || 0)
      setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE) || 1)
    } catch (error) {
      addToast('Failed to load feedback', 'error')
    } finally {
      setLoading(false)
    }
  }, [filterCategory, filterResolved, debouncedSearch, page, addToast])

  useEffect(() => {
    if (!isLoading && user?.role === 'admin') {
      fetchFeedbacks()
    }
  }, [fetchFeedbacks, isLoading, user])

  const handleResolve = async (id) => {
    setResolving(prev => ({ ...prev, [id]: true }))
    try {
      await resolveFeedback(id)
      setFeedbacks(prev => prev.map(f =>
        f.id === id ? { ...f, is_resolved: true } : f
      ))
      addToast('Feedback resolved', 'success')
    } catch {
      addToast('Failed to resolve feedback', 'error')
    } finally {
      setResolving(prev => ({ ...prev, [id]: false }))
    }
  }

  const handleReply = async (feedbackId) => {
    const msg = replyText[feedbackId]?.trim()
    if (!msg) return
    setSending(prev => ({ ...prev, [feedbackId]: true }))
    try {
      const res = await createFeedbackReply(feedbackId, msg)
      setFeedbacks(prev => prev.map(fb =>
        fb.id === feedbackId
          ? { ...fb, replies: [...(fb.replies || []), res.data] }
          : fb
      ))
      setReplyText(prev => ({ ...prev, [feedbackId]: '' }))
    } catch {
      addToast('Failed to send reply', 'error')
    } finally {
      setSending(prev => ({ ...prev, [feedbackId]: false }))
    }
  }

  if (isLoading) return <AdminLayout><div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div></AdminLayout>
  if (!user || user.role !== 'admin') return null

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-display font-bold text-ink-primary">Feedback</h1>
        <p className="text-ink-secondary mt-1">Review and respond to user feedback</p>
      </div>

      <div className="glass-card p-4 mb-6 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
            <IconSearch className="w-4 h-4" />
          </span>
          <input
            type="text"
            placeholder="Search by message, user name or email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10 pr-4 py-2 text-sm w-full"
          />
        </div>
        <select value={filterCategory} onChange={e => { setFilterCategory(e.target.value); setPage(1) }}
          className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
        <select value={filterResolved} onChange={e => { setFilterResolved(e.target.value); setPage(1) }}
          className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
          <option value="">All Status</option>
          <option value="false">Unresolved</option>
          <option value="true">Resolved</option>
        </select>
        <button onClick={() => { setPage(1); fetchFeedbacks() }} className="btn-ghost text-sm !px-4 !py-2 flex items-center gap-2">
          <IconRefresh className="w-4 h-4" /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" className="text-accent" /></div>
      ) : feedbacks.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <p className="text-ink-muted text-lg">No feedback found</p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {feedbacks.map(fb => (
              <div key={fb.id} className={`glass-card p-6 transition-all ${fb.is_resolved ? 'opacity-70' : ''}`}>
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <span className="font-medium text-ink-primary">{fb.user_name || 'Anonymous'}</span>
                      <span className="text-xs bg-bg-surface px-2 py-0.5 rounded-full text-ink-secondary capitalize">{fb.category?.replace('_', ' ')}</span>
                      {fb.is_resolved && <span className="text-xs bg-success/10 text-success px-2 py-0.5 rounded-full">Resolved</span>}
                    </div>
                    <p className="text-ink-secondary text-sm whitespace-pre-wrap">{fb.message}</p>
                    <p className="text-xs text-ink-muted mt-1">{new Date(fb.created_at).toLocaleString()}</p>
                  </div>
                </div>

                {fb.replies && fb.replies.length > 0 && (
                  <div className="ml-4 pl-4 border-l-2 border-accent/30 space-y-3 mt-4 mb-4">
                    {fb.replies.map(reply => (
                      <div key={reply.id}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-medium ${reply.is_admin ? 'text-accent' : 'text-ink-primary'}`}>
                            {reply.user_name}
                          </span>
                          {reply.is_admin && (
                            <span className="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded">Admin</span>
                          )}
                          <span className="text-xs text-ink-muted">{new Date(reply.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-sm text-ink-primary whitespace-pre-wrap">{reply.message}</p>
                      </div>
                    ))}
                  </div>
                )}

                {!fb.is_resolved && (
                  <div className="ml-4 pl-4 border-l-2 border-accent/30">
                    <div className="flex gap-2 items-start">
                      <textarea
                        value={replyText[fb.id] || ''}
                        onChange={e => setReplyText(prev => ({ ...prev, [fb.id]: e.target.value }))}
                        placeholder="Write a reply..."
                        rows={2}
                        className="flex-1 bg-bg-surface border border-border rounded-lg px-3 py-2 text-sm text-ink-primary placeholder-ink-muted focus:outline-none focus:border-accent resize-none"
                      />
                      <div className="flex gap-1 flex-shrink-0">
                        <button
                          onClick={() => handleReply(fb.id)}
                          disabled={sending[fb.id] || !replyText[fb.id]?.trim()}
                          className="btn-ghost text-xs !px-3 !py-2"
                        >
                          {sending[fb.id] ? <LoadingSpinner size="sm" /> : 'Reply'}
                        </button>
                        <button
                          onClick={() => handleResolve(fb.id)}
                          disabled={resolving[fb.id]}
                          className="btn-ghost text-xs !px-3 !py-2 flex items-center gap-1"
                          title="Resolve"
                        >
                          {resolving[fb.id] ? <LoadingSpinner size="sm" /> : <><IconCheck className="w-3 h-3" /> Resolve</>}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
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
