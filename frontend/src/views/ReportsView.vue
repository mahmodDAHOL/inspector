<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('reports.title') }}</h1>

      <div class="report-card">
        <h3>{{ $t('reports.summary') }}</h3>
        <p class="desc">{{ $t('reports.summaryDesc') }}</p>

        <form class="filters" @submit.prevent="generate">
          <div class="field">
            <label>{{ $t('reports.fromDate') }}</label>
            <input v-model="fromDate" type="date" />
          </div>
          <div class="field">
            <label>{{ $t('reports.toDate') }}</label>
            <input v-model="toDate" type="date" />
          </div>
          <button type="submit" class="btn-primary" :disabled="store.loading">
            {{ store.loading ? $t('reports.generating') : $t('reports.generate') }}
          </button>
        </form>

        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div v-if="store.report" class="report-card result">
        <div class="result-header">
          <div>
            <div class="mono">{{ store.report.report_id }}</div>
            <div class="muted">{{ $t('reports.generatedAt') }}: {{ formatDate(store.report.generated_at) }}</div>
          </div>
          <button class="btn-secondary" @click="store.downloadJson()">{{ $t('reports.download') }}</button>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ store.report.total_complaints }}</div>
            <div class="stat-label">{{ $t('dashboard.totalComplaints') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ store.report.response.response_rate }}%</div>
            <div class="stat-label">{{ $t('dashboard.responseRate') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ store.report.response.avg_response_hours }}{{ $t('dashboard.hoursShort') }}</div>
            <div class="stat-label">{{ $t('dashboard.avgResponseTime') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ store.report.response.awaiting_response }}</div>
            <div class="stat-label">{{ $t('dashboard.awaitingResponse') }}</div>
          </div>
        </div>

        <div class="charts-row">
          <div class="chart-card">
            <h3>{{ $t('dashboard.byStatus') }}</h3>
            <SimpleBarChart :data="store.report.by_status" :colors="statusColors" :labels="statusLabels" />
          </div>
          <div class="chart-card">
            <h3>{{ $t('dashboard.byPriority') }}</h3>
            <SimpleBarChart :data="store.report.by_priority" :colors="priorityColors" :labels="priorityLabels" />
          </div>
          <div class="chart-card">
            <h3>{{ $t('dashboard.byCategory') }}</h3>
            <SimpleBarChart :data="store.report.by_category" />
          </div>
        </div>
      </div>

      <div v-else-if="!store.loading" class="empty-state">{{ $t('reports.empty') }}</div>
    </main>
  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLayout from '../components/AppLayout.vue'
import SimpleBarChart from '../components/SimpleBarChart.vue'
import { useReportsStore } from '../stores/reports'

const { t } = useI18n()
const store = useReportsStore()
const fromDate = ref('')
const toDate = ref('')
const error = ref('')

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

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function generate() {
  error.value = ''
  try {
    await store.generateSummary(fromDate.value, toDate.value)
  } catch (e) {
    error.value = e.response?.data?.detail || t('common.error')
  }
}
</script>

<style scoped>
.report-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.report-card h3 { margin-bottom: 8px; }
.desc { color: var(--text-secondary); font-size: 13px; margin-bottom: 16px; }
.filters { display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; color: var(--text-tertiary); }
.field input { margin: 0; width: auto; }
.error { color: var(--color-danger); font-size: 13px; margin-top: 12px; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.muted { color: var(--text-tertiary); font-size: 13px; margin-top: 2px; }
.btn-secondary { padding: 10px 20px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; color: var(--text-primary); }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: var(--bg-muted); padding: 16px; border-radius: 10px; text-align: center; }
.stat-card .stat-value { font-size: 24px; font-weight: 600; color: var(--color-primary); }
.stat-card .stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }
.charts-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.chart-card { background: var(--bg-muted); padding: 16px; border-radius: 10px; }
.chart-card h3 { margin-bottom: 12px; font-size: 14px; }
.empty-state { color: var(--text-tertiary); text-align: center; padding: 40px 0; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
}
</style>
