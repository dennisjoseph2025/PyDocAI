import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { analyzeFile, analyzeFolder, importFromGithub, getGithubRepos, getGithubRepoFolders, getPublicRepoInfo, getPublicRepoFolders, importPublicRepo } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import StepIndicator from '../components/StepIndicator'
import { IconFile, IconArchive, IconLink, IconFolder, IconChevron, IconRefresh } from '../components/Icons'

const tabs = [
  { id: 'upload', label: 'Local Directory (.zip)',  icon: IconArchive },
  { id: 'git',    label: 'Cloud Git System',        icon: IconLink },
  { id: 'single', label: 'Isolated Module (.py)',   icon: IconFile },
]

const defaultSteps = [
  { label: 'Initializing IO Stream Pipelines...', done: false, active: false },
  { label: 'Decomposing Python Syntax Trees (AST)...', done: false, active: false },
  { label: 'Mapping Class Interfaces & Serializers...', done: false, active: false },
  { label: 'Compiling API Schemas & Document Trees...', done: false, active: false },
  { label: 'Finalizing Output Buffers...', done: false, active: false },
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
    if (active === 'git') {
      fetchRepos()
    }
  }, [active])

  const fetchRepos = async () => {
    setLoadingRepos(true)
    try {
      const res = await getGithubRepos()
      setRepos(res.data || [])
      setGithubConnected(true)
    } catch (err) {
      setGithubConnected(false)
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
      setSelectedPublicBranch(res.data.default_branch || 'main')
      fetchPublicFolders(res.data.full_name, res.data.default_branch)
    } catch (err) {
      addToast('Failed to fetch public repo info', 'error')
    } finally {
      setLoadingPublicRepo(false)
    }
  }

  const fetchPublicFolders = async (fullName, branch) => {
    setLoadingPublicFolders(true)
    try {
      const res = await getPublicRepoFolders(fullName, branch)
      setPublicFolders(res.data || [])
    } catch (err) {
      addToast('Failed to load folders', 'error')
    } finally {
      setLoadingPublicFolders(false)
    }
  }

  const handlePublicFolderSelect = (folder) => {
    setSelectedPublicFolder(folder.path || '/')
    setShowPublicFolderDropdown(false)
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
      addToast('Please input project name.', 'error')
      return
    }

    setLoading(true)
    setSteps(defaultSteps)
    const stepsPromise = simulateSteps()

    try {
      let res;
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
        res = await analyzeFile(fd, true)
      } else {
        if (githubConnected && selectedRepo) {
          res = await importFromGithub({
            full_name: selectedRepo.full_name,
            branch: selectedBranch || githubBranch,
            folder_path: selectedFolder || '/',
            name: projectName,
            description: projectDesc,
          })
        } else {
          if (!publicRepoUrl.trim()) { addToast('Please input Git remote url', 'error'); setLoading(false); return }
          res = await importPublicRepo({
            url: publicRepoUrl,
            branch: selectedPublicBranch || publicRepoInfo?.default_branch || 'main',
            folder_path: selectedPublicFolder || '/',
            name: projectName,
            description: projectDesc,
          })
        }
      }

      await stepsPromise
      addToast('Document parsing finished.', 'success')
      navigate(`/output/${res.data.project_id || res.data.id}`)
    } catch (err) {
      addToast('Failed compiling AST tree.', 'error')
      setLoading(false)
      setSteps(defaultSteps)
    }
  }

  // Generates real-time manifest file text on the right side based on user inputs
  const liveManifestJSON = JSON.stringify({
    compiler_target: active.toUpperCase(),
    workspace_declaration: {
      name: projectName || "untitled_ast",
      description: projectDesc || "No context specified",
      source_io: active === 'upload' ? zipFile?.name || null : active === 'single' ? singleFile?.name || null : gitUrl || publicRepoUrl || null,
      custom_attributes: customInfo ? { details: customInfo } : null,
      git_environment: active === 'git' ? {
        connection: githubConnected ? "AUTHORIZED_API" : "UNRESTRICTED_PUBLIC",
        branch: githubConnected ? selectedBranch : selectedPublicBranch || "main",
        target_directory: githubConnected ? selectedFolder : selectedPublicFolder
      } : null
    }
  }, null, 2);

  return (
    <div className="relative z-10 bg-bg-primary min-h-screen text-ink-primary font-body">
      <Navbar />
      
      <main className="max-w-7xl w-full mx-auto px-6 py-8 flex flex-col lg:flex-row gap-8">
        
        {/* Left Side: Compiler Config Forms */}
        <section className="flex-1 space-y-6">
          <div>
            <h1 className="text-3xl font-display font-bold text-ink-primary">Configuration Studio</h1>
            <p className="text-xs text-ink-secondary mt-1">Configure workspace inputs for local directories or remote Git targets.</p>
          </div>

          {/* Form Tabs */}
          <div className="flex bg-bg-surface border border-border p-1 rounded-xl">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setActive(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-mono font-medium transition-all duration-200 ${active === tab.id ? 'bg-accent-blue text-white shadow-md' : 'text-ink-secondary hover:text-ink-primary'}`}>
                <tab.icon className="w-4 h-4" /> {tab.label}
              </button>
            ))}
          </div>

          {/* Core Configuration Inputs */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-mono text-accent uppercase tracking-widest border-b border-border/40 pb-2">Workspace Identification</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-mono text-ink-secondary uppercase tracking-wider mb-2">Project Package Name</label>
                <input value={projectName} onChange={e => setProjectName(e.target.value)} className="input-field text-xs font-mono" placeholder="django_core" />
              </div>
              <div>
                <label className="block text-[10px] font-mono text-ink-secondary uppercase tracking-wider mb-2">Module Descriptors</label>
                <input value={projectDesc} onChange={e => setProjectDesc(e.target.value)} className="input-field text-xs font-mono" placeholder="Backend user auth views" />
              </div>
            </div>
          </div>

          {/* Dynamic IO Config Content based on tabs */}
          {active === 'single' && (
            <div className="animate-fade-in">
              <label className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer block ${isDragging ? 'border-accent bg-accent/5 shadow-glow' : 'border-border hover:border-accent-blue/50 hover:bg-bg-surface'}`}
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
                <p className="text-accent-blue mb-3"><IconFile className="w-10 h-10 mx-auto" /></p>
                <p className="text-ink-primary text-xs font-mono">
                  {singleFile ? `[Target]: ${singleFile.name}` : 'Drop localized .py script file or browse'}
                </p>
              </label>
            </div>
          )}

          {active === 'upload' && (
            <div className="animate-fade-in space-y-4">
              <label className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer block ${isDragging ? 'border-accent bg-accent/5 shadow-glow' : 'border-border hover:border-accent-blue/50 hover:bg-bg-surface'}`}
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
                <p className="text-accent mb-3"><IconArchive className="w-10 h-10 mx-auto" /></p>
                <p className="text-ink-primary text-xs font-mono">
                  {zipFile ? `[Archive]: ${zipFile.name} (${(zipFile.size / 1024 / 1024).toFixed(2)} MB)` : 'Drop repository ZIP packaging or browse'}
                </p>
              </label>

              <div className="glass-card p-5 space-y-2">
                <label className="block text-[10px] font-mono text-ink-secondary uppercase tracking-wider">
                  Additional Project details <span className="text-danger">*</span>
                </label>
                <textarea
                  value={customInfo}
                  onChange={e => setCustomInfo(e.target.value)}
                  rows={3}
                  className="input-field resize-none text-xs font-mono"
                  placeholder="Provide system features, database schema variables, or framework targets..."
                />
              </div>
            </div>
          )}

          {active === 'git' && (
            <div className="animate-fade-in space-y-4">
              <div className="glass-card p-6 space-y-4">
                {!githubConnected && (
                  <div className="p-4 bg-bg-surface rounded-xl border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <p className="text-xs text-ink-secondary">Authorize secure REST pipeline connection to your GitHub profile.</p>
                    <a href={`https://github.com/login/oauth/authorize?client_id=${import.meta.env.VITE_GITHUB_CLIENT_ID || ''}&redirect_uri=${window.location.origin}/auth/github/callback&scope=repo`}
                      className="text-xs font-mono bg-[#24292e] text-white px-4 py-2.5 rounded-lg border border-[#444c56] hover:bg-[#2f363d] flex-shrink-0">
                      Link GitHub
                    </a>
                  </div>
                )}

                {githubConnected ? (
                  <div className="space-y-4 text-xs font-mono">
                    <div>
                      <label className="block text-[10px] text-ink-secondary uppercase tracking-wider mb-2">Repository Workspace</label>
                      <div className="relative">
                        <button type="button" onClick={() => setShowRepoDropdown(!showRepoDropdown)} className="w-full flex items-center justify-between input-field text-xs">
                          <span>{selectedRepo ? selectedRepo.full_name : 'Select git repository...'}</span>
                          <IconChevron className="w-4 h-4 text-ink-muted" />
                        </button>
                        {showRepoDropdown && (
                          <div className="absolute z-50 w-full mt-1 bg-bg-surface border border-border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                            {repos.map(repo => (
                              <button key={repo.id} onClick={() => handleRepoSelect(repo)} className="w-full text-left px-4 py-2 hover:bg-bg-primary text-xs">
                                {repo.full_name}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {selectedRepo && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-[10px] text-ink-secondary uppercase tracking-wider mb-2">Target branch</label>
                          <input value={selectedBranch || ''} onChange={e => { setSelectedBranch(e.target.value); setGithubBranch(e.target.value); }} className="input-field text-xs" placeholder={selectedRepo.default_branch || 'main'} />
                        </div>
                        <div>
                          <label className="block text-[10px] text-ink-secondary uppercase tracking-wider mb-2">Workspace Base path</label>
                          <input value={selectedFolder} onChange={e => setSelectedFolder(e.target.value)} className="input-field text-xs" placeholder="/" />
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-[10px] font-mono text-ink-secondary uppercase tracking-wider mb-2">Unauthenticated Repository Remote Path (URL)</label>
                      <div className="flex gap-2">
                        <input value={publicRepoUrl} onChange={e => { setPublicRepoUrl(e.target.value); setPublicRepoInfo(null); }} className="input-field text-xs font-mono" placeholder="https://github.com/django/django" />
                        <button type="button" onClick={fetchPublicRepoInfo} disabled={loadingPublicRepo} className="px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 text-white rounded-lg text-xs font-mono">
                          {loadingPublicRepo ? 'Fetching...' : 'Fetch'}
                        </button>
                      </div>
                    </div>

                    {publicRepoInfo && (
                      <div className="p-4 bg-bg-surface border border-border rounded-lg space-y-2 text-xs font-mono">
                        <p className="text-accent font-bold">{publicRepoInfo.full_name}</p>
                        <div className="grid grid-cols-2 gap-4 pt-2">
                          <div>
                            <label className="block text-[9px] text-ink-muted uppercase">Selected Branch</label>
                            <input value={selectedPublicBranch} onChange={e => setSelectedPublicBranch(e.target.value)} className="input-field text-xs mt-1" />
                          </div>
                          <div>
                            <label className="block text-[9px] text-ink-muted uppercase">Target Path</label>
                            <input value={selectedPublicFolder} onChange={e => setSelectedPublicFolder(e.target.value)} className="input-field text-xs mt-1" />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {!loading && (
            <button id="generate-btn" onClick={handleSubmit} className="btn-accent w-full py-4 text-xs font-mono uppercase tracking-widest shadow-md">
              EXECUTE_COMPILER()
            </button>
          )}

          {loading && (
            <div className="mt-6">
              <StepIndicator steps={steps} />
            </div>
          )}
        </section>

        {/* Right Side: Simulated Active Manifest Visualizer */}
        <section className="w-full lg:w-96 flex-shrink-0 flex flex-col">
          <div className="glass-card bg-code border border-border rounded-xl flex-1 flex flex-col overflow-hidden shadow-2xl h-[480px]">
            <div className="bg-bg-surface px-4 py-2.5 border-b border-border flex items-center justify-between">
              <span className="text-[10px] font-mono text-ink-secondary uppercase tracking-widest flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-accent" /> pydoc_compilation_manifest.json
              </span>
              <span className="text-[10px] font-mono text-ink-muted">JSON</span>
            </div>
            <pre className="p-4 font-mono text-xs text-accent-blue overflow-auto flex-1 leading-relaxed">
              <code>{liveManifestJSON}</code>
            </pre>
          </div>
        </section>

      </main>
    </div>
  )
}