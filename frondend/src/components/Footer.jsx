import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer id="footer" className="border-t border-border bg-bg-primary py-8 sm:py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row justify-between items-center gap-4 sm:gap-6">
        <Link to="/" className="font-display font-bold text-base sm:text-lg order-2 md:order-1">
          <span className="text-ink-primary">Py</span>
          <span className="text-accent">Doc</span>
          <span className="text-ink-primary">AI</span>
        </Link>

        <div className="flex items-center gap-4 sm:gap-6 order-1 md:order-2">
          <a href="#features" className="text-ink-muted hover:text-ink-secondary text-xs sm:text-sm transition-colors">Features</a>
          <a href="https://github.com/dennisjoseph2025/PyDocAI" target="_blank" rel="noopener noreferrer" className="text-ink-muted hover:text-ink-secondary text-xs sm:text-sm transition-colors">GitHub</a>
        </div>

        <p className="text-ink-muted text-[10px] sm:text-sm order-3">
          &copy; {new Date().getFullYear()} PyDocAI. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
