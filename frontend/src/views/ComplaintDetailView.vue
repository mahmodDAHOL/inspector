<template>
  <AppLayout>
    <main class="content">
      <button class="back-btn" @click="$router.back()">← {{ $t('common.back') }}</button>

      <div v-if="store.currentComplaint" class="detail-card">
        <div class="detail-header">
          <h1>{{ store.currentComplaint.title_ar }}</h1>
          <div class="badges">
            <span :class="['badge', store.currentComplaint.priority]">{{ store.currentComplaint.priority }}</span>
            <span :class="['badge', store.currentComplaint.status]">{{ store.currentComplaint.status }}</span>
          </div>
        </div>

        <div class="detail-meta">
          <p><strong>{{ $t('complaint.number') }}:</strong> {{ store.currentComplaint.complaint_number }}</p>
          <p><strong>{{ $t('complaint.category') }}:</strong> {{ store.currentComplaint.category }}</p>
          <p><strong>{{ $t('complaint.source') }}:</strong> {{ store.currentComplaint.source }}</p>
          <p><strong>{{ $t('complaint.createdAt') }}:</strong> {{ formatDate(store.currentComplaint.created_at) }}</p>
        </div>

        <div class="detail-section">
          <h3>{{ $t('complaint.description') }}</h3>
          <p>{{ store.currentComplaint.description }}</p>
        </div>

        <div class="workflow-section">
          <h3>{{ $t('complaint.workflow') }}</h3>
          <div class="workflow-actions">
            <select v-model="nextStatus" class="status-select">
              <option value="">{{ $t('complaint.selectAction') }}</option>
              <option v-for="status in allowedTransitions" :key="status" :value="status">{{ status }}</option>
            </select>
            <button class="btn-primary" @click="changeStatus" :disabled="!nextStatus">{{ $t('complaint.updateStatus') }}</button>
            <button v-if="canEscalate" class="btn-warning" @click="escalate">{{ $t('complaint.escalate') }}</button>
            <button v-if="store.currentComplaint.status === 'closed'" class="btn-success" @click="showSignModal = true">{{ $t('complaint.signReport') }}</button>
          </div>
        </div>

        <div class="assignment-section">
          <h3>{{ $t('complaint.assignment') }}</h3>
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
          <form @submit.prevent="addNote" class="note-form">
            <textarea v-model="noteContent" rows="3" :placeholder="$t('complaint.notePlaceholder')"></textarea>
            <label class="checkbox-label">
              <input v-model="noteConfidential" type="checkbox" />
              {{ $t('complaint.confidential') }}
            </label>
            <button type="submit" class="btn-primary">{{ $t('complaint.addNote') }}</button>
          </form>

          <div v-for="note in store.notes" :key="note.id" class="note-card">
            <p>{{ note.content }}</p>
            <span v-if="note.is_confidential" class="badge urgent">{{ $t('complaint.confidential') }}</span>
            <small>{{ formatDate(note.created_at) }}</small>
          </div>
        </div>
      </div>

      <div v-else-if="store.loading">{{ $t('common.loading') }}</div>
      <div v-else>{{ $t('complaint.notFound') }}</div>
    </main>

    <div v-if="showSignModal" class="modal-overlay" @click.self="showSignModal = false">
      <div class="modal">
        <h3>{{ $t('complaint.signReport') }}</h3>
        <input v-model="signPin" type="password" :placeholder="$t('complaint.enterPin')" />
        <p class="hint">{{ $t('complaint.demoPin') }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showSignModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn-primary" @click="sign">{{ $t('complaint.sign') }}</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useComplaintStore } from '../stores/complaints'
import { useUsersStore } from '../stores/users'

const route = useRoute()
const store = useComplaintStore()
const usersStore = useUsersStore()

const nextStatus = ref('')
const selectedUser = ref('')
const noteContent = ref('')
const noteConfidential = ref(false)
const showSignModal = ref(false)
const signPin = ref('')

const statusTransitions = {
  received: ['under_investigation', 'closed'],
  under_investigation: ['received', 'escalated', 'closed'],
  escalated: ['under_investigation', 'closed'],
  closed: [],
}

const allowedTransitions = computed(() => statusTransitions[store.currentComplaint?.status] || [])
const canEscalate = computed(() => ['received', 'under_investigation'].includes(store.currentComplaint?.status))

onMounted(() => {
  store.fetchOne(route.params.id)
  store.fetchNotes(route.params.id)
  usersStore.fetchUsers()
})

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function changeStatus() {
  await store.updateStatus(route.params.id, nextStatus.value)
  nextStatus.value = ''
}

async function escalate() {
  await store.escalate(route.params.id)
}

async function assign() {
  await store.assign(route.params.id, selectedUser.value)
  selectedUser.value = ''
}

async function addNote() {
  if (!noteContent.value.trim()) return
  await store.addNote(route.params.id, noteContent.value, noteConfidential.value)
  noteContent.value = ''
  noteConfidential.value = false
}

async function sign() {
  await store.sign(route.params.id, signPin.value)
  showSignModal.value = false
  signPin.value = ''
  alert('Report signed successfully')
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
.workflow-section, .assignment-section, .notes-section { margin-bottom: 24px; padding: 16px; background: var(--bg-muted); border-radius: 10px; }
.workflow-section h3, .assignment-section h3, .notes-section h3 { margin-bottom: 12px; }
.workflow-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.status-select { width: auto; min-width: 180px; margin: 0; }
.assign-row { display: flex; gap: 10px; align-items: center; }
.assign-row select { width: auto; min-width: 220px; margin: 0; }
.note-form { margin-bottom: 16px; }
.note-form textarea { margin-bottom: 8px; }
.note-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 10px; }
.note-card p { margin: 0 0 6px; }
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
</style>
