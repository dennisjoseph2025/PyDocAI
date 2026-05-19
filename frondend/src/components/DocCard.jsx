import { Link } from 'react-router-dom'

const typeBadge = {
  files: 'text-blue-400 border-blue-400/30 bg-blue-400/10',
  git: 'text-success border-success/30 bg-success/10',
  folder: 'text-warning border-warning/30 bg-warning/10',
}

export default function DocCard({ doc, onDelete }) {
  const badge = typeBadge[doc.source_type] || typeBadge.files

  return (
    <tr className="border-t border-border hover:bg-bg-elevated/50 transition-colors">
      <td className="px-6 py-4 text-sm">
        <Link to={`/output/${doc.id}`} className="text-ink-primary hover:text-accent transition-colors font-medium">
          {doc.name || 'Untitled'}
        </Link>
      </td>
      <td className="px-6 py-4">
        <span className={`text-xs font-mono px-2 py-0.5 rounded border ${badge}`}>
          {doc.source_type || 'files'}
        </span>
      </td>
      <td className="px-6 py-4 text-sm text-ink-secondary">
        {new Date(doc.created_at).toLocaleDateString('en-US', {
          month: 'short', day: 'numeric', year: 'numeric',
        })}
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-1">
          <Link
            to={`/output/${doc.id}`}
            className="p-1.5 rounded-lg hover:bg-bg-elevated text-ink-muted hover:text-ink-primary transition-all"
            title="View"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </Link>
          <button
            onClick={() => onDelete(doc.id)}
            className="p-1.5 rounded-lg hover:bg-bg-elevated text-ink-muted hover:text-danger transition-all"
            title="Delete"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </td>
    </tr>
  )
}
