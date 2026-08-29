<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('complaints.new') }}</h1>

      <form @submit.prevent="submit">
        <section class="form-section">
          <h3>{{ $t('complaint.complaintInfoSection') }}</h3>

          <div class="form-row">
            <div class="form-group">
              <label>{{ $t('complaint.category') }} <span class="required">*</span></label>
              <select v-model="form.category" required>
                <option value="">{{ $t('complaint.selectCategory') }}</option>
                <option v-for="key in categoryKeys" :key="key" :value="key">{{ $t(`complaint.categories.${key}`) }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ $t('complaint.priorityLabel') }} <span class="required">*</span></label>
              <select v-model="form.priority" required>
                <option v-for="key in priorityKeys" :key="key" :value="key">{{ $t(`complaint.priority.${key}`) }}</option>
              </select>
            </div>
          </div>

          <div class="form-group full">
            <label>{{ $t('complaint.title') }} <span class="required">*</span></label>
            <input v-model="form.title_ar" :placeholder="$t('complaint.titleArPlaceholder')" required />
          </div>
          <div class="form-group full">
            <input v-model="form.title_en" :placeholder="$t('complaint.titleEnPlaceholder')" />
          </div>
          <div class="form-group full">
            <label>{{ $t('complaint.description') }} <span class="required">*</span></label>
            <textarea v-model="form.description" :placeholder="$t('complaint.descriptionPlaceholder')" required rows="5"></textarea>
          </div>
        </section>

        <section class="form-section">
          <h3>{{ $t('complaint.complainantInfoSection') }}</h3>

          <label class="checkbox-row">
            <input v-model="isAnonymous" type="checkbox" />
            {{ $t('complaint.anonymousLabel') }}
          </label>

          <div v-if="!isAnonymous" class="complainant-fields">
            <div class="form-row">
              <div class="form-group">
                <label>{{ $t('complaint.complainantName') }}</label>
                <input v-model="form.complainant_name" :placeholder="$t('complaint.complainantNamePlaceholder')" />
              </div>
              <div class="form-group">
                <label>{{ $t('complaint.complainantPhone') }}</label>
                <input v-model="form.complainant_phone" type="tel" :placeholder="$t('complaint.complainantPhonePlaceholder')" />
              </div>
            </div>
            <div class="form-group full">
              <label>{{ $t('complaint.complainantEmail') }}</label>
              <input v-model="form.complainant_email" type="email" :placeholder="$t('complaint.complainantEmailPlaceholder')" />
            </div>
          </div>
        </section>

        <section class="form-section">
          <h3>{{ $t('complaint.attachmentsSection') }}</h3>
          <p class="attachments-note">{{ $t('complaint.attachmentsComingSoon') }}</p>
        </section>

        <section class="form-section">
          <h3>{{ $t('complaint.confirmationSection') }}</h3>
          <label class="checkbox-row">
            <input v-model="confirmed" type="checkbox" required />
            {{ $t('complaint.confirmationLabel') }}
          </label>
        </section>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="submit-row">
          <button type="submit" class="btn-primary" :disabled="!confirmed || submitting">{{ $t('common.save') }}</button>
        </div>

        <p class="submit-notice">🔒 {{ $t('complaint.submitNotice') }}</p>
      </form>
    </main>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useComplaintStore } from '../stores/complaints'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()
const store = useComplaintStore()
const { t } = useI18n()

const categoryKeys = ['financial_fraud', 'procurement_violation', 'abuse_of_power', 'bribery', 'embezzlement', 'nepotism', 'document_forgery', 'misconduct', 'other']
const priorityKeys = ['normal', 'urgent', 'critical']

const isAnonymous = ref(false)
const confirmed = ref(false)
const submitting = ref(false)
const error = ref('')

const form = reactive({
  title_ar: '',
  title_en: '',
  description: '',
  category: '',
  priority: 'normal',
  complainant_name: '',
  complainant_phone: '',
  complainant_email: '',
})

watch(isAnonymous, (value) => {
  if (value) {
    form.complainant_name = ''
    form.complainant_phone = ''
    form.complainant_email = ''
  }
})

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    await store.create({ ...form, is_anonymous: isAnonymous.value })
    router.push('/complaints')
  } catch (e) {
    error.value = e.response?.data?.detail || t('common.saveFailed')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-section { background: var(--bg-muted); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.form-section h3 { font-size: 15px; color: var(--color-primary); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--color-gold); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.form-group.full { grid-column: 1 / -1; }
.form-group label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.required { color: var(--color-danger); }
.checkbox-row { display: flex; align-items: center; gap: 10px; font-size: 14px; padding: 10px 12px; background: var(--bg-card); border-radius: 8px; margin-bottom: 8px; }
.checkbox-row input { width: auto; margin: 0; }
.complainant-fields { margin-top: 12px; }
.attachments-note { font-size: 13px; color: var(--text-tertiary); margin: 0; }
.error { color: var(--color-danger); font-size: 13px; margin-bottom: 12px; }
.submit-row { text-align: center; padding: 10px 0 4px; }
.submit-row .btn-primary { padding: 12px 48px; }
.submit-row .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.submit-notice { text-align: center; font-size: 12px; color: var(--text-tertiary); margin-top: 12px; }

@media (max-width: 600px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
