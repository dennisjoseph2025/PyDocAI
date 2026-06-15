import { useState } from "react"
import { useSearchParams, useNavigate, Link } from "react-router-dom"
import { Helmet } from "react-helmet-async"
import api from "../api"
import { IconLock, IconKey, IconEye, IconEyeOff, IconCheck } from "../components/Icons"
import LoadingSpinner from "../components/LoadingSpinner"

export default function ResetPassword() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [password, setPassword] = useState("")
  const [showPw, setShowPw] = useState(false)
  const [done, setDone] = useState(false)
  const [err,  setErr]  = useState("")
  const [loading, setLoading] = useState(false)

  const strength = (() => {
    const p = password
    let s = 0
    if (p.length >= 6) s++
    if (p.length >= 10) s++
    if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s++
    if (/[^a-zA-Z0-9]/.test(p)) s++
    return s
  })()
  const strengthColors = ['bg-danger', 'bg-warning', 'bg-yellow-400', 'bg-success']
  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong']

  const submit = async (e) => {
    e.preventDefault()
    if (password.length < 8) { setErr("Password must be at least 8 characters"); return }
    setErr("")
    setLoading(true)
    try {
      await api.post("/users/password-reset/confirm/", {
        email:        params.get("email"),
        token:        params.get("token"),
        new_password: password,
      })
      setDone(true)
      setTimeout(() => navigate("/login"), 2000)
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Invalid or expired link.")
    } finally {
      setLoading(false)
    }
  }

  if (done) return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4 relative z-10">
      <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
      <div className="glass-card w-full max-w-md p-10 animate-fade-in relative z-10 text-center">
        <div className="w-16 h-16 rounded-2xl bg-success/10 flex items-center justify-center mx-auto mb-6">
          <IconCheck className="w-8 h-8 text-success" />
        </div>
        <h1 className="font-display font-bold text-2xl text-ink-primary mb-2">Password Reset!</h1>
        <p className="text-ink-secondary text-sm mb-2">Redirecting to login...</p>
        <div className="flex justify-center mt-4"><LoadingSpinner size="md" className="text-accent" /></div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4 relative z-10">
      <Helmet>
        <title>Reset Password — PyDocAI</title>
        <meta name="description" content="Set a new password for your PyDocAI account." />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
      <div className="glass-card w-full max-w-md p-10 animate-fade-in relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="font-display font-bold text-2xl inline-block">
            <span className="text-ink-primary">Py</span><span className="text-accent">Doc</span><span className="text-ink-primary">AI</span>
          </Link>
          <h1 className="font-display font-bold text-2xl text-center mt-4 mb-2 text-ink-primary">Set New Password</h1>
          <p className="text-ink-secondary text-sm text-center">Choose a strong password for your account</p>
        </div>

        <form onSubmit={submit}>
          <div className="mb-6">
            <label className="block text-sm font-medium text-ink-secondary mb-2">New Password</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconKey /></span>
              <input
                id="reset-password"
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="input-field pl-10 pr-10"
                placeholder="Min 8 characters"
                minLength={8}
                required
              />
              <button
                type="button"
                onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-primary cursor-pointer"
              >
                {showPw ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
            {password && (
              <div className="mt-2 space-y-1">
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className={`h-1 flex-1 rounded-full transition-colors duration-300 ${strength >= i ? strengthColors[i - 1] : 'bg-border'}`} />
                  ))}
                </div>
                <p className={`text-xs ${strength > 0 ? strengthLabels[strength - 1] === 'Weak' ? 'text-danger' : strengthLabels[strength - 1] === 'Fair' ? 'text-warning' : strengthLabels[strength - 1] === 'Good' ? 'text-yellow-400' : 'text-success' : 'text-ink-muted'}`}>
                  {strength > 0 ? strengthLabels[strength - 1] : ''}
                </p>
              </div>
            )}
          </div>

          {err && <p className="text-danger text-sm text-center mb-4">{err}</p>}

          <button
            id="reset-password-btn"
            type="submit"
            disabled={loading}
            className="btn-accent w-full flex items-center justify-center gap-2"
          >
            {loading ? <><LoadingSpinner size="sm" /> Resetting...</> : 'Reset Password'}
          </button>
        </form>

        <p className="text-center text-sm text-ink-secondary mt-6">
          <Link to="/login" className="text-accent hover:text-accent-hover font-medium">Back to Sign In →</Link>
        </p>
      </div>
    </div>
  )
}
