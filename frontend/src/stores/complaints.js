import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useComplaintStore = defineStore('complaints', () => {
  const complaints = ref([])
  const currentComplaint = ref(null)
  const notes = ref([])
  const history = ref([])
  const loading = ref(false)

  const totalCount = computed(() => complaints.value.length)
  const pendingCount = computed(() => complaints.value.filter(c => c.status === 'under_investigation').length)
  const urgentCount = computed(() => complaints.value.filter(c => c.priority === 'urgent').length)

  async function fetchAll(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/complaints', { params })
      complaints.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const res = await api.get(`/complaints/${id}`)
      currentComplaint.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function create(data) {
    const res = await api.post('/complaints', data)
    complaints.value.unshift(res.data)
    return res.data
  }

  async function updateStatus(id, status) {
    const res = await api.patch(`/complaints/${id}/status`, { status })
    const index = complaints.value.findIndex(c => c.id === id)
    if (index !== -1) complaints.value[index].status = status
    if (currentComplaint.value?.id === id) currentComplaint.value.status = status
    return res.data
  }

  async function assign(id, assigned_to) {
    const res = await api.post(`/complaints/${id}/assign`, { assigned_to })
    if (currentComplaint.value?.id === id) currentComplaint.value.assigned_to = assigned_to
    return res.data
  }

  async function escalate(id) {
    const res = await api.post(`/complaints/${id}/escalate`)
    const index = complaints.value.findIndex(c => c.id === id)
    if (index !== -1) {
      complaints.value[index].status = 'escalated'
      complaints.value[index].priority = 'urgent'
    }
    if (currentComplaint.value?.id === id) {
      currentComplaint.value.status = 'escalated'
      currentComplaint.value.priority = 'urgent'
    }
    return res.data
  }

  async function fetchNotes(id) {
    const res = await api.get(`/complaints/${id}/notes`)
    notes.value = res.data
  }

  async function fetchHistory(id) {
    const res = await api.get(`/complaints/${id}/history`)
    history.value = res.data
  }

  async function addNote(id, content, is_confidential = false, note_type = 'investigation') {
    const res = await api.post(`/complaints/${id}/notes`, { content, is_confidential, note_type })
    notes.value.unshift(res.data)
    return res.data
  }

  async function sign(id, totpCode) {
    const res = await api.post(`/complaints/${id}/sign`, { totp_code: totpCode })
    return res.data
  }

  return {
    complaints,
    currentComplaint,
    notes,
    history,
    loading,
    totalCount,
    pendingCount,
    urgentCount,
    fetchAll,
    fetchOne,
    create,
    updateStatus,
    assign,
    escalate,
    fetchNotes,
    fetchHistory,
    addNote,
    sign,
  }
})
