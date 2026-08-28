import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const roles = ref([])
  const loading = ref(false)

  const activeUsers = computed(() => users.value.filter(u => u.is_active))

  async function fetchUsers() {
    loading.value = true
    const res = await api.get('/users')
    users.value = res.data
    loading.value = false
  }

  async function fetchRoles() {
    const res = await api.get('/users/roles')
    roles.value = res.data.roles
  }

  async function createUser(data) {
    const res = await api.post('/users', data)
    users.value.unshift(res.data)
    return res.data
  }

  async function updateUser(id, data) {
    const res = await api.patch(`/users/${id}`, data)
    const index = users.value.findIndex(u => u.id === id)
    if (index !== -1) users.value[index] = res.data
    return res.data
  }

  async function deactivateUser(id) {
    await api.post(`/users/${id}/deactivate`)
    const index = users.value.findIndex(u => u.id === id)
    if (index !== -1) users.value[index].is_active = false
  }

  return {
    users,
    roles,
    loading,
    activeUsers,
    fetchUsers,
    fetchRoles,
    createUser,
    updateUser,
    deactivateUser,
  }
})
