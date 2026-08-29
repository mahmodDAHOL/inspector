<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('audit.title') }}</h1>
      <p class="subtitle">{{ $t('audit.subtitle') }}</p>

      <div class="filters">
        <select v-model="filterTable" @change="reload">
          <option value="">{{ $t('audit.filterTable') }}</option>
          <option v-for="key in entityKeys" :key="key" :value="key">{{ $t(`audit.entity.${key}`) }}</option>
        </select>
        <select v-model="filterAction" @change="reload">
          <option value="">{{ $t('audit.filterAction') }}</option>
          <option v-for="key in actionKeys" :key="key" :value="key">{{ $t(`audit.actions.${key}`) }}</option>
        </select>
      </div>

      <p class="hint">{{ $t('audit.clickForDetails') }}</p>

      <table>
        <thead>
          <tr>
            <th>{{ $t('audit.time') }}</th>
            <th>{{ $t('audit.user') }}</th>
            <th>{{ $t('audit.table') }}</th>
            <th>{{ $t('audit.action') }}</th>
            <th>{{ $t('audit.description') }}</th>
            <th>{{ $t('audit.context') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in store.items" :key="log.id" class="log-row" @click="openDetail(log)">
            <td class="mono">{{ formatDate(log.timestamp) }}</td>
            <td>{{ log.performed_by || '—' }}</td>
            <td><span class="badge">{{ $t(`audit.entity.${log.table_name}`) }}</span></td>
            <td>{{ $t(`audit.actions.${log.action}`) }}</td>
            <td>{{ log.description }}</td>
            <td class="mono">
              <router-link v-if="log.table_name === 'complaint'" :to="`/complaints/${log.record_id}`" @click.stop>{{ log.context }}</router-link>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="!store.loading && !store.items.length" class="empty-state">{{ $t('audit.noLogs') }}</p>

      <div class="pagination">
        <button class="btn-secondary" :disabled="store.page <= 1" @click="goToPage(store.page - 1)">← {{ $t('audit.prev') }}</button>
        <span class="page-label">{{ $t('audit.pageOf', { page: store.page }) }}</span>
        <button class="btn-secondary" :disabled="!store.hasMore" @click="goToPage(store.page + 1)">{{ $t('audit.next') }} →</button>
      </div>
    </main>

    <div v-if="selectedLog" class="modal-overlay" @click.self="selectedLog = null">
      <div class="modal">
        <h2>{{ $t('audit.detailsTitle') }}</h2>
        <dl class="detail-list">
          <dt>{{ $t('audit.logId') }}</dt>
          <dd class="mono">{{ selectedLog.id }}</dd>

          <dt>{{ $t('audit.time') }}</dt>
          <dd>{{ formatDate(selectedLog.timestamp) }}</dd>

          <dt>{{ $t('audit.user') }}</dt>
          <dd>{{ selectedLog.performed_by || $t('complaint.unknownUser') }}</dd>

          <dt>{{ $t('audit.table') }}</dt>
          <dd><span class="badge">{{ $t(`audit.entity.${selectedLog.table_name}`) }}</span></dd>

          <dt>{{ $t('audit.action') }}</dt>
          <dd>{{ $t(`audit.actions.${selectedLog.action}`) }} <span class="mono muted">({{ selectedLog.action }})</span></dd>

          <dt>{{ $t('audit.description') }}</dt>
          <dd>{{ selectedLog.description }}</dd>

          <dt v-if="selectedLog.record_id">{{ $t('audit.recordId') }}</dt>
          <dd v-if="selectedLog.record_id" class="mono">{{ selectedLog.record_id }}</dd>

          <dt v-if="selectedLog.context">{{ $t('audit.context') }}</dt>
          <dd v-if="selectedLog.context" class="mono">{{ selectedLog.context }}</dd>
        </dl>

        <div class="form-actions">
          <router-link
            v-if="selectedLog.table_name === 'complaint'"
            :to="`/complaints/${selectedLog.record_id}`"
            class="btn-primary"
          >{{ $t('audit.viewComplaint') }}</router-link>
          <button class="btn-secondary" @click="selectedLog = null">{{ $t('common.close') }}</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { useAuditStore } from '../stores/audit'

const store = useAuditStore()
const filterTable = ref('')
const filterAction = ref('')
const selectedLog = ref(null)

const entityKeys = ['complaint', 'auth', 'user', 'department', 'report']
const actionKeys = [
  'created', 'status_changed', 'assigned', 'escalated', 'note_added', 'signed',
  'login_success', 'login_failed', 'account_locked', 'mfa_failed',
  'user_created', 'user_updated', 'user_deactivated',
  'department_created', 'department_updated', 'report_generated',
]

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

function reload() {
  store.fetchLogs({ table: filterTable.value, action: filterAction.value, page: 1 })
}

function goToPage(p) {
  if (p < 1) return
  store.fetchLogs({ table: filterTable.value, action: filterAction.value, page: p })
}

function openDetail(log) {
  selectedLog.value = log
}

onMounted(() => store.fetchLogs())
</script>

<style scoped>
.subtitle { color: var(--text-secondary); font-size: 13px; margin: -12px 0 16px; }
.hint { color: var(--text-tertiary); font-size: 12px; margin-bottom: 8px; }
.empty-state { color: var(--text-tertiary); text-align: center; padding: 24px 0; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 16px; }
.page-label { color: var(--text-secondary); font-size: 13px; }
.btn-secondary { padding: 8px 16px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; color: var(--text-primary); text-decoration: none; display: inline-block; }
.btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }
.log-row { cursor: pointer; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; padding: 20px; }
.modal { background: var(--bg-card); padding: 24px; border-radius: 12px; width: 100%; max-width: 480px; max-height: 90vh; overflow-y: auto; }
.modal h2 { margin-bottom: 16px; font-size: 18px; }
.detail-list { display: grid; grid-template-columns: 140px 1fr; row-gap: 12px; column-gap: 12px; }
.detail-list dt { color: var(--text-tertiary); font-size: 12px; align-self: start; padding-top: 2px; }
.detail-list dd { margin: 0; color: var(--text-primary); font-size: 14px; word-break: break-word; }
.detail-list .muted { color: var(--text-tertiary); font-size: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
</style>
