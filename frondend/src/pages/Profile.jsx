import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getProjects, deleteProject, updateProfile, changePassword } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import DocCard from '../components/DocCard'
import LoadingSpinner from '../components/LoadingSpinner'
import FeedbackModal from '../components/FeedbackModal'
import {
  IconUser, IconLock, IconKey, IconEye, IconEyeOff,
  IconCheck, IconX, IconEdit, IconFile, IconCalendar,
  IconGithub, IconCode, IconChartIncreasing,
} from '../components/Icons'

const avatarColors = ['bg-accent', 'bg-success', 'bg-warning', 'bg-danger', 'bg-blue-500', 'bg-purple-500', 'bg-pink-500']

// ─── Edit Profile Modal ────────────────────────────────────────────────────────
function EditProfileModal({ user, onClose, onSaved }) {
  const { addToast } = useAuth()
  const [tab, setTab] = useState('info')          // 'info' | 'password'

  // Info tab state
  const [name, setName] = useState(user?.name || '')
  const [username, setUsername] = useState(user?.username || '')
  const [savingInfo, setSavingInfo] = useState(false)

  // Password tab state
  const [pw, setPw] = useState({ old: '', newPw: '', confirm: '' })
  const [showOld, setShowOld] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [savingPw, setSavingPw] = useState(false)

  const strength = (() => {
    const p = pw.newPw
    let s = 0
    if (p.length >= 6) s++
    if (p.length >= 10) s++
    if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s++
    if (/[^a-zA-Z0-9]/.test(p)) s++
    return s
  })()
  const strengthColors = ['bg-danger', 'bg-warning', 'bg-yellow-400', 'bg-success']
  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong']

  const handleSaveInfo = async (e) => {
    e.preventDefault()
    if (!name.trim()) { addToast('Name is required', 'error'); return }
    setSavingInfo(true)
    try {
      const res = await updateProfile({ name: name.trim(), username: username.trim() || undefined })
      onSaved(res.data)
      addToast('Profile updated!', 'success')
      onClose()
    } catch (err) {
      const data = err.response?.data
      const msg = data?.name?.[0] || data?.username?.[0] || data?.detail || 'Update failed'
      addToast(msg, 'error')
    } finally {
      setSavingInfo(false)
    }
  }

  const handleSavePw = async (e) => {
    e.preventDefault()
    if (user?.has_password && !pw.old) { addToast('Current password is required', 'error'); return }
    if (pw.newPw.length < 8) { addToast('New password must be at least 8 characters', 'error'); return }
    if (pw.newPw !== pw.confirm) { addToast('Passwords do not match', 'error'); return }
    setSavingPw(true)
    try {
      const payload = { new_password: pw.newPw }
      if (pw.old) payload.old_password = pw.old
      await changePassword(payload)
      addToast('Password changed successfully!', 'success')
      setPw({ old: '', newPw: '', confirm: '' })
      onClose()
    } catch (err) {
      const data = err.response?.data
      const msg = data?.old_password?.[0] || data?.new_password?.[0] || data?.detail || 'Password change failed'
      addToast(msg, 'error')
    } finally {
      setSavingPw(false)
    }
  }

  // Close on backdrop click
  const handleBackdrop = (e) => { if (e.target === e.currentTarget) onClose() }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      onClick={handleBackdrop}
      style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)' }}
    >
      <div className="glass-card w-full max-w-md animate-fade-in overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="font-display font-bold text-lg text-ink-primary">Edit Profile</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-ink-muted hover:text-ink-primary hover:bg-bg-surface transition-all"
            aria-label="Close"
          >
            <IconX className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          {[
            { id: 'info', label: <><IconUser className="w-4 h-4 inline mr-1" /> Profile Info</> },
            { id: 'password', label: <><IconLock className="w-4 h-4 inline mr-1" /> Change Password</> },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 py-3 text-sm font-display font-semibold transition-colors duration-200 ${
                tab === t.id
                  ? 'text-accent border-b-2 border-accent -mb-px'
                  : 'text-ink-secondary hover:text-ink-primary'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* ── Info Tab ── */}
          {tab === 'info' && (
            <form onSubmit={handleSaveInfo} className="space-y-5">
              {/* Avatar preview */}
              <div className="flex items-center gap-4 mb-2">
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-xl font-display font-bold text-white ${avatarColors[(name || 'U').charCodeAt(0) % avatarColors.length]}`}>
                  {(name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)}
                </div>
                <div>
                  <p className="text-ink-primary font-medium text-sm">{name || 'Your Name'}</p>
                  <p className="text-ink-muted text-xs">{user?.email}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-ink-secondary mb-2">Full Name</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconUser /></span>
                  <input
                    id="edit-name"
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    className="input-field pl-10"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-ink-secondary mb-2">Username</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-sm">@</span>
                  <input
                    id="edit-username"
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    className="input-field pl-8"
                    placeholder="johndoe"
                  />
                </div>
              </div>

              <div className="pt-1">
                <label className="block text-sm font-medium text-ink-secondary mb-2">Email</label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="input-field opacity-50 cursor-not-allowed"
                />
                <p className="text-ink-muted text-xs mt-1">Email cannot be changed</p>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={onClose} className="btn-ghost flex-1">
                  Cancel
                </button>
                <button
                  id="save-profile"
                  type="submit"
                  disabled={savingInfo}
                  className="btn-accent flex-1 flex items-center justify-center gap-2"
                >
                  {savingInfo ? <><LoadingSpinner size="sm" /> Saving...</> : 'Save Changes'}
                </button>
              </div>
            </form>
          )}

          {/* ── Password Tab ── */}
          {tab === 'password' && (
            <form onSubmit={handleSavePw} className="space-y-5">
              {user?.has_password && (
                <div>
                  <label className="block text-sm font-medium text-ink-secondary mb-2">Current Password</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconLock /></span>
                    <input
                      id="edit-old-pw"
                      type={showOld ? 'text' : 'password'}
                      value={pw.old}
                      onChange={e => setPw(p => ({ ...p, old: e.target.value }))}
                      className="input-field pl-10 pr-10"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOld(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-primary"
                    >
                      {showOld ? <IconEyeOff /> : <IconEye />}
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-ink-secondary mb-2">New Password</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconKey /></span>
                  <input
                    id="edit-new-pw"
                    type={showNew ? 'text' : 'password'}
                    value={pw.newPw}
                    onChange={e => setPw(p => ({ ...p, newPw: e.target.value }))}
                    className="input-field pl-10 pr-10"
                    placeholder="Min 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNew(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-primary"
                  >
                    {showNew ? <IconEyeOff /> : <IconEye />}
                  </button>
                </div>
                {pw.newPw && (
                  <div className="mt-2 space-y-1">
                    <div className="flex gap-1">
                      {[1, 2, 3, 4].map(i => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded-full transition-colors duration-300 ${strength >= i ? strengthColors[i - 1] : 'bg-border'}`}
                        />
                      ))}
                    </div>
                    <p className={`text-xs ${strengthColors[strength - 1]?.replace('bg-', 'text-') || 'text-ink-muted'}`}>
                      {strength > 0 ? strengthLabels[strength - 1] : ''}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-ink-secondary mb-2">Confirm New Password</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconKey /></span>
                  <input
                    id="edit-confirm-pw"
                    type="password"
                    value={pw.confirm}
                    onChange={e => setPw(p => ({ ...p, confirm: e.target.value }))}
                    className="input-field pl-10"
                    placeholder="••••••••"
                  />
                </div>
                {pw.confirm.length > 0 && (
                  <p className={`text-xs mt-1 ${pw.newPw === pw.confirm ? 'text-success' : 'text-danger'}`}>
                    {pw.newPw === pw.confirm ? <><IconCheck className="w-3 h-3 inline mr-1" />Passwords match</> : <><IconX className="w-3 h-3 inline mr-1" />Passwords do not match</>}
                  </p>
                )}
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={onClose} className="btn-ghost flex-1">
                  Cancel
                </button>
                <button
                  id="save-password"
                  type="submit"
                  disabled={savingPw}
                  className="btn-accent flex-1 flex items-center justify-center gap-2"
                >
                  {savingPw ? <><LoadingSpinner size="sm" /> Saving...</> : 'Change Password'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Main Profile Page ─────────────────────────────────────────────────────────
export default function Profile() {
  const { user, addToast, updateUser } = useAuth()
  const navigate = useNavigate()
  const [localUser, setLocalUser] = useState(user)
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)

  // Keep localUser in sync with auth context
  useEffect(() => { setLocalUser(user) }, [user])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getProjects()
        setDocs(res.data.results || res.data || [])
      } catch {
        addToast('Failed to load history', 'error')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [addToast])

  const handleDelete = async (id) => {
    try {
      await deleteProject(id)
      setDocs(prev => prev.filter(d => d.id !== id))
      addToast('Document deleted', 'success')
    } catch {
      addToast('Delete failed', 'error')
    }
  }

  // Update both local state and global AuthContext so Navbar/avatar reflect changes instantly
  const handleProfileSaved = (updatedUser) => {
    setLocalUser(prev => ({ ...prev, ...updatedUser }))
    updateUser(updatedUser)
  }

  const displayUser = localUser || user
  const nameHash = (displayUser?.name || displayUser?.email || 'U').charCodeAt(0) % avatarColors.length
  const initials = (displayUser?.name || displayUser?.email || 'U')
    .split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  const totalDocs = docs.length
  const thisMonth = docs.filter(d => {
    const created = new Date(d.created_at)
    const now = new Date()
    return created.getMonth() === now.getMonth() && created.getFullYear() === now.getFullYear()
  }).length

  return (
    <div className="relative z-10">
      <Navbar />
      <div className="min-h-screen bg-bg-primary py-12 px-4">
        <div className="max-w-5xl mx-auto">

          {/* Profile Header */}
          <div className="glass-card p-8 flex flex-col md:flex-row items-start md:items-center gap-8 mb-8 animate-fade-in">
            <div className={`w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-display font-bold text-white flex-shrink-0 ${avatarColors[nameHash]}`}>
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="font-display font-bold text-3xl text-ink-primary truncate">
                {displayUser?.name || 'User'}
              </h1>
              {displayUser?.username && (
                <p className="text-ink-secondary text-sm mt-0.5">@{displayUser.username}</p>
              )}
              <p className="text-ink-muted text-sm mt-1">{displayUser?.email}</p>
              {displayUser?.created_at && (
                <p className="text-ink-muted text-xs mt-1">
                  Joined {new Date(displayUser.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </p>
              )}
              <div className="flex flex-wrap gap-3 mt-4">
                <span className="bg-bg-surface border border-border rounded-full px-4 py-1.5 text-sm flex items-center gap-2 text-ink-secondary">
                  <IconFile className="w-4 h-4" /> {totalDocs} docs
                </span>
                <span className="bg-bg-surface border border-border rounded-full px-4 py-1.5 text-sm flex items-center gap-2 text-ink-secondary">
                  <IconCalendar className="w-4 h-4" /> {thisMonth} this month
                </span>
                {displayUser?.is_verified && (
                  <span className="bg-success/10 border border-success/30 rounded-full px-4 py-1.5 text-sm flex items-center gap-2 text-success">
                    <IconCheck className="w-4 h-4" /> Verified
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-2 self-start flex-shrink-0">
              {user?.role !== 'admin' && (
                <>
                  <button
                    id="feedback-btn"
                    onClick={() => setShowFeedback(true)}
                    className="btn-ghost self-start text-sm flex items-center gap-2"
                  >
                    <IconEdit className="w-4 h-4" /> Feedback
                  </button>
                  <button
                    id="my-feedback-btn"
                    onClick={() => navigate('/my-feedback')}
                    className="btn-ghost self-start text-sm flex items-center gap-2"
                  >
                    <IconCheck className="w-4 h-4" /> My Feedback
                  </button>
                </>
              )}
               {user?.role === 'admin' && (
                 <button
                   id="admin-dashboard-btn"
                   onClick={() => navigate('/admin/stats')}
                   className="btn-accent self-start text-sm flex items-center gap-2"
                 >
                   <IconChartIncreasing className="w-4 h-4" /> Admin Dashboard
                 </button>
               )}
              <button
                id="edit-profile-btn"
                onClick={() => setShowEditModal(true)}
                className="btn-ghost self-start text-sm flex items-center gap-2"
              >
                <IconEdit className="w-4 h-4" /> Edit Profile
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
            {[
              { value: totalDocs, label: 'Total Docs', icon: IconFile },
              { value: thisMonth, label: 'This Month', icon: IconCalendar },
              { value: docs.filter(d => d.source_type === 'github').length, label: 'Git Projects', icon: IconGithub },
            ].map(s => (
              <div key={s.label} className="glass-card p-6 flex items-center gap-4">
                <span className="text-accent"><s.icon className="w-8 h-8" /></span>
                <div>
                  <p className="font-display font-bold text-4xl text-accent">{s.value}</p>
                  <p className="text-ink-secondary text-sm mt-1">{s.label}</p>
                </div>
              </div>
            ))}
          </div>

          {/* History */}
          <div className="glass-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h2 className="font-display font-bold text-ink-primary">Documentation History</h2>
              <Link to="/input" className="text-accent text-sm hover:text-accent-hover transition-colors">+ New</Link>
            </div>
            {loading ? (
              <div className="py-20 text-center"><LoadingSpinner size="lg" className="text-accent mx-auto" /></div>
            ) : docs.length === 0 ? (
              <div className="py-20 text-center">
                <p className="text-4xl mb-3 text-ink-muted"><IconCode className="w-12 h-12 mx-auto" /></p>
                <p className="text-ink-primary font-display font-bold mb-1">No documentation yet</p>
                <p className="text-ink-muted text-sm mb-4">Generate your first docs to see them here.</p>
                <Link to="/input" className="text-accent hover:underline text-sm">Generate Documentation →</Link>
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="bg-bg-elevated">
                    <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-3">Name</th>
                    <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-3">Type</th>
                    <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-3">Date</th>
                    <th className="text-left text-xs font-display font-bold text-ink-muted uppercase tracking-widest px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map(doc => <DocCard key={doc.id} doc={doc} onDelete={handleDelete} />)}
                </tbody>
              </table>
            )}
          </div>

        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedback && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)' }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowFeedback(false) }}
        >
          <div className="w-full max-w-lg">
            <FeedbackModal onClose={() => setShowFeedback(false)} />
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <EditProfileModal
          user={displayUser}
          onClose={() => setShowEditModal(false)}
          onSaved={handleProfileSaved}
        />
      )}
    </div>
  )
}
