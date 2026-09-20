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

  async function addMinute(complaintId, { minuteType, title, minuteDate, summary, attendees, idImages, file }) {
    const form = new FormData()
    form.append('minute_type', minuteType)
    form.append('title', title)
    form.append('minute_date', minuteDate)
    form.append('summary', summary)
    form.append('attendees', JSON.stringify(attendees || []))
    const imageIndices = []
      ; (idImages || []).forEach((image, index) => {
        if (image) {
          form.append('id_images', image)
          imageIndices.push(index)
        }
      })
    form.append('id_image_indices', JSON.stringify(imageIndices))
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

  async function downloadAttendeeIdImage(complaintId, minuteId, attendeeIndex) {
    const res = await api.get(`/complaints/${complaintId}/minutes/${minuteId}/attendee/${attendeeIndex}/id-image`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    window.open(url, '_blank', 'noopener,noreferrer')
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  }

  async function archiveMinute(complaintId, minuteId, reason) {
    const res = await api.post(`/complaints/${complaintId}/minutes/${minuteId}/archive`, { reason })
    const minute = minutes.value.find(item => item.id === minuteId)
    if (minute) Object.assign(minute, res.data)
    return res.data
  }

  return { minutes, loading, fetchMinutes, addMinute, downloadMinuteFile, downloadAttendeeIdImage, archiveMinute }
})
