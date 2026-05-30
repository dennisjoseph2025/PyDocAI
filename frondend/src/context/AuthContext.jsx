import { createContext, useState, useEffect, useCallback } from 'react'
import { getUserProfile, logoutUser, refreshToken } from '../api'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('pydocai_token'))
  const [refreshTokenValue, setRefreshTokenValue] = useState(() => localStorage.getItem('pydocai_refresh'))
  const [isLoading, setIsLoading] = useState(true)

  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  // Decode JWT token to get expiration time
  const decodeToken = (token) => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        window
          .atob(base64)
          .split('')
          .map((c) => `%${('00' + c.charCodeAt(0).toString(16)).slice(-2)}`)
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch (e) {
      return null
    }
  }

  // Refresh token if it's about to expire (within 60 seconds)
  const refreshIfNeeded = useCallback(async () => {
    if (!token) return

    const decoded = decodeToken(token)
    if (!decoded || !decoded.exp) return

    const now = Math.floor(Date.now() / 1000)
    // Refresh if token expires in 60 seconds or less
    if (decoded.exp - now <= 60) {
      try {
        const response = await refreshToken(refreshTokenValue)
        // Update only the access token (refresh token remains same unless rotated)
        localStorage.setItem('pydocai_token', response.data.access)
        setToken(response.data.access)
        // Optionally update user data if needed
        const userData = localStorage.getItem('pydocai_user')
        if (userData) {
          const parsedUser = JSON.parse(userData)
          // We don't have new user data from refresh, so we keep existing
          // setUser(parsedUser) // Only update if we got new user data
        }
        return true
      } catch (error) {
        console.error('Token refresh failed:', error)
        // If refresh fails, log out
        logout()
        return false
      }
    }
    return false
  }, [token, refreshTokenValue])

  // Set up interval to check token expiration
  useEffect(() => {
    if (!token) {
      // Clear interval when there's no token
      return
    }

    const intervalId = setInterval(refreshIfNeeded, 30000) // Check every 30 seconds
    return () => clearInterval(intervalId)
  }, [token, refreshIfNeeded])

  useEffect(() => {
    const loadUser = async () => {
      if (!token) {
        setIsLoading(false)
        return
      }
      try {
        const res = await getUserProfile()
        setUser(res.data)
        // Attempt initial token refresh if needed
        refreshIfNeeded()
      } catch (err) {
        if (err.response?.status === 401) {
          localStorage.removeItem('pydocai_token')
          localStorage.removeItem('pydocai_refresh')
          setToken(null)
          setRefreshTokenValue(null)
        }
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
    loadUser()
  }, [token, refreshIfNeeded])

  const login = (accessToken, refreshToken, userData) => {
    localStorage.setItem('pydocai_token', accessToken)
    localStorage.setItem('pydocai_refresh', refreshToken)
    setToken(accessToken)
    setRefreshTokenValue(refreshToken)
    setUser(userData)
    addToast('Welcome back!', 'success')
  }

  const updateUser = (updatedData) => {
    setUser(prev => ({ ...prev, ...updatedData }))
  }

  const logout = async () => {
    const rt = refreshTokenValue || localStorage.getItem('pydocai_refresh')
    try {
      if (rt) await logoutUser(rt)
    } catch {}
    localStorage.removeItem('pydocai_token')
    localStorage.removeItem('pydocai_refresh')
    // Hard reload to / — this wipes all React state naturally.
    // Don't clear React state beforehand to prevent ProtectedRoute
    // from seeing "not authenticated" and redirecting to /login
    // before the browser navigates away.
    window.location.href = '/'
  }

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout,
    updateUser,
    toasts,
    addToast,
    removeToast,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}