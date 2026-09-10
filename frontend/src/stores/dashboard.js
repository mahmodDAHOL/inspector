import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref(null)
  const loading = ref(false)

  const total = computed(() => stats.value?.total || 0)
  const pending = computed(() => stats.value?.pending || 0)
  const urgent = computed(() => stats.value?.urgent || 0)
  const closed = computed(() => stats.value?.closed || 0)
  const recent = computed(() => stats.value?.recent || [])
  const byStatus = computed(() => stats.value?.by_status || {})
  const byPriority = computed(() => stats.value?.by_priority || {})
  const byCategory = computed(() => stats.value?.by_category || {})
  const byInspector = computed(() => stats.value?.by_inspector || {})
  const response = computed(() => stats.value?.response || { responded: 0, awaiting_response: 0, response_rate: 0, avg_response_hours: 0 })

  async function fetchStats() {
    loading.value = true
    try {
      const res = await api.get('/dashboard/stats')
      stats.value = res.data
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    loading,
    total,
    pending,
    urgent,
    closed,
    recent,
    byStatus,
    byPriority,
    byCategory,
    byInspector,
    response,
    fetchStats,
  }
})
