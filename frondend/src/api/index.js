import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pydocai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

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
          const newToken = res.data.access
          localStorage.setItem('pydocai_token', newToken)
          originalRequest.headers.Authorization = `Bearer ${newToken}`
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

export function getAllProjects(params = {}) {
  return api.get('/admin-dashboard/projects/', { params })
}

export function adminGetUsers(params = {}) {
  return api.get('/admin-dashboard/users/', { params })
}

export function adminGetUserDetail(id) {
  return api.get(`/admin-dashboard/users/${id}/`)
}

export function adminGetProjectDetail(id) {
  return api.get(`/admin-dashboard/projects/${id}/`)
}

export default api
