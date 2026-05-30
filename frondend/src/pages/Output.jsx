import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { getProjectDetail } from '../api'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  IconWarning, IconFile, IconX, IconBook, IconPuzzle,
  IconDatabase, IconClipboard, IconCheck, IconDownload,
  IconSparkles, IconArchive, IconSearch,
} from '../components/Icons'

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
  normalized = normalized.replace(/(^|\n)mermaid\s*\n(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|gantt|pie|erDiagram|journey|gitGraph)/g, '$1```mermaid\n$2')
  normalized = normalized.replace(/(^|\n)((?:flowchart|graph)\s+(?:TD|LR|RL|BT)[\s\S]+?)(?=\n{2,}|\n#{1,6}\s|$)/g, '$1```mermaid\n$2\n```')
  normalized = normalized.replace(/```mermaid\n([\s\S]*?)(\n##|\n###|\n#|\n---\n|$)/g, (match, content, ending) => {
    const trimmed = content.trim()
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
        if (isMounted) {
          setSvgData(svg)
          setError(false)
        }
      } catch (err) {
        if (isMounted) setError(true)
      }
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

  return (
    <div className="my-6 p-6 bg-code border border-border rounded-xl flex justify-center overflow-x-auto" dangerouslySetInnerHTML={{ __html: svgData }} />
  )
}

function VsCodeMarkdown({ markdown }) {
  if (!markdown) {
    return (
      <div className="text-center py-20 text-ink-muted">
        <p className="text-accent mb-4"><IconFile className="w-10 h-10 mx-auto" /></p>
        <p className="text-xs font-mono">No target workspace payload parsed.</p>
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
                  <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest">{lang || 'py-code'}</span>
                  <CopyButton text={codeStr} />
                </div>
                <SyntaxHighlighter
                  PreTag="div"
                  language={lang || 'python'}
                  style={vscDarkPlus}
                  customStyle={{
                    margin: 0,
                    padding: '16px',
                    background: '#080e17',
                    fontSize: '12px',
                    lineHeight: '1.5',
                  }}
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
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
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

function StatusDisplay({ status, error }) {
  if (status === 'failed') {
    return (
      <div className="text-center py-24 font-mono text-xs">
        <p className="text-danger mb-4">[compiler_critical_exception] compilation aborted.</p>
        <p className="text-ink-secondary max-w-md mx-auto">{error || 'Unknown syntax error during directory compilation.'}</p>
        <Link to="/input" className="btn-accent inline-block mt-8">RESTART_COMPILER()</Link>
      </div>
    )
  }
  return (
    <div className="text-center py-24 font-mono text-xs text-accent-blue space-y-4">
      <div className="w-12 h-12 rounded-full border-4 border-t-accent-blue border-r-transparent animate-spin mx-auto" />
      <h2 className="text-ink-primary">COMPILING_WORKSPACE() - RUNNING SYNTAX PIPELINES</h2>
      <p className="text-ink-muted">Estimated compilation runtime: 15s - 30s. Auto-refreshing context variables...</p>
    </div>
  )
}

const DOC_TABS = [
  { id: 'readme', label: 'README.md', icon: IconBook, field: 'readme_docs', hint: 'Overview & system instructions' },
  { id: 'api', label: 'endpoints.py', icon: IconPuzzle, field: 'api_docs', hint: 'API interfaces, endpoints, schemas' },
  { id: 'summary', label: 'architect.json', icon: IconDatabase, field: 'generated_docs', hint: 'Syntax breakdown & module hierarchies' },
]

export default function Output() {
  const { docId } = useParams()
  const { addToast } = useAuth()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('readme')
  const [copyLabel, setCopyLabel] = useState('COPY_MD()')

  const rawContent = project ? project[DOC_TABS.find(t => t.id === activeTab)?.field] || '' : ''
  const activeContent = normalizeMarkdown(rawContent.replace(/^```(?:markdown|md)?\s*\n/, '').replace(/\n```\s*$/, ''))

  const load = useCallback(async () => {
    try {
      const res = await getProjectDetail(docId)
      setProject(res.data)
      return res.data
    } catch (err) {
      addToast('Pipeline load failed.', 'error')
      return null
    } finally {
      setLoading(false)
    }
  }, [docId, addToast])

  useEffect(() => {
    let interval = null
    const poll = async () => {
      const data = await load()
      if (data && (data.status === 'pending' || data.status === 'processing')) {
        if (!interval) interval = setInterval(poll, 3000)
      } else {
        clearInterval(interval)
        interval = null
      }
    }
    poll()
    return () => { if (interval) clearInterval(interval) }
  }, [load])

  useEffect(() => {
    if (!project) return
    const first = DOC_TABS.find(t => project[t.field]?.trim())
    if (first) setActiveTab(first.id)
  }, [project?.status])

  const handleCopy = async () => {
    if (!activeContent) return
    await navigator.clipboard.writeText(activeContent)
    setCopyLabel('COPIED!')
    setTimeout(() => setCopyLabel('COPY_MD()'), 2000)
    addToast('Content copied to local clipboard.', 'success')
  }

  const handleDownload = () => {
    if (!activeContent) return
    const tab = DOC_TABS.find(t => t.id === activeTab)
    const filename = `${project?.name || 'docs'}_${tab?.id || 'doc'}.md`
    const blob = new Blob([activeContent], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading && !project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <LoadingSpinner size="lg" className="text-accent" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center text-xs font-mono">
        <p className="text-ink-muted">Workspace catalog target ID not found.</p>
      </div>
    )
  }

  const isDone = project.status === 'done'

  return (
    <div className="relative z-10 h-screen bg-bg-primary overflow-hidden flex flex-col">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* ── LEFT SIDEBAR ── */}
        <aside className="w-72 flex-shrink-0 border-r border-border bg-[#0b1320] flex flex-col">
          <div className="p-5 flex-1 overflow-y-auto custom-scrollbar">
            <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest border-b border-border/40 pb-2">
              Workspace Properties
            </div>
            
            <div className="space-y-4 font-mono text-xs mt-4">
              <div>
                <span className="text-[10px] text-ink-muted uppercase">SYS_PACKAGE</span>
                <p className="font-bold text-accent truncate">{project.name}</p>
              </div>
              <div>
                <span className="text-[10px] text-ink-muted uppercase">STATUS</span>
                <p className={`font-bold ${isDone ? 'text-success' : 'text-warning animate-pulse'}`}>
                  {project.status.toUpperCase()}
                </p>
              </div>
              <div>
                <span className="text-[10px] text-ink-muted uppercase">SOURCE</span>
                <p className="text-ink-secondary">{project.source_type}</p>
              </div>
            </div>

            {isDone && (
              <div className="space-y-3 pt-4 mt-4 border-t border-border/40">
                <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest block">Module index</span>
                <nav className="space-y-1">
                  {DOC_TABS.map((tab) => {
                    const hasContent = !!project[tab.field]?.trim()
                    return (
                      <button
                        key={tab.id}
                        disabled={!hasContent}
                        onClick={() => setActiveTab(tab.id)}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs font-mono transition-all duration-150 ${
                          activeTab === tab.id && hasContent
                            ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/30'
                            : hasContent
                            ? 'text-ink-secondary hover:bg-bg-elevated/50'
                            : 'text-ink-muted opacity-40 cursor-not-allowed'
                        }`}
                      >
                        {tab.label}
                      </button>
                    )
                  })}
                </nav>
              </div>
            )}
          </div>

          {isDone && (
            <div className="p-6 border-t border-border/40 space-y-2">
              <button onClick={handleCopy} className="btn-ghost w-full py-2.5 text-xs font-mono">
                {copyLabel}
              </button>
              <button onClick={handleDownload} className="btn-accent w-full py-2.5 text-xs font-mono">
                DOWNLOAD_FILE()
              </button>
            </div>
          )}
        </aside>

        {/* IDE Document View Window */}
        {/* ADDED 'overflow-y-auto' HERE SO THE DOCUMENT BODY CAN SCROLL */}
        <main className="flex-1 min-w-0 bg-code/20 flex flex-col overflow-y-auto relative">
          {isDone && (
            <div className="sticky top-0 z-20 bg-bg-surface/95 backdrop-blur border-b border-border flex items-center px-4 py-2 font-mono text-xs shadow-sm">
              <span className="text-ink-muted mr-2">active_file:</span>
              <span className="text-accent font-bold">/{DOC_TABS.find(t => t.id === activeTab)?.label}</span>
              <span className="ml-auto text-[10px] text-ink-muted uppercase tracking-wider">{project.name} Workspace</span>
            </div>
          )}

          <div className="flex-1 max-w-4xl w-full mx-auto px-6 py-8">
            {!isDone ? (
              <StatusDisplay status={project.status} error={project.error_message} />
            ) : (
              <div className="glass-card bg-code/40 border border-border rounded-2xl p-8 shadow-2xl">
                <VsCodeMarkdown markdown={activeContent} />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}