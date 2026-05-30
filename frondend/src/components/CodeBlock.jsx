import { useState } from 'react'

export default function CodeBlock({ code, filename = '', language = 'python' }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const highlight = (src) => {
    if (!src) return ''
    const escaped = src
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')

    return escaped
      // Comments
      .replace(/(#.*)/g, '<span class="text-ink-muted italic">$1</span>')
      // Strings (double/single quoted)
      .replace(/(["'`])(?:(?=(\\?))\2.)*?\1/g, '<span class="text-green-400">$&</span>')
      // Keywords
      .replace(
        /\b(from|import|class|def|return|if|elif|else|for|while|try|except|finally|with|as|yield|lambda|True|False|None|self|raise|pass|break|continue|and|or|not|in|is)\b/g,
        '<span class="text-accent-blue font-bold">$1</span>'
      )
      // Numbers
      .replace(/\b(\d+\.?\d*)\b/g, '<span class="text-accent">$1</span>')
      // Decorators
      .replace(/(@\w+)/g, '<span class="text-yellow-200">$1</span>')
  }

  return (
    <div className="bg-code border border-border rounded-xl overflow-hidden shadow-lg">
      <div className="flex items-center justify-between px-4 py-2 bg-bg-elevated border-b border-border">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-danger/80" />
            <div className="w-3 h-3 rounded-full bg-warning/80" />
            <div className="w-3 h-3 rounded-full bg-success/80" />
          </div>
          {filename && (
            <span className="text-xs font-mono text-ink-muted ml-2">{filename}</span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="text-xs font-mono text-ink-muted hover:text-ink-primary transition-colors flex items-center gap-1"
        >
          {copied ? (
            <><svg className="w-3 h-3 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>Copied</>
          ) : (
            <><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</>
          )}
        </button>
      </div>
      <pre className="p-5 font-mono text-sm overflow-x-auto leading-relaxed">
        <code dangerouslySetInnerHTML={{ __html: highlight(code) }} />
      </pre>
    </div>
  )
}