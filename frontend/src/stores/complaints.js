import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useComplaintStore = defineStore('complaints', () => {
  const complaints = ref([])
  const loading = ref(false)

  const totalCount = computed(() => complaints.value.length)
  const pendingCount = computed(() => complaints.value.filter(c => c.status === 'under_investigation').length)
  const urgentCount = computed(() => complaints.value.filter(c => c.priority === 'urgent').length)

  async function fetchAll() {
    loading.value = true
    const res = await api.get('/complaints')
    complaints.value = res.data
    loading.value = false
  }

  async function create(data) {
    const res = await api.post('/complaints', data)
    complaints.value.unshift(res.data)
    return res.data
  }

  return { complaints, loading, totalCount, pendingCount, urgentCount, fetchAll, create }
})
