<template>
  <AppLayout>
    <main class="content">
      <button class="back-btn" @click="$router.back()">← {{ $t('common.back') }}</button>

      <ComplaintProgressTracker
        v-if="store.currentComplaint"
        :status="store.currentComplaint.status"
        :created-at="store.currentComplaint.created_at"
        :closed-at="store.currentComplaint.closed_at"
        :first-response-at="store.currentComplaint.first_response_at"
        :assignee-name="store.currentComplaint.assigned_to_name"
      />

      <div v-if="store.currentComplaint" class="detail-card">
        <div class="detail-header">
          <h1>{{ store.currentComplaint.title_ar }}</h1>
          <div class="badges">
            <span :class="['badge', store.currentComplaint.priority]">{{ $t(`complaint.priority.${store.currentComplaint.priority}`) }}</span>
            <span :class="['badge', store.currentComplaint.status]">{{ $t(`complaint.status.${store.currentComplaint.status}`) }}</span>
          </div>
        </div>

        <div class="detail-meta">
          <p><strong>{{ $t('complaint.number') }}:</strong> {{ store.currentComplaint.complaint_number }}</p>
          <p><strong>{{ $t('complaint.category') }}:</strong> {{ $t(`complaint.categories.${store.currentComplaint.category}`) }}</p>
          <p><strong>{{ $t('complaint.source') }}:</strong> {{ store.currentComplaint.source }}</p>
          <p><strong>{{ $t('complaint.createdAt') }}:</strong> {{ formatDate(store.currentComplaint.created_at) }}</p>
        </div>

        <div class="detail-section">
          <h3>{{ $t('complaint.description') }}</h3>
          <p>{{ store.currentComplaint.description }}</p>
        </div>

        <div class="workflow-section">
          <h3>{{ $t('complaint.workflow') }}</h3>
          <div v-if="canWrite" class="workflow-actions">
            <select v-model="nextStatus" class="status-select">
              <option value="">{{ $t('complaint.selectAction') }}</option>
              <option v-for="s in allowedTransitions" :key="s" :value="s">{{ $t(`complaint.status.${s}`) }}</option>
            </select>
            <button class="btn-primary" @click="changeStatus" :disabled="!nextStatus">{{ $t('complaint.updateStatus') }}</button>
            <button v-if="canEscalate" class="btn-warning" @click="escalate">{{ $t('complaint.escalate') }}</button>
            <button v-if="canSign && store.currentComplaint.status === 'closed'" class="btn-success" @click="showSignModal = true">{{ $t('complaint.signReport') }}</button>
          </div>
          <p v-else class="readonly-hint">{{ $t('complaint.readOnlyHint') }}</p>
          <p v-if="actionError" class="error">{{ actionError }}</p>
        </div>

        <div v-if="canWrite" class="assignment-section">
          <h3>{{ $t('complaint.assignment') }}</h3>
          <p class="current-assignee">
            {{ $t('complaint.assignedInvestigator') }}:
            <strong>{{ store.currentComplaint.assigned_to_name || $t('complaint.unassigned') }}</strong>
          </p>
          <div class="assign-row">
            <select v-model="selectedUser">
              <option value="">{{ $t('complaint.selectInspector') }}</option>
              <option v-for="user in usersStore.users" :key="user.id" :value="user.id">{{ user.full_name_ar }} ({{ user.role }})</option>
            </select>
            <button class="btn-primary" @click="assign" :disabled="!selectedUser">{{ $t('complaint.assign') }}</button>
          </div>
        </div>

        <div class="notes-section">
          <h3>{{ $t('complaint.notes') }}</h3>
          <form v-if="canWrite" @submit.prevent="addNote" class="note-form">
            <textarea v-model="noteContent" rows="3" :placeholder="$t('complaint.notePlaceholder')"></textarea>
            <div class="note-form-row">
              <select v-model="noteType" class="note-type-select">
                <option value="investigation">{{ $t('complaint.noteTypes.investigation') }}</option>
                <option value="finding">{{ $t('complaint.noteTypes.finding') }}</option>
                <option value="action">{{ $t('complaint.noteTypes.action') }}</option>
              </select>
              <label class="checkbox-label">
                <input v-model="noteConfidential" type="checkbox" />
                {{ $t('complaint.confidential') }}
              </label>
            </div>
            <button type="submit" class="btn-primary">{{ $t('complaint.addNote') }}</button>
          </form>

          <div v-for="note in store.notes" :key="note.id" class="note-card">
            <div class="note-card-top">
              <span class="badge note-type" :class="note.note_type">{{ $t(`complaint.noteTypes.${note.note_type || 'investigation'}`) }}</span>
              <span v-if="note.is_confidential" class="badge urgent">{{ $t('complaint.confidential') }}</span>
            </div>
            <p v-if="note.hidden" class="hidden-note">🔒 {{ $t('complaint.hiddenNote') }}</p>
            <p v-else>{{ note.content }}</p>
            <small>{{ formatDate(note.created_at) }}</small>
          </div>
        </div>

        <ComplaintMinutes :complaint-id="route.params.id" :can-write="canWrite" />

        <InvestigationReport
          :complaint-id="route.params.id"
          :complaint-status="store.currentComplaint.status"
        />

        <ComplaintEvidence :complaint-id="route.params.id" :can-write="canWrite" />

        <div class="history-section">
          <h3>{{ $t('complaint.activityLog') }}</h3>
          <ol v-if="store.history.length" class="timeline">
            <li v-for="entry in store.history" :key="entry.id" class="timeline-item">
              <span class="timeline-dot" :class="entry.action"></span>
              <div class="timeline-body">
                <div class="timeline-title">{{ $t(`complaint.action.${entry.action}`) }}</div>
                <div class="timeline-desc">{{ entry.description }}</div>
                <small>{{ entry.performed_by || $t('complaint.unknownUser') }} · {{ formatDate(entry.created_at) }}</small>
              </div>
            </li>
          </ol>
          <p v-else class="empty-state">{{ $t('complaint.noActivity') }}</p>
        </div>
      </div>

      <div v-else-if="store.loading">{{ $t('common.loading') }}</div>
      <div v-else>{{ $t('complaint.notFound') }}</div>
    </main>

    <div v-if="showSignModal" class="modal-overlay" @click.self="showSignModal = false">
      <div class="modal">
        <h3>{{ $t('complaint.signReport') }}</h3>
        <input v-model="signTotp" type="text" inputmode="numeric" maxlength="6" :placeholder="$t('complaint.enterTotp')" />
        <p class="hint">{{ $t('complaint.signTotpHint') }}</p>
        <p v-if="signError" class="error">{{ signError }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showSignModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn-primary" @click="sign" :disabled="signing">{{ $t('complaint.sign') }}</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppLayout from '../components/AppLayout.vue'
import ComplaintProgressTracker from '../components/ComplaintProgressTracker.vue'
import ComplaintMinutes from '../components/ComplaintMinutes.vue'
import InvestigationReport from '../components/InvestigationReport.vue'
import ComplaintEvidence from '../components/ComplaintEvidence.vue'
import { useComplaintStore } from '../stores/complaints'
import { useUsersStore } from '../stores/users'

const route = useRoute()
const store = useComplaintStore()
const usersStore = useUsersStore()
const { t } = useI18n()

const nextStatus = ref('')
const selectedUser = ref('')
const noteContent = ref('')
const noteType = ref('investigation')
const noteConfidential = ref(false)
const showSignModal = ref(false)
const signTotp = ref('')
const signError = ref('')
const signing = ref(false)

const statusTransitions = {
  received: ['under_investigation', 'closed'],
  under_investigation: ['received', 'escalated', 'closed'],
  escalated: ['under_investigation', 'closed'],
  closed: [],
}

const currentRole = (() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}').role || ''
  } catch {
    return ''
  }
})()

const allowedTransitions = computed(() => statusTransitions[store.currentComplaint?.status] || [])
const canEscalate = computed(() => ['received', 'under_investigation'].includes(store.currentComplaint?.status))
const canWrite = computed(() => currentRole !== 'viewer' && currentRole !== '')
const canSign = computed(() => ['senior_inspector', 'admin', 'super_admin'].includes(currentRole))

function loadComplaint() {
  store.clearCurrentComplaint()
  store.fetchOne(route.params.id)
  store.fetchNotes(route.params.id)
  store.fetchHistory(route.params.id)
  usersStore.fetchUsers()
}

onMounted(loadComplaint)
watch(() => route.params.id, loadComplaint)

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

const actionError = ref('')

async function changeStatus() {
  actionError.value = ''
  try {
    await store.updateStatus(route.params.id, nextStatus.value)
    nextStatus.value = ''
    store.fetchHistory(route.params.id)
  } catch (e) {
    actionError.value = e.response?.data?.detail || t('common.actionFailed')
  }
}

async function escalate() {
  actionError.value = ''
  try {
    await store.escalate(route.params.id)
    store.fetchHistory(route.params.id)
  } catch (e) {
    actionError.value = e.response?.data?.detail || t('common.actionFailed')
  }
}

async function assign() {
  actionError.value = ''
  try {
    await store.assign(route.params.id, selectedUser.value)
    selectedUser.value = ''
    store.fetchHistory(route.params.id)
  } catch (e) {
    actionError.value = e.response?.data?.detail || t('common.actionFailed')
  }
}

async function addNote() {
  if (!noteContent.value.trim()) return
  actionError.value = ''
  try {
    await store.addNote(route.params.id, noteContent.value, noteConfidential.value, noteType.value)
    noteContent.value = ''
    noteConfidential.value = false
    noteType.value = 'investigation'
    store.fetchHistory(route.params.id)
  } catch (e) {
    actionError.value = e.response?.data?.detail || t('common.actionFailed')
  }
}

async function sign() {
  signError.value = ''
  signing.value = true
  try {
    await store.sign(route.params.id, signTotp.value)
    showSignModal.value = false
    signTotp.value = ''
    store.fetchHistory(route.params.id)
  } catch (e) {
    signError.value = e.response?.data?.detail || t('common.signingFailed')
  } finally {
    signing.value = false
  }
}
</script>

<style scoped>
.detail-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 24px; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.detail-header h1 { margin: 0; font-size: 22px; }
.badges { display: flex; gap: 8px; }
.detail-meta { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px; color: var(--text-secondary); }
.detail-section { margin-bottom: 24px; }
.detail-section h3 { margin-bottom: 10px; color: var(--color-primary); }
.workflow-section, .assignment-section, .notes-section, .history-section { margin-bottom: 24px; padding: 16px; background: var(--bg-muted); border-radius: 10px; }
.workflow-section h3, .assignment-section h3, .notes-section h3, .history-section h3 { margin-bottom: 12px; }
.workflow-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.status-select { width: auto; min-width: 180px; margin: 0; }
.assign-row { display: flex; gap: 10px; align-items: center; }
.assign-row select { width: auto; min-width: 220px; margin: 0; }
.note-form { margin-bottom: 16px; }
.note-form textarea { margin-bottom: 8px; }
.note-form-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 4px; }
.note-type-select { width: auto; min-width: 160px; margin: 0; }
.note-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 10px; }
.note-card-top { display: flex; gap: 8px; margin-bottom: 8px; }
.badge.note-type { background: rgba(122,122,122,0.12); color: var(--text-secondary); }
.badge.note-type.finding { background: rgba(59,126,161,0.12); color: var(--color-info); }
.badge.note-type.action { background: rgba(76,175,80,0.12); color: var(--color-success); }
.note-card p { margin: 0 0 6px; }
.current-assignee { font-size: 13px; color: var(--text-secondary); margin: 0 0 12px; }
.hidden-note { color: var(--text-tertiary); font-style: italic; }
.readonly-hint { color: var(--text-tertiary); font-size: 13px; }
.error { color: var(--color-danger); font-size: 13px; margin-top: 8px; }
.back-btn { margin-bottom: 16px; padding: 8px 16px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; }
.btn-warning { padding: 10px 20px; background: var(--color-warning); color: white; border: none; border-radius: 8px; cursor: pointer; }
.btn-success { padding: 10px 20px; background: var(--color-success); color: white; border: none; border-radius: 8px; cursor: pointer; }
.checkbox-label { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
.checkbox-label input { width: auto; margin: 0; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { background: var(--bg-card); padding: 24px; border-radius: 12px; width: 100%; max-width: 360px; }
.modal h3 { margin-bottom: 12px; }
.modal .hint { font-size: 12px; color: var(--text-tertiary); margin: 8px 0; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-secondary { padding: 10px 20px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; }

.timeline { list-style: none; margin: 0; padding: 0; }
.timeline-item { display: flex; gap: 12px; padding-inline-start: 2px; }
.timeline-item:not(:last-child) { padding-bottom: 18px; position: relative; }
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  inset-inline-start: 5px;
  top: 14px;
  bottom: -4px;
  width: 2px;
  background: var(--border-color);
}
.timeline-dot { width: 12px; height: 12px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; background: var(--color-neutral); z-index: 1; }
.timeline-dot.created { background: var(--color-info); }
.timeline-dot.status_changed { background: var(--color-primary); }
.timeline-dot.assigned { background: var(--color-info); }
.timeline-dot.escalated { background: var(--color-danger); }
.timeline-dot.note_added { background: var(--color-neutral); }
.timeline-dot.minute_added { background: var(--color-gold); }
.timeline-dot.signed { background: var(--color-success); }
.timeline-body { flex: 1; }
.timeline-title { font-weight: 600; font-size: 14px; color: var(--text-primary); }
.timeline-desc { font-size: 13px; color: var(--text-secondary); margin: 2px 0; }
.timeline-body small { color: var(--text-tertiary); font-size: 12px; }
.history-section .empty-state { color: var(--text-tertiary); font-size: 13px; }
</style>
