import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeFile, analyzeFolder, importFromGithub } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import StepIndicator from '../components/StepIndicator'
import { IconFile, IconArchive, IconLink, IconWarning } from '../components/Icons'

const tabs = [
  { id: 'single', label: 'Single File',  icon: IconFile },
  { id: 'upload', label: 'Project ZIP',  icon: IconArchive },
  { id: 'git',    label: 'Git Repo',     icon: IconLink },
]

const defaultSteps = [
  { label: 'Uploading files...', done: false, active: false },
  { label: 'Parsing Django project structure...', done: false, active: false },
  { label: 'Analyzing models, views & serializers...', done: false, active: false },
  { label: 'Generating documentation...', done: false, active: false },
  { label: 'Finalizing output...', done: false, active: false },
]

export default function Input() {
  const [active, setActive] = useState('upload')
  const [projectName, setProjectName] = useState('')
  const [projectDesc, setProjectDesc] = useState('')
  const [githubBranch, setGithubBranch] = useState('main')
  const [zipFile, setZipFile] = useState(null)
  const [singleFile, setSingleFile] = useState(null)
  const [gitUrl, setGitUrl] = useState('')
  const [customInfo, setCustomInfo] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState(defaultSteps)
  const navigate = useNavigate()
  const { addToast } = useAuth()

  const simulateSteps = () => {
    return new Promise((resolve) => {
      let i = 0
      const tick = () => {
        setSteps(prev => prev.map((s, idx) => ({
          ...s,
          done: idx < i,
          active: idx === i,
        })))
        i++
        if (i <= defaultSteps.length) setTimeout(tick, 1000)
        else resolve()
      }
      tick()
    })
  }

  const handleSubmit = async () => {
    if (!projectName.trim()) {
      addToast('Please enter a project name', 'error')
      return
    }

    setLoading(true)
    setSteps(defaultSteps)
    const stepsPromise = simulateSteps()

    try {
      let res;
      if (active === 'upload') {
        if (!zipFile) { addToast('Please upload a ZIP file', 'error'); setLoading(false); return }
        if (!customInfo.trim()) { addToast('Please provide additional project details', 'error'); setLoading(false); return }
        const fd = new FormData()
        fd.append('folder', zipFile)
        fd.append('name', projectName)
        fd.append('description', projectDesc)
        fd.append('source_type', 'folder')
        // custom_info is mandatory for folder uploads (backend enforced)
        try {
          JSON.parse(customInfo)
          fd.append('custom_info', customInfo)
        } catch {
          fd.append('custom_info', JSON.stringify({ details: customInfo }))
        }
        res = await analyzeFolder(fd)
      } else if (active === 'single') {
        if (!singleFile) { addToast('Please upload a .py file', 'error'); setLoading(false); return }
        const fd = new FormData()
        fd.append('file', singleFile)
        fd.append('name', projectName)
        fd.append('description', projectDesc)
        fd.append('source_type', 'file')
        res = await analyzeFile(fd, true)
      } else {
        if (!gitUrl.trim()) { addToast('Please enter a Git URL', 'error'); setLoading(false); return }
        res = await importFromGithub({ 
          repo_url: gitUrl, 
          name: projectName,
          description: projectDesc,
          github_branch: githubBranch,
          source_type: 'github'
        })
      }

      await stepsPromise
      addToast('Documentation generated!', 'success')
      const projectId = res.data.project_id || res.data.id
      navigate(`/output/${projectId}`)
    } catch (err) {
      addToast(err.response?.data?.error || 'Generation failed', 'error')
      setLoading(false)
      setSteps(defaultSteps)
    }
  }

  return (
    <div className="relative z-10">
      <Navbar />
      <div className="min-h-screen bg-bg-primary py-16 px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="font-display font-bold text-4xl text-ink-primary mb-2">Generate Documentation</h1>
          <p className="text-ink-secondary mb-10">Upload your Django project and let AI do the heavy lifting.</p>

          {/* Project Details */}
          <div className="glass-card p-6 mb-8 space-y-4 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-ink-muted uppercase tracking-widest mb-2">Project Name</label>
                <input 
                  value={projectName} 
                  onChange={e => setProjectName(e.target.value)} 
                  className="input-field" 
                  placeholder="e.g. My Awesome API" 
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-ink-muted uppercase tracking-widest mb-2">Short Description (Optional)</label>
                <input 
                  value={projectDesc} 
                  onChange={e => setProjectDesc(e.target.value)} 
                  className="input-field" 
                  placeholder="e.g. Documentation for the blog module" 
                />
              </div>
            </div>
          </div>

          {/* Tab selector */}
          <div className="flex gap-1 bg-bg-surface border border-border rounded-xl p-1 mb-8">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setActive(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${active === tab.id ? 'bg-accent text-white shadow-glow' : 'text-ink-secondary hover:text-ink-primary'}`}>
                <tab.icon className="w-4 h-4" /> {tab.label}
              </button>
            ))}
          </div>

          {/* Single File Tab */}
          {active === 'single' && (
            <div className="animate-fade-in">
              <label className={`border-2 border-dashed rounded-2xl p-16 text-center transition-all duration-200 cursor-pointer block ${isDragging ? 'border-accent bg-accent/5 shadow-glow' : 'border-border hover:border-accent/50 hover:bg-bg-surface'}`}
                onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={e => { 
                  e.preventDefault(); 
                  setIsDragging(false); 
                  const file = e.dataTransfer.files[0];
                  setSingleFile(file);
                  if (!projectName) setProjectName(file.name.split('.')[0]);
                }}>
                <input type="file" className="hidden" accept=".py" onChange={e => {
                  const file = e.target.files[0];
                  setSingleFile(file);
                  if (!projectName) setProjectName(file.name.split('.')[0]);
                }} />
                <p className="text-accent mb-3"><IconFile className="w-12 h-12 mx-auto" /></p>
                <p className="text-ink-primary font-display font-bold">
                  {singleFile ? singleFile.name : 'Drop a .py file here or click to browse'}
                </p>
                <p className="text-ink-muted text-sm mt-1">Select a single Python file</p>
              </label>
            </div>
          )}
          {/* Project ZIP Tab */}
          {active === 'upload' && (
            <div className="animate-fade-in space-y-4">
              <label className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer block ${isDragging ? 'border-accent bg-accent/5 shadow-glow' : 'border-border hover:border-accent/50 hover:bg-bg-surface'}`}
                onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={e => { 
                  e.preventDefault(); 
                  setIsDragging(false); 
                  const file = e.dataTransfer.files[0];
                  setZipFile(file);
                  if (!projectName) setProjectName(file.name.split('.')[0]);
                }}>
                <input type="file" className="hidden" accept=".zip" onChange={e => {
                  const file = e.target.files[0];
                  setZipFile(file);
                  if (!projectName) setProjectName(file.name.split('.')[0]);
                }} />
                <p className="text-accent mb-3"><IconArchive className="w-12 h-12 mx-auto" /></p>
                <p className="text-ink-primary font-display font-bold">
                  {zipFile ? zipFile.name : 'Drop project ZIP here or click to browse'}
                </p>
                <p className="text-ink-muted text-sm mt-1">
                  {zipFile ? `${(zipFile.size / 1024 / 1024).toFixed(2)} MB` : 'Maximum 50MB (.zip only)'}
                </p>
              </label>

              {/* custom_info — mandatory for folder uploads */}
              <div className="glass-card p-5">
                <label className="block text-xs font-mono text-ink-muted uppercase tracking-widest mb-2">
                  Additional Project Details <span className="text-danger">*</span>
                </label>
                <textarea
                  value={customInfo}
                  onChange={e => setCustomInfo(e.target.value)}
                  rows={4}
                  className="input-field resize-none font-body"
                  placeholder={`Describe your project's purpose, main features, tech stack, etc.\n\nExample: This is a Django REST API for a task management app. It uses Celery for async jobs, Redis as broker, PostgreSQL for storage, and JWT for auth.`}
                />
                <p className="text-[11px] text-ink-muted mt-2">
                  <IconWarning className="w-3 h-3 inline mr-1" /> Required — helps the AI generate much more accurate documentation.
                  You can write plain text or valid JSON.
                </p>
              </div>
            </div>
          )}


          {/* Git Tab */}
          {active === 'git' && (
            <div className="animate-fade-in space-y-4">
              <div className="glass-card p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-ink-secondary mb-2">Repository URL</label>
                    <input value={gitUrl} onChange={e => setGitUrl(e.target.value)} className="input-field" placeholder="https://github.com/user/repo.git" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-ink-secondary mb-2">Branch</label>
                    <input value={githubBranch} onChange={e => setGithubBranch(e.target.value)} className="input-field" placeholder="main" />
                  </div>
                </div>
                <p className="text-ink-muted text-xs mt-3">We will clone the repository and analyze all .py files.</p>
              </div>
            </div>
          )}

          {/* Submit */}
          {!loading && (
            <button id="generate-btn" onClick={handleSubmit} className="btn-accent w-full py-4 text-base mt-8 shadow-glow">
              {active === 'git' ? 'Connect & Generate →' : 'Upload & Generate →'}
            </button>
          )}

          {/* Progress */}
          {loading && (
            <div className="mt-8">
              <StepIndicator steps={steps} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
