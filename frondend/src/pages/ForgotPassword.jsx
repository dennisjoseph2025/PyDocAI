import { useState } from "react"
import { Link } from "react-router-dom"
import api from "../api"
import { IconMail, IconCheck } from "../components/Icons"
import LoadingSpinner from "../components/LoadingSpinner"

export default function ForgotPassword() {
  const [email, setEmail] = useState("")
  const [sent,  setSent]  = useState(false)
  const [err,   setErr]   = useState("")
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!email.trim()) { setErr("Email is required"); return }
    setErr("")
    setLoading(true)
    try {
      await api.post("/users/password-reset/", { email })
      setSent(true)
    } catch {
      setErr("Something went wrong. Try again.")
    } finally {
      setLoading(false)
    }
  }

  if (sent) return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4 relative z-10">
      <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
      <div className="glass-card w-full max-w-md p-10 animate-fade-in relative z-10 text-center">
        <div className="w-16 h-16 rounded-2xl bg-success/10 flex items-center justify-center mx-auto mb-6">
          <IconCheck className="w-8 h-8 text-success" />
        </div>
        <h1 className="font-display font-bold text-2xl text-ink-primary mb-2">Check Your Email</h1>
        <p className="text-ink-secondary text-sm mb-8">
          If that email is registered, you&apos;ll receive a reset link shortly.
        </p>
        <Link to="/login" className="text-accent hover:text-accent-hover text-sm font-medium">
          Back to Login →
        </Link>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4 relative z-10">
      <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
      <div className="glass-card w-full max-w-md p-10 animate-fade-in relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="font-display font-bold text-2xl inline-block">
            <span className="text-ink-primary">Py</span><span className="text-accent">Doc</span><span className="text-ink-primary">AI</span>
          </Link>
          <h1 className="font-display font-bold text-2xl text-center mt-4 mb-2 text-ink-primary">Forgot Password</h1>
          <p className="text-ink-secondary text-sm text-center">Enter your email and we&apos;ll send you a reset link</p>
        </div>

        <form onSubmit={submit}>
          <div className="mb-6">
            <label className="block text-sm font-medium text-ink-secondary mb-2">Email</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconMail /></span>
              <input
                id="reset-email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-field pl-10"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          {err && <p className="text-danger text-sm text-center mb-4">{err}</p>}

          <button
            id="send-reset-link"
            type="submit"
            disabled={loading}
            className="btn-accent w-full flex items-center justify-center gap-2"
          >
            {loading ? <><LoadingSpinner size="sm" /> Sending...</> : 'Send Reset Link'}
          </button>
        </form>

        <p className="text-center text-sm text-ink-secondary mt-6">
          Remember your password?{' '}
          <Link to="/login" className="text-accent hover:text-accent-hover font-medium">Sign In →</Link>
        </p>
      </div>
    </div>
  )
}
