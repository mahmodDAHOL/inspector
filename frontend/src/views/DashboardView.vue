<template>
  <div class="dashboard">
    <AppHeader />
    <main class="content">
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">{{ store.totalCount }}</div><div class="stat-label">Total</div></div>
        <div class="stat-card"><div class="stat-value" style="color:var(--color-warning)">{{ store.pendingCount }}</div><div class="stat-label">Pending</div></div>
        <div class="stat-card"><div class="stat-value" style="color:var(--color-success)">{{ store.urgentCount }}</div><div class="stat-label">Urgent</div></div>
      </div>
      <div class="actions">
        <button class="btn-primary" @click="$router.push('/complaints/new')">+ {{ $t('dashboard.newComplaint') }}</button>
      </div>
      <div class="recent-section">
        <h3>Recent Complaints</h3>
        <div v-for="c in store.complaints.slice(0, 5)" :key="c.id" class="complaint-row" @click="$router.push(`/complaints/${c.id}`)">
          <span class="mono">{{ c.complaint_number }}</span>
          <span>{{ c.title_ar }}</span>
          <span :class="['badge', c.priority]">{{ c.priority }}</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useComplaintStore } from '../stores/complaints'
import AppHeader from '../components/AppHeader.vue'

const store = useComplaintStore()
onMounted(() => store.fetchAll())
</script>

<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--bg-card); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border-color); }
.stat-value { font-size: 32px; font-weight: 600; color: var(--text-primary); }
.stat-label { font-size: 13px; color: var(--text-tertiary); margin-top: 4px; }
.actions { margin-bottom: 24px; }
.recent-section { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); }
.complaint-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid var(--border-color); cursor: pointer; }
.complaint-row:hover { background: var(--bg-muted); }
.badge { padding: 3px 10px; border-radius: 20px; font-size: 12px; }
.badge.urgent { background: rgba(184,84,80,0.12); color: var(--color-danger); }
</style>
