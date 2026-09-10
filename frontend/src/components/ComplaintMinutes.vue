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
          <label>{{ $t('minutes.attendees') }}</label>
          <input v-model="form.attendees" type="text" :placeholder="$t('minutes.attendeesPlaceholder')" />
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
          <strong class="minute-title">{{ m.title }}</strong>
          <span class="minute-date">{{ formatDate(m.minute_date) }}</span>
        </div>
        <p v-if="m.attendees" class="minute-attendees">👥 {{ m.attendees }}</p>
        <p class="minute-summary">{{ m.summary }}</p>
        <div class="minute-card-bottom">
          <button class="btn-link" @click="download(m)">📄 {{ m.original_file_name }} ({{ formatSize(m.file_size_bytes) }})</button>
          <small>{{ m.uploaded_by_name || $t('complaint.unknownUser') }} · {{ formatDate(m.created_at) }}</small>
        </div>
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

const form = reactive({ minuteType: 'investigation', title: '', minuteDate: '', attendees: '', summary: '' })
const fileInput = ref(null)
const selectedFile = ref(null)
const formError = ref('')
const submitting = ref(false)

onMounted(() => store.fetchMinutes(props.complaintId))

function onFileChange(e) {
  selectedFile.value = e.target.files?.[0] || null
}

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
  }
  if (selectedFile.value.type && selectedFile.value.type !== 'application/pdf' && !selectedFile.value.name.toLowerCase().endsWith('.pdf')) {
    formError.value = t('minutes.pdfOnlyHint')
    return
  }
  submitting.value = true
  try {
    await store.addMinute(props.complaintId, { ...form, file: selectedFile.value })
    form.title = ''
    form.attendees = ''
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
</script>

<style scoped>
.minutes-section { margin-bottom: 24px; padding: 16px; background: var(--bg-muted); border-radius: 10px; }
.minutes-section h3 { margin-bottom: 12px; }
.minute-form { margin-bottom: 18px; padding-bottom: 16px; border-bottom: 1px solid var(--border-color); }
.minute-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 10px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field-wide { grid-column: 1 / -1; }
.field label { font-size: 12.5px; color: var(--text-secondary); }
.field input, .field select, .field textarea { margin: 0; }
.field-hint { font-size: 11.5px; color: var(--text-tertiary); margin: 2px 0 0; }
.error { color: var(--color-danger); font-size: 13px; margin: 4px 0 10px; }

.minute-list { display: flex; flex-direction: column; gap: 10px; }
.minute-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; }
.minute-card-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.minute-title { flex: 1; font-size: 14px; }
.minute-date { font-size: 12px; color: var(--text-tertiary); }
.badge.minute-type { background: rgba(59,126,161,0.12); color: var(--color-info); }
.badge.minute-type.meeting { background: rgba(166,139,91,0.16); color: var(--color-gold); }
.minute-attendees { font-size: 12.5px; color: var(--text-secondary); margin: 0 0 6px; }
.minute-summary { margin: 0 0 8px; font-size: 13.5px; color: var(--text-primary); white-space: pre-wrap; }
.minute-card-bottom { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; }
.btn-link { background: none; border: none; color: var(--color-primary); cursor: pointer; font-size: 13px; padding: 0; text-decoration: underline; }
.btn-link:hover { color: var(--color-gold); }
.minute-card-bottom small { color: var(--text-tertiary); font-size: 11.5px; }
.empty-state { color: var(--text-tertiary); font-size: 13px; padding: 8px 0; }

@media (max-width: 640px) {
  .minute-form-grid { grid-template-columns: 1fr; }
}
</style>
