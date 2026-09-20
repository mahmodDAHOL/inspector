import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useEvidenceStore = defineStore('evidence', () => {
    const items = ref([])
    const loading = ref(false)

    async function fetchEvidence(complaintId) {
        loading.value = true
        try {
            const res = await api.get(`/complaints/${complaintId}/evidence`)
            items.value = res.data
        } finally {
            loading.value = false
        }
    }

    async function uploadEvidence(complaintId, description, file) {
        const form = new FormData()
        form.append('description', description)
        form.append('file', file)
        const res = await api.post(`/complaints/${complaintId}/evidence`, form, {
            headers: { 'Content-Type': undefined },
        })
        items.value.unshift(res.data)
        return res.data
    }

    async function downloadEvidence(complaintId, item) {
        const res = await api.get(`/complaints/${complaintId}/evidence/${item.id}/file`, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        const link = document.createElement('a')
        link.href = url
        link.download = item.original_file_name || 'evidence'
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)
    }

    function clear() {
        items.value = []
    }

    return { items, loading, fetchEvidence, uploadEvidence, downloadEvidence, clear }
})
