import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { uploadUniversal, getGithubRepos, getGithubRepoFolders, getPublicRepoInfo, getPublicRepoFolders } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import { IconFile, IconArchive, IconLink, IconChevron, IconFolder } from './Icons'

const INPUT_TABS = [
  { id: 'zip', label: 'Local Directory (.zip)', icon: IconArchive },
  { id: 'file', label: 'Single File', icon: IconFile },
  { id: 'github', label: 'GitHub Repository', icon: IconLink },
]

export default function UniversalUploadForm({ mode, theme }) {
  const navigate = useNavigate()
  const { addToast } = useAuth()
  const t = theme

  const [activeTab, setActiveTab] = useState('zip')
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  const [githubUrl, setGithubUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [githubConnected, setGithubConnected] = useState(false)
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [showRepoDropdown, setShowRepoDropdown] = useState(false)
  const [folders, setFolders] = useState([])
  const [selectedFolder, setSelectedFolder] = useState('/')
  const [showFolderDropdown, setShowFolderDropdown] = useState(false)
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [publicRepoUrl, setPublicRepoUrl] = useState('')
  const [publicRepoInfo, setPublicRepoInfo] = useState(null)
  const [publicFolders, setPublicFolders] = useState([])
  const [selectedPublicFolder, setSelectedPublicFolder] = useState('/')
  const [selectedPublicBranch, setSelectedPublicBranch] = useState('main')
  const [loadingPublicRepo, setLoadingPublicRepo] = useState(false)
  const [loadingPublicFolders, setLoadingPublicFolders] = useState(false)
  const [showPublicFolderDropdown, setShowPublicFolderDropdown] = useState(false)
  const [gitSource, setGitSource] = useState('public')

  const [step, setStep] = useState(1)

  useEffect(() => {
    if (activeTab === 'github' && gitSource === 'authenticated') fetchRepos()
  }, [activeTab, gitSource])

  const fetchRepos = async () => {
    setLoadingRepos(true)
    try { const res = await getGithubRepos(); setRepos(res.data || []); setGithubConnected(true) }
    catch { setGithubConnected(false) }
    finally { setLoadingRepos(false) }
  }

  const fetchFolders = useCallback(async (fn, br) => {
    setLoadingFolders(true)
    try { const res = await getGithubRepoFolders(fn, br); setFolders(res.data || []) }
    catch { setFolders([]) }
    finally { setLoadingFolders(false) }
  }, [])

  const handleRepoSelect = (repo) => {
    setSelectedRepo(repo); setShowRepoDropdown(false); setGithubUrl(repo.url)
    if (!name) setName(repo.full_name.split('/')[1])
    const br = repo.default_branch || 'main'; setBranch(br); fetchFolders(repo.full_name, br)
  }

  const fetchPublicRepoInfo = async () => {
    if (!publicRepoUrl.trim()) return
    setLoadingPublicRepo(true)
    try {
      const res = await getPublicRepoInfo(publicRepoUrl)
      setPublicRepoInfo(res.data)
      if (!name) setName(res.data.full_name.split('/')[1])
      const br = res.data.default_branch || 'main'; setSelectedPublicBranch(br)
      fetchPublicFolders(res.data.full_name, br)
    } catch { addToast('Failed to fetch public repo info', 'error') }
    finally { setLoadingPublicRepo(false) }
  }

  const fetchPublicFolders = async (fn, br) => {
    setLoadingPublicFolders(true)
    try { const res = await getPublicRepoFolders(fn, br); setPublicFolders(res.data || []) }
    catch { setPublicFolders([]) }
    finally { setLoadingPublicFolders(false) }
  }

  const isReady = name.trim() && (activeTab !== 'github' || (selectedRepo || publicRepoUrl.trim())) && (activeTab === 'github' || file)

  const handleSubmit = async () => {
    if (!name.trim()) { addToast('Project name required', 'error'); return }
    if (activeTab === 'github') {
      const url = selectedRepo ? selectedRepo.url : publicRepoUrl.trim()
      if (!url) { addToast('Please select a GitHub repository', 'error'); return }
    } else if (!file) { addToast('Please select a file', 'error'); return }
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('name', name); fd.append('description', desc); fd.append('mode', mode)
      if (activeTab === 'github') {
        if (selectedRepo) { fd.append('github_url', selectedRepo.url); fd.append('branch', branch); fd.append('folder_path', selectedFolder) }
        else { fd.append('github_url', publicRepoUrl.trim()); fd.append('branch', selectedPublicBranch); fd.append('folder_path', selectedPublicFolder) }
      } else { fd.append('file', file) }
      const res = await uploadUniversal(fd)
      addToast('Upload started', 'success')
      navigate(`/output/universal/${res.data.project_id}`)
    } catch { addToast('Upload failed', 'error') }
    finally { setLoading(false) }
  }

  const pageTitle = `${t.label} - New Generation`

  const TabBar = () => (
    <div className="glass-card p-1 flex gap-1">
      {INPUT_TABS.map(tab => (
        <button key={tab.id} onClick={() => { setActiveTab(tab.id); setFile(null) }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-xs font-mono transition-all flex-1 justify-center ${activeTab === tab.id ? `${t.accentBgSoft} ${t.accent} font-semibold` : 'text-ink-muted hover:text-ink-primary'}`}
        ><tab.icon className="w-4 h-4" />{tab.label}</button>
      ))}
    </div>
  )

  const DropZone = ({ accept, isZip }) => {
    const IconCmp = isZip ? IconArchive : IconFile
    return (
      <div
        className={`border-2 border-dashed rounded-md p-10 text-center transition-all cursor-pointer bg-bg-surface ${isDragging ? 'border-accent-blue bg-accent-blue/5' : 'border-border hover:border-accent-blue/50'}`}
        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={e => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files[0]; setFile(f); if (!name) setName(f.name.split('.')[0]) }}
        onClick={() => inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" className="hidden" accept={accept} onChange={e => { const f = e.target.files[0]; setFile(f); if (!name) setName(f.name.split('.')[0]) }} />
        {file ? (
          <><IconCmp className={`w-10 h-10 mx-auto mb-3 ${t.accent}`} /><p className="text-sm font-mono">{file.name}</p><p className="text-xs text-ink-muted mt-1">{(file.size / 1024 / (isZip ? 1024 : 1)).toFixed(isZip ? 2 : 1)} {isZip ? 'MB' : 'KB'}</p></>
        ) : (
          <><IconCmp className="w-10 h-10 mx-auto mb-3 text-ink-muted" /><p className="text-sm font-mono text-ink-secondary">Drop here or browse</p><p className="text-xs text-ink-muted mt-1">{isZip ? 'Upload a ZIP of your project' : 'Any language, any framework'}</p></>
        )}
      </div>
    )
  }

  const GitHubPanel = () => (
    <div className="glass-card p-5 space-y-4">
      <div className="flex gap-2">
        <button onClick={() => setGitSource('public')} className={`px-4 py-2 rounded-md text-xs font-mono transition-all ${gitSource === 'public' ? `${t.accentBgSoft} ${t.accent} font-semibold` : 'text-ink-muted hover:text-ink-primary'}`}>Public Repository</button>
        <button onClick={() => setGitSource('authenticated')} className={`px-4 py-2 rounded-md text-xs font-mono transition-all ${gitSource === 'authenticated' ? `${t.accentBgSoft} ${t.accent} font-semibold` : 'text-ink-muted hover:text-ink-primary'}`}>My Repositories</button>
      </div>
      {gitSource === 'public' ? (
        <div className="space-y-3">
          <div className="flex gap-2">
            <input value={publicRepoUrl} onChange={e => { setPublicRepoUrl(e.target.value); setPublicRepoInfo(null) }} className="input-field flex-1" placeholder="https://github.com/owner/repo" />
            <button onClick={fetchPublicRepoInfo} disabled={loadingPublicRepo} className="btn-accent px-4 text-xs font-mono">{loadingPublicRepo ? '...' : 'Fetch'}</button>
          </div>
          {publicRepoInfo && (
            <div className="bg-bg-primary border border-border rounded-md p-3 space-y-2">
              <div className="flex items-center gap-2"><IconLink className={`w-4 h-4 ${t.accent}`} /><p className="text-sm font-semibold">{publicRepoInfo.full_name}</p></div>
              {publicRepoInfo.description && <p className="text-xs text-ink-muted">{publicRepoInfo.description}</p>}
              <div className="flex gap-4 text-[10px] text-ink-muted font-mono"><span>Branch: {selectedPublicBranch}</span><span>{publicRepoInfo.language}</span></div>
              <div className="relative">
                <button onClick={() => setShowPublicFolderDropdown(!showPublicFolderDropdown)} className="input-field text-xs flex items-center justify-between">
                  <span className="flex items-center gap-2"><IconFolder className="w-3.5 h-3.5 text-ink-muted" />{selectedPublicFolder === '/' ? 'Entire repository' : selectedPublicFolder}</span>
                  <IconChevron className={`w-3 h-3 transition-transform ${showPublicFolderDropdown ? 'rotate-180' : ''}`} />
                </button>
                {showPublicFolderDropdown && (
                  <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-md max-h-48 overflow-y-auto shadow-md">
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
      ) : (
        <div className="space-y-3">
          {loadingRepos ? <p className="text-sm text-ink-muted text-center py-4">Loading your repositories...</p>
          : !githubConnected ? (
            <div className="text-center py-4 space-y-2 bg-bg-primary border border-border rounded-md">
              <p className="text-sm text-ink-muted">Connect your GitHub account first</p>
              <a href="/auth/github/" className="btn-accent text-xs font-mono inline-block px-4 py-2">Connect GitHub</a>
            </div>
          ) : (
            <>
              <div className="relative">
                <button onClick={() => setShowRepoDropdown(!showRepoDropdown)} className="input-field text-xs flex items-center justify-between">
                  <span>{selectedRepo ? selectedRepo.full_name : 'Select a repository...'}</span>
                  <IconChevron className={`w-3 h-3 transition-transform ${showRepoDropdown ? 'rotate-180' : ''}`} />
                </button>
                {showRepoDropdown && (
                  <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-md max-h-48 overflow-y-auto shadow-md">
                    {repos.map((r, i) => (<button key={i} onClick={() => handleRepoSelect(r)} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{r.full_name}</button>))}
                  </div>
                )}
              </div>
              {selectedRepo && (
                <>
                  <div className="flex gap-2">
                    <input value={branch} onChange={e => { setBranch(e.target.value); fetchFolders(selectedRepo.full_name, e.target.value) }} className="input-field flex-1 text-xs" placeholder="Branch (e.g. main)" />
                    <button onClick={() => { setSelectedRepo(null); setBranch('main'); setSelectedFolder('/'); setGithubUrl('') }} className="btn-ghost px-3 text-xs font-mono">Change</button>
                  </div>
                  <div className="relative">
                    <button onClick={() => setShowFolderDropdown(!showFolderDropdown)} className="input-field text-xs flex items-center justify-between">
                      <span className="flex items-center gap-2"><IconFolder className="w-3.5 h-3.5 text-ink-muted" />{selectedFolder === '/' ? 'Entire repository' : selectedFolder}</span>
                      <IconChevron className={`w-3 h-3 transition-transform ${showFolderDropdown ? 'rotate-180' : ''}`} />
                    </button>
                    {showFolderDropdown && (
                      <div className="absolute z-10 mt-1 w-full bg-bg-elevated border border-border rounded-md max-h-48 overflow-y-auto shadow-md">
                        <button onClick={() => { setSelectedFolder('/'); setShowFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">Entire repository</button>
                        {loadingFolders ? <div className="px-3 py-2 text-xs text-ink-muted">Loading folders...</div> : folders.filter(f => f.path !== '/').map((f, i) => (
                          <button key={i} onClick={() => { setSelectedFolder(f.path); setShowFolderDropdown(false) }} className="w-full text-left px-3 py-2 text-xs hover:bg-bg-surface transition-colors font-mono">{f.path}</button>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )

  const SubmitBtn = () => (
    <button onClick={handleSubmit} disabled={!isReady || loading}
      className={`w-full py-4 text-xs font-mono uppercase tracking-widest rounded-md font-display font-bold transition-all duration-150 active:scale-[0.98] ${isReady && !loading ? `${t.accentBg} text-[#0b1320] hover:opacity-90` : 'bg-ink-muted/20 text-ink-muted cursor-not-allowed'}`}>
      {loading ? 'Processing...' : 'Compile Documentation'}
    </button>
  )

  /* ══════════════════════════════════════════════════════════════
     1. UniDoc — 3-step wizard
     ══════════════════════════════════════════════════════════════ */
  if (mode === 'universal') {
    return (
      <div className="min-h-screen bg-bg-primary text-ink-primary font-body">
        <Helmet><title>{pageTitle}</title></Helmet>
        <Navbar />
        <div className="max-w-2xl mx-auto px-6 py-10 space-y-8">
          <div className="text-center space-y-2">
            <div className={`text-4xl ${t.accent}`}>{t.symbol}</div>
            <h1 className={`text-3xl font-display font-bold ${t.accent}`}>{t.label}</h1>
            <p className="text-sm text-ink-secondary max-w-md mx-auto">{t.desc}</p>
          </div>
          <div className="flex items-center justify-center gap-3 text-xs font-mono">
            {[1, 2, 3].map(s => (
              <div key={s} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-md flex items-center justify-center text-sm font-display font-bold ${step >= s ? `${t.accentBg} text-[#0b1320]` : 'bg-bg-surface text-ink-muted border border-border'}`}>{s}</div>
                <span className={step >= s ? t.accent : 'text-ink-muted'}>{['Project Info', 'Upload Code', 'Generate'][s - 1]}</span>
                {s < 3 && <div className={`w-12 h-px ${step > s ? t.accentBg.replace('bg-', 'bg-').replace(/-\w+$/, '') : 'bg-border'}`} />}
              </div>
            ))}
          </div>
          {step === 1 && (
            <div className="glass-card p-6 space-y-5">
              <h3 className={`text-sm font-display font-bold ${t.accent}`}>Tell us about your project</h3>
              <div><label htmlFor="uni-name" className="block text-xs font-mono text-ink-secondary mb-1">Project Name</label><input id="uni-name" value={name} onChange={e => setName(e.target.value)} className="input-field" placeholder="my-awesome-project" /></div>
              <div><label htmlFor="uni-desc" className="block text-xs font-mono text-ink-secondary mb-1">Description</label><textarea id="uni-desc" value={desc} onChange={e => setDesc(e.target.value)} rows={3} className="input-field resize-none" placeholder="What does your project do?" /></div>
              <button onClick={() => setStep(2)} disabled={!name.trim()} className={`w-full py-3 rounded-md text-xs font-mono uppercase tracking-wider font-display font-bold transition-all duration-150 active:scale-[0.98] ${name.trim() ? `${t.accentBg} text-[#0b1320] hover:opacity-90` : 'bg-ink-muted/20 text-ink-muted cursor-not-allowed'}`}>Continue</button>
            </div>
          )}
          {step === 2 && (
            <div className="space-y-5">
              <TabBar />
              {activeTab === 'github' ? <GitHubPanel /> : <DropZone accept={activeTab === 'zip' ? '.zip' : undefined} isZip={activeTab === 'zip'} />}
              <div className="flex gap-3">
                <button onClick={() => setStep(1)} className="btn-ghost flex-1 py-3 text-xs font-mono">Back</button>
                <button onClick={() => { if (isReady) setStep(3) }} disabled={!isReady} className={`flex-1 py-3 rounded-md text-xs font-mono uppercase tracking-wider font-display font-bold transition-all duration-150 active:scale-[0.98] ${isReady ? `${t.accentBg} text-[#0b1320] hover:opacity-90` : 'bg-ink-muted/20 text-ink-muted cursor-not-allowed'}`}>Review & Generate</button>
              </div>
            </div>
          )}
          {step === 3 && (
            <div className="glass-card p-6 text-center space-y-4">
              <div className={`text-4xl ${t.accent}`}>&#10003;</div>
              <h3 className={`text-lg font-display font-bold ${t.accent}`}>Ready to generate</h3>
              <div className="text-left space-y-2 text-sm bg-bg-primary border border-border rounded-md p-4"><div className="flex justify-between"><span className="text-ink-muted">Project:</span><span>{name}</span></div><div className="flex justify-between"><span className="text-ink-muted">Source:</span><span>{activeTab === 'github' ? 'GitHub' : file?.name || 'Unknown'}</span></div><div className="flex justify-between"><span className="text-ink-muted">Mode:</span><span className={t.accent}>{t.label}</span></div></div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setStep(2)} className="btn-ghost flex-1 py-3 text-xs font-mono">Change</button>
                <SubmitBtn />
              </div>
            </div>
          )}
          <p className="text-center text-[10px] text-ink-muted font-mono">{t.label} &middot; v1</p>
        </div>
      </div>
    )
  }

  return null
}
