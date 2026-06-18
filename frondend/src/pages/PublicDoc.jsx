import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { getPublicProject } from '../api'
import { IconUser, IconClock, IconBook, IconCode, IconFile, IconMessage, IconSparkles } from '../components/Icons'
import CommentSection from '../components/CommentSection'
import Navbar from '../components/Navbar'

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Fira Code, monospace',
  suppressErrorRendering: true,
})

const TABS = [
  { id: 'documentation', label: 'Documentation', icon: IconBook, field: 'generated_docs' },
  { id: 'readme', label: 'README', icon: IconFile, field: 'readme_docs' },
  { id: 'api', label: 'API Reference', icon: IconCode, field: 'api_docs' },
  { id: 'comments', label: 'Comments', icon: IconMessage, field: null },
]

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
      } catch {
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

export default function PublicDoc() {
  const { slug } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [activeTab, setActiveTab] = useState('documentation')

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const res = await getPublicProject(slug)
        setProject(res.data)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    fetchProject()
  }, [slug])

  useEffect(() => {
    if (!project) return
    const hash = window.location.hash
    if (hash.startsWith('#comment-')) {
      setActiveTab('comments')
      const targetId = hash.slice(1)
      let attempts = 0
      const interval = setInterval(() => {
        const el = document.getElementById(targetId)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' })
          clearInterval(interval)
        }
        if (++attempts > 50) clearInterval(interval)
      }, 200)
      return () => clearInterval(interval)
    }
    const first = TABS.find(t => {
      if (t.id === 'comments') return true
      return project[t.field]?.trim()
    })
    if (first) setActiveTab(first.id)
  }, [project])

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <p className="text-ink-muted text-sm font-mono">Loading...</p>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center font-mono text-xs">
          <p className="text-ink-muted mb-4">Project not found</p>
          <Link to="/published" className="btn-accent inline-block">Browse published projects</Link>
        </div>
      </div>
    )
  }

  const tabs = TABS.filter(t => {
    if (t.id === 'comments') return true
    return project[t.field]?.trim()
  })

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  }

  const isGithub = project.source_type === 'github' || !!project.github_url

  const renderMarkdown = (content) => {
    if (!content) return null
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
              const codeStr = String(children).replace(/\n$/, '')
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
                    <span className="text-[10px] font-mono text-ink-muted uppercase tracking-widest">{match ? match[1] : 'code'}</span>
                  </div>
                  <pre className="p-4 m-0 text-xs font-mono text-ink-secondary overflow-x-auto">{codeStr}</pre>
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
          {content}
        </ReactMarkdown>
      </div>
    )
  }

  const renderContent = (content) => {
    const hasOuterFence = /^```(?:markdown|md)?\s*\n/.test(content || '')
    const processed = normalizeMarkdown(
      hasOuterFence
        ? (content || '').replace(/^```(?:markdown|md)?\s*\n/, '').replace(/\n```\s*$/, '')
        : (content || '')
    )
    return renderMarkdown(processed)
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Helmet>
        <title>{project.name} — PyDocAI</title>
        <meta name="description" content={project.description || `Documentation for ${project.name}`} />
      </Helmet>
      <Navbar />

      <div className="max-w-4xl mx-auto px-4 py-10 flex-1 w-full">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-ink-primary mb-2">{project.name}</h1>
          {project.description && (
            <p className="text-ink-secondary text-sm mb-4">{project.description}</p>
          )}
          <div className="flex items-center gap-4 text-xs text-ink-muted font-mono flex-wrap">
            <span className="flex items-center gap-1">
              <IconUser className="w-3.5 h-3.5" />
              {project.user_name}
            </span>
            <span className="flex items-center gap-1">
              <IconClock className="w-3.5 h-3.5" />
              Created {formatDate(project.created_at)}
            </span>
            {project.updated_at && project.updated_at !== project.created_at && (
              <span className="flex items-center gap-1">
                <IconClock className="w-3.5 h-3.5" />
                Updated {formatDate(project.updated_at)}
              </span>
            )}
            {isGithub && project.github_url && (
              <a
                href={project.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-accent-blue hover:text-accent"
              >
                <IconSparkles className="w-3.5 h-3.5" />
                {project.github_branch ? `github.com/${project.github_url.replace(/^https?:\/\/github\.com\//, '').replace(/\/$/, '')} (${project.github_branch})` : project.github_url}
              </a>
            )}
          </div>
        </div>

        <div className="flex border-b border-border mb-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-mono transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-accent-blue text-ink-primary'
                  : 'text-ink-muted hover:text-ink-primary border-b-2 border-transparent'
              }`}
            >
              <tab.icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="mb-8 min-h-[200px]">
          {activeTab === 'documentation' && renderContent(project.generated_docs)}
          {activeTab === 'readme' && renderContent(project.readme_docs)}
          {activeTab === 'api' && renderContent(project.api_docs)}
          {activeTab === 'comments' && (
            <CommentSection projectId={project.id} isPublic={true} />
          )}
        </div>
      </div>
    </div>
  )
}