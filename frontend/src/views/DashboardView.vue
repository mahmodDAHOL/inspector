<template>
  <AppLayout>
    <div class="dashboard">
      <main class="content">
        <h1>{{ $t('dashboard.title') }}</h1>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">▣</div>
            <div class="stat-value">{{ store.total }}</div>
            <div class="stat-label">{{ $t('dashboard.totalComplaints') }}</div>
          </div>
          <div class="stat-card pending">
            <div class="stat-icon">◷</div>
            <div class="stat-value">{{ store.pending }}</div>
            <div class="stat-label">{{ $t('dashboard.pendingInvestigation') }}</div>
          </div>
          <div class="stat-card urgent">
            <div class="stat-icon">!</div>
            <div class="stat-value">{{ store.urgent }}</div>
            <div class="stat-label">{{ $t('dashboard.urgentComplaints') }}</div>
          </div>
          <div class="stat-card closed">
            <div class="stat-icon">✓</div>
            <div class="stat-value">{{ store.closed }}</div>
            <div class="stat-label">{{ $t('dashboard.closedComplaints') }}</div>
          </div>
        </div>

        <div class="charts-row">
          <div class="chart-card">
            <h3>{{ $t('dashboard.byStatus') }}</h3>
            <SimpleBarChart :data="store.byStatus" />
          </div>
          <div class="chart-card">
            <h3>{{ $t('dashboard.byPriority') }}</h3>
            <SimpleBarChart :data="store.byPriority" />
          </div>
          <div class="chart-card">
            <h3>{{ $t('dashboard.byCategory') }}</h3>
            <SimpleBarChart :data="store.byCategory" />
          </div>
        </div>

        <div class="actions">
          <button class="btn-primary" @click="$router.push('/complaints/new')">+ {{ $t('dashboard.newComplaint') }}</button>
          <button class="btn-primary" @click="$router.push('/complaints')">{{ $t('dashboard.viewAll') }}</button>
        </div>

        <div class="recent-section">
          <h3>{{ $t('dashboard.recentComplaints') }}</h3>
          <div v-for="c in store.recent" :key="c.id" class="complaint-row" @click="$router.push(`/complaints/${c.id}`)">
            <span class="mono">{{ c.complaint_number }}</span>
            <span>{{ c.title_ar }}</span>
            <span :class="['badge', c.priority]">{{ c.priority }}</span>
            <span :class="['badge', c.status]">{{ c.status }}</span>
          </div>
        </div>
      </main>
    </div>
  </AppLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import SimpleBarChart from '../components/SimpleBarChart.vue'
import { useDashboardStore } from '../stores/dashboard'

const store = useDashboardStore()
onMounted(() => store.fetchStats())
</script>

<style scoped>
.dashboard { padding: 24px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--bg-card); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border-color); }
.stat-card .stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-card .stat-value { font-size: 32px; font-weight: 600; color: var(--text-primary); }
.stat-card .stat-label { font-size: 13px; color: var(--text-tertiary); margin-top: 4px; }
.stat-card.pending .stat-icon { color: var(--color-warning); }
.stat-card.urgent .stat-icon { color: var(--color-danger); }
.stat-card.closed .stat-icon { color: var(--color-success); }

.charts-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.chart-card { background: var(--bg-card); padding: 20px; border-radius: 12px; border: 1px solid var(--border-color); }
.chart-card h3 { margin-bottom: 16px; font-size: 16px; }

.actions { display: flex; gap: 12px; margin-bottom: 24px; }
.recent-section { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); }
.recent-section h3 { margin-bottom: 16px; }
.complaint-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid var(--border-color); cursor: pointer; }
.complaint-row:hover { background: var(--bg-muted); }
.complaint-row span { margin-inline-end: 12px; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
}
</style>
