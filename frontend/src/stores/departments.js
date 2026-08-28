import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useDepartmentsStore = defineStore('departments', () => {
  const departments = ref([])
  const loading = ref(false)

  async function fetchDepartments() {
    loading.value = true
    try {
      const res = await api.get('/departments')
      departments.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createDepartment(data) {
    const res = await api.post('/departments', data)
    departments.value.unshift(res.data)
    return res.data
  }

  async function updateDepartment(id, data) {
    const res = await api.patch(`/departments/${id}`, data)
    const index = departments.value.findIndex(d => d.id === id)
    if (index !== -1) departments.value[index] = res.data
    return res.data
  }

  return {
    departments,
    loading,
    fetchDepartments,
    createDepartment,
    updateDepartment,
  }
})
