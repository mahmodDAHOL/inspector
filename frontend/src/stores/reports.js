import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useReportsStore = defineStore('reports', () => {
  const report = ref(null)
  const loading = ref(false)

  async function generateSummary(fromDate, toDate) {
    loading.value = true
    try {
      const res = await api.post('/reports/summary', {
        from_date: fromDate || null,
        to_date: toDate || null,
      })
      report.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  function downloadJson() {
    if (!report.value) return
    const blob = new Blob([JSON.stringify(report.value, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.value.report_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    report,
    loading,
    generateSummary,
    downloadJson,
  }
})
