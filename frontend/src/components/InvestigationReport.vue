<template>
  <section class="report-section">
    <div class="section-heading">
      <div>
        <h3>{{ $t('investigationReport.title') }}</h3>
        <p class="hint">{{ $t('investigationReport.description') }}</p>
      </div>
      <span v-if="store.report" :class="['badge', store.report.status]">{{ $t(`investigationReport.status.${store.report.status}`) }}</span>
    </div>

    <div v-if="store.loading" class="empty-state">{{ $t('common.loading') }}</div>
    <form v-else-if="canWrite && (!store.report || store.report.status === 'draft')" @submit.prevent="save" class="report-form">
      <label>{{ $t('investigationReport.fields.title') }}<input v-model="form.title" required maxlength="200" /></label>
      <label>{{ $t('investigationReport.fields.scope') }}<textarea v-model="form.scope" rows="3" required /></label>
      <label>{{ $t('investigationReport.fields.methodology') }}<textarea v-model="form.methodology" rows="3" required /></label>
      <label>{{ $t('investigationReport.fields.findings') }}<textarea v-model="form.findings" rows="5" required /></label>
      <label>{{ $t('investigationReport.fields.evidenceSummary') }}<textarea v-model="form.evidence_summary" rows="3" required /></label>
      <label>{{ $t('investigationReport.fields.conclusion') }}<textarea v-model="form.conclusion" rows="3" required /></label>
      <label>{{ $t('investigationReport.fields.recommendations') }}<textarea v-model="form.recommendations" rows="3" required /></label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn-primary" :disabled="saving">{{ saving ? $t('investigationReport.saving') : $t('common.save') }}</button>
    </form>

    <div v-else-if="store.report" class="report-readonly">
      <h4>{{ store.report.title }}</h4>
      <dl>
        <template v-for="field in reportFields" :key="field.key">
          <dt>{{ $t(`investigationReport.fields.${field.i18n}`) }}</dt>
          <dd>{{ store.report[field.key] }}</dd>
        </template>
      </dl>
      <small v-if="store.report.content_hash" class="hash">SHA-256: {{ store.report.content_hash }}</small>
    </div>
    <p v-else class="empty-state">{{ $t('investigationReport.empty') }}</p>

    <div v-if="store.report?.status === 'draft' && canFinalize" class="finalize-row">
      <button class="btn-success" :disabled="!isClosed" @click="showFinalize = true">{{ $t('investigationReport.finalize') }}</button>
      <span v-if="!isClosed" class="hint">{{ $t('investigationReport.finalizeClosedOnly') }}</span>
    </div>

    <div v-if="showFinalize" class="modal-overlay" @click.self="showFinalize = false">
      <div class="modal">
        <h3>{{ $t('investigationReport.finalize') }}</h3>
        <p class="hint">{{ $t('investigationReport.finalizeHint') }}</p>
        <input v-model="totpCode" inputmode="numeric" maxlength="6" :placeholder="$t('complaint.enterTotp')" />
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showFinalize = false">{{ $t('common.cancel') }}</button>
          <button class="btn-primary" :disabled="finalizing" @click="finalize">{{ $t('complaint.sign') }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useInvestigationReportsStore } from '../stores/investigationReports'

const props = defineProps({ complaintId: { type: String, required: true }, complaintStatus: { type: String, required: true } })
const { t } = useI18n()
const store = useInvestigationReportsStore()
const saving = ref(false)
const finalizing = ref(false)
const showFinalize = ref(false)
const totpCode = ref('')
const error = ref('')
const form = reactive({ title: '', scope: '', methodology: '', findings: '', evidence_summary: '', conclusion: '', recommendations: '' })
const reportFields = [
  { key: 'scope', i18n: 'scope' },
  { key: 'methodology', i18n: 'methodology' },
  { key: 'findings', i18n: 'findings' },
  { key: 'evidence_summary', i18n: 'evidenceSummary' },
  { key: 'conclusion', i18n: 'conclusion' },
  { key: 'recommendations', i18n: 'recommendations' },
]
const role = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}').role || '' } catch { return '' }
})
const canWrite = computed(() => ['super_admin', 'admin', 'senior_inspector', 'inspector'].includes(role.value))
const canFinalize = computed(() => ['super_admin', 'admin', 'senior_inspector'].includes(role.value))
const isClosed = computed(() => props.complaintStatus === 'closed')

function fillForm() {
  if (store.report) Object.assign(form, store.report)
}

async function loadReport() {
  error.value = ''
  Object.keys(form).forEach(key => { form[key] = '' })
  try { await store.fetchReport(props.complaintId); fillForm() } catch (e) { error.value = e.response?.data?.detail || t('common.error') }
}

onMounted(loadReport)
watch(() => props.complaintId, loadReport)
watch(() => store.report, fillForm)

async function save() {
  error.value = ''
  saving.value = true
  try {
    if (store.report) await store.updateReport(props.complaintId, form)
    else await store.createReport(props.complaintId, form)
  } catch (e) { error.value = e.response?.data?.detail || t('common.saveFailed') } finally { saving.value = false }
}

async function finalize() {
  error.value = ''
  finalizing.value = true
  try { await store.finalizeReport(props.complaintId, totpCode.value); showFinalize.value = false; totpCode.value = '' }
  catch (e) { error.value = e.response?.data?.detail || t('common.signingFailed') }
  finally { finalizing.value = false }
}
</script>

<style scoped>
.report-section { margin-bottom: 24px; padding: 20px; background: var(--bg-muted); border: 1px solid var(--border-color); border-radius: 12px; box-shadow: var(--shadow-soft); }
.section-heading, .finalize-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.section-heading h3 { margin-bottom: 4px; font-size: 17px; color: var(--color-primary); }
.hint { color: var(--text-secondary); font-size: 13px; margin: 0 0 12px; }
.report-form { display: grid; gap: 12px; }
.report-form label { display: grid; gap: 4px; font-size: 12.5px; color: var(--text-secondary); }
.report-form input, .report-form textarea { margin: 0; }
.report-readonly { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px; box-shadow: var(--shadow-soft); }
.report-readonly h4 { margin: 0 0 14px; font-size: 16px; }
dl { display: grid; grid-template-columns: minmax(140px, .3fr) 1fr; gap: 8px 16px; }
dt { color: var(--text-secondary); font-size: 13px; }
dd { margin: 0; white-space: pre-wrap; }
.hash { display: block; margin-top: 14px; color: var(--text-tertiary); overflow-wrap: anywhere; }
.finalize-row { margin-top: 16px; align-items: center; }
.error { color: var(--color-danger); font-size: 13px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { background: var(--bg-card); padding: 24px; border-radius: 12px; width: 100%; max-width: 360px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-success { padding: 10px 20px; background: var(--color-success); color: white; border: none; border-radius: 8px; cursor: pointer; }
.btn-secondary { padding: 10px 20px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; color: var(--text-primary); }
.empty-state { color: var(--text-tertiary); font-size: 13px; }
@media (max-width: 640px) { .report-section { padding: 14px; } .section-heading, .finalize-row { align-items: flex-start; flex-direction: column; } dl { grid-template-columns: 1fr; } }
</style>
