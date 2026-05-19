import LoadingSpinner from './LoadingSpinner'

export default function StepIndicator({ steps }) {
  return (
    <div className="glass-card p-8 mt-8 animate-fade-in">
      <p className="font-display font-bold text-center mb-6 text-ink-primary">
        Generating your documentation...
      </p>
      <div className="space-y-4">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-4">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                step.done
                  ? 'bg-success'
                  : step.active
                  ? 'bg-accent animate-pulse-glow'
                  : 'bg-border'
              }`}
            >
              {step.done ? (
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : step.active ? (
                <LoadingSpinner size="sm" className="text-white" />
              ) : (
                <span className="text-xs text-ink-muted">{i + 1}</span>
              )}
            </div>
            <span
              className={`text-sm ${
                step.done
                  ? 'text-success'
                  : step.active
                  ? 'text-ink-primary'
                  : 'text-ink-muted'
              }`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
