import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useInvestigationReportsStore = defineStore('investigationReports', () => {
    const report = ref(null)
    const loading = ref(false)

    async function fetchReport(complaintId) {
        loading.value = true
        report.value = null
        try {
            const res = await api.get(`/complaints/${complaintId}/investigation-report`)
            report.value = res.data
        } catch (error) {
            if (error.response?.status === 404) report.value = null
            else throw error
        } finally {
            loading.value = false
        }
    }

    async function createReport(complaintId, payload) {
        const res = await api.post(`/complaints/${complaintId}/investigation-report`, payload)
        report.value = res.data
        return res.data
    }

    async function updateReport(complaintId, payload) {
        const res = await api.put(`/complaints/${complaintId}/investigation-report`, payload)
        report.value = res.data
        return res.data
    }

    async function finalizeReport(complaintId, totpCode) {
        const res = await api.post(`/complaints/${complaintId}/investigation-report/finalize`, { totp_code: totpCode })
        report.value = res.data
        return res.data
    }

    return { report, loading, fetchReport, createReport, updateReport, finalizeReport }
})
