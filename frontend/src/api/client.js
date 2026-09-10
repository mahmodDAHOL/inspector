import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('temp_token')
  localStorage.removeItem('user')
}

// Access tokens are short-lived (15 min, see ACCESS_TOKEN_EXPIRE_MINUTES) so
// they *will* expire mid-session — e.g. while someone is writing a long
// investigation note. Rather than hard-logging them out on the first 401,
// try the refresh token once (a plain axios call, not `api`, so this request
// itself never recurses through this same interceptor) and silently retry
// the original call. Concurrent 401s share one in-flight refresh instead of
// each firing their own.
let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) throw new Error('No refresh token available')
  const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
  localStorage.setItem('access_token', res.data.access_token)
  return res.data.access_token
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const isAuthEndpoint = originalRequest?.url?.startsWith('/auth/')

    if (error.response?.status === 401 && !isAuthEndpoint && !originalRequest._retriedAfterRefresh) {
      originalRequest._retriedAfterRefresh = true
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => { refreshPromise = null })
        }
        const newToken = await refreshPromise
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        clearSession()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    if (error.response?.status === 401 && !isAuthEndpoint) {
      // Already retried once after a refresh and still unauthorized — the
      // refresh token itself is gone/expired too. Nothing left to try.
      clearSession()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
