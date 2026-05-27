import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getMyFeedback, createFeedbackReply } from '../api'
import useAuth from '../hooks/useAuth'
import LoadingSpinner from '../components/LoadingSpinner'
import { IconCheck, IconRefresh, IconClock } from '../components/Icons'

export default function MyFeedback() {
  const { user, isLoading, addToast } = useAuth()
  const navigate = useNavigate()
  const [feedbacks, setFeedbacks] = useState([])
  const [loading, setLoading] = useState(true)
  const [replyText, setReplyText] = useState({})
  const [sending, setSending] = useState({})

  useEffect(() => {
    if (isLoading) return
    if (!user) {
      navigate('/login', { replace: true })
      return
    }
    fetchMyFeedback()
  }, [user, isLoading, navigate])

  const fetchMyFeedback = async () => {
    setLoading(true)
    try {
      const res = await getMyFeedback()
      setFeedbacks(res.data)
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

  if (isLoading) return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="glass-card w-full max-w-md p-10">
        <div className="flex items-center justify-center py-20">
          <LoadingSpinner size="lg" className="text-accent" />
        </div>
      </div>
    </div>
  )
  if (!user) return null

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="bg-bg-primary/80 backdrop-blur-xl sticky top-0 z-20 border-b border-border/0">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/profile" className="text-ink-secondary hover:text-ink-primary text-sm font-medium">
            ← Back to Profile
          </Link>
          <h1 className="text-2xl font-display font-bold text-ink-primary">My Feedback</h1>
        </div>
      </header>

      <main className="py-12 px-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-2xl opacity-20"><IconClock className="w-16 h-16" /></div>
            <p className="ml-4 text-xl font-bold text-ink-primary">Loading your feedback...</p>
          </div>
        ) : feedbacks.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <div className="space-y-4">
              <div className="text-5xl opacity-10">💬</div>
              <p className="text-ink-muted text-lg">You haven't submitted any feedback yet</p>
              <p className="text-ink-secondary text-sm">
                Your feedback helps us improve PyDocAI for everyone
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {feedbacks.map(fb => (
              <div key={fb.id} className="glass-card p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-medium text-ink-primary">{fb.user_name || 'You'}</span>
                      <span className="text-xs bg-bg-surface px-2 py-0.5 rounded-full text-ink-secondary capitalize">{fb.category?.replace('_', ' ')}</span>
                      {fb.is_resolved && <span className="text-xs bg-success/10 text-success px-2 py-0.5 rounded-full">Resolved</span>}
                    </div>
                    <p className="text-ink-secondary text-sm whitespace-pre-wrap">{fb.message}</p>
                    <p className="text-xs text-ink-muted mt-1">{new Date(fb.created_at).toLocaleString()}</p>
                  </div>
                </div>

                {/* Threaded Replies */}
                {fb.replies && fb.replies.length > 0 && (
                  <div className="ml-4 pl-4 border-l-2 border-accent/30 space-y-3 mt-4">
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

                {/* Reply Input (only when not resolved) */}
                {!fb.is_resolved && (
                  <div className="mt-4 flex gap-2 items-start">
                    <textarea
                      value={replyText[fb.id] || ''}
                      onChange={e => setReplyText(prev => ({ ...prev, [fb.id]: e.target.value }))}
                      placeholder="Write a reply..."
                      rows={1}
                      className="flex-1 bg-bg-surface border border-border rounded-lg px-3 py-2 text-sm text-ink-primary placeholder-ink-muted focus:outline-none focus:border-accent resize-none"
                    />
                    <button
                      onClick={() => handleReply(fb.id)}
                      disabled={sending[fb.id] || !replyText[fb.id]?.trim()}
                      className="btn-accent text-sm !px-4 !py-2 flex items-center gap-1"
                    >
                      {sending[fb.id] ? <LoadingSpinner size="sm" /> : 'Send'}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
