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

        <section class="response-section">
          <h2 class="section-title">{{ $t('dashboard.responsePerformance') }}</h2>
          <div class="response-grid">
            <div class="response-card">
              <div class="response-value">{{ store.response.response_rate }}%</div>
              <div class="response-label">{{ $t('dashboard.responseRate') }}</div>
              <div class="response-bar"><div class="response-bar-fill" :style="{ width: store.response.response_rate + '%' }"></div></div>
            </div>
            <div class="response-card">
              <div class="response-value">{{ store.response.avg_response_hours }}<span class="unit">{{ $t('dashboard.hoursShort') }}</span></div>
              <div class="response-label">{{ $t('dashboard.avgResponseTime') }}</div>
            </div>
            <div class="response-card" :class="{ warn: store.response.awaiting_response > 0 }">
              <div class="response-value">{{ store.response.awaiting_response }}</div>
              <div class="response-label">{{ $t('dashboard.awaitingResponse') }}</div>
            </div>
          </div>
        </section>

        <div class="charts-row">
          <div class="chart-card">
            <h3>{{ $t('dashboard.byStatus') }}</h3>
            <SimpleBarChart :data="store.byStatus" :colors="statusColors" :labels="statusLabels" />
          </div>
          <div class="chart-card">
            <h3>{{ $t('dashboard.byPriority') }}</h3>
            <SimpleBarChart :data="store.byPriority" :colors="priorityColors" :labels="priorityLabels" />
          </div>
          <div class="chart-card">
            <h3>{{ $t('dashboard.byCategory') }}</h3>
            <SimpleBarChart :data="store.byCategory" :labels="categoryLabels" />
          </div>
        </div>

        <h2 class="section-title">{{ $t('dashboard.quickActions') }}</h2>
        <div class="actions">
          <button class="btn-primary" @click="$router.push('/complaints/new')">+ {{ $t('dashboard.newComplaint') }}</button>
          <button class="btn-primary" @click="$router.push('/complaints')">{{ $t('dashboard.viewAll') }}</button>
          <button class="btn-primary" @click="$router.push('/reports')">{{ $t('landing.reports') }}</button>
          <button v-if="canManageUsers" class="btn-primary" @click="$router.push('/admin')">{{ $t('dashboard.manageUsers') }}</button>
        </div>

        <div class="recent-section">
          <h3>{{ $t('dashboard.recentComplaints') }}</h3>
          <div v-for="c in store.recent" :key="c.id" class="complaint-row" @click="$router.push(`/complaints/${c.id}`)">
            <span class="mono">{{ c.complaint_number }}</span>
            <span>{{ c.title_ar }}</span>
            <span :class="['badge', c.priority]">{{ priorityLabels[c.priority] || c.priority }}</span>
            <span :class="['badge', c.status]">{{ statusLabels[c.status] || c.status }}</span>
          </div>
          <div v-if="!store.recent.length" class="empty-state">{{ $t('common.loading') }}</div>
        </div>
      </main>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLayout from '../components/AppLayout.vue'
import SimpleBarChart from '../components/SimpleBarChart.vue'
import { useDashboardStore } from '../stores/dashboard'

const { t } = useI18n()
const store = useDashboardStore()
onMounted(() => store.fetchStats())

const canManageUsers = computed(() => {
  try {
    return ['admin', 'super_admin'].includes(JSON.parse(localStorage.getItem('user') || '{}').role)
  } catch {
    return false
  }
})

const statusColors = {
  received: 'var(--color-info)',
  under_investigation: 'var(--color-warning)',
  escalated: 'var(--color-danger)',
  closed: 'var(--color-success)',
}
const priorityColors = {
  normal: 'var(--color-neutral)',
  urgent: 'var(--color-warning)',
  critical: 'var(--color-danger)',
}
const statusLabels = computed(() => ({
  received: t('complaint.status.received'),
  under_investigation: t('complaint.status.under_investigation'),
  escalated: t('complaint.status.escalated'),
  closed: t('complaint.status.closed'),
}))
const priorityLabels = computed(() => ({
  normal: t('complaint.priority.normal'),
  urgent: t('complaint.priority.urgent'),
  critical: t('complaint.priority.critical'),
}))
const categoryLabels = computed(() => ({
  financial_fraud: t('complaint.category.financial_fraud'),
  procurement_violation: t('complaint.category.procurement_violation'),
  bribery: t('complaint.category.bribery'),
  misconduct: t('complaint.category.misconduct'),
}))
</script>

<style scoped>
.dashboard { padding: 24px; }
.section-title { font-size: 16px; margin: 28px 0 14px; color: var(--text-secondary); }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 8px; }
.stat-card { background: var(--bg-card); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border-color); box-shadow: var(--shadow-md); }
.stat-card .stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-card .stat-value { font-size: 32px; font-weight: 600; color: var(--text-primary); }
.stat-card .stat-label { font-size: 13px; color: var(--text-tertiary); margin-top: 4px; }
.stat-card.pending .stat-icon { color: var(--color-warning); }
.stat-card.urgent .stat-icon { color: var(--color-danger); }
.stat-card.closed .stat-icon { color: var(--color-success); }

.response-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.response-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 18px 20px; }
.response-card.warn { border-color: var(--color-warning); }
.response-value { font-size: 26px; font-weight: 700; color: var(--color-primary); }
.response-card.warn .response-value { color: var(--color-warning); }
.response-value .unit { font-size: 14px; font-weight: 500; margin-inline-start: 2px; color: var(--text-tertiary); }
.response-label { font-size: 13px; color: var(--text-tertiary); margin-top: 4px; }
.response-bar { margin-top: 10px; height: 6px; border-radius: 3px; background: var(--bg-muted); overflow: hidden; }
.response-bar-fill { height: 100%; background: var(--color-primary); border-radius: 3px; transition: width 0.3s; }

.charts-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.chart-card { background: var(--bg-card); padding: 20px; border-radius: 12px; border: 1px solid var(--border-color); }
.chart-card h3 { margin-bottom: 16px; font-size: 16px; }

.actions { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.recent-section { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); }
.recent-section h3 { margin-bottom: 16px; }
.complaint-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid var(--border-color); cursor: pointer; }
.complaint-row:hover { background: var(--bg-muted); }
.complaint-row span { margin-inline-end: 12px; }
.empty-state { color: var(--text-tertiary); font-size: 13px; padding: 12px 0; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .response-grid { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr; }
}
</style>
