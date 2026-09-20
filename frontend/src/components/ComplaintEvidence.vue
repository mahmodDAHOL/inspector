<template>
  <section class="evidence-section">
    <div class="section-heading">
      <div>
        <h3>{{ $t('evidence.title') }}</h3>
        <p class="hint">{{ $t('evidence.description') }}</p>
      </div>
    </div>

    <form v-if="canWrite" @submit.prevent="submit" class="evidence-form">
      <label>{{ $t('evidence.file') }}<input ref="fileInput" type="file" accept="application/pdf,image/jpeg,image/png" required @change="selectFile" /></label>
      <label>{{ $t('evidence.descriptionLabel') }}<input v-model="description" maxlength="500" required /></label>
      <p class="hint">{{ $t('evidence.allowedTypes') }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn-primary" :disabled="uploading">{{ uploading ? $t('evidence.uploading') : $t('evidence.upload') }}</button>
    </form>

    <div v-if="store.loading" class="empty-state">{{ $t('common.loading') }}</div>
    <div v-else-if="!store.items.length" class="empty-state">{{ $t('evidence.empty') }}</div>
    <div v-else class="evidence-list">
      <article v-for="item in store.items" :key="item.id" class="evidence-card">
        <div class="evidence-top">
          <strong>{{ item.original_file_name }}</strong>
          <span class="badge">{{ formatSize(item.file_size_bytes) }}</span>
        </div>
        <p>{{ item.description }}</p>
        <small>{{ item.uploaded_by_name || $t('complaint.unknownUser') }} · {{ formatDate(item.created_at) }}</small>
        <code>{{ item.sha256 }}</code>
        <button class="btn-link" @click="download(item)">{{ $t('evidence.download') }}</button>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useEvidenceStore } from '../stores/evidence'

const props = defineProps({ complaintId: { type: String, required: true }, canWrite: { type: Boolean, default: false } })
const { t } = useI18n()
const store = useEvidenceStore()
const fileInput = ref(null)
const selectedFile = ref(null)
const description = ref('')
const error = ref('')
const uploading = ref(false)
const maxBytes = 50 * 1024 * 1024
const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png']

onMounted(() => store.fetchEvidence(props.complaintId))

function selectFile(event) {
  selectedFile.value = event.target.files?.[0] || null
  error.value = ''
}

function formatDate(value) { return value ? new Date(value).toLocaleString() : '' }
function formatSize(bytes) {
  if (!bytes) return '0 KB'
  if (bytes < 1024 * 1024) return `${Math.ceil(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function submit() {
  error.value = ''
  if (!selectedFile.value) return
  if (!allowedTypes.includes(selectedFile.value.type)) {
    error.value = t('evidence.invalidType')
    return
  }
  if (selectedFile.value.size > maxBytes) {
    error.value = t('evidence.tooLarge')
    return
  }
  uploading.value = true
  try {
    await store.uploadEvidence(props.complaintId, description.value, selectedFile.value)
    description.value = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || t('common.saveFailed')
  } finally {
    uploading.value = false
  }
}

function download(item) { store.downloadEvidence(props.complaintId, item) }
</script>

<style scoped>
.evidence-section { margin-bottom: 24px; padding: 20px; background: var(--bg-muted); border: 1px solid var(--border-color); border-radius: 12px; box-shadow: var(--shadow-soft); }
.section-heading h3 { margin-bottom: 4px; font-size: 17px; color: var(--color-primary); }
.hint { color: var(--text-secondary); font-size: 13px; margin: 0 0 12px; }
.evidence-form { display: grid; gap: 10px; margin-bottom: 16px; }
.evidence-form label { display: grid; gap: 4px; font-size: 12.5px; color: var(--text-secondary); }
.evidence-form input { margin: 0; }
.error { color: var(--color-danger); font-size: 13px; }
.evidence-list { display: grid; gap: 10px; }
.evidence-card { padding: 15px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; box-shadow: var(--shadow-soft); }
.evidence-top { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
.evidence-card p { margin: 8px 0; white-space: pre-wrap; }
.evidence-card small { color: var(--text-tertiary); display: block; margin-bottom: 8px; }
.evidence-card code { display: block; color: var(--text-tertiary); font-size: 10px; overflow-wrap: anywhere; margin-bottom: 8px; }
.btn-link { background: none; border: none; color: var(--color-primary); cursor: pointer; padding: 0; text-decoration: underline; }
.empty-state { color: var(--text-tertiary); font-size: 13px; }
@media (max-width: 640px) { .evidence-section { padding: 14px; } .evidence-top { align-items: flex-start; flex-direction: column; } }
</style>
