import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useAuditStore = defineStore('audit', () => {
  const items = ref([])
  const page = ref(1)
  const perPage = ref(25)
  const total = ref(0)
  const hasMore = ref(false)
  const loading = ref(false)

  async function fetchLogs({ table = '', action = '', page: p = 1 } = {}) {
    loading.value = true
    try {
      const res = await api.get('/audit/logs', {
        params: { table: table || undefined, action: action || undefined, page: p, per_page: perPage.value },
      })
      items.value = res.data.items
      total.value = res.data.total
      hasMore.value = res.data.has_more
      page.value = p
    } finally {
      loading.value = false
    }
  }

  return { items, page, perPage, total, hasMore, loading, fetchLogs }
})
