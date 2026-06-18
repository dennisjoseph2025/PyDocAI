import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const decodeToken = (token) => {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      window.atob(base64).split('').map((c) => `%${('00' + c.charCodeAt(0).toString(16)).slice(-2)}`).join('')
    )
    return JSON.parse(jsonPayload)
  } catch { return null }
}

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Proactive refresh: check expiry before every request
api.interceptors.request.use(async (config) => {
  const token = localStorage.getItem('pydocai_token')
  if (token) {
    const decoded = decodeToken(token)
    if (decoded?.exp) {
      const now = Math.floor(Date.now() / 1000)
      // Refresh if token expires within 2 minutes (gives buffer for slow requests)
      if (decoded.exp - now <= 120) {
        const refresh = localStorage.getItem('pydocai_refresh')
        if (refresh) {
          try {
            const res = await axios.post(`${API_BASE}/users/token/refresh/`, { refresh })
            localStorage.setItem('pydocai_token', res.data.access)
            if (res.data.refresh) {
              localStorage.setItem('pydocai_refresh', res.data.refresh)
            }
            config.headers.Authorization = `Bearer ${res.data.access}`
            return config
          } catch {
            localStorage.removeItem('pydocai_token')
            localStorage.removeItem('pydocai_refresh')
            window.location.href = '/login'
            return Promise.reject(new Error('Token refresh failed'))
          }
        }
      }
    }
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Reactive refresh: fallback if a 401 still slips through
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refresh = localStorage.getItem('pydocai_refresh')
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/users/token/refresh/`, { refresh })
          localStorage.setItem('pydocai_token', res.data.access)
          if (res.data.refresh) {
            localStorage.setItem('pydocai_refresh', res.data.refresh)
          }
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`
          return api(originalRequest)
        } catch {
          localStorage.removeItem('pydocai_token')
          localStorage.removeItem('pydocai_refresh')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export function loginUser(data) {
  return api.post('/users/login/', data)
}

export function registerUser(data) {
  return api.post('/users/register/', data)
}

export function getUserProfile() {
  return api.get('/users/profile/')
}

export function updateProfile(data) {
  return api.patch('/users/profile/', data)
}

export function changePassword(data) {
  return api.post('/users/change-password/', data)
}

export function logoutUser(refreshToken) {
  return api.post('/users/logout/', { refresh: refreshToken })
}

export function refreshToken(refreshTokenValue) {
  return api.post('/users/token/refresh/', { refresh: refreshTokenValue })
}

export function adminListUsers(params = {}) {
  return api.get('/users/list/', { params })
}

export function githubAuth(code) {
  return api.post('/users/auth/github/', { code })
}

export function getProjects(params = {}) {
  return api.get('/projects/', { params })
}

export function getProjectDetail(id) {
  return api.get(`/projects/${id}/`)
}

export function deleteProject(id) {
  return api.delete(`/projects/${id}/`)
}

export function analyzeFile(formData) {
  return api.post('/parser/file/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function analyzeFolder(formData) {
  return api.post('/parser/folder/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function importFromGithub(data) {
  return api.post('/github/repos/import/', data)
}

export function getGithubRepos() {
  return api.get('/github/repos/')
}

export function getGithubRepoFolders(repoFullName) {
  return api.get('/github/repos/folders/', { params: { repo: repoFullName } })
}

export function getPublicRepoInfo(url) {
  return api.get('/github/public-repo/info/', { params: { url } })
}

export function getPublicRepoFolders(fullName, branch) {
  return api.get('/github/public-repo/folders/', { params: { full_name: fullName, branch } })
}

export function importPublicRepo(data) {
  return api.post('/github/public-repo/import/', data)
}

export function getAllFeedback(params = {}) {
  return api.get('/feedback/admin/', { params })
}

export function getMyFeedback(params = {}) {
  return api.get('/feedback/my/', { params })
}

export function resolveFeedback(id) {
  return api.patch(`/feedback/admin/${id}/resolve/`)
}

export function createFeedbackReply(feedbackId, message) {
  return api.post(`/feedback/${feedbackId}/replies/`, { message })
}

export function getAdminStats() {
  return api.get('/admin-dashboard/stats/')
}

export function adminGetUserProjects(userId, params = {}) {
  return api.get(`/admin-dashboard/users/${userId}/publish/`, { params })
}

export function adminDeleteUser(userId, reason) {
  return api.post(`/admin-dashboard/users/${userId}/delete/`, { reason })
}

export function adminBlockUser(userId) {
  return api.post(`/admin-dashboard/users/${userId}/block/`)
}

// ── Universal Docs ─────────────────────────────────────────
export function uploadUniversal(formData) {
  return api.post('/universal/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getUniversalStatus(projectId) {
  return api.get(`/universal/status/${projectId}/`)
}

export default api

// ── Publish / Share ──────────────────────────────────────────
export function publishProject(id, data) {
  return api.patch(`/projects/${id}/publish/`, data)
}

// ── Public Projects ──────────────────────────────────────────
export function getPublicProjects(params = {}) {
  return api.get('/public/projects/', { params })
}

export function getPublicProject(slug) {
  return api.get(`/public/projects/${slug}/`)
}

// ── Comments ─────────────────────────────────────────────────
export function getComments(projectId, offset = 0, limit = 20) {
  return api.get(`/comments/${projectId}/comments/`, { params: { offset, limit } })
}

export function createComment(projectId, data) {
  return api.post(`/comments/${projectId}/comments/create/`, data)
}

export function deleteComment(id) {
  return api.delete(`/comments/${id}/`)
}

// ── Notifications ────────────────────────────────────────────
export function getNotifications(params = {}) {
  return api.get('/notifications/', { params })
}

export function getUnreadCount() {
  return api.get('/notifications/unread-count/')
}

export function markNotificationRead(id) {
  return api.patch(`/notifications/${id}/read/`)
}

export function markAllNotificationsRead() {
  return api.patch('/notifications/read-all/')
}

export function deleteNotification(id) {
  return api.delete(`/notifications/${id}/`)
}

export function clearAllNotifications() {
  return api.delete('/notifications/clear-all/')
}
