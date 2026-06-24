import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { analyzeFile, analyzeFolder, importFromGithub, getGithubRepos, getGithubRepoFolders, getPublicRepoInfo, getPublicRepoFolders, importPublicRepo, getProjects, deleteProject } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import StepIndicator from '../components/StepIndicator'
import { IconFile, IconArchive, IconLink, IconFolder, IconChevron } from '../components/Icons'

const tabs = [
  { id: 'upload', label: 'Local Directory (.zip)', icon: IconArchive },
  { id: 'git',    label: 'Cloud Git System',        icon: IconLink },
  { id: 'single', label: 'Isolated Module (.py)',   icon: IconFile },
]

const stepsData = [
  { label: 'Initializing IO Stream Pipelines...', done: false, active: false },
  { label: 'Decomposing Python Syntax Trees (AST)...', done: false, active: false },
  { label: 'Mapping Class Interfaces & Serializers...', done: false, active: false },
  { label: 'Compiling API Schemas & Document Trees...', done: false, active: false },
  { label: 'Finalizing Output Buffers...', done: false, active: false },
]

export default function InputPython() {
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
  const [steps, setSteps] = useState(stepsData)
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [branches, setBranches] = useState([])
  const [selectedBranch, setSelectedBranch] = useState('')
  const [folders, setFolders] = useState([])
  const [selectedFolder, setSelectedFolder] = useState('/')
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [showRepoDropdown, setShowRepoDropdown] = useState(false)
  const [showFolderDropdown, setShowFolderDropdown] = useState(false)
  const [githubConnected, setGithubConnected] = useState(false)
  const [publicRepoUrl, setPublicRepoUrl] = useState('')
  const [publicRepoInfo, setPublicRepoInfo] = useState(null)
  const [publicFolders, setPublicFolders] = useState([])
  const [selectedPublicFolder, setSelectedPublicFolder] = useState('/')
  const [selectedPublicBranch, setSelectedPublicBranch] = useState('')
  const [loadingPublicRepo, setLoadingPublicRepo] = useState(false)
  const [loadingPublicFolders, setLoadingPublicFolders] = useState(false)
  const [showPublicFolderDropdown, setShowPublicFolderDropdown] = useState(false)
  const [showConflictModal, setShowConflictModal] = useState(false)
  const [conflictData, setConflictData] = useState(null)
  const [showBranchDropdown, setShowBranchDropdown] = useState(false)
  const nameInputRef = useRef(null)
  const navigate = useNavigate()
  const { addToast } = useAuth()

  useEffect(() => {
    if (active === 'git') fetchRepos()
  }, [active])

  const fetchRepos = async () => {
    setLoadingRepos(true)
    try {
      const res = await getGithubRepos()
      setRepos(res.data || [])
      setGithubConnected(true)
    } catch { setGithubConnected(false) }
    finally { setLoadingRepos(false) }
  }

  const fetchFolders = async (repoFullName, branch) => {
    setLoadingFolders(true)
    try {
      const res = await getGithubRepoFolders(repoFullName, branch)
      setFolders(res.data || [])
    } catch { addToast('Failed to load folders', 'error') }
    finally { setLoadingFolders(false) }
  }

  const handleRepoSelect = (repo) => {
    setSelectedRepo(repo)
    setShowRepoDropdown(false)
    setGitUrl(repo.url)
    if (!projectName) setProjectName(repo.full_name.split('/')[1])
    if (repo.branches_url && repo.default_branch) {
      setSelectedBranch(repo.default_branch)
      setGithubBranch(repo.default_branch)
      fetchFolders(repo.full_name, repo.default_branch)
    }
  }

  const handleFolderSelect = (folder) => {
    setSelectedFolder(folder.path || folder.name)
    setShowFolderDropdown(false)
  }

  const fetchPublicRepoInfo = async () => {
    if (!publicRepoUrl.trim()) return
    setLoadingPublicRepo(true)
    try {
      const res = await getPublicRepoInfo(publicRepoUrl)
      setPublicRepoInfo(res.data)
      if (!projectName) setProjectName(res.data.full_name.split('/')[1])
      setSelectedPublicBranch(res.data.default_branch || 'main')
      fetchPublicFolders(res.data.full_name, res.data.default_branch)
    } catch { addToast('Failed to fetch public repo info', 'error') }
    finally { setLoadingPublicRepo(false) }
  }

  const fetchPublicFolders = async (fullName, branch) => {
    setLoadingPublicFolders(true)
    try {
      const res = await getPublicRepoFolders(fullName, branch)
      setPublicFolders(res.data || [])
    } catch { setPublicFolders([]) }
    finally { setLoadingPublicFolders(false) }
  }

  const simulateSteps = () => {
    return new Promise((resolve) => {
      let i = 0
      const tick = () => {
        setSteps(prev => prev.map((s, idx) => ({
          ...s, done: idx < i, active: idx === i,
        })))
        i++
        if (i <= stepsData.length) setTimeout(tick, 1000)
        else resolve()
      }
      tick()
    })
  }

  const checkConflicts = async () => {
    try {
      const res = await getProjects({ page_size: 100 })
      const existing = res.data?.results || []
      const nameTrimmed = projectName.trim().toLowerCase()
      const nameConflict = existing.find(p => p.name.toLowerCase() === nameTrimmed)
      let repoConflict = null
      if (active === 'git') {
        let repoUrl = null
        if (selectedRepo) repoUrl = `https://github.com/${selectedRepo.full_name}`
        else if (publicRepoUrl.trim()) repoUrl = publicRepoUrl.trim().replace(/\.git$/, '')
        if (repoUrl) repoConflict = existing.find(p => p.github_url && p.github_url.replace(/\.git$/, '') === repoUrl)
      }
      const cp = nameConflict || repoConflict
      if (cp) { setConflictData({ existingProject: cp }); setShowConflictModal(true); return true }
    } catch {}
    return false
  }

  const doSubmit = async () => {
    setLoading(true)
    setSteps(stepsData)
    const stepsPromise = simulateSteps()

    try {
      let res
      if (active === 'upload') {
        if (!zipFile) { addToast('Target directory archive (.zip) required', 'error'); setLoading(false); return }
        if (!customInfo.trim()) { addToast('Context attributes are required', 'error'); setLoading(false); return }
        const fd = new FormData()
        fd.append('folder', zipFile)
        fd.append('name', projectName)
        fd.append('description', projectDesc)
        fd.append('source_type', 'folder')
        fd.append('custom_info', JSON.stringify({ details: customInfo }))
        res = await analyzeFolder(fd)
      } else if (active === 'single') {
        if (!singleFile) { addToast('Source .py file required', 'error'); setLoading(false); return }
        const fd = new FormData()
        fd.append('file', singleFile)
        fd.append('name', projectName)
        fd.append('description', projectDesc)
        fd.append('source_type', 'file')
        res = await analyzeFile(fd)
      } else if (active === 'git') {
        if (selectedRepo) {
          if (!publicRepoUrl.trim() && !selectedRepo) { addToast('Select a repository', 'error'); setLoading(false); return }
          res = await importFromGithub({
            full_name: selectedRepo.full_name,
            branch: selectedBranch || githubBranch,
            folder_path: selectedFolder,
            name: projectName,
            description: projectDesc,
            custom_info: customInfo ? { details: customInfo } : {},
          })
        } else if (publicRepoUrl.trim()) {
          res = await importPublicRepo({
            url: publicRepoUrl.trim(),
            branch: selectedPublicBranch,
            folder_path: selectedPublicFolder,
            name: projectName,
            description: projectDesc,
            custom_info: customInfo ? { details: customInfo } : {},
          })
        } else { addToast('Select a repository or paste a Git URL', 'error'); setLoading(false); return }
      }

      await stepsPromise
      addToast('Document parsing finished.', 'success')
      navigate(`/output/${res.data.project_id}`)
    } catch (err) {
      addToast('Failed compiling AST tree.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!projectName.trim()) { addToast('Please input project name.', 'error'); return }
    const conflicted = await checkConflicts()
    if (conflicted) return
    doSubmit()
  }

  const resolveConflict = () => {
    setShowConflictModal(false)
    if (!conflictData) return
    deleteProject(conflictData.existingProject.id).then(() => {
      addToast('Existing project removed.', 'success')
      doSubmit()
    }).catch(() => addToast('Failed to remove existing project.', 'error'))
    setConflictData(null)
  }

  const liveManifestJSON = JSON.stringify({
    compiler_target: active.toUpperCase(),
    workspace_declaration: {
      name: projectName || 'untitled_ast',
      description: projectDesc || 'No context specified',
      source_io: active === 'upload' ? zipFile?.name || null : active === 'single' ? singleFile?.name || null : gitUrl || publicRepoUrl || null,
      custom_attributes: customInfo ? { details: customInfo } : null,
      parser_mode: 'PyDocAI (AST-based)',
      git_environment: active === 'git' ? {
        branch: selectedRepo ? selectedBranch : selectedPublicBranch || 'main',
        target_directory: selectedRepo ? selectedFolder : selectedPublicFolder,
      } : null,
    },
  }, null, 2)

  return (
    <div className="relative z-10 bg-bg-primary min-h-screen text-ink-primary font-body">
      <Helmet>
        <title>New Generation — Python Doc</title>
        <meta name="description" content="Generate AI-powered documentation for your Django or Python project. Upload a .zip, paste a GitHub URL, or upload a single .py file." />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Navbar />

      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 flex flex-col lg:flex-row gap-6 sm:gap-8">

        {/* Left Side: Form */}
        <section className="flex-1 space-y-4 sm:space-y-6">
          <div>
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-display font-bold text-ink-primary">PyDocAI &mdash; Python Documentation</h1>
            <p className="text-xs text-ink-secondary mt-1">Upload your Python project. AST-parsed, full documentation.</p>
          </div>

          {loading ? (
            <StepIndicator steps={steps} />
          ) : (
            <>
              <div className="glass-card p-1 flex gap-1">
                {tabs.map(tab => (
                  <button key={tab.id} onClick={() => setActive(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-mono transition-all flex-1 justify-center ${active === tab.id ? 'bg-accent-blue/10 text-accent-blue font-semibold' : 'text-ink-muted hover:text-ink-primary'}`}
                  ><tab.icon className="w-4 h-4" />{tab.label}</button>
                ))}
              </div>

              {active === 'upload' && (
                <div className="glass-card p-6 space-y-5">
                  <div>
                    <label htmlFor="py-name" className="block text-xs font-mono text-ink-secondary mb-1.5">Project Name</label>
                    <input id="py-name" value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-sm w-full" placeholder="my-django-app" />
                  </div>
                  <div>
                    <label htmlFor="py-desc" className="block text-xs font-mono text-ink-secondary mb-1.5">Description</label>
                    <input id="py-desc" value={projectDesc} onChange={e => setProjectDesc(e.target.value)} className="input-field text-sm w-full" placeholder="What does this project do?" />
                  </div>
                  <div>
                    <label htmlFor="py-context" className="block text-xs font-mono text-ink-secondary mb-1.5">Context Attributes</label>
                    <textarea id="py-context" value={customInfo} onChange={e => setCustomInfo(e.target.value)} rows={3} className="input-field text-sm w-full resize-none" placeholder="Model name, endpoint prefix, custom behaviors, etc." />
                  </div>
                  <div
                    className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer ${isDragging ? 'border-accent-blue bg-accent-blue/5' : 'border-border hover:border-accent-blue/50 hover:bg-bg-surface'}`}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={e => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files[0]; if (f && f.name.endsWith('.zip')) { setZipFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) } else { addToast('Please upload a .zip file', 'error') } }}
                    onClick={() => document.getElementById('zip-input')?.click()}
                  >
                    <input id="zip-input" type="file" className="hidden" accept=".zip" onChange={e => { const f = e.target.files[0]; setZipFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) }} />
                    {zipFile ? (
                      <><IconArchive className="w-10 h-10 mx-auto mb-3 text-accent-blue" /><p className="text-sm font-mono">{zipFile.name}</p><p className="text-xs text-ink-muted mt-1">{(zipFile.size / 1024 / 1024).toFixed(2)} MB</p></>
                    ) : (
                      <><IconArchive className="w-10 h-10 mx-auto mb-3 text-ink-muted" /><p className="text-sm font-mono text-ink-secondary">Drop your .zip here or browse</p><p className="text-xs text-ink-muted mt-1">Upload a ZIP of your Django project folder</p></>
                    )}
                  </div>
                </div>
              )}

              {active === 'single' && (
                <div className="glass-card p-6 space-y-5">
                  <div>
                    <label htmlFor="py-single-name" className="block text-xs font-mono text-ink-secondary mb-1.5">Project Name</label>
                    <input id="py-single-name" value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-sm w-full" placeholder="my-module" />
                  </div>
                  <div>
                    <label htmlFor="py-single-desc" className="block text-xs font-mono text-ink-secondary mb-1.5">Description</label>
                    <input id="py-single-desc" value={projectDesc} onChange={e => setProjectDesc(e.target.value)} className="input-field text-sm w-full" placeholder="What does this module do?" />
                  </div>
                  <div
                    className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer ${isDragging ? 'border-accent-blue bg-accent-blue/5' : 'border-border hover:border-accent-blue/50 hover:bg-bg-surface'}`}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={e => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files[0]; setSingleFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) }}
                    onClick={() => document.getElementById('py-input')?.click()}
                  >
                    <input id="py-input" type="file" className="hidden" accept=".py" onChange={e => { const f = e.target.files[0]; setSingleFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) }} />
                    {singleFile ? (
                      <><IconFile className="w-10 h-10 mx-auto mb-3 text-accent-blue" /><p className="text-sm font-mono">{singleFile.name}</p><p className="text-xs text-ink-muted mt-1">{(singleFile.size / 1024).toFixed(1)} KB</p></>
                    ) : (
                      <><IconFile className="w-10 h-10 mx-auto mb-3 text-ink-muted" /><p className="text-sm font-mono text-ink-secondary">Drop a .py file here or browse</p><p className="text-xs text-ink-muted mt-1">Single Python module</p></>
                    )}
                  </div>
                </div>
              )}

              {active === 'git' && (
                <div className="glass-card p-6 space-y-5">
                  <div>
                    <label htmlFor="py-git-name" className="block text-xs font-mono text-ink-secondary mb-1.5">Project Name</label>
                    <input id="py-git-name" value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-sm w-full" placeholder="my-repo" />
                  </div>

                  <div className="flex gap-2">
                    <button onClick={() => { setPublicRepoUrl(''); setPublicRepoInfo(null); setSelectedRepo(null) }}
                      className={`px-4 py-2 rounded-lg text-xs font-mono transition-all ${publicRepoInfo || (!selectedRepo && !publicRepoUrl) ? 'bg-accent-blue/10 text-accent-blue font-semibold' : 'text-ink-muted'}`}>Public Repository</button>
                    <button onClick={() => setSelectedRepo(null)}
                      className={`px-4 py-2 rounded-lg text-xs font-mono transition-all ${selectedRepo ? 'bg-accent-blue/10 text-accent-blue font-semibold' : 'text-ink-muted'}`}>My Repositories</button>
                  </div>

                  {selectedRepo ? (
                    <div className="space-y-3">
                      <div className="relative">
                        <button onClick={() => setShowRepoDropdown(!showRepoDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                          <span>{selectedRepo.full_name}</span>
                          <IconChevron className={`w-3 h-3 transition-transform ${showRepoDropdown ? 'rotate-180' : ''}`} />
                        </button>
                        {showRepoDropdown && (
                          <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-xl">
                            {repos.filter(r => r.full_name !== selectedRepo.full_name).map((r, i) => (
                              <button key={i} onClick={() => handleRepoSelect(r)} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{r.full_name}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <button onClick={() => setShowBranchDropdown(!showBranchDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                            <span>{selectedBranch || githubBranch}</span>
                            <IconChevron className={`w-3 h-3 transition-transform ${showBranchDropdown ? 'rotate-180' : ''}`} />
                          </button>
                          {showBranchDropdown && (
                            <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-xl">
                              {[selectedRepo.default_branch || 'main', 'develop', 'staging'].filter(Boolean).map((b, i) => (
                                <button key={i} onClick={() => { setSelectedBranch(b); setGithubBranch(b); setShowBranchDropdown(false); fetchFolders(selectedRepo.full_name, b) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{b}</button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="relative">
                        <button onClick={() => setShowFolderDropdown(!showFolderDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                          <span className="flex items-center gap-2"><IconFolder className="w-3.5 h-3.5 text-ink-muted" />{selectedFolder === '/' ? 'Entire repository' : selectedFolder}</span>
                          <IconChevron className={`w-3 h-3 transition-transform ${showFolderDropdown ? 'rotate-180' : ''}`} />
                        </button>
                        {showFolderDropdown && (
                          <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-xl">
                            <button onClick={() => { setSelectedFolder('/'); setShowFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">Entire repository</button>
                            {loadingFolders ? <div className="px-3 py-2 text-xs text-ink-muted">Loading folders...</div> : folders.filter(f => f.path !== '/').map((f, i) => (
                              <button key={i} onClick={() => { handleFolderSelect(f); setShowFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{f.path}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => { setSelectedRepo(null); setSelectedBranch(''); setGithubBranch('main'); setSelectedFolder('/'); setGitUrl('') }} className="btn-ghost text-xs font-mono flex-1">Change Repository</button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        <input value={publicRepoUrl} onChange={e => { setPublicRepoUrl(e.target.value); setPublicRepoInfo(null) }} className="input-field text-sm flex-1" placeholder="https://github.com/owner/repo" />
                        <button onClick={fetchPublicRepoInfo} disabled={loadingPublicRepo} className="btn-ghost text-xs font-mono px-4">{loadingPublicRepo ? '...' : 'Fetch'}</button>
                      </div>
                      {loadingRepos ? (
                        <p className="text-sm text-ink-muted text-center py-4">Loading your repositories...</p>
                      ) : !githubConnected ? (
                        <div className="text-center py-4 space-y-2 bg-bg-surface rounded-lg border border-border">
                          <p className="text-sm text-ink-muted">Connect your GitHub account for private repos</p>
                          <a href="/auth/github/" className="btn-accent text-xs font-mono inline-block px-4 py-2">Connect GitHub</a>
                        </div>
                      ) : (
                        <div className="relative">
                          <button onClick={() => setShowRepoDropdown(!showRepoDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                            <span>Select a repository...</span>
                            <IconChevron className={`w-3 h-3 transition-transform ${showRepoDropdown ? 'rotate-180' : ''}`} />
                          </button>
                          {showRepoDropdown && (
                            <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-xl">
                              {repos.map((r, i) => (
                                <button key={i} onClick={() => handleRepoSelect(r)} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{r.full_name}</button>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      {publicRepoInfo && (
                        <div className="bg-bg-surface rounded-xl p-3 border border-border space-y-2">
                          <p className="text-sm font-semibold">{publicRepoInfo.full_name}</p>
                          {publicRepoInfo.description && <p className="text-xs text-ink-muted">{publicRepoInfo.description}</p>}
                          <div className="flex gap-4 text-[10px] text-ink-muted font-mono"><span>Branch: {selectedPublicBranch}</span><span>{publicRepoInfo.language}</span></div>
                          <div className="relative">
                            <button onClick={() => setShowPublicFolderDropdown(!showPublicFolderDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                              <span className="flex items-center gap-2"><IconFolder className="w-3.5 h-3.5 text-ink-muted" />{selectedPublicFolder === '/' ? 'Entire repository' : selectedPublicFolder}</span>
                              <IconChevron className={`w-3 h-3 transition-transform ${showPublicFolderDropdown ? 'rotate-180' : ''}`} />
                            </button>
                            {showPublicFolderDropdown && (
                              <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-xl">
                                <button onClick={() => { setSelectedPublicFolder('/'); setShowPublicFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">Entire repository</button>
                                {loadingPublicFolders ? <div className="px-3 py-2 text-xs text-ink-muted">Loading folders...</div> : publicFolders.filter(f => f.path !== '/').map((f, i) => (
                                  <button key={i} onClick={() => { setSelectedPublicFolder(f.path); setShowPublicFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{f.path}</button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <button onClick={handleSubmit} disabled={loading} className="btn-accent w-full py-4 text-xs font-mono uppercase tracking-widest shadow-md disabled:opacity-50">
                {loading ? 'Processing...' : 'Compile Documentation'}
              </button>
            </>
          )}
        </section>

        {/* Right Side: Manifest Preview */}
        <section className="w-full lg:w-96 flex-shrink-0 flex-col hidden lg:flex">
          <div className="glass-card bg-code border border-border rounded-xl flex-1 flex flex-col overflow-hidden shadow-2xl h-[480px]">
            <div className="bg-bg-surface px-4 py-2.5 border-b border-border flex items-center justify-between">
              <span className="text-[10px] font-mono text-ink-secondary uppercase tracking-widest flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-accent-blue" /> pydoc_compilation_manifest.json
              </span>
              <span className="text-[10px] font-mono text-ink-muted">JSON</span>
            </div>
            <pre className="p-4 font-mono text-xs text-accent-blue overflow-auto flex-1 leading-relaxed">
              <code>{liveManifestJSON}</code>
            </pre>
          </div>
        </section>

      </main>

      {showConflictModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-elevated border border-border rounded-2xl shadow-2xl max-w-sm w-full mx-4 p-8 space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-warning/20 border border-warning/30 flex items-center justify-center text-warning text-lg font-bold">!</div>
              <div>
                <h3 className="text-base font-display font-bold text-ink-primary">Project Already Exists</h3>
                <p className="text-[11px] text-ink-muted font-mono">Same name or repo detected</p>
              </div>
            </div>
            <p className="text-xs text-ink-secondary font-mono leading-relaxed">
              A project with the same name or repository already exists. Delete the existing project and continue?
            </p>
            <div className="flex gap-3">
              <button onClick={() => setShowConflictModal(false)} className="flex-1 py-2.5 px-4 rounded-xl border border-border bg-bg-surface hover:bg-bg-primary text-ink-primary text-xs font-mono transition-all">Cancel</button>
              <button onClick={resolveConflict} className="flex-1 py-2.5 px-4 rounded-xl bg-danger hover:bg-danger/80 text-white text-xs font-mono transition-all">Replace</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
