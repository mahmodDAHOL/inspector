import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const isAuthenticated = computed(() => !!accessToken.value)
  const userRole = computed(() => user.value?.role)

  async function login(username, password) {
    const res = await api.post('/auth/login', { username, password })
    if (res.data.temp_token) {
      localStorage.setItem('temp_token', res.data.temp_token)
    }
    return res.data
  }

  async function verifyTOTP(code) {
    const res = await api.post('/auth/verify-totp', {
      temp_token: localStorage.getItem('temp_token'),
      totp_code: code
    })
    accessToken.value = res.data.access_token
    localStorage.setItem('access_token', accessToken.value)
    localStorage.removeItem('temp_token')
    user.value = res.data.user
    localStorage.setItem('user', JSON.stringify(res.data.user))
    return res.data
  }

  function logout() {
    user.value = null
    accessToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('temp_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return { user, accessToken, isAuthenticated, userRole, login, verifyTOTP, logout }
})
