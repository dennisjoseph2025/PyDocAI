import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getProjects, updateProfile, changePassword } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import { IconUser, IconLock, IconCheck, IconFile, IconCalendar, IconEdit, IconGithub } from '../components/Icons'

export default function Profile() {
  const { user, addToast, updateUser, logout } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('general')
  const [docs, setDocs] = useState([])
  
  // Settings state
  const [name, setName] = useState(user?.name || '')
  const [username, setUsername] = useState(user?.username || '')
  const [pw, setPw] = useState({ old: '', newPw: '', confirm: '' })

  useEffect(() => {
    getProjects().then(res => setDocs(res.data.results || res.data || [])).catch(() => {})
  }, [])

  const handleSaveInfo = async (e) => {
    e.preventDefault()
    try {
      const res = await updateProfile({ name, username })
      updateUser(res.data)
      addToast('Profile updated!', 'success')
    } catch (err) {
      addToast('Update failed', 'error')
    }
  }

  const handleSavePw = async (e) => {
    e.preventDefault()
    if (pw.newPw !== pw.confirm) return addToast('Passwords do not match', 'error')
    try {
      await changePassword({ old_password: pw.old, new_password: pw.newPw })
      addToast('Password changed!', 'success')
      setPw({ old: '', newPw: '', confirm: '' })
    } catch (err) {
      addToast('Password change failed', 'error')
    }
  }

  const initials = (user?.name || user?.email || 'U').charAt(0).toUpperCase()

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-[1000px] w-full mx-auto px-6 py-10 flex flex-col md:flex-row gap-8">
        
        {/* Settings Sidebar */}
        <aside className="w-full md:w-64 flex-shrink-0 space-y-1">
          <div className="flex items-center gap-4 p-3 mb-4">
            <div className="w-12 h-12 rounded-md bg-accent-blue/20 border border-accent-blue/50 flex items-center justify-center text-accent-blue font-bold text-xl">
              {initials}
            </div>
            <div>
              <h2 className="font-display font-bold text-ink-primary truncate">{user?.name}</h2>
              <p className="text-xs font-mono text-ink-muted">@{user?.username || 'user'}</p>
            </div>
          </div>
          
          <button onClick={() => setActiveTab('general')} className={`w-full text-left px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'general' ? 'bg-bg-elevated border-l-2 border-accent text-ink-primary' : 'text-ink-secondary hover:bg-bg-surface'}`}>
            <IconUser className="w-4 h-4 inline mr-2" /> General Profile
          </button>
          <button onClick={() => setActiveTab('security')} className={`w-full text-left px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'security' ? 'bg-bg-elevated border-l-2 border-accent text-ink-primary' : 'text-ink-secondary hover:bg-bg-surface'}`}>
            <IconLock className="w-4 h-4 inline mr-2" /> Security & Password
          </button>
          <div className="pt-4 mt-4 border-t border-border">
             <button onClick={logout} className="w-full text-left px-4 py-2 text-sm text-danger hover:bg-danger/10 rounded-md transition-colors">
               Sign Out
             </button>
          </div>
        </aside>

        {/* Content Area */}
        <div className="flex-1 bg-bg-surface border border-border rounded-md p-8">
          {activeTab === 'general' && (
            <div className="animate-fade-in max-w-lg">
              <h3 className="text-xl font-display font-bold text-ink-primary mb-6 pb-4 border-b border-border">Public Profile</h3>
              <form onSubmit={handleSaveInfo} className="space-y-5">
                <div>
                  <label className="block text-xs font-mono text-ink-muted uppercase mb-2">Name</label>
                  <input value={name} onChange={e => setName(e.target.value)} className="input-field" />
                </div>
                <div>
                  <label className="block text-xs font-mono text-ink-muted uppercase mb-2">Username</label>
                  <input value={username} onChange={e => setUsername(e.target.value)} className="input-field" />
                </div>
                <div>
                  <label className="block text-xs font-mono text-ink-muted uppercase mb-2">Email Address</label>
                  <input value={user?.email || ''} disabled className="input-field opacity-50 cursor-not-allowed" />
                </div>
                <button type="submit" className="btn-accent text-sm">Save Profile</button>
              </form>

              <div className="mt-12 pt-8 border-t border-border">
                <h4 className="font-display font-bold text-ink-primary mb-4">Account Stats</h4>
                <div className="flex gap-4">
                   <div className="bg-bg-primary border border-border p-4 rounded-md flex-1">
                     <p className="text-2xl font-bold text-ink-primary">{docs.length}</p>
                     <p className="text-xs font-mono text-ink-muted">Total Generations</p>
                   </div>
                   <div className="bg-bg-primary border border-border p-4 rounded-md flex-1">
                     <p className="text-2xl font-bold text-ink-primary">{new Date(user?.created_at || Date.now()).getFullYear()}</p>
                     <p className="text-xs font-mono text-ink-muted">Member Since</p>
                   </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="animate-fade-in max-w-lg">
              <h3 className="text-xl font-display font-bold text-ink-primary mb-6 pb-4 border-b border-border">Change Password</h3>
              <form onSubmit={handleSavePw} className="space-y-5">
                {user?.has_password && (
                  <div>
                    <label className="block text-xs font-mono text-ink-muted uppercase mb-2">Current Password</label>
                    <input type="password" value={pw.old} onChange={e => setPw(p => ({...p, old: e.target.value}))} className="input-field" />
                  </div>
                )}
                <div>
                  <label className="block text-xs font-mono text-ink-muted uppercase mb-2">New Password</label>
                  <input type="password" value={pw.newPw} onChange={e => setPw(p => ({...p, newPw: e.target.value}))} className="input-field" placeholder="Min 8 characters" />
                </div>
                <div>
                  <label className="block text-xs font-mono text-ink-muted uppercase mb-2">Confirm New Password</label>
                  <input type="password" value={pw.confirm} onChange={e => setPw(p => ({...p, confirm: e.target.value}))} className="input-field" />
                </div>
                <button type="submit" className="btn-accent text-sm">Update Password</button>
              </form>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}