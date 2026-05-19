import useAuth from '../hooks/useAuth'

const icons = {
  success: (
    <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  info: (
    <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z" />
    </svg>
  ),
}

const borderColors = {
  success: 'border-l-success',
  error: 'border-l-danger',
  info: 'border-l-accent',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useAuth()

  if (!toasts.length) return null

  return (
    <div id="toast-container" className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`glass-card px-5 py-3 flex items-center gap-3 min-w-[18rem] animate-slide-up shadow-glow-lg border-l-4 ${borderColors[toast.type] || borderColors.info}`}
        >
          {icons[toast.type] || icons.info}
          <span className="text-sm text-ink-primary flex-1">{toast.message}</span>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-ink-muted hover:text-ink-primary transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  )
}
