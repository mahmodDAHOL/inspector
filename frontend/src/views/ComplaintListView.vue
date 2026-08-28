<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('complaints.title') }}</h1>
      <div class="filters">
        <select v-model="filter.status">
          <option value="">{{ $t('common.all') }}</option>
          <option value="received">{{ $t('complaint.status.received') }}</option>
          <option value="under_investigation">{{ $t('complaint.status.under_investigation') }}</option>
          <option value="escalated">{{ $t('complaint.status.escalated') }}</option>
          <option value="closed">{{ $t('complaint.status.closed') }}</option>
        </select>
        <input v-model="filter.search" :placeholder="$t('complaints.search')" />
      </div>
      <table>
        <thead><tr><th>{{ $t('complaint.number') }}</th><th>{{ $t('complaint.title') }}</th><th>{{ $t('complaint.statusLabel') }}</th><th>{{ $t('complaint.priorityLabel') }}</th></tr></thead>
        <tbody>
          <tr v-for="c in filteredComplaints" :key="c.id" @click="$router.push(`/complaints/${c.id}`)">
            <td class="mono">{{ c.complaint_number }}</td>
            <td>{{ c.title_ar }}</td>
            <td><span :class="['badge', c.status]">{{ $t(`complaint.status.${c.status}`) }}</span></td>
            <td><span :class="['badge', c.priority]">{{ $t(`complaint.priority.${c.priority}`) }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-if="!filteredComplaints.length" class="empty-state">{{ $t('common.loading') }}</div>
    </main>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useComplaintStore } from '../stores/complaints'
import AppLayout from '../components/AppLayout.vue'

const store = useComplaintStore()
const filter = ref({ status: '', search: '' })

const filteredComplaints = computed(() => {
  let result = store.complaints
  if (filter.value.status) result = result.filter(c => c.status === filter.value.status)
  if (filter.value.search) result = result.filter(c => c.title_ar.includes(filter.value.search))
  return result
})

onMounted(() => store.fetchAll())
</script>

<style scoped>
.empty-state { color: var(--text-tertiary); font-size: 13px; padding: 16px 0; text-align: center; }
</style>
