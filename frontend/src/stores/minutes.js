import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useMinutesStore = defineStore('minutes', () => {
  const minutes = ref([])
  const loading = ref(false)

  async function fetchMinutes(complaintId) {
    loading.value = true
    try {
      const res = await api.get(`/complaints/${complaintId}/minutes`)
      minutes.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function addMinute(complaintId, { minuteType, title, minuteDate, summary, attendees, file }) {
    const form = new FormData()
    form.append('minute_type', minuteType)
    form.append('title', title)
    form.append('minute_date', minuteDate)
    form.append('summary', summary)
    if (attendees) form.append('attendees', attendees)
    form.append('file', file)

    // Let the browser set its own multipart boundary — the axios instance's
    // default 'application/json' header would otherwise win and break the upload.
    const res = await api.post(`/complaints/${complaintId}/minutes`, form, {
      headers: { 'Content-Type': undefined },
    })
    minutes.value.unshift(res.data)
    return res.data
  }

  async function downloadMinuteFile(complaintId, minuteId, filename) {
    const res = await api.get(`/complaints/${complaintId}/minutes/${minuteId}/file`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = filename || 'minute.pdf'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  return { minutes, loading, fetchMinutes, addMinute, downloadMinuteFile }
})
