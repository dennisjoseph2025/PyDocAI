import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { getComments, createComment, deleteComment } from '../api'
import useAuth from '../hooks/useAuth'
import { IconTrash } from './Icons'

function relativeTime(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return 'just now'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}d ago`
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function CommentForm({ projectId, parent, onSuccess, placeholder = "Write a comment..." }) {
  const { isAuthenticated } = useAuth()
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!isAuthenticated) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!content.trim()) return
    setSubmitting(true)
    try {
      const body = parent ? { content: content.trim(), parent } : { content: content.trim() }
      const res = await createComment(projectId, body)
      onSuccess(res.data)
      setContent('')
    } catch {
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder}
        rows={1}
        className="flex-1 bg-bg-surface border border-border rounded-lg px-3 py-2 text-sm text-ink-primary placeholder-ink-muted focus:outline-none focus:border-accent resize-none"
      />
      <button
        type="submit"
        disabled={submitting || !content.trim()}
        className="self-end btn-accent text-sm !py-1.5 !px-3 disabled:opacity-50"
      >
        {submitting ? 'Posting...' : 'Post'}
      </button>
    </form>
  )
}

function CommentItem({ comment, projectId, depth = 0, currentUserEmail }) {
  const [showReply, setShowReply] = useState(false)
  const [replies, setReplies] = useState(comment.replies || [])
  const isOwner = currentUserEmail && comment.user_email === currentUserEmail
  const maxDepth = 3

  const handleDelete = async () => {
    try {
      await deleteComment(comment.id)
    } catch {
    }
  }

  const handleReplySuccess = (newReply) => {
    setReplies((prev) => [newReply, ...prev])
    setShowReply(false)
  }

  const indent = depth > 0 ? 'ml-8' : ''
  const borderStyle = depth > 0 ? 'border-l-2 border-border pl-4' : ''

  return (
    <div id={`comment-${comment.id}`} className={`${indent} ${borderStyle} mb-4`}>
      <div className="flex items-start gap-3 group">
        <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center text-xs font-bold text-accent shrink-0 mt-0.5">
          {comment.user_name ? comment.user_name[0].toUpperCase() : '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-ink-primary">{comment.user_name}</span>
            <span className="text-xs text-ink-muted">{relativeTime(comment.created_at)}</span>
          </div>
          <p className="text-sm text-ink-secondary mt-1 whitespace-pre-wrap break-words">{comment.content}</p>
          <div className="flex items-center gap-3 mt-1.5">
            {depth < maxDepth - 1 && (
              <button
                onClick={() => setShowReply((prev) => !prev)}
                className="text-xs text-ink-muted hover:text-accent transition-colors"
              >
                Reply
              </button>
            )}
            {isOwner && (
              <button
                onClick={handleDelete}
                className="text-xs text-ink-muted hover:text-danger transition-colors flex items-center gap-1"
              >
                <IconTrash className="w-3 h-3" />
                Delete
              </button>
            )}
          </div>
          {showReply && (
            <div className="mt-3">
              <CommentForm
                projectId={projectId}
                parent={comment.id}
                onSuccess={handleReplySuccess}
                placeholder="Write a reply..."
              />
            </div>
          )}
        </div>
      </div>
      {replies.length > 0 && (
        <div className="mt-2">
          {replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              projectId={projectId}
              depth={depth + 1}
              currentUserEmail={currentUserEmail}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function CommentSection({ projectId, isPublic = false }) {
  const { user, isAuthenticated } = useAuth()
  const [comments, setComments] = useState([])
  const [offset, setOffset] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const sentinelRef = useRef(null)

  const fetchComments = useCallback(async (currentOffset, append = false) => {
    if (append) {
      setLoadingMore(true)
    } else {
      setLoading(true)
    }
    try {
      const res = await getComments(projectId, currentOffset, 20)
      const data = res.data
      if (append) {
        setComments((prev) => [...prev, ...data.comments])
      } else {
        setComments(data.comments)
      }
      setHasNext(data.has_next)
      setTotal(data.total)
      setOffset(currentOffset + 20)
    } catch {
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchComments(0, false)
  }, [fetchComments])

  useEffect(() => {
    if (!sentinelRef.current) return
    const el = sentinelRef.current
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNext && !loadingMore) {
          fetchComments(offset, true)
        }
      },
      { threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasNext, loadingMore, offset, fetchComments])

  const handleNewComment = (newComment) => {
    setComments((prev) => [newComment, ...prev])
    setTotal((prev) => prev + 1)
  }

  const handleDeleteFromList = async (commentId) => {
    try {
      await deleteComment(commentId)
      setComments((prev) => prev.filter((c) => c.id !== commentId))
      setTotal((prev) => Math.max(0, prev - 1))
    } catch {
    }
  }

  return (
    <div className="bg-bg-elevated border border-border rounded-xl p-5">
      <h3 className="text-lg font-semibold text-ink-primary mb-4">
        Comments{total > 0 && <span className="text-ink-muted text-sm font-normal ml-1">({total})</span>}
      </h3>

      {isAuthenticated ? (
        <div className="mb-6">
          <CommentForm projectId={projectId} onSuccess={handleNewComment} />
        </div>
      ) : isPublic && (
        <div className="mb-6 text-sm text-ink-secondary bg-bg-surface rounded-lg px-4 py-3 border border-border">
          Please{' '}
          <Link to="/login" className="text-accent hover:underline">
            log in
          </Link>
          {' '}to comment
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-sm text-ink-muted">Loading...</div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8 text-sm text-ink-muted">No comments yet.</div>
      ) : (
        <div>
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              projectId={projectId}
              depth={0}
              currentUserEmail={user?.email}
            />
          ))}
        </div>
      )}

      <div ref={sentinelRef} className="h-4" />

      {loadingMore && (
        <div className="text-center py-3 text-sm text-ink-muted">Loading...</div>
      )}
    </div>
  )
}
