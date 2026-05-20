import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pydocai_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('pydocai_token')
      localStorage.removeItem('pydocai_refresh')
      localStorage.removeItem('pydocai_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const registerUser = (data) => api.post('/users/register/', data)
export const loginUser = (data) => api.post('/users/login/', data)
export const refreshToken = (refresh) => api.post('/users/token/refresh/', { refresh })
export const logoutUser = (refresh) => api.post('/users/logout/', { refresh: refresh || localStorage.getItem('pydocai_refresh') })
export const githubAuth = (code) => api.post('/users/auth/github/', { code })

export const getUserProfile = () => api.get('/users/profile/')
export const updateProfile = (data) => api.patch('/users/profile/', data)
export const changePassword = (data) => api.post('/users/change-password/', data)
export const adminListUsers = () => api.get('/users/list/')

export const analyzeFile = (data, isFormData = false) => {
  const config = isFormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : {}
  return api.post('/parser/file/', data, config)
}

export const analyzeFolder = (formData) => api.post('/parser/folder/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getProjects = () => api.get('/projects/')
export const getProjectDetail = (id) => api.get(`/projects/${id}/`)
export const deleteProject = (id) => api.delete(`/projects/${id}/`)

export const exportMarkdown = (projectId) => api.get(`/exports/${projectId}/markdown/`)
export const downloadMarkdown = (projectId) => api.get(`/exports/${projectId}/markdown/`, { responseType: 'blob' })

export const chatWithAI = (message, projectId) => api.post('/ai/chat/', { message, project_id: projectId })

export const getGithubRepos = () => api.get('/github/repos/')
export const getGithubRepoFolders = (repo, branch) => api.get(`/github/repos/folders/?repo=${encodeURIComponent(repo)}${branch ? `&branch=${encodeURIComponent(branch)}` : ''}`)
export const importFromGithub = (data) => api.post('/github/repos/import/', data)

export default api