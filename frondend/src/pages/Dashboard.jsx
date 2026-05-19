import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getProjects, deleteProject } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import DocCard from '../components/DocCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { IconFolder, IconSparkles, IconFile, IconConstruction, IconSatellite, IconTrash } from '../components/Icons'

export default function Dashboard() {
  const { user, addToast } = useAuth()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await getProjects()
        setProjects(res.data.results || res.data || [])
      } catch (error) {
        console.error('Error fetching projects:', error)
        addToast('Failed to load your projects', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [addToast])

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return
    try {
      await deleteProject(id)
      setProjects(prev => prev.filter(p => p.id !== id))
      addToast('Project deleted successfully', 'success')
    } catch (error) {
      addToast('Failed to delete project', 'error')
    }
  }

  const stats = [
    { label: 'Total Projects', value: projects.length, icon: IconFolder },
    { label: 'Recently Created', value: projects.filter(p => {
      const created = new Date(p.created_at)
      const now = new Date()
      return (now - created) < (7 * 24 * 60 * 60 * 1000) // 7 days
    }).length, icon: IconSparkles },
    { label: 'Source Files', value: projects.reduce((acc, p) => acc + (p.file_count || 0), 0), icon: IconFile }
  ]

  return (
    <div className="relative min-h-screen bg-bg-primary">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-display font-bold text-ink-primary">
              Welcome back, <span className="text-accent">{user?.name || user?.full_name || 'User'}</span>
            </h1>
            <p className="text-ink-secondary mt-2">Manage your documentation projects and generate new ones.</p>
          </div>
          <Link to="/input" className="btn-accent flex items-center gap-2">
            <span>+</span> New Project
          </Link>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
          {stats.map(stat => (
            <div key={stat.label} className="glass-card p-6 flex items-center gap-4">
              <div className="text-accent bg-accent/10 p-3 rounded-xl border border-accent/20">
                <stat.icon className="w-7 h-7" />
              </div>
              <div>
                <p className="text-sm text-ink-muted uppercase tracking-wider font-medium">{stat.label}</p>
                <p className="text-2xl font-bold text-ink-primary">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Projects Section */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-display font-bold text-ink-primary">Recent Projects</h2>
            {projects.length > 0 && (
              <Link to="/profile" className="text-sm text-accent hover:underline">View all history →</Link>
            )}
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-bg-surface/30 rounded-3xl border border-dashed border-border">
              <LoadingSpinner size="lg" className="text-accent mb-4" />
              <p className="text-ink-secondary">Loading your workspace...</p>
            </div>
          ) : projects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 bg-bg-surface/30 rounded-3xl border border-dashed border-border text-center">
              <div className="text-6xl mb-6 opacity-20 text-ink-muted"><IconConstruction className="w-16 h-16" /></div>
              <h3 className="text-xl font-bold text-ink-primary mb-2">No projects yet</h3>
              <p className="text-ink-secondary max-w-sm mb-8">
                You haven't generated any documentation yet. Upload your first Django project to get started.
              </p>
              <Link to="/input" className="btn-accent">
                Generate First Document
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.slice(0, 6).map((project, idx) => (
                <div 
                  key={project.id} 
                  className="glass-card group hover:border-accent/50 transition-all duration-500 hover:shadow-glow-lg animate-slide-up"
                  style={{ animationDelay: `${idx * 100}ms` }}
                >
                  <div className="p-6 flex flex-col h-full">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-accent/10 rounded-xl group-hover:scale-110 transition-transform duration-300">
                          <span className="text-xl">
                            {project.source_type === 'git' ? <IconSatellite /> : project.source_type === 'folder' ? <IconFolder /> : <IconFile />}
                          </span>
                        </div>
                        <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full border ${
                          project.source_type === 'git' ? 'text-success border-success/30 bg-success/5' : 
                          project.source_type === 'folder' ? 'text-warning border-warning/30 bg-warning/5' : 
                          'text-accent border-accent/30 bg-accent/5'
                        }`}>
                          {project.source_type || 'files'}
                        </span>
                      </div>
                      <button 
                        onClick={() => handleDelete(project.id)}
                        className="p-2 text-ink-muted hover:text-danger transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete Project"
                      >
                        <IconTrash className="w-4 h-4" />
                      </button>
                    </div>
                    
                    <h3 className="font-display font-bold text-xl text-ink-primary mb-2 truncate group-hover:text-accent transition-colors">
                      {project.name || 'Untitled Project'}
                    </h3>
                    <p className="text-sm text-ink-secondary mb-6 line-clamp-2 leading-relaxed">
                      {project.description || 'No description provided for this documentation project.'}
                    </p>
                    
                    <div className="flex items-center justify-between mt-auto pt-5 border-t border-border/50">
                      <div className="flex flex-col">
                        <span className="text-[10px] text-ink-muted uppercase tracking-tighter">Created</span>
                        <span className="text-xs text-ink-secondary font-medium">
                          {new Date(project.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                      <Link 
                        to={`/output/${project.id}`}
                        className="flex items-center gap-1.5 text-sm font-bold text-accent hover:text-accent-hover transition-all group-hover:translate-x-1"
                      >
                        Open Docs
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
      
      <Footer />
    </div>
  )
}
