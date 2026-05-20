import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeFile, analyzeFolder, importFromGithub, getGithubRepos, getGithubRepoFolders } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import StepIndicator from '../components/StepIndicator'
import { IconFile, IconArchive, IconLink, IconWarning, IconFolder, IconChevron, IconRefresh } from '../components/Icons'

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
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [branches, setBranches] = useState([])
  const [selectedBranch, setSelectedBranch] = useState('')
  const [folders, setFolders] = useState([])
  const [selectedFolder, setSelectedFolder] = useState('/')
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [showRepoDropdown, setShowRepoDropdown] = useState(false)
  const [showBranchDropdown, setShowBranchDropdown] = useState(false)
  const [showFolderDropdown, setShowFolderDropdown] = useState(false)
  const navigate = useNavigate()
  const { addToast } = useAuth()

  useEffect(() => {
    if (active === 'git') {
      fetchRepos()
    }
  }, [active])

  const fetchRepos = async () => {
    setLoadingRepos(true)
    try {
      const res = await getGithubRepos()
      setRepos(res.data || [])
    } catch (err) {
      if (err.response?.status === 400) {
        addToast('Please connect your GitHub account first', 'error')
      }
    } finally {
      setLoadingRepos(false)
    }
  }

  const fetchFolders = async (repoFullName, branch) => {
    setLoadingFolders(true)
    try {
      const res = await getGithubRepoFolders(repoFullName, branch)
      setFolders(res.data || [])
    } catch (err) {
      addToast('Failed to load folders', 'error')
    } finally {
      setLoadingFolders(false)
    }
  }

  const handleRepoSelect = (repo) => {
    setSelectedRepo(repo)
    setShowRepoDropdown(false)
    setGitUrl(repo.html_url)
    if (repo.branches_url && repo.default_branch) {
      setSelectedBranch(repo.default_branch)
      setGithubBranch(repo.default_branch)
      fetchFolders(repo.full_name, repo.default_branch)
    }
  }

  const handleBranchSelect = (branch) => {
    setSelectedBranch(branch)
    setGithubBranch(branch)
    setShowBranchDropdown(false)
    if (selectedRepo) {
      fetchFolders(selectedRepo.full_name, branch)
    }
  }

  const handleFolderSelect = (folder) => {
    setSelectedFolder(folder.path || folder.name)
    setShowFolderDropdown(false)
  }

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
        if (!selectedRepo) { addToast('Please select a repository', 'error'); setLoading(false); return }
        res = await importFromGithub({
          full_name: selectedRepo.full_name,
          branch: selectedBranch || githubBranch,
          folder_path: selectedFolder || '/',
          name: projectName,
          description: projectDesc,
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
              <div className="glass-card p-6 space-y-4">
                {repos.length === 0 && !loadingRepos && (
                  <div className="mb-4 p-4 bg-bg-surface rounded-lg border border-border">
                    <p className="text-sm text-ink-secondary mb-3">Connect your GitHub account to import repositories</p>
                    <a
                      href={`https://github.com/login/oauth/authorize?client_id=${import.meta.env.VITE_GITHUB_CLIENT_ID || ''}&redirect_uri=${window.location.origin}/auth/github/callback&scope=repo`}
                      className="inline-flex items-center gap-2 bg-ink-primary text-white px-4 py-2 rounded-lg hover:bg-ink-secondary transition-colors text-sm font-medium"
                    >
                      <IconLink className="w-4 h-4" />
                      Connect GitHub
                    </a>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-ink-secondary mb-2">Repository</label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setShowRepoDropdown(!showRepoDropdown)}
                      className="w-full flex items-center justify-between input-field"
                    >
                      <span className={selectedRepo ? 'text-ink-primary' : 'text-ink-muted'}>
                        {selectedRepo ? selectedRepo.full_name : 'Select a repository...'}
                      </span>
                      <IconChevron className="w-4 h-4 text-ink-muted" />
                    </button>
                    {showRepoDropdown && (
                      <div className="absolute z-50 w-full mt-1 bg-bg-surface border border-border rounded-lg shadow-lg max-h-64 overflow-y-auto">
                        {loadingRepos ? (
                          <div className="p-4 text-center text-ink-muted">Loading repositories...</div>
                        ) : repos.length === 0 ? (
                          <div className="p-4 text-center text-ink-muted">
                            No repositories found. Connect your GitHub account first.
                          </div>
                        ) : (
                          repos.map(repo => (
                            <button
                              key={repo.id}
                              onClick={() => handleRepoSelect(repo)}
                              className={`w-full text-left px-4 py-3 hover:bg-bg-primary transition-colors ${selectedRepo?.id === repo.id ? 'bg-accent/10' : ''}`}
                            >
                              <div className="font-medium text-ink-primary">{repo.name}</div>
                              <div className="text-xs text-ink-muted">{repo.full_name}</div>
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {selectedRepo && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-ink-secondary mb-2">Branch</label>
                      <div className="flex gap-2">
                        <input
                          value={selectedBranch || ''}
                          onChange={e => {
                            setSelectedBranch(e.target.value)
                            setGithubBranch(e.target.value)
                          }}
                          className="input-field flex-1"
                          placeholder={selectedRepo.default_branch || 'main'}
                        />
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedBranch(selectedRepo.default_branch)
                            setGithubBranch(selectedRepo.default_branch)
                            fetchFolders(selectedRepo.full_name, selectedRepo.default_branch)
                          }}
                          className="px-3 py-2 bg-bg-surface border border-border rounded-lg text-sm text-ink-secondary hover:text-ink-primary transition-colors"
                          title={`Use default: ${selectedRepo.default_branch}`}
                        >
                          Default
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-ink-secondary mb-2">Folder Path</label>
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setShowFolderDropdown(!showFolderDropdown)}
                          className="w-full flex items-center justify-between input-field"
                        >
                          <span className="text-ink-primary flex items-center gap-2">
                            <IconFolder className="w-4 h-4" />
                            {selectedFolder || '/'}
                          </span>
                          <IconChevron className="w-4 h-4 text-ink-muted" />
                        </button>
                        {showFolderDropdown && (
                          <div className="absolute z-50 w-full mt-1 bg-bg-surface border border-border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                            <button
                              onClick={() => handleFolderSelect({ path: '/' })}
                              className={`w-full text-left px-4 py-2 hover:bg-bg-primary flex items-center gap-2 ${selectedFolder === '/' ? 'bg-accent/10' : ''}`}
                            >
                              <IconFolder className="w-4 h-4" /> / (root)
                            </button>
                            {loadingFolders ? (
                              <div className="px-4 py-2 text-ink-muted text-sm">Loading folders...</div>
                            ) : (
                              folders.filter(f => f.type === 'tree').map(folder => (
                                <button
                                  key={folder.path}
                                  onClick={() => handleFolderSelect(folder)}
                                  className={`w-full text-left px-4 py-2 hover:bg-bg-primary flex items-center gap-2 ${selectedFolder === folder.path ? 'bg-accent/10' : ''}`}
                                >
                                  <IconFolder className="w-4 h-4 text-ink-muted" />
                                  <span className="text-ink-primary text-sm">{folder.path}</span>
                                </button>
                              ))
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
              {!selectedRepo && (
                <button onClick={fetchRepos} className="flex items-center gap-2 text-accent hover:text-accent/80 text-sm">
                  <IconRefresh className="w-4 h-4" /> Refresh repositories
                </button>
              )}
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
