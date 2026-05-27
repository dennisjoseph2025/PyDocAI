import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { loginUser } from '../api'
import useAuth from '../hooks/useAuth'
import LoadingSpinner from '../components/LoadingSpinner'
import { IconMail, IconLock, IconEye, IconEyeOff } from '../components/Icons'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const { login, addToast, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [sp] = useSearchParams()
  const redirect = sp.get('redirect') || '/input'

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirect, { replace: true })
    }
  }, [isAuthenticated, navigate, redirect])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const v = {}
    if (!email.trim()) v.email = 'Email is required'
    if (!password) v.password = 'Password is required'
    if (Object.keys(v).length) { setErrors(v); return }
    setErrors({})
    setLoading(true)
    try {
      // Reverting to axios now that proxy is fixed.
      // Sending username as email which is the standard for most backends.
      const res = await loginUser({ 
        email: email, 
        password: password 
      })
      
      // Backend returns { tokens: { access: '...', refresh: '...' }, user: { ... } }
      login(res.data.tokens.access, res.data.tokens.refresh, res.data.user)
      setLoading(false)
      navigate(redirect, { replace: true })
    } catch (err) {
      console.error('Login error details:', err.response?.data)
      const data = err.response?.data
      const msg = data?.detail || data?.non_field_errors?.[0] || data?.email?.[0] || data?.username?.[0] || 'Invalid credentials'
      addToast(msg, 'error')
      setErrors({ general: msg })
      setLoading(false)
    }
  }

  const handleGitHubLogin = () => {
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
    const redirectUri = `${window.location.origin}/auth/github/callback`
    const scope = 'read:user user:email'
    const url = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}`
    window.location.href = url
  }

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4 relative z-10">
      <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
      <div className="glass-card w-full max-w-md p-10 animate-fade-in relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="font-display font-bold text-2xl inline-block">
            <span className="text-ink-primary">Py</span><span className="text-accent">Doc</span><span className="text-ink-primary">AI</span>
          </Link>
          <h1 className="font-display font-bold text-2xl text-center mt-4 mb-2 text-ink-primary">Welcome back</h1>
          <p className="text-ink-secondary text-sm text-center">Sign in to continue generating docs</p>
        </div>

        {/* GitHub OAuth button */}
        <button
          id="login-github"
          type="button"
          onClick={handleGitHubLogin}
          className="w-full flex items-center justify-center gap-3 bg-[#24292e] hover:bg-[#2f363d] text-white font-display font-semibold px-6 py-3 rounded-xl transition-all duration-200 hover:shadow-lg active:scale-95 border border-[#444c56] mb-6"
        >
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
          </svg>
          Continue with GitHub
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 h-px bg-border" />
          <span className="text-ink-muted text-xs font-medium">or sign in with email</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label className="block text-sm font-medium text-ink-secondary mb-2">Email</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconMail /></span>
              <input id="login-email" type="email" value={email} onChange={e => setEmail(e.target.value)} className="input-field pl-10" placeholder="you@example.com" />
            </div>
            {errors.email && <p className="text-danger text-xs mt-1">{errors.email}</p>}
          </div>
          <div className="mb-5">
            <label className="block text-sm font-medium text-ink-secondary mb-2">Password</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"><IconLock /></span>
              <input id="login-password" type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} className="input-field pl-10 pr-10" placeholder="••••••••" />
              <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-primary cursor-pointer">
                {showPw ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
            {errors.password && <p className="text-danger text-xs mt-1">{errors.password}</p>}
            <div className="text-right mt-1">
              <Link to="/forgot-password" className="text-accent hover:text-accent-hover text-xs font-medium">Forgot password?</Link>
            </div>
          </div>
          {errors.general && <p className="text-danger text-sm text-center mb-4">{errors.general}</p>}
          <button id="login-submit" type="submit" disabled={loading} className="btn-accent w-full mt-2 flex items-center justify-center gap-2">
            {loading ? <><LoadingSpinner size="sm" /> Signing in...</> : 'Sign In'}
          </button>
        </form>
        <p className="text-center text-sm text-ink-secondary mt-6">Don&apos;t have an account?{' '}<Link to="/register" className="text-accent hover:text-accent-hover font-medium">Register →</Link></p>
      </div>
    </div>
  )
}
