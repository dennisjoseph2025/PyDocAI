import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMyFeedback, createFeedbackReply } from '../api'
import useAuth from '../hooks/useAuth'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import { IconSearch, IconClock } from '../components/Icons'

const PAGE_SIZE = 10

export default function MyFeedbackView() {
  const { user, isLoading, addToast } = useAuth()
  const navigate = useNavigate()
  const [feedbacks, setFeedbacks] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [filterResolved, setFilterResolved] = useState('')
  const [replyText, setReplyText] = useState({})
  const [sending, setSending] = useState({})

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
    if (!user) {
      navigate('/login', { replace: true })
      return
    }
    fetchMyFeedback()
  }, [user, isLoading, navigate, debouncedSearch, filterCategory, filterResolved, page])

  const fetchMyFeedback = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (debouncedSearch) params.search = debouncedSearch
      if (filterCategory) params.category = filterCategory
      if (filterResolved) params.is_resolved = filterResolved

      const res = await getMyFeedback(params)
      const data = res.data || {}
      setFeedbacks(data.results || [])
      setTotalCount(data.count || 0)
      setTotalPages(Math.ceil((data.count || 0) / PAGE_SIZE) || 1)
    } catch (error) {
      addToast('Failed to load your feedback', 'error')
    } finally {
      setLoading(false)
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

  if (isLoading || loading) return (
    <div className="flex flex-col items-center justify-center py-20 bg-bg-surface/10 rounded-xl border border-dashed border-border text-center">
      <LoadingSpinner size="lg" className="text-accent mb-4" />
      <p className="text-sm text-ink-secondary font-mono">Querying historical feedback entries...</p>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Filtering Actions Block */}
      <div className="glass-card p-4 flex flex-wrap gap-4 items-center border-border/80">
        <div className="relative flex-1 min-w-[200px]">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
            <IconSearch className="w-4 h-4" />
          </span>
          <input
            type="text"
            placeholder="Search your feedback..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10 pr-4 py-2 text-sm w-full"
          />
        </div>
        <select value={filterCategory} onChange={e => { setFilterCategory(e.target.value); setPage(1) }}
          className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
          <option value="">All Categories</option>
          <option value="general">General</option>
          <option value="docs_quality">Docs Quality</option>
          <option value="ui_ux">UI / UX</option>
          <option value="performance">Performance</option>
          <option value="bug">Bug Report</option>
          <option value="feature">Feature Request</option>
        </select>
        <select value={filterResolved} onChange={e => { setFilterResolved(e.target.value); setPage(1) }}
          className="bg-bg-surface border border-border rounded-xl px-4 py-2 text-sm text-ink-primary focus:outline-none focus:border-accent">
          <option value="">All Status</option>
          <option value="false">Unresolved</option>
          <option value="true">Resolved</option>
        </select>
      </div>

      {feedbacks.length === 0 ? (
        <div className="glass-card p-12 text-center border-border/60">
          <p className="text-ink-muted text-base mb-1">
            {search || filterCategory || filterResolved ? 'No feedback matches your filters' : "You haven't submitted any feedback yet"}
          </p>
          <p className="text-ink-secondary text-xs">
            Your logs will populate immediately once a ticket is sent out.
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-6">
            {feedbacks.map(fb => (
              <div key={fb.id} className="glass-card p-6 border-border/80">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-medium text-sm text-ink-primary">{fb.user_name || 'You'}</span>
                      <span className="text-xs bg-bg-surface px-2 py-0.5 rounded-full text-ink-secondary border border-border/40 capitalize">{fb.category?.replace('_', ' ')}</span>
                      {fb.is_resolved && <span className="text-xs bg-success/10 text-success border border-success/20 px-2 py-0.5 rounded-full">Resolved</span>}
                    </div>
                    <p className="text-ink-secondary text-sm whitespace-pre-wrap leading-relaxed">{fb.message}</p>
                    <p className="text-[11px] text-ink-muted mt-2 font-mono">{new Date(fb.created_at).toLocaleString()}</p>
                  </div>
                </div>

                {/* Reply Threads */}
                {fb.replies && fb.replies.length > 0 && (
                  <div className="ml-4 pl-4 border-l-2 border-accent/30 space-y-3 mt-4">
                    {fb.replies.map(reply => (
                      <div key={reply.id} className="bg-bg-surface/40 p-3 rounded-lg border border-border/20">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-bold ${reply.is_admin ? 'text-accent' : 'text-ink-primary'}`}>
                            {reply.user_name}
                          </span>
                          {reply.is_admin && (
                            <span className="text-[10px] font-mono bg-accent/10 text-accent border border-accent/20 px-1.5 py-0.2 rounded">Admin</span>
                          )}
                          <span className="text-[10px] text-ink-muted font-mono">{new Date(reply.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-xs text-ink-primary whitespace-pre-wrap">{reply.message}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Submit New Reply Input */}
                {!fb.is_resolved && (
                  <div className="mt-4 flex gap-2 items-start">
                    <textarea
                      value={replyText[fb.id] || ''}
                      onChange={e => setReplyText(prev => ({ ...prev, [fb.id]: e.target.value }))}
                      placeholder="Write a follow-up reply..."
                      rows={1}
                      className="flex-1 bg-bg-surface border border-border rounded-lg px-3 py-2 text-xs text-ink-primary focus:outline-none focus:border-accent resize-none"
                    />
                    <button
                      onClick={() => handleReply(fb.id)}
                      disabled={sending[fb.id] || !replyText[fb.id]?.trim()}
                      className="btn-accent text-xs !px-4 !py-2 h-[34px] flex items-center justify-center gap-1"
                    >
                      {sending[fb.id] ? <LoadingSpinner size="sm" /> : 'Send'}
                    </button>
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
    </div>
  )
}