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

/* ──────────────────────────────────────────────
   Mermaid Renderer Component
   ────────────────────────────────────────────── */
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'JetBrains Mono, monospace',
  suppressErrorRendering: true,
})

/* Sanitize Mermaid chart syntax to fix common AI-generated errors */
function sanitizeMermaid(chart) {
  if (!chart) return chart
  let sanitized = chart

  // Fix '-->|text|>' → '-->|text|' (extra trailing bracket)
  sanitized = sanitized.replace(/-->\|([^|]*)\|>/g, '-->|$1|')
  // Fix '-->>' → '-->'
  sanitized = sanitized.replace(/-->>/g, '-->')
  // Fix '-.->|text|>' → '-.->|text|'
  sanitized = sanitized.replace(/-\.->\|([^|]*)\|>/g, '-.->|$1|')
  // Fix '==>|text|>' → '==>|text|'
  sanitized = sanitized.replace(/==>\|([^|]*)\|>/g, '==>|$1|')

  // Ensure diagram starts with a valid mermaid type declaration
  // Valid starters: graph, flowchart, sequenceDiagram, classDiagram, etc.
  const firstLine = sanitized.trimStart().split('\n')[0].trim()
  const validTypes = /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|gantt|pie|erDiagram|journey|gitGraph|quadrantChart|requirementDiagram)/i
  if (!validTypes.test(firstLine)) {
    // Prepend graph TD if the content looks like a flowchart (has -->, -.-, ==> etc.)
    if (/-->|-\.->|==>|~~>/.test(sanitized)) {
      sanitized = 'graph TD\n' + sanitized
    }
  }

  // Force graph TD for any graph statement missing direction
  sanitized = sanitized.replace(/^graph\s*$/m, 'graph TD')
  sanitized = sanitized.replace(/^graph\s+(?:LR|RL|BT)\s*$/m, (m) => m.trim())

  return sanitized
}

/* Normalize markdown to ensure proper rendering by react-markdown */
function normalizeMarkdown(text) {
  if (!text) return text
  
  // Replace literal \n sequences with actual newlines (fixes double-escaped JSON)
  let normalized = text.replace(/\\n/g, '\n')
  
  // Remove "code" and "Copy" artifacts from AI output (must do this before other fixes)
  normalized = normalized.replace(/\n?\s*code\s*\n\s*Copy\s*\n?/g, '\n')
  
  // Fix mermaid code blocks: detect mermaid diagrams and wrap them properly
  // Case 1: "mermaid" on its own line followed by graph/flowchart/etc
  normalized = normalized.replace(/(^|\n)mermaid\s*\n(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|gantt|pie|erDiagram|journey|gitGraph)/g, '$1```mermaid\n$2')
  
  // Case 2: Ensure closing ``` for mermaid blocks that don't have it
  // Match from ```mermaid to the next heading or end of content
  normalized = normalized.replace(/```mermaid\n([\s\S]*?)(\n##|\n###|\n#|\n---\n|$)/g, (match, content, ending) => {
    const trimmed = content.trim()
    if (trimmed.endsWith('```')) {
      return '```mermaid\n' + trimmed + '\n' + ending
    }
    return '```mermaid\n' + trimmed + '\n```\n' + ending
  })
  
  // Fix code blocks: ensure ``` is on its own line
  normalized = normalized.replace(/([^\n])```/g, '$1\n```')
  normalized = normalized.replace(/```([^\n])/g, '```\n$1')
  
  // Ensure blank line before headings (### ## #)
  normalized = normalized.replace(/([^\n])\n(#{1,6} )/g, '$1\n\n$2')
  
  // Ensure blank line after headings
  normalized = normalized.replace(/(#{1,6} .+)\n([^\n#])/g, '$1\n\n$2')
  
  // Ensure blank line before list items that follow non-list content
  normalized = normalized.replace(/([^\n\-*])\n(\s*[-*] )/g, '$1\n\n$2')
  
  // Ensure blank line after list blocks before headings
  normalized = normalized.replace(/(\n\s*[-*] .+)\n+(#{1,6} )/g, '$1\n\n$2')
  
  // Fix bold/list items that lost their formatting
  normalized = normalized.replace(/\n-\s+\*\*(Description|Input Payload|Output Response|Authentication|Request Headers|Path Parameters|Query Parameters|Request Body|Response|Status Codes|Example Usage)\*\*/g, '\n\n- **$1**')
  
  // Remove excessive blank lines (more than 2)
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
        console.error('Mermaid render error', err)
        if (isMounted) setError(true)
      }
    }
    renderChart()
    return () => { isMounted = false }
  }, [chart])

  if (error) {
    return (
      <div className="my-4 rounded-md overflow-hidden border border-danger/30">
        <div className="bg-danger/10 text-danger text-xs px-4 py-2 border-b border-danger/30 font-mono flex items-center justify-between">
          <span><IconWarning className="w-3 h-3 inline mr-1" /> Diagram Generation Failed (Invalid Syntax)</span>
        </div>
        <pre className="p-4 bg-[#1e1e1e] text-[#858585] text-[11px] font-mono overflow-x-auto m-0">
          {chart}
        </pre>
      </div>
    )
  }

  return (
    <div 
      className="my-6 p-6 bg-[#1e1e1e] border border-[#3e3e42] rounded-md flex justify-center overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svgData }}
    />
  )
}

/* ──────────────────────────────────────────────
   VS Code-style Markdown renderer
   Matches the look of Ctrl+Shift+V in VS Code
   ────────────────────────────────────────────── */
function VsCodeMarkdown({ markdown }) {
  if (!markdown) {
    return (
      <div className="text-center py-20 text-ink-muted">
        <p className="text-accent mb-4"><IconFile className="w-10 h-10 mx-auto" /></p>
        <p>No content available for this document type.</p>
      </div>
    )
  }

  return (
    <div className="vscode-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          /* Headings */
          h1: ({ node, ...props }) => (
            <h1
              className="text-[2em] font-bold text-ink-primary mt-0 mb-4 pb-2 border-b border-[#3e3e42] leading-tight"
              {...props}
            />
          ),
          h2: ({ node, ...props }) => (
            <h2
              className="text-[1.5em] font-bold text-ink-primary mt-8 mb-3 pb-2 border-b border-[#3e3e42] leading-tight"
              {...props}
            />
          ),
          h3: ({ node, ...props }) => (
            <h3
              className="text-[1.25em] font-bold text-ink-primary mt-6 mb-2 leading-tight"
              {...props}
            />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-[1em] font-bold text-ink-primary mt-5 mb-2" {...props} />
          ),
          h5: ({ node, ...props }) => (
            <h5 className="text-[0.875em] font-bold text-ink-primary mt-4 mb-2" {...props} />
          ),
          h6: ({ node, ...props }) => (
            <h6 className="text-[0.85em] font-bold text-ink-muted mt-4 mb-2" {...props} />
          ),

          /* Paragraph */
          p: ({ node, ...props }) => {
            // Check if paragraph contains a mermaid diagram
            const children = props.children
            if (children && typeof children === 'string') {
              const mermaidMatch = children.match(/^(?:mermaid\s*\n)?(graph\s+[A-Z]+[\s\S]+)$/i)
              if (mermaidMatch) {
                const chart = mermaidMatch[1].trim()
                if (chart.includes('-->') || chart.includes('~~>') || chart.includes('-.-')) {
                  return <MermaidDiagram chart={chart} />
                }
              }
            }
            return (
              <p className="text-[#cccccc] leading-[1.6] mb-4 text-[14px]" {...props} />
            )
          },

          /* Lists */
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-6 mb-4 space-y-1 text-[#cccccc] text-[14px]" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-6 mb-4 space-y-1 text-[#cccccc] text-[14px]" {...props} />
          ),
          li: ({ node, ...props }) => <li className="leading-[1.6]" {...props} />,

          /* Horizontal rule */
          hr: () => <hr className="border-t border-[#3e3e42] my-6" />,

          /* Block code wrapper */
          pre: ({ node, children, ...props }) => <>{children}</>,

          /* Code — inline vs block */
          code: ({ node, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '')
            const lang = match ? match[1] : ''
            let codeStr = String(children).replace(/\n$/, '')
            
            // Clean up AI artifacts from code blocks
            codeStr = codeStr.replace(/^code\s*\n\s*Copy\s*\n?/i, '').trim()
            
            // In react-markdown v9+, inline is not passed. 
            // We infer it's block if it has a language match or contains newlines.
            const isBlock = match || codeStr.includes('\n')

            if (!isBlock) {
              return (
                <code
                  className="font-mono text-[#ce9178] bg-[#1e1e1e] border border-[#3e3e42] px-1.5 py-0.5 rounded text-[0.875em]"
                  {...props}
                >
                  {children}
                </code>
              )
            }

            // Detect mermaid diagrams even if lang isn't set but content starts with "mermaid"
            if (lang === 'mermaid' || codeStr.startsWith('mermaid\n')) {
              let chart = codeStr.replace(/^mermaid\s*\n/, '').trim()
              return <MermaidDiagram chart={chart} />
            }

            return (
              <div className="my-4 rounded-md overflow-hidden border border-[#3e3e42]">
                {/* VS Code title bar */}
                <div className="flex items-center justify-between bg-[#252526] px-4 py-1.5 border-b border-[#3e3e42]">
                  <span className="text-[11px] font-mono text-[#858585] uppercase tracking-widest">
                    {lang || 'code'}
                  </span>
                  <CopyButton text={codeStr} />
                </div>
                <SyntaxHighlighter
                  PreTag="div"
                  language={lang || 'text'}
                  style={vscDarkPlus}
                  customStyle={{
                    margin: 0,
                    padding: '16px',
                    background: '#1e1e1e',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    borderRadius: 0,
                  }}
                  showLineNumbers={codeStr.split('\n').length > 5}
                  lineNumberStyle={{ color: '#4a4a6a', minWidth: '2.5em' }}
                >
                  {codeStr}
                </SyntaxHighlighter>
              </div>
            )
          },

          /* Blockquote */
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-[#4a9eff] pl-4 py-0.5 my-4 text-[#858585] italic"
              {...props}
            />
          ),

          /* Lists */
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-6 mb-4 space-y-1 text-[#cccccc] text-[14px]" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-6 mb-4 space-y-1 text-[#cccccc] text-[14px]" {...props} />
          ),
          li: ({ node, ...props }) => <li className="leading-[1.6]" {...props} />,

          /* Horizontal rule */
          hr: () => <hr className="border-t border-[#3e3e42] my-6" />,

          /* Tables */
          table: ({ node, ...props }) => (
            <div className="w-full overflow-x-auto my-6 rounded-md border border-[#3e3e42]">
              <table className="w-full text-[13px] border-collapse" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-[#252526]" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th
              className="text-left px-4 py-2 font-bold text-[#cccccc] border-b border-[#3e3e42] text-[12px] uppercase tracking-wider"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="px-4 py-2 border-t border-[#3e3e42] text-[#cccccc]"
              {...props}
            />
          ),
          tr: ({ node, ...props }) => (
            <tr className="hover:bg-[#2a2d2e] transition-colors" {...props} />
          ),

          /* Links */
          a: ({ node, ...props }) => (
            <a
              className="text-[#4a9eff] hover:text-[#6ab0ff] underline underline-offset-2"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),

          /* Images */
          img: ({ node, ...props }) => (
            <img className="max-w-full rounded-md my-4 border border-[#3e3e42]" {...props} />
          ),

          /* Strong / Em */
          strong: ({ node, ...props }) => (
            <strong className="font-bold text-[#dcdcdc]" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic text-[#cccccc]" {...props} />
          ),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}

/* Small inline copy-button used inside code block header */
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={copy}
      className="text-[11px] font-mono text-[#858585] hover:text-[#cccccc] transition-colors flex items-center gap-1"
    >
      {copied ? (
        <>
          <svg className="w-3 h-3 text-[#22d3a0]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Copied
        </>
      ) : (
        <>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy
        </>
      )}
    </button>
  )
}

/* ──────────────────────────────────────────────
   Processing / Error status panel
   ────────────────────────────────────────────── */
function StatusDisplay({ status, error }) {
  if (status === 'failed') {
    return (
      <div className="text-center py-24">
        <p className="text-danger mb-6"><IconX className="w-16 h-16 mx-auto" /></p>
        <h2 className="text-2xl font-display font-bold text-ink-primary mb-3">Analysis Failed</h2>
        <p className="text-ink-secondary max-w-md mx-auto text-sm leading-relaxed">
          {error || 'An unexpected error occurred during the analysis of your project.'}
        </p>
        <Link to="/input" className="btn-accent inline-block mt-8">
          Try Again
        </Link>
      </div>
    )
  }
  return (
    <div className="text-center py-24">
      <div className="relative w-20 h-20 mx-auto mb-8">
        <div className="absolute inset-0 rounded-full border-4 border-accent/10" />
        <div className="absolute inset-0 rounded-full border-4 border-t-accent border-r-accent/30 border-b-transparent border-l-transparent animate-spin" />
        <div className="absolute inset-2 rounded-full border-4 border-t-transparent border-r-transparent border-b-accent/40 border-l-accent/40 animate-spin-slow" />
      </div>
      <h2 className="text-2xl font-display font-bold text-ink-primary mb-3">
        {status === 'processing' ? 'AI is Analyzing...' : 'Preparing Workspace...'}
      </h2>
      <p className="text-ink-secondary max-w-md mx-auto text-sm leading-relaxed">
        Parsing your project structure, generating comprehensive documentation — this usually takes 15–30 seconds.
      </p>
      <p className="text-ink-muted text-xs mt-4 font-mono animate-pulse">
        Auto-refreshing every 3 seconds…
      </p>
    </div>
  )
}

/* ──────────────────────────────────────────────
   Doc tab definitions
   ────────────────────────────────────────────── */
const DOC_TABS = [
  {
    id: 'readme',
    label: 'README',
    icon: IconBook,
    field: 'readme_docs',
    hint: 'Project overview, installation & architecture',
  },
  {
    id: 'api',
    label: 'API Docs',
    icon: IconPuzzle,
    field: 'api_docs',
    hint: 'Endpoint reference, request/response schemas',
  },
  {
    id: 'summary',
    label: 'Summary',
    icon: IconDatabase,
    field: 'generated_docs',
    hint: 'Deep architectural analysis & code breakdown',
  },
]

/* ──────────────────────────────────────────────
   Main Output page
   ────────────────────────────────────────────── */
export default function Output() {
  const { docId } = useParams()
  const { addToast } = useAuth()

  const [project, setProject]       = useState(null)
  const [loading, setLoading]       = useState(true)
  const [activeTab, setActiveTab]   = useState('readme')
  const [copyLabel, setCopyLabel]   = useState('Copy Markdown')

  /* Determine which tabs have content */
  const availableTabs = project
    ? DOC_TABS.filter((t) => project[t.field]?.trim())
    : DOC_TABS

  /* Active content */
  const rawContent = project
    ? project[DOC_TABS.find((t) => t.id === activeTab)?.field] || ''
    : ''
    
  /* Strip out wrapping markdown fences and normalize formatting */
  const activeContent = normalizeMarkdown(
    rawContent.replace(/^```(?:markdown|md)?\s*\n/, '').replace(/\n```\s*$/, '')
  )

  /* ── Polling loader ── */
  const load = useCallback(async () => {
    try {
      const res = await getProjectDetail(docId)
      const data = res.data
      setProject(data)
      return data
    } catch (err) {
      console.error('Error loading project:', err)
      addToast('Failed to load documentation', 'error')
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

  /* When project loads, pick the first available tab */
  useEffect(() => {
    if (!project) return
    const first = DOC_TABS.find((t) => project[t.field]?.trim())
    if (first) setActiveTab(first.id)
  }, [project?.status])

  /* ── Actions ── */
  const handleCopy = async () => {
    if (!activeContent) return
    await navigator.clipboard.writeText(activeContent)
    setCopyLabel('Copied!')
    setTimeout(() => setCopyLabel('Copy Markdown'), 2000)
    addToast('Copied to clipboard!', 'success')
  }

  const handleDownload = () => {
    if (!activeContent) return
    const tab = DOC_TABS.find((t) => t.id === activeTab)
    const filename = `${project?.name || 'docs'}_${tab?.id || 'doc'}.md`
    const blob = new Blob([activeContent], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  /* ── Loading screen ── */
  if (loading && !project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <LoadingSpinner size="lg" className="text-accent" />
      </div>
    )
  }

  /* ── Not found ── */
  if (!project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <p className="text-accent mb-4"><IconSearch className="w-14 h-14 mx-auto" /></p>
          <p className="text-ink-muted text-lg mb-4">Documentation not found</p>
          <Link to="/input" className="text-accent hover:underline text-sm">
            Generate new docs →
          </Link>
        </div>
      </div>
    )
  }

  const isDone   = project.status === 'done'
  const isFailed = project.status === 'failed'
  const isFolder = project.source_type === 'folder'

  return (
    <div className="relative z-10 min-h-screen bg-bg-primary">
      <Navbar />

      <div className="flex min-h-[calc(100vh-64px)]">

        {/* ── LEFT SIDEBAR ── */}
        <aside className="w-72 flex-shrink-0 border-r border-border bg-bg-surface sticky top-16 h-[calc(100vh-64px)] overflow-y-auto hidden lg:flex flex-col">
          <div className="p-6 flex-1">

            {/* Project info */}
            <p className="font-mono text-[10px] text-ink-muted uppercase tracking-widest mb-5">
              Project Details
            </p>
            <div className="space-y-5 mb-8">
              <div>
                <p className="text-[10px] text-ink-muted uppercase tracking-wider mb-1">Name</p>
                <p className="text-sm font-semibold text-ink-primary font-display truncate">{project.name}</p>
              </div>
              <div>
                <p className="text-[10px] text-ink-muted uppercase tracking-wider mb-1">Status</p>
                <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full border ${
                  isDone   ? 'text-success border-success/30 bg-success/5' :
                  isFailed ? 'text-danger  border-danger/30  bg-danger/5'  :
                             'text-warning border-warning/30 bg-warning/5 animate-pulse'
                }`}>
                  {project.status}
                </span>
              </div>
              <div>
                <p className="text-[10px] text-ink-muted uppercase tracking-wider mb-1">Source</p>
                <p className="text-xs text-ink-secondary capitalize">{project.source_type}</p>
              </div>
              {project.description && (
                <div>
                  <p className="text-[10px] text-ink-muted uppercase tracking-wider mb-1">Description</p>
                  <p className="text-xs text-ink-secondary leading-relaxed line-clamp-3">{project.description}</p>
                </div>
              )}
              <div>
                <p className="text-[10px] text-ink-muted uppercase tracking-wider mb-1">Created</p>
                <p className="text-xs text-ink-secondary">
                  {new Date(project.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Doc-type nav (only shown when done) */}
            {isDone && (
              <>
                <p className="font-mono text-[10px] text-ink-muted uppercase tracking-widest mb-3">
                  Documents
                </p>
                <nav className="space-y-1">
                  {DOC_TABS.map((tab) => {
                    const hasContent = !!project[tab.field]?.trim()
                    return (
                      <button
                        key={tab.id}
                        disabled={!hasContent}
                        onClick={() => setActiveTab(tab.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-sm transition-all duration-150 ${
                          activeTab === tab.id && hasContent
                            ? 'bg-accent/15 text-accent border border-accent/30'
                            : hasContent
                            ? 'text-ink-secondary hover:text-ink-primary hover:bg-bg-elevated'
                            : 'text-ink-muted opacity-40 cursor-not-allowed'
                        }`}
                      >
                        <span className="text-base">{tab.icon}</span>
                        <div className="min-w-0">
                          <p className="font-medium truncate">{tab.label}</p>
                          <p className="text-[10px] text-ink-muted leading-tight truncate">{tab.hint}</p>
                        </div>
                        {hasContent && (
                          <span className="ml-auto text-[9px] font-mono text-success bg-success/10 px-1.5 py-0.5 rounded-full flex-shrink-0">
                            <IconCheck className="w-3 h-3" />
                          </span>
                        )}
                      </button>
                    )
                  })}
                </nav>
              </>
            )}
          </div>

          {/* Action buttons */}
          {isDone && (
            <div className="p-6 border-t border-border space-y-2">
              <button
                onClick={handleCopy}
                disabled={!activeContent}
                className="btn-ghost w-full text-sm flex items-center justify-center gap-2 disabled:opacity-40"
              >
                {copyLabel}
              </button>
              <button
                onClick={handleDownload}
                disabled={!activeContent}
                className="btn-accent w-full text-sm flex items-center justify-center gap-2 disabled:opacity-40"
              >
                <IconDownload className="w-4 h-4" /> Download .md
              </button>
              <Link
                to="/input"
                className="btn-ghost w-full text-sm flex items-center justify-center gap-2 border border-border"
              >
                <IconSparkles className="w-4 h-4" /> New Generation
              </Link>
            </div>
          )}
        </aside>

        {/* ── MAIN CONTENT ── */}
        <main className="flex-1 min-w-0">

          {/* ── Tab bar (top, VS Code style) ── */}
          {isDone && (
            <div className="sticky top-16 z-20 bg-[#1e1e1e] border-b border-[#3e3e42] flex items-center px-2 pt-1">
              {DOC_TABS.map((tab) => {
                const hasContent = !!project[tab.field]?.trim()
                const isActive   = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    disabled={!hasContent}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      relative flex items-center gap-2 px-4 py-2.5 text-sm font-mono transition-all duration-150
                      border-r border-[#3e3e42] min-w-[120px] justify-center
                      ${isActive
                        ? 'bg-[#1e1e1e] text-[#cccccc] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-[#7c6af7]'
                        : hasContent
                        ? 'bg-[#2d2d30] text-[#858585] hover:text-[#cccccc] hover:bg-[#252526]'
                        : 'bg-[#2d2d30] text-[#555] cursor-not-allowed opacity-50'
                      }
                    `}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.label}</span>
                    {!hasContent && (
                      <span className="text-[9px] text-[#555]">—</span>
                    )}
                  </button>
                )
              })}

              {/* Right side: source badge */}
              <div className="ml-auto px-4 flex items-center gap-3">
                {isFolder && (
                  <span className="text-[10px] font-mono text-[#858585] bg-[#252526] border border-[#3e3e42] px-2 py-0.5 rounded">
                    <IconArchive className="w-3 h-3" /> Folder Upload
                  </span>
                )}
                <span className="text-[10px] font-mono text-[#858585]">
                  {project.name}
                </span>
              </div>
            </div>
          )}

          {/* ── Document body ── */}
          <div className="max-w-4xl mx-auto">
            {!isDone ? (
              /* Processing / Error state */
              <div className="px-8 py-12">
                <StatusDisplay status={project.status} error={project.error_message} />
              </div>
            ) : (
              /* VS Code markdown preview body */
              <div className="px-10 py-10 animate-fade-in">
                {/* Current tab hint */}
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">
                      {DOC_TABS.find((t) => t.id === activeTab)?.icon}
                    </span>
                    <div>
                      <h1 className="text-xl font-display font-bold text-ink-primary leading-none">
                        {DOC_TABS.find((t) => t.id === activeTab)?.label}
                      </h1>
                      <p className="text-xs text-ink-muted mt-0.5">
                        {DOC_TABS.find((t) => t.id === activeTab)?.hint}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 lg:hidden">
                    <button
                      onClick={handleCopy}
                      className="btn-ghost text-xs px-3 py-1.5"
                    >
                      <IconClipboard className="w-3 h-3" /> Copy
                    </button>
                    <button
                      onClick={handleDownload}
                      className="btn-accent text-xs px-3 py-1.5"
                    >
                      <IconDownload className="w-3 h-3" /> Download
                    </button>
                  </div>
                </div>

                {/* Mobile tab switcher */}
                <div className="flex lg:hidden gap-1 bg-[#1e1e1e] border border-[#3e3e42] rounded-xl p-1 mb-6">
                  {DOC_TABS.map((tab) => {
                    const hasContent = !!project[tab.field]?.trim()
                    return (
                      <button
                        key={tab.id}
                        disabled={!hasContent}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg text-xs font-mono transition-all ${
                          activeTab === tab.id
                            ? 'bg-accent text-white'
                            : hasContent
                            ? 'text-[#858585] hover:text-[#cccccc]'
                            : 'text-[#555] opacity-50 cursor-not-allowed'
                        }`}
                      >
                        {tab.icon} {tab.label}
                      </button>
                    )
                  })}
                </div>

                {/* The actual VS Code-style rendered markdown */}
                <div
                  className="rounded-xl border border-[#3e3e42] overflow-hidden"
                  style={{ background: '#1e1e1e' }}
                >
                  <div className="px-8 py-8">
                    <VsCodeMarkdown markdown={activeContent} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
