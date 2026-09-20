<template>
  <div class="minutes-section">
    <h3>{{ $t('minutes.title') }}</h3>

    <form v-if="canWrite" @submit.prevent="submit" class="minute-form">
      <div class="minute-form-grid">
        <div class="field">
          <label>{{ $t('minutes.type') }}</label>
          <select v-model="form.minuteType">
            <option value="investigation">{{ $t('minutes.types.investigation') }}</option>
            <option value="meeting">{{ $t('minutes.types.meeting') }}</option>
          </select>
        </div>
        <div class="field">
          <label>{{ $t('minutes.minuteDate') }}</label>
          <input v-model="form.minuteDate" type="date" required />
        </div>
        <div class="field field-wide">
          <label>{{ $t('minutes.titleLabel') }}</label>
          <input v-model="form.title" type="text" :placeholder="$t('minutes.titlePlaceholder')" required />
        </div>
        <div class="field field-wide">
          <div class="attendee-heading">
            <label>{{ $t('minutes.attendees') }}</label>
            <button type="button" class="btn-small" @click="addAttendee">+ {{ $t('minutes.addAttendee') }}</button>
          </div>
          <div class="attendee-table-wrap">
            <table class="attendee-table">
              <thead><tr><th>{{ $t('minutes.attendeeName') }}</th><th>{{ $t('minutes.attendeeRole') }}</th><th>{{ $t('minutes.attendeeId') }}</th><th>{{ $t('minutes.attendeePhone') }}</th><th></th></tr></thead>
              <tbody>
                <tr v-for="(attendee, index) in form.attendees" :key="attendee.key">
                  <td><input v-model="attendee.name" :placeholder="$t('minutes.attendeeName')" required /></td>
                  <td><input v-model="attendee.role" /></td>
                  <td><input type="file" accept="image/jpeg,image/png" @change="selectIdImage(index, $event)" /></td>
                  <td><input v-model="attendee.phone" type="tel" /></td>
                  <td><button type="button" class="remove-btn" @click="removeAttendee(index)">×</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="field field-wide">
          <label>{{ $t('minutes.summary') }}</label>
          <textarea v-model="form.summary" rows="3" :placeholder="$t('minutes.summaryPlaceholder')" required></textarea>
        </div>
        <div class="field field-wide">
          <label>{{ $t('minutes.file') }}</label>
          <input ref="fileInput" type="file" accept="application/pdf,.pdf" @change="onFileChange" required />
          <p class="field-hint">{{ $t('minutes.pdfOnlyHint') }}</p>
        </div>
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <button type="submit" class="btn-primary" :disabled="submitting">
        {{ submitting ? $t('minutes.uploading') : $t('minutes.upload') }}
      </button>
    </form>

    <div v-if="store.loading" class="empty-state">{{ $t('common.loading') }}</div>
    <div v-else-if="!store.minutes.length" class="empty-state">{{ $t('minutes.empty') }}</div>
    <div v-else class="minute-list">
      <div v-for="m in store.minutes" :key="m.id" class="minute-card">
        <div class="minute-card-top">
          <span class="badge minute-type" :class="m.minute_type">{{ $t(`minutes.types.${m.minute_type}`) }}</span>
          <span v-if="m.archived_at" class="badge archived">{{ $t('minutes.archived') }}</span>
          <strong class="minute-title">{{ m.title }}</strong>
          <span class="minute-date">{{ formatDate(m.minute_date) }}</span>
        </div>
        <div v-if="m.attendees?.length" class="minute-attendees">
          <strong>{{ $t('minutes.attendees') }}</strong>
          <ul><li v-for="(attendee, index) in m.attendees" :key="index">{{ attendee.name }}<span v-if="attendee.role"> · {{ attendee.role }}</span><span v-if="attendee.phone"> · {{ attendee.phone }}</span><button v-if="attendee.id_image" class="btn-link" @click="downloadIdImage(m, index)">{{ $t('minutes.viewId') }}</button></li></ul>
        </div>
        <p class="minute-summary">{{ m.summary }}</p>
        <div class="minute-card-bottom">
          <button class="btn-link" @click="download(m)">📄 {{ m.original_file_name }} ({{ formatSize(m.file_size_bytes) }})</button>
          <div class="minute-meta">
            <small>{{ m.uploaded_by_name || $t('complaint.unknownUser') }} · {{ formatDate(m.created_at) }}</small>
            <small v-if="m.archived_at">{{ $t('minutes.archivedAt') }}: {{ formatDateTime(m.archived_at) }} · {{ m.archived_by_name || $t('complaint.unknownUser') }}</small>
            <small v-if="m.archived_at && m.archived_reason">{{ $t('minutes.archiveReason') }}: {{ m.archived_reason }}</small>
            <button v-if="canArchive && !m.archived_at" type="button" class="archive-action" @click="openArchiveModal(m)">
              <span aria-hidden="true">▣</span>
              {{ $t('minutes.archive') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-if="showArchiveModal" class="modal-overlay" @click.self="closeArchiveModal">
    <div class="archive-modal">
      <h3>{{ $t('minutes.archiveTitle') }}</h3>
      <p class="hint">{{ $t('minutes.archivePrompt') }}</p>
      <textarea v-model="archiveReason" :placeholder="$t('minutes.archiveReasonPlaceholder')" maxlength="2000" />
      <p v-if="formError" class="error">{{ formError }}</p>
      <div class="archive-modal-actions">
        <button type="button" class="btn-secondary" @click="closeArchiveModal">{{ $t('common.cancel') }}</button>
        <button type="button" class="archive-action" :disabled="archiving" @click="archive">{{ $t('minutes.archive') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMinutesStore } from '../stores/minutes'

const props = defineProps({
  complaintId: { type: String, required: true },
  canWrite: { type: Boolean, default: false },
})

const { t } = useI18n()
const store = useMinutesStore()

const form = reactive({ minuteType: 'investigation', title: '', minuteDate: '', attendees: [], summary: '' })
const fileInput = ref(null)
const selectedFile = ref(null)
const formError = ref('')
const submitting = ref(false)
const archiving = ref(false)
const showArchiveModal = ref(false)
const archiveReason = ref('')
const minuteToArchive = ref(null)
const currentRole = (() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}').role || '' } catch { return '' }
})()
const canArchive = ['super_admin', 'admin', 'senior_inspector'].includes(currentRole)
let attendeeKey = 0

onMounted(() => store.fetchMinutes(props.complaintId))

function onFileChange(e) {
  selectedFile.value = e.target.files?.[0] || null
}

function newAttendee() { return { key: attendeeKey++, name: '', role: '', phone: '', idImage: null } }
function addAttendee() { form.attendees.push(newAttendee()) }
function removeAttendee(index) { form.attendees.splice(index, 1) }
function selectIdImage(index, event) { form.attendees[index].idImage = event.target.files?.[0] || null }

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString()
}
function formatSize(bytes) {
  if (!bytes) return '0 KB'
  const kb = bytes / 1024
  return kb < 1024 ? `${kb.toFixed(0)} KB` : `${(kb / 1024).toFixed(1)} MB`
}

async function submit() {
  formError.value = ''
  if (!selectedFile.value) {
    formError.value = t('minutes.fileRequired')
    return
    formError.value = t('minutes.pdfOnlyHint')
    return
  }
  submitting.value = true
  try {
    const attendees = form.attendees.map(({ key, idImage, ...attendee }) => attendee)
    const idImages = form.attendees.map(attendee => attendee.idImage)
    await store.addMinute(props.complaintId, { ...form, attendees, idImages, file: selectedFile.value })
    form.title = ''
    form.attendees = []
    form.summary = ''
    form.minuteDate = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    formError.value = e.response?.data?.detail || t('common.saveFailed')
  } finally {
    submitting.value = false
  }
}

function download(m) {
  store.downloadMinuteFile(props.complaintId, m.id, m.original_file_name)
}

function downloadIdImage(m, index) {
  store.downloadAttendeeIdImage(props.complaintId, m.id, index)
}
function openArchiveModal(m) {
  minuteToArchive.value = m
  archiveReason.value = ''
  formError.value = ''
  showArchiveModal.value = true
}

function closeArchiveModal() {
  showArchiveModal.value = false
  minuteToArchive.value = null
  archiveReason.value = ''
}

async function archive() {
  if (archiving.value || !minuteToArchive.value || !archiveReason.value.trim()) {
    formError.value = t('minutes.archiveReasonRequired')
    return
  }
  archiving.value = true
  try {
    await store.archiveMinute(props.complaintId, minuteToArchive.value.id, archiveReason.value.trim())
    closeArchiveModal()
  }
  catch (e) { formError.value = e.response?.data?.detail || t('common.actionFailed') }
  finally { archiving.value = false }
}
</script>

<style scoped>
.minutes-section { margin-bottom: 24px; padding: 20px; background: var(--bg-muted); border: 1px solid var(--border-color); border-radius: 12px; box-shadow: var(--shadow-soft); }
.minutes-section h3 { margin-bottom: 4px; font-size: 17px; color: var(--color-primary); }
.minute-form { margin-bottom: 18px; padding-bottom: 16px; border-bottom: 1px solid var(--border-color); }
.minute-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 10px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field-wide { grid-column: 1 / -1; }
.field label { font-size: 12.5px; color: var(--text-secondary); }
.field input, .field select, .field textarea { margin: 0; }
.field-hint { font-size: 11.5px; color: var(--text-tertiary); margin: 2px 0 0; }
.attendee-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.attendee-table-wrap { overflow-x: auto; }
.attendee-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 8px; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; background: var(--bg-card); }
.attendee-table th { font-size: 11px; color: var(--text-secondary); text-align: start; padding: 8px; background: var(--bg-body); border-bottom: 1px solid var(--border-color); }
.attendee-table td { padding: 6px; vertical-align: middle; border-bottom: 1px solid var(--border-color); }
.attendee-table tr:last-child td { border-bottom: 0; }
.attendee-table input { min-width: 100px; margin: 0; }
.attendee-table input[type='file'] { min-width: 170px; font-size: 11px; }
.btn-small, .remove-btn { padding: 5px 9px; border: 1px solid var(--border-color); background: transparent; border-radius: 6px; cursor: pointer; color: var(--text-primary); white-space: nowrap; }
.remove-btn { color: var(--color-danger); font-size: 18px; line-height: 1; }
.error { color: var(--color-danger); font-size: 13px; margin: 4px 0 10px; }

.minute-list { display: flex; flex-direction: column; gap: 10px; }
.minute-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px; box-shadow: var(--shadow-soft); }
.minute-card-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.minute-title { flex: 1; font-size: 14px; }
.minute-date { font-size: 12px; color: var(--text-tertiary); }
.badge.archived { background: rgba(122,122,122,.15); color: var(--text-secondary); }
.badge.minute-type { background: rgba(59,126,161,0.12); color: var(--color-info); }
.badge.minute-type.meeting { background: rgba(166,139,91,0.16); color: var(--color-gold); }
.minute-attendees { font-size: 12.5px; color: var(--text-secondary); margin: 0 0 6px; }
.minute-attendees ul { margin: 5px 0 0; padding-inline-start: 20px; }
.minute-attendees li { margin-bottom: 4px; }
.minute-summary { margin: 0 0 8px; font-size: 13.5px; color: var(--text-primary); white-space: pre-wrap; }
.minute-card-bottom { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; }
.btn-link { background: none; border: none; color: var(--color-primary); cursor: pointer; font-size: 13px; padding: 0; text-decoration: underline; }
.btn-link:hover { color: var(--color-gold); }
.minute-card-bottom small { color: var(--text-tertiary); font-size: 11.5px; display: block; }
.minute-meta { display: grid; gap: 4px; text-align: end; }
.archive-action { display: inline-flex; align-items: center; justify-content: center; gap: 6px; width: fit-content; justify-self: end; padding: 5px 10px; border: 1px solid rgba(184,84,80,.45); border-radius: 6px; background: rgba(184,84,80,.07); color: var(--color-danger); font-size: 12px; line-height: 1.2; cursor: pointer; }
.archive-action:hover { background: rgba(184,84,80,.14); border-color: var(--color-danger); }
.archive-action:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(184,84,80,.16); }
.empty-state { color: var(--text-tertiary); font-size: 13px; padding: 8px 0; }

@media (max-width: 640px) {
  .minute-form-grid { grid-template-columns: 1fr; }
  .minutes-section { padding: 14px; }
  .minute-card-bottom { align-items: flex-start; flex-direction: column; }
  .minute-meta { width: 100%; text-align: start; }
}
</style>
