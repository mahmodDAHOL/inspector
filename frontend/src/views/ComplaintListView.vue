<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('complaints.title') }}</h1>
      <div class="filters">
        <select v-model="filter.status"><option value="">All Status</option><option value="received">Received</option><option value="under_investigation">Investigating</option><option value="closed">Closed</option></select>
        <input v-model="filter.search" placeholder="Search..." />
      </div>
      <table>
        <thead><tr><th>Number</th><th>Title</th><th>Status</th><th>Priority</th></tr></thead>
        <tbody>
          <tr v-for="c in filteredComplaints" :key="c.id" @click="$router.push(`/complaints/${c.id}`)">
            <td class="mono">{{ c.complaint_number }}</td>
            <td>{{ c.title_ar }}</td>
            <td><span :class="['badge', c.status]">{{ c.status }}</span></td>
            <td><span :class="['badge', c.priority]">{{ c.priority }}</span></td>
          </tr>
        </tbody>
      </table>
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
