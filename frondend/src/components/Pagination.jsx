export default function Pagination({ page, totalPages, totalCount, onPageChange }) {
  if (totalPages <= 1) return null

  const pages = []
  const maxVisible = 5
  let start = Math.max(1, page - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages, start + maxVisible - 1)
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return (
    <div className="flex items-center justify-between border-t border-border pt-4 mt-6">
      <span className="text-xs text-ink-muted font-mono">
        {totalCount} item{totalCount !== 1 ? 's' : ''}
      </span>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(1)}
          disabled={page === 1}
          className="px-2 py-1.5 text-xs font-mono text-ink-secondary hover:text-ink-primary disabled:text-ink-muted disabled:cursor-not-allowed transition-colors"
          title="First page"
        >
          ««
        </button>
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          className="px-2 py-1.5 text-xs font-mono text-ink-secondary hover:text-ink-primary disabled:text-ink-muted disabled:cursor-not-allowed transition-colors"
        >
          «
        </button>
        {start > 1 && (
          <span className="px-1 text-ink-muted text-xs">...</span>
        )}
        {pages.map((p) => (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`min-w-[32px] px-2 py-1.5 text-xs font-mono rounded-md transition-colors ${
              p === page
                ? 'bg-accent text-bg-primary font-bold'
                : 'text-ink-secondary hover:text-ink-primary hover:bg-bg-surface'
            }`}
          >
            {p}
          </button>
        ))}
        {end < totalPages && (
          <span className="px-1 text-ink-muted text-xs">...</span>
        )}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === totalPages}
          className="px-2 py-1.5 text-xs font-mono text-ink-secondary hover:text-ink-primary disabled:text-ink-muted disabled:cursor-not-allowed transition-colors"
        >
          »
        </button>
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={page === totalPages}
          className="px-2 py-1.5 text-xs font-mono text-ink-secondary hover:text-ink-primary disabled:text-ink-muted disabled:cursor-not-allowed transition-colors"
          title="Last page"
        >
          »»
        </button>
      </div>
    </div>
  )
}
