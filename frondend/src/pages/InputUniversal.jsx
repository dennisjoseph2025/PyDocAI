import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { uploadUniversal, getGithubRepos, getGithubRepoFolders, getPublicRepoInfo, getPublicRepoFolders } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import StepIndicator from '../components/StepIndicator'
import { IconFile, IconArchive, IconLink, IconFolder, IconChevron } from '../components/Icons'

const tabs = [
  { id: 'upload', label: 'Local Directory (.zip)', icon: IconArchive },
  { id: 'file',   label: 'Single File',             icon: IconFile },
  { id: 'git',    label: 'GitHub Repository',       icon: IconLink },
]

const stepsData = [
  { label: 'Scanning project structure...', done: false, active: false },
  { label: 'Analyzing source files & dependencies...', done: false, active: false },
  { label: 'Extracting APIs & interfaces...', done: false, active: false },
  { label: 'Building documentation tree...', done: false, active: false },
  { label: 'Finalizing output...', done: false, active: false },
]

export default function InputUniversal() {
  const [active, setActive] = useState('upload')
  const [projectName, setProjectName] = useState('')
  const [projectDesc, setProjectDesc] = useState('')
  const [githubBranch, setGithubBranch] = useState('main')
  const [zipFile, setZipFile] = useState(null)
  const [singleFile, setSingleFile] = useState(null)
  const [gitUrl, setGitUrl] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState(stepsData)
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [selectedBranch, setSelectedBranch] = useState('')
  const [folders, setFolders] = useState([])
  const [selectedFolder, setSelectedFolder] = useState('/')
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [showRepoDropdown, setShowRepoDropdown] = useState(false)
  const [showBranchDropdown, setShowBranchDropdown] = useState(false)
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

  const handleSubmit = async () => {
    if (!projectName.trim()) { addToast('Please input project name.', 'error'); return }
    setLoading(true)
    setSteps(stepsData)
    const stepsPromise = simulateSteps()

    try {
      const fd = new FormData()
      fd.append('name', projectName)
      fd.append('description', projectDesc)
      fd.append('mode', 'universal')

      if (active === 'upload') {
        if (!zipFile) { addToast('Please select a .zip file', 'error'); setLoading(false); return }
        fd.append('file', zipFile)
      } else if (active === 'file') {
        if (!singleFile) { addToast('Please select a file', 'error'); setLoading(false); return }
        fd.append('file', singleFile)
      } else if (active === 'git') {
        if (selectedRepo) {
          fd.append('github_url', `https://github.com/${selectedRepo.full_name}`)
          fd.append('branch', selectedBranch || githubBranch)
          fd.append('folder_path', selectedFolder)
        } else if (publicRepoUrl.trim()) {
          fd.append('github_url', publicRepoUrl.trim())
          fd.append('branch', selectedPublicBranch)
          fd.append('folder_path', selectedPublicFolder)
        } else { addToast('Select a repository or paste a URL', 'error'); setLoading(false); return }
      }

      const res = await uploadUniversal(fd)
      await stepsPromise
      addToast('Documentation generated.', 'success')
      navigate(`/output/universal/${res.data.project_id}`)
    } catch (err) {
      addToast('Generation failed.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const liveManifestJSON = JSON.stringify({
    compiler_target: active.toUpperCase(),
    workspace_declaration: {
      name: projectName || 'untitled',
      description: projectDesc || 'No context specified',
      source_io: active === 'upload' ? zipFile?.name || null : active === 'file' ? singleFile?.name || null : gitUrl || publicRepoUrl || null,
      generator_mode: 'UniDoc (Multi-Language)',
      git_environment: active === 'git' ? {
        branch: selectedRepo ? selectedBranch : selectedPublicBranch || 'main',
        target_directory: selectedRepo ? selectedFolder : selectedPublicFolder,
      } : null,
    },
  }, null, 2)

  return (
    <div className="relative z-10 bg-bg-primary min-h-screen text-ink-primary font-body">
      <Helmet>
        <title>New Generation — Universal Doc</title>
        <meta name="description" content="Generate AI-powered documentation for any programming language. Upload code files or connect a GitHub repo — works with JavaScript, Rust, Go, Java, Python, and more." />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Navbar />

      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 flex flex-col lg:flex-row gap-6 sm:gap-8">

        {/* LEFT: Manifest Preview (reversed — manifest first) */}
        <section className="w-full lg:w-96 flex-shrink-0 flex-col order-2 lg:order-1 hidden lg:flex">
          <div className="bg-bg-surface border border-border rounded-lg flex-1 flex flex-col overflow-hidden shadow-sm h-[480px]">
            <div className="border-b border-border px-4 py-2 flex items-center justify-between">
              <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> manifest.json
              </span>
            </div>
            <pre className="p-4 font-mono text-[11px] text-emerald-400/90 overflow-auto flex-1 leading-relaxed">
              <code>{liveManifestJSON}</code>
            </pre>
          </div>
          <p className="text-[9px] font-mono text-ink-muted/50 text-center mt-2">Live preview &mdash; updates as you type</p>
        </section>

        {/* RIGHT: Form (reversed — form second) */}
        <section className="flex-1 space-y-5 order-1 lg:order-2">
          {/* Compact header */}
          <div className="flex items-center gap-3">
            <span className="text-emerald-400 text-lg font-mono font-bold">&#8704;</span>
            <div>
            <h1 className="text-xl font-display font-bold text-ink-primary tracking-tight">Universal Doc</h1>
              <p className="text-[10px] font-mono text-ink-muted uppercase tracking-wider">Multi-language documentation</p>
            </div>
          </div>

          {loading ? (
            <StepIndicator steps={steps} />
          ) : (
            <>
              {/* Minimal underline tab bar */}
              <div className="flex border-b border-border gap-0">
                {tabs.map(tab => (
                  <button key={tab.id} onClick={() => setActive(tab.id)}
                    className={`flex items-center gap-1.5 px-4 py-2.5 text-[11px] font-mono transition-all border-b-2 -mb-[1px] ${active === tab.id ? 'border-emerald-400 text-emerald-400 font-semibold' : 'border-transparent text-ink-muted hover:text-ink-primary'}`}
                  ><tab.icon className="w-3.5 h-3.5" />{tab.label}</button>
                ))}
              </div>

              {active === 'upload' && (
                <div className="border border-border rounded-lg p-5 space-y-4 bg-bg-surface/40">
                  <div>
                    <label htmlFor="uni-name" className="block text-[10px] font-mono text-ink-muted uppercase tracking-wider mb-1.5">Project Name</label>
                    <input id="uni-name" value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-sm w-full" placeholder="my-project" />
                  </div>
                  <div>
                    <label htmlFor="uni-desc" className="block text-[10px] font-mono text-ink-muted uppercase tracking-wider mb-1.5">Description</label>
                    <input id="uni-desc" value={projectDesc} onChange={e => setProjectDesc(e.target.value)} className="input-field text-sm w-full" placeholder="What does this project do?" />
                  </div>
                  <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${isDragging ? 'border-emerald-400 bg-emerald-500/5' : 'border-border hover:border-emerald-400/40 hover:bg-bg-surface'}`}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={e => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files[0]; if (f && f.name.endsWith('.zip')) { setZipFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) } else { addToast('Please upload a .zip file', 'error') } }}
                    onClick={() => document.getElementById('uni-zip-input')?.click()}
                  >
                    <input id="uni-zip-input" type="file" className="hidden" accept=".zip" onChange={e => { const f = e.target.files[0]; setZipFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) }} />
                    {zipFile ? (
                      <><IconArchive className="w-8 h-8 mx-auto mb-2 text-emerald-400" /><p className="text-sm font-mono">{zipFile.name}</p><p className="text-[10px] text-ink-muted mt-1">{(zipFile.size / 1024 / 1024).toFixed(2)} MB</p></>
                    ) : (
                      <><IconArchive className="w-8 h-8 mx-auto mb-2 text-ink-muted" /><p className="text-sm font-mono text-ink-secondary">Drop .zip or browse</p><p className="text-[10px] text-ink-muted mt-1">Project directory archive</p></>
                    )}
                  </div>
                </div>
              )}

              {active === 'file' && (
                <div className="border border-border rounded-lg p-5 space-y-4 bg-bg-surface/40">
                  <div>
                    <label htmlFor="uni-file-name" className="block text-[10px] font-mono text-ink-muted uppercase tracking-wider mb-1.5">Project Name</label>
                    <input id="uni-file-name" value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-sm w-full" placeholder="my-module" />
                  </div>
                  <div>
                    <label htmlFor="uni-file-desc" className="block text-[10px] font-mono text-ink-muted uppercase tracking-wider mb-1.5">Description</label>
                    <input id="uni-file-desc" value={projectDesc} onChange={e => setProjectDesc(e.target.value)} className="input-field text-sm w-full" placeholder="What does this file do?" />
                  </div>
                  <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${isDragging ? 'border-emerald-400 bg-emerald-500/5' : 'border-border hover:border-emerald-400/40 hover:bg-bg-surface'}`}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={e => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files[0]; setSingleFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) }}
                    onClick={() => document.getElementById('uni-file-input')?.click()}
                  >
                    <input id="uni-file-input" type="file" className="hidden" onChange={e => { const f = e.target.files[0]; setSingleFile(f); if (!projectName) setProjectName(f.name.split('.')[0]) }} />
                    {singleFile ? (
                      <><IconFile className="w-8 h-8 mx-auto mb-2 text-emerald-400" /><p className="text-sm font-mono">{singleFile.name}</p><p className="text-[10px] text-ink-muted mt-1">{(singleFile.size / 1024).toFixed(1)} KB</p></>
                    ) : (
                      <><IconFile className="w-8 h-8 mx-auto mb-2 text-ink-muted" /><p className="text-sm font-mono text-ink-secondary">Drop file or browse</p><p className="text-[10px] text-ink-muted mt-1">Any language file</p></>
                    )}
                  </div>
                </div>
              )}

              {active === 'git' && (
                <div className="border border-border rounded-lg p-5 space-y-4 bg-bg-surface/40">
                  <div>
                    <label htmlFor="uni-git-name" className="block text-[10px] font-mono text-ink-muted uppercase tracking-wider mb-1.5">Project Name</label>
                    <input id="uni-git-name" value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-sm w-full" placeholder="my-repo" />
                  </div>

                  <div className="flex gap-2">
                    <button onClick={() => { setPublicRepoUrl(''); setPublicRepoInfo(null); setSelectedRepo(null) }}
                      className={`px-3 py-1.5 rounded text-[10px] font-mono transition-all uppercase tracking-wider ${publicRepoInfo || (!selectedRepo && !publicRepoUrl) ? 'text-emerald-400 bg-emerald-500/10' : 'text-ink-muted hover:text-ink-primary'}`}>Public</button>
                    <button onClick={() => setSelectedRepo(null)}
                      className={`px-3 py-1.5 rounded text-[10px] font-mono transition-all uppercase tracking-wider ${selectedRepo ? 'text-emerald-400 bg-emerald-500/10' : 'text-ink-muted hover:text-ink-primary'}`}>Authenticated</button>
                  </div>

                  {selectedRepo ? (
                    <div className="space-y-3">
                      <div className="relative">
                        <button onClick={() => setShowRepoDropdown(!showRepoDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                          <span>{selectedRepo.full_name}</span>
                          <IconChevron className={`w-3 h-3 transition-transform ${showRepoDropdown ? 'rotate-180' : ''}`} />
                        </button>
                        {showRepoDropdown && (
                          <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-lg">
                            {repos.filter(r => r.full_name !== selectedRepo.full_name).map((r, i) => (
                              <button key={i} onClick={() => handleRepoSelect(r)} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{r.full_name}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="relative">
                        <button onClick={() => setShowBranchDropdown(!showBranchDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                          <span>{selectedBranch || selectedRepo.default_branch || 'main'}</span>
                          <IconChevron className={`w-3 h-3 transition-transform ${showBranchDropdown ? 'rotate-180' : ''}`} />
                        </button>
                        {showBranchDropdown && (
                          <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-lg">
                            {[selectedRepo.default_branch || 'main', 'develop', 'staging'].filter(Boolean).map((b, i) => (
                              <button key={i} onClick={() => { setSelectedBranch(b); setGithubBranch(b); setShowBranchDropdown(false); fetchFolders(selectedRepo.full_name, b) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{b}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="relative">
                        <button onClick={() => setShowFolderDropdown(!showFolderDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                          <span className="flex items-center gap-2"><IconFolder className="w-3.5 h-3.5 text-ink-muted" />{selectedFolder === '/' ? 'Entire repository' : selectedFolder}</span>
                          <IconChevron className={`w-3 h-3 transition-transform ${showFolderDropdown ? 'rotate-180' : ''}`} />
                        </button>
                        {showFolderDropdown && (
                          <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-lg">
                            <button onClick={() => { setSelectedFolder('/'); setShowFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">Entire repository</button>
                            {loadingFolders ? <div className="px-3 py-2 text-xs text-ink-muted">Loading folders...</div> : folders.filter(f => f.path !== '/').map((f, i) => (
                              <button key={i} onClick={() => { setSelectedFolder(f.path); setShowFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{f.path}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <button onClick={() => { setSelectedRepo(null); setSelectedBranch(''); setGithubBranch('main'); setSelectedFolder('/'); setGitUrl('') }} className="text-[10px] font-mono text-ink-muted hover:text-ink-primary transition-colors">+ Change repository</button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        <input value={publicRepoUrl} onChange={e => { setPublicRepoUrl(e.target.value); setPublicRepoInfo(null) }} className="input-field text-sm flex-1" placeholder="https://github.com/owner/repo" />
                        <button onClick={fetchPublicRepoInfo} disabled={loadingPublicRepo} className="px-3 py-2 rounded border border-emerald-500/30 text-emerald-400 text-[10px] font-mono hover:bg-emerald-500/10 transition-all disabled:opacity-50">{loadingPublicRepo ? '...' : 'Fetch'}</button>
                      </div>
                      {loadingRepos ? (
                        <p className="text-xs text-ink-muted text-center py-3">Loading your repositories...</p>
                      ) : !githubConnected ? (
                        <div className="text-center py-3 space-y-2 bg-bg-surface rounded border border-border">
                          <p className="text-xs text-ink-muted">Connect GitHub for private repos</p>
                          <a href="/auth/github/" className="inline-block px-4 py-1.5 rounded border border-emerald-500/30 text-emerald-400 text-[10px] font-mono hover:bg-emerald-500/10 transition-all">Connect</a>
                        </div>
                      ) : (
                        <div className="relative">
                          <button onClick={() => setShowRepoDropdown(!showRepoDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                            <span>Select a repository...</span>
                            <IconChevron className={`w-3 h-3 transition-transform ${showRepoDropdown ? 'rotate-180' : ''}`} />
                          </button>
                          {showRepoDropdown && (
                            <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-lg">
                              {repos.map((r, i) => (
                                <button key={i} onClick={() => handleRepoSelect(r)} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{r.full_name}</button>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      {publicRepoInfo && (
                        <div className="bg-bg-surface rounded border border-border p-3 space-y-2">
                          <p className="text-sm font-semibold">{publicRepoInfo.full_name}</p>
                          {publicRepoInfo.description && <p className="text-[10px] text-ink-muted">{publicRepoInfo.description}</p>}
                          <div className="flex gap-3 text-[9px] text-ink-muted font-mono"><span>Branch: {selectedPublicBranch}</span><span>{publicRepoInfo.language}</span></div>
                          <div className="relative">
                            <button onClick={() => setShowPublicFolderDropdown(!showPublicFolderDropdown)} className="input-field text-xs w-full flex items-center justify-between">
                              <span className="flex items-center gap-2"><IconFolder className="w-3 h-3 text-ink-muted" />{selectedPublicFolder === '/' ? 'Entire repository' : selectedPublicFolder}</span>
                              <IconChevron className={`w-2.5 h-2.5 transition-transform ${showPublicFolderDropdown ? 'rotate-180' : ''}`} />
                            </button>
                            {showPublicFolderDropdown && (
                              <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-lg max-h-48 overflow-y-auto shadow-lg">
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

              <button onClick={handleSubmit} disabled={loading} className="w-full py-3 rounded-lg border-2 border-emerald-500/40 text-emerald-400 text-xs font-mono uppercase tracking-widest font-display font-bold transition-all duration-150 hover:bg-emerald-500/10 active:scale-[0.98] disabled:opacity-30 disabled:cursor-not-allowed">
                {loading ? 'Processing...' : 'Generate Docs'}
              </button>
            </>
          )}
        </section>

      </main>
    </div>
  )
}
