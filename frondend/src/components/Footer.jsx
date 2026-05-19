import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer id="footer" className="border-t border-border bg-bg-primary py-12">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <Link to="/" className="font-display font-bold text-lg">
          <span className="text-ink-primary">Py</span>
          <span className="text-accent">Doc</span>
          <span className="text-ink-primary">AI</span>
        </Link>

        <div className="flex items-center gap-6">
          <a href="#features" className="text-ink-muted hover:text-ink-secondary text-sm transition-colors">Features</a>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-ink-muted hover:text-ink-secondary text-sm transition-colors">GitHub</a>
          <a href="#" className="text-ink-muted hover:text-ink-secondary text-sm transition-colors">Docs</a>
        </div>

        <p className="text-ink-muted text-sm">
          © {new Date().getFullYear()} PyDocAI. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
