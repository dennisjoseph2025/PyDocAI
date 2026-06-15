import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { githubAuth } from '../api'
import useAuth from '../hooks/useAuth'

export default function GitHubCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login, addToast } = useAuth()
  const called = useRef(false)

  useEffect(() => {
    if (called.current) return
    called.current = true

    const code = searchParams.get('code')
    const error = searchParams.get('error')

    if (error || !code) {
      addToast(
        error === 'access_denied'
          ? 'GitHub access was denied.'
          : 'GitHub login failed. Please try again.',
        'error'
      )
      navigate('/login', { replace: true })
      return
    }

    ;(async () => {
      try {
        const res = await githubAuth(code)
        login(res.data.tokens.access, res.data.tokens.refresh, res.data.user)
        addToast(
          res.data.created ? 'Account created with GitHub!' : 'Signed in with GitHub!',
          'success'
        )
        navigate('/input', { replace: true })
      } catch (err) {
        const msg =
          err.response?.data?.detail ||
          'GitHub authentication failed. Please try again.'
        addToast(msg, 'error')
        navigate('/login', { replace: true })
      }
    })()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center gap-5">
      {/* Animated GitHub mark */}
      <div className="relative flex items-center justify-center w-20 h-20">
        <div className="absolute inset-0 rounded-full bg-accent/20 animate-ping" />
        <div className="relative w-16 h-16 rounded-full bg-bg-elevated flex items-center justify-center border border-border">
          <svg className="w-9 h-9 text-accent" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
          </svg>
        </div>
      </div>

      <Helmet>
        <title>Authenticating — PyDocAI</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      <p className="text-ink-primary font-display font-semibold text-lg">
        Connecting with GitHub…
      </p>
      <p className="text-ink-secondary text-sm">Hang tight, this only takes a second.</p>
    </div>
  )
}
