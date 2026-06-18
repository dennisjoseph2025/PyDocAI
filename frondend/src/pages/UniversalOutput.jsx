import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { getUniversalStatus } from '../api'
import useAuth from '../hooks/useAuth'
import { getMode } from '../config/themes'
import {
  IconWarning, IconFile, IconBook, IconPuzzle,
  IconDatabase, IconDownload,
} from '../components/Icons'
import Navbar from '../components/Navbar'

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Fira Code, monospace',
  suppressErrorRendering: true,
})

function sanitizeMermaid(chart) {
  if (!chart) return chart
  let sanitized = chart
  sanitized = sanitized.replace(/-->\|([^|]*)\|>/g, '-->|$1|')
  sanitized = sanitized.replace(/-->>/g, '-->')
  sanitized = sanitized.replace(/-\.->\|([^|]*)\|>/g, '-.->|$1|')
  sanitized = sanitized.replace(/==>\|([^|]*)\|>/g, '==>|$1|')
  sanitized = sanitized.replace(/=>>/g, '==>')
  sanitized = sanitized.replace(/-\.->>/g, '-.->')
  const firstLine = sanitized.trimStart().split('\n')[0].trim()
  const validTypes = /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|gantt|pie|erDiagram|journey|gitGraph|quadrantChart|requirementDiagram)/i
  if (!validTypes.test(firstLine)) {
    if (/-->|-\.->|==>|~~>/.test(sanitized)) {
      sanitized = 'graph TD\n' + sanitized
    }
  }
  sanitized = sanitized.replace(/^graph\s*$/m, 'graph TD')
  sanitized = sanitized.replace(/^graph\s+(?:LR|RL|BT)\s*$/m, (m) => m.trim())
  return sanitized
}

function normalizeMarkdown(text) {
  if (!text) return text
  let normalized = text.replace(/\\n/g, '\n')
  normalized = normalized.replace(/\n?\s*code\s*\n\s*Copy\s*\n?/g, '\n')
  normalized = normalized.replace(/(^|\n)mermaid\s*\n(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|gantt|pie|erDiagram|journey|gitGraph)/g, (match, prefix, diagramType, offset) => {
    const before = normalized.substring(0, offset + prefix.length)
    const backtickCount = (before.match(/```/g) || []).length
    if (backtickCount % 2 !== 0) return match
    return prefix + '```mermaid\n' + diagramType
  })
  normalized = normalized.replace(/(^|\n)((?:flowchart|graph)\s+(?:TD|LR|RL|BT)[\s\S]+?)(?=\n{2,}|\n#{1,6}\s|$)/g, (match, prefix, diagram, offset) => {
    const before = normalized.substring(0, offset + prefix.length)
    const backtickCount = (before.match(/```/g) || []).length
    if (backtickCount % 2 !== 0) return match
    return prefix + '```mermaid\n' + diagram + '\n```'
  })
  normalized = normalized.replace(/```mermaid\n([\s\S]*?)(\n##|\n###|\n#|\n---\n|\n```|$)/g, (match, content, ending) => {
    const trimmed = content.trim()
    if (ending && ending.startsWith('\n```')) {
      return '```mermaid\n' + trimmed + ending
    }
    if (trimmed.endsWith('```')) {
      return '```mermaid\n' + trimmed + '\n' + ending
    }
    return '```mermaid\n' + trimmed + '\n```\n' + ending
  })
  normalized = normalized.replace(/([^\n])```/g, '$1\n```')
  normalized = normalized.replace(/```([^\n])/g, '```\n$1')
  normalized = normalized.replace(/([^\n])\n(#{1,6} )/g, '$1\n\n$2')
  normalized = normalized.replace(/(#{1,6} .+)\n([^\n#])/g, '$1\n\n$2')
  normalized = normalized.replace(/([^\n\-*])\n(\s*[-*] )/g, '$1\n\n$2')
  normalized = normalized.replace(/(\n\s*[-*] .+)\n+(#{1,6} )/g, '$1\n\n$2')
  normalized = normalized.replace(/\n-\s+\*\*(Description|Input Payload|Output Response|Authentication|Request Headers|Path Parameters|Query Parameters|Request Body|Response|Status Codes|Example Usage)\*\"/g, '\n\n- **$1**')
  normalized = normalized.replace(/\n{3,}/g, '\n\n')
  return normalized.trim()
}

function MermaidDiagram({ chart }) {
  const [svgData, setSvgData] = useState('')
  const [error, setError] = useState(false)

  useEffect(() => {
    let isMounted = true
    const renderChart = async () => {
      try {
        if (!chart) return
        const sanitized = sanitizeMermaid(chart)
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`
        const { svg } = await mermaid.render(id, sanitized)
        if (isMounted) { setSvgData(svg); setError(false) }
      } catch { if (isMounted) setError(true) }
    }
    renderChart()
    return () => { isMounted = false }
  }, [chart])

  if (error) {
    return (
      <div className="my-4 rounded-md overflow-hidden border border-danger/30">
        <div className="bg-danger/10 text-danger text-[10px] px-4 py-2 border-b border-danger/30 font-mono flex items-center justify-between">
          <span>Diagram Rendering Blocked</span>
        </div>
        <pre className="p-4 bg-code text-ink-muted text-[10px] font-mono overflow-x-auto m-0">{chart}</pre>
      </div>
    )
  }
  return <div className="my-6 p-6 bg-code border border-border rounded-xl flex justify-center overflow-x-auto" dangerouslySetInnerHTML={{ __html: svgData }} />
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button onClick={copy} className="text-[10px] font-mono text-ink-muted hover:text-ink-primary flex items-center gap-1">
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function VsCodeMarkdown({ markdown }) {
  if (!markdown) {
    return (
      <div className="text-center py-20 text-ink-muted">
        <p className="text-accent mb-4"><IconFile className="w-10 h-10 mx-auto" /></p>
        <p className="text-xs font-mono">No documentation content available.</p>
      </div>
    )
  }

  return (
    <div className="vscode-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ node, ...props }) => <h1 className="text-[1.8em] font-display font-bold text-ink-primary mt-0 mb-4 pb-2 border-b border-border leading-tight" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-[1.4em] font-display font-bold text-ink-primary mt-8 mb-3 pb-2 border-b border-border leading-tight" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-[1.15em] font-display font-bold text-ink-primary mt-6 mb-2 leading-tight" {...props} />,
          h4: ({ node, ...props }) => <h4 className="text-[1.05em] font-display font-bold text-ink-primary mt-5 mb-2 leading-tight" {...props} />,
          h5: ({ node, ...props }) => <h5 className="text-[1em] font-display font-bold text-ink-muted mt-4 mb-1 leading-tight" {...props} />,
          h6: ({ node, ...props }) => <h6 className="text-[0.9em] font-display font-bold text-ink-muted mt-4 mb-1 leading-tight" {...props} />,
          p: ({ node, ...props }) => {
            const children = props.children
            if (children && typeof children === 'string') {
              const mermaidMatch = children.match(/^(?:mermaid\s*\n)?((?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|gantt|pie|erDiagram|journey|gitGraph)\s+[\s\S]+)$/i)
              if (mermaidMatch) {
                const chart = mermaidMatch[1].trim()
                if (chart.includes('-->') || chart.includes('~~>') || chart.includes('-.-')) {
                  return <MermaidDiagram chart={chart} />
                }
              }
            }
            return <p className="text-ink-secondary leading-[1.6] mb-4 text-xs font-mono" {...props} />
          },
          ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-1 text-ink-secondary text-xs font-mono" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-1 text-ink-secondary text-xs font-mono" {...props} />,
          li: ({ node, ...props }) => <li className="leading-[1.6]" {...props} />,
          hr: () => <hr className="border-t border-border my-6" />,
          pre: ({ node, children, ...props }) => <>{children}</>,
          code: ({ node, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '')
            const lang = match ? match[1] : ''
            let codeStr = String(children).replace(/\n$/, '')
            codeStr = codeStr.replace(/^code\s*\n\s*Copy\s*\n?/i, '').trim()
            const isBlock = match || codeStr.includes('\n')

            if (!isBlock) {
              return <code className="font-mono text-accent bg-bg-surface border border-border px-1.5 py-0.5 rounded text-[0.875em]" {...props}>{children}</code>
            }

            if (lang === 'mermaid' || codeStr.startsWith('mermaid\n') || /^(?:flowchart|graph)\s+(?:TD|LR|RL|BT)\b/.test(codeStr)) {
              let chart = codeStr.replace(/^mermaid\s*\n/, '').trim()
              return <MermaidDiagram chart={chart} />
            }

            return (
              <div className="my-4 rounded-xl overflow-hidden border border-border bg-code shadow-lg">
                <div className="flex items-center justify-between bg-bg-surface px-4 py-1.5 border-b border-border">
                  <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest">{lang || 'code'}</span>
                  <CopyButton text={codeStr} />
                </div>
                <SyntaxHighlighter
                  PreTag="div"
                  language={lang || 'python'}
                  style={vscDarkPlus}
                  customStyle={{ margin: 0, padding: '16px', background: '#080e17', fontSize: '12px', lineHeight: '1.5' }}
                  showLineNumbers={codeStr.split('\n').length > 5}
                  lineNumberStyle={{ color: '#475569', minWidth: '2.5em' }}
                >
                  {codeStr}
                </SyntaxHighlighter>
              </div>
            )
          },
          blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-accent-blue pl-4 py-0.5 my-4 text-ink-muted italic" {...props} />,
          table: ({ node, ...props }) => (
            <div className="w-full overflow-x-auto my-6 rounded-xl border border-border bg-bg-surface/35">
              <table className="w-full text-xs font-mono border-collapse" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => <thead className="bg-bg-surface" {...props} />,
          th: ({ node, ...props }) => <th className="text-left px-4 py-2 font-bold text-ink-primary border-b border-border tracking-wider uppercase text-[10px]" {...props} />,
          td: ({ node, ...props }) => <td className="px-4 py-2 border-t border-border text-ink-secondary" {...props} />,
          tr: ({ node, ...props }) => <tr className="hover:bg-bg-surface/50 transition-colors" {...props} />,
          a: ({ node, ...props }) => <a className="text-accent-blue hover:text-accent underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />,
          img: ({ node, ...props }) => <img className="max-w-full rounded-lg my-4 border border-border" {...props} />,
          strong: ({ node, ...props }) => <strong className="font-bold text-ink-primary" {...props} />,
          em: ({ node, ...props }) => <em className="italic text-ink-secondary" {...props} />,
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}

/* ── Section Parsing ────────────────────────────────────────── */

function buildDocTabs(docs) {
  if (!docs) return [{ id: 'readme', label: 'README.md', icon: IconBook, content: '' }]

  const sections = []
  const lines = docs.split('\n')
  let currentHeading = null
  let currentContent = []
  let introLines = []

  for (const line of lines) {
    const headingMatch = line.match(/^##\s+(.+)$/)
    if (headingMatch) {
      if (currentHeading !== null) {
        sections.push({ heading: currentHeading, content: currentContent.join('\n').trim() })
      } else if (introLines.length > 0) {
        sections.push({ heading: null, content: introLines.join('\n').trim() })
      }
      currentHeading = headingMatch[1].trim()
      currentContent = []
    } else if (currentHeading !== null) {
      currentContent.push(line)
    } else {
      introLines.push(line)
    }
  }

  if (currentHeading !== null) {
    sections.push({ heading: currentHeading, content: currentContent.join('\n').trim() })
  } else if (introLines.length > 0) {
    sections.push({ heading: null, content: introLines.join('\n').trim() })
  }

  const readmeSections = []
  const apiSections = []
  const archSections = []

  for (const s of sections) {
    const h = (s.heading || '').toLowerCase().trim()

    const isApi = /^api|endpoint|route|rest|graphql|backend\s+(api|endpoint)/.test(h)
    const isArch = /^project\s+structure|^file\s+structure|^directory|^architecture|^workflow|^component|^module|^data\s+flow|^state\s+management|^configuration|^deployment|^error\s+handling|^logging/.test(h)

    if (isApi) {
      apiSections.push(s)
    } else if (isArch) {
      archSections.push(s)
    } else {
      readmeSections.push(s)
    }
  }

  const tabs = []

  const readmeContent = readmeSections
    .map(s => (s.heading ? `## ${s.heading}\n\n${s.content}` : s.content))
    .join('\n\n')
  tabs.push({ id: 'readme', label: 'README.md', icon: IconBook, content: readmeContent || docs })

  if (apiSections.length > 0) {
    const apiContent = apiSections
      .map(s => `## ${s.heading}\n\n${s.content}`)
      .join('\n\n')
    tabs.push({ id: 'api', label: 'API Reference', icon: IconPuzzle, content: apiContent })
  }

  if (archSections.length > 0) {
    const archContent = archSections
      .map(s => `## ${s.heading}\n\n${s.content}`)
      .join('\n\n')
    tabs.push({ id: 'architecture', label: 'Architecture', icon: IconDatabase, content: archContent })
  }

  return tabs
}

/* ── Progress Display ──────────────────────────────────────── */

function StatusDisplay({ status, error, mode }) {
  const t = getMode(mode || 'universal')
  if (status === 'failed') {
    return (
      <div className="text-center py-24 font-mono text-xs">
        <div className={`w-14 h-14 mx-auto rounded-md border border-border bg-bg-surface flex items-center justify-center ${t.accent} mb-6`}>
          <IconWarning className="w-7 h-7" />
        </div>
        <p className={`${t.accent} mb-4`}>Documentation generation failed</p>
        <p className="text-ink-secondary max-w-md mx-auto">{error || 'An unexpected error occurred.'}</p>
        <Link to="/dashboard" className="btn-accent inline-block mt-8 text-xs font-mono">Back to Dashboard</Link>
      </div>
    )
  }
  return (
    <div className="text-center py-24 font-mono text-xs text-accent-blue space-y-4">
      <div className="w-12 h-12 rounded-full border-4 border-t-accent-blue border-r-transparent animate-spin mx-auto" />
      <h2 className="text-ink-primary">Analyzing codebase & generating documentation...</h2>
      <p className="text-ink-muted">This usually takes a moment. Auto-refreshing...</p>
    </div>
  )
}

/* ── Main Component ────────────────────────────────────────── */

export default function UniversalOutput() {
  const { id } = useParams()
  const { addToast } = useAuth()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('readme')
  const [copyLabel, setCopyLabel] = useState('Copy')

  const fetchStatus = useCallback(async () => {
    try {
      const res = await getUniversalStatus(id)
      setProject(res.data)
      return res.data
    } catch {
      setProject(s => s ? s : null)
      return null
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    let interval = null
    const poll = async () => {
      const data = await fetchStatus()
      if (data && (data.status === 'pending' || data.status === 'processing')) {
        if (!interval) interval = setInterval(poll, 4000)
      } else {
        if (interval) { clearInterval(interval); interval = null }
      }
    }
    poll()
    return () => { if (interval) clearInterval(interval) }
  }, [fetchStatus])

  useEffect(() => {
    if (!project || project.status !== 'done') return
    const tabs = buildDocTabs(project.docs)
    if (tabs.length > 0) setActiveTab(tabs[0].id)
  }, [project?.status])

  if (loading && !project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center space-y-3">
          <IconWarning className="w-12 h-12 mx-auto text-warning" />
          <p className="text-ink-secondary text-sm">Project not found</p>
          <Link to="/dashboard" className="btn-accent inline-block text-xs font-mono px-6 py-2">Back to Dashboard</Link>
        </div>
      </div>
    )
  }

  const t = getMode(project.mode || 'universal')
  const Icon = t.icon
  const isDone = project.status === 'done'
  const docs = project.docs || ''
  const docTabs = buildDocTabs(docs)

  if (project.status === 'processing') {
    return (
      <div className="min-h-screen bg-bg-primary text-ink-primary font-body">
        <Helmet><title>Generating... - PyDocAI</title></Helmet>
        <Navbar />
        <div className="flex items-center justify-center min-h-[calc(100vh-64px)]">
          <div className="text-center space-y-6 max-w-sm">
            <div className={`text-4xl ${t.accent}`}>{t.symbol}</div>
            <div className={`w-10 h-10 rounded-full border-2 mx-auto border-t-transparent animate-spin ${t.accent.replace('text-', 'border-').replace(/-\w+$/, '-500')}`} style={{ borderColor: `${t.primary}33`, borderTopColor: t.primary }} />
            <div>
              <p className={`text-lg font-display font-bold ${t.accent}`}>{t.label} is generating your documentation...</p>
              <p className="text-sm text-ink-muted mt-1">This usually takes a moment</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (project.status === 'failed') {
    return (
      <div className="min-h-screen bg-bg-primary text-ink-primary font-body">
        <Helmet><title>Generation Failed - PyDocAI</title></Helmet>
        <Navbar />
        <div className="flex items-center justify-center min-h-[calc(100vh-64px)]">
          <div className="text-center space-y-6 max-w-md">
            <div className={`w-14 h-14 mx-auto rounded-md border border-border bg-bg-surface flex items-center justify-center ${t.accent}`}>
              <IconWarning className="w-7 h-7" />
            </div>
            <div>
              <p className={`text-xl font-display font-bold ${t.accent}`}>Generation Failed</p>
              <p className="text-sm text-ink-secondary mt-2">{project.error || project.docs || 'An unexpected error occurred.'}</p>
            </div>
            <Link to="/dashboard" className="btn-accent inline-block text-xs font-mono px-6 py-2">Back to Dashboard</Link>
          </div>
        </div>
      </div>
    )
  }

  const activeContent = docTabs.find(t => t.id === activeTab)?.content || ''
  const normalizedContent = normalizeMarkdown(activeContent)

  const handleCopy = async () => {
    if (!normalizedContent) return
    await navigator.clipboard.writeText(normalizedContent)
    setCopyLabel('Copied!')
    setTimeout(() => setCopyLabel('Copy'), 2000)
    addToast('Content copied to clipboard.', 'success')
  }

  const handleDownload = () => {
    if (!normalizedContent) return
    const tab = docTabs.find(t => t.id === activeTab)
    const filename = `${project?.name || 'docs'}_${tab?.id || 'doc'}.md`
    const blob = new Blob([normalizedContent], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Helmet>
        <title>{project?.name ? `${project.name} — ${t.label}` : 'Documentation — PyDocAI'}</title>
        <meta name="description" content={project?.description ? `AI-generated documentation for ${project.name}: ${project.description}` : 'View your AI-generated project documentation.'} />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* ── LEFT SIDEBAR ── */}
        <aside className="w-72 flex-shrink-0 border-r border-border bg-[#0b1320] flex flex-col overflow-y-auto">
          <div className="p-5">
            <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest border-b border-border/40 pb-2">
              Project Properties
            </div>

            <div className="space-y-4 font-mono text-xs mt-4">
              <div>
                <span className="text-[10px] text-ink-muted uppercase">Name</span>
                <p className="font-bold text-accent truncate">{project.name}</p>
              </div>
              <div>
                <span className="text-[10px] text-ink-muted uppercase">Mode</span>
                <p className={`font-bold ${t.accent}`}>{t.label}</p>
              </div>
              <div>
                <span className="text-[10px] text-ink-muted uppercase">Status</span>
                <p className={`font-bold ${isDone ? 'text-success' : 'text-warning'}`}>
                  {project.status.toUpperCase()}
                </p>
              </div>
              {project.description && (
                <div>
                  <span className="text-[10px] text-ink-muted uppercase">Description</span>
                  <p className="text-ink-secondary text-[11px]">{project.description}</p>
                </div>
              )}
            </div>

            {isDone && (
              <>
                <div className="space-y-3 pt-4 mt-4 border-t border-border/40">
                  <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest block">
                    Documentation
                  </span>
                  <nav className="space-y-1">
                    {docTabs.map((tab) => {
                      const isActive = activeTab === tab.id
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs font-mono transition-all duration-150 ${
                            isActive
                              ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/30'
                              : 'text-ink-secondary hover:bg-bg-elevated/50'
                          }`}
                        >
                          <tab.icon className="w-3.5 h-3.5 flex-shrink-0" />
                          {tab.label}
                        </button>
                      )
                    })}
                  </nav>
                </div>

                <div className="mt-6 space-y-2">
                  <button onClick={handleCopy} className="btn-ghost w-full py-2.5 text-xs font-mono">
                    {copyLabel}
                  </button>
                  <button onClick={handleDownload} className="btn-accent w-full py-2.5 text-xs font-mono">
                    Download .md
                  </button>
                </div>
              </>
            )}
          </div>
        </aside>

        {/* ── MAIN CONTENT ── */}
        <main className="flex-1 min-w-0 bg-code/20 flex flex-col overflow-y-auto relative">
          {isDone && (
            <div className="sticky top-0 z-20 bg-bg-surface/95 backdrop-blur border-b border-border flex items-center px-4 py-2 font-mono text-xs shadow-sm">
              <span className="text-ink-muted mr-2">active_file:</span>
              <span className="text-accent font-bold">/{docTabs.find(t => t.id === activeTab)?.label || 'docs.md'}</span>
              <span className="ml-auto text-[10px] text-ink-muted uppercase tracking-wider">{project.name}</span>
            </div>
          )}

          <div className="flex-1 max-w-4xl w-full mx-auto px-6 py-8">
            {!isDone ? (
              <StatusDisplay status={project.status} error={project.error} mode={project.mode} />
            ) : (
              <div className="glass-card bg-code/40 border border-border rounded-2xl p-8 shadow-2xl">
                <VsCodeMarkdown markdown={normalizedContent} />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}


