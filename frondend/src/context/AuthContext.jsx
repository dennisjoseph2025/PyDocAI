import { createContext, useState, useEffect, useCallback } from 'react'
import { getUserProfile, logoutUser } from '../api'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('pydocai_token'))
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('pydocai_refresh'))
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

  useEffect(() => {
    const loadUser = async () => {
      if (!token) {
        setIsLoading(false)
        return
      }
      try {
        const res = await getUserProfile()
        setUser(res.data)
      } catch (err) {
        if (err.response?.status === 401) {
          localStorage.removeItem('pydocai_token')
          localStorage.removeItem('pydocai_refresh')
          setToken(null)
          setRefreshToken(null)
        }
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
    loadUser()
  }, [token])

  const login = (accessToken, refreshToken, userData) => {
    localStorage.setItem('pydocai_token', accessToken)
    localStorage.setItem('pydocai_refresh', refreshToken)
    setToken(accessToken)
    setRefreshToken(refreshToken)
    setUser(userData)
    addToast('Welcome back!', 'success')
  }

  const updateUser = (updatedData) => {
    setUser(prev => ({ ...prev, ...updatedData }))
  }

  const logout = async () => {
    const rt = refreshToken || localStorage.getItem('pydocai_refresh')
    try {
      if (rt) await logoutUser(rt)
    } catch {}
    localStorage.removeItem('pydocai_token')
    localStorage.removeItem('pydocai_refresh')
    setToken(null)
    setRefreshToken(null)
    setUser(null)
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