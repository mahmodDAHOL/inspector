<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-section">
        <img src="/logo.jpg" alt="" class="logo-box" />
        <h2 class="ministry-title">{{ $t('landing.title') }}</h2>
        <h1>{{ $t('login.title') }}</h1>
        <p>{{ $t('login.subtitle') }}</p>
      </div>

      <div v-if="step === 'credentials'">
        <form @submit.prevent="submitCredentials">
          <input v-model="form.username" type="text" :placeholder="$t('common.username')" required />
          <input v-model="form.password" type="password" :placeholder="$t('common.password')" required />
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" class="btn-primary" :disabled="submitting">{{ $t('login.next') }}</button>
        </form>
      </div>

      <div v-else>
        <p>{{ $t('login.otpHint') }}</p>
        <div class="otp-inputs">
          <input
            v-for="i in 6"
            :key="i"
            :ref="el => (otpRefs[i - 1] = el)"
            v-model="totpDigits[i - 1]"
            type="text"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="1"
            class="otp-digit"
            @input="onOtpInput(i - 1, $event)"
            @keydown="onOtpKeydown(i - 1, $event)"
            @paste="onOtpPaste($event)"
          />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn-primary" @click="verify" :disabled="submitting">{{ $t('login.verify') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()
const step = ref('credentials')
const form = reactive({ username: '', password: '' })
const totpDigits = reactive(['', '', '', '', '', ''])
const otpRefs = ref([])
const error = ref('')
const submitting = ref(false)

function onOtpInput(index, event) {
  const digit = event.target.value.replace(/\D/g, '').slice(-1)
  totpDigits[index] = digit
  if (digit && index < 5) {
    otpRefs.value[index + 1]?.focus()
  }
}

function onOtpKeydown(index, event) {
  if (event.key === 'Backspace' && !totpDigits[index] && index > 0) {
    otpRefs.value[index - 1]?.focus()
  }
}

function onOtpPaste(event) {
  event.preventDefault()
  const pasted = (event.clipboardData || window.clipboardData).getData('text')
  const digits = pasted.replace(/\D/g, '').slice(0, 6).split('')
  if (!digits.length) return
  digits.forEach((digit, i) => {
    totpDigits[i] = digit
  })
  const focusIndex = Math.min(digits.length, 6) - 1
  otpRefs.value[focusIndex]?.focus()
}

async function submitCredentials() {
  error.value = ''
  submitting.value = true
  try {
    const data = await auth.login(form.username, form.password)
    if (data.requires_mfa === false) {
      router.push('/dashboard')
    } else {
      step.value = 'mfa'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || t('common.loginFailed')
  } finally {
    submitting.value = false
  }
}

async function verify() {
  error.value = ''
  submitting.value = true
  try {
    await auth.verifyTOTP(totpDigits.join(''))
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || t('common.verificationFailed')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: var(--bg-body); }
.login-card { background: var(--bg-card); padding: 40px; border-radius: 16px; box-shadow: var(--shadow-lg); width: 100%; max-width: 400px; }
.logo-section { text-align: center; margin-bottom: 24px; }
.logo-box { width: 72px; height: 72px; object-fit: contain; margin: 0 auto 12px; display: block; }
.ministry-title { font-size: 15px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; }
input { width: 100%; padding: 12px; margin-bottom: 12px; border: 1px solid var(--border-color); border-radius: 8px; background: transparent; color: var(--text-primary); }
.btn-primary { width: 100%; padding: 12px; background: #1B5E5E; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
.otp-inputs { display: flex; gap: 8px; justify-content: center; margin: 16px 0; }
.otp-digit { width: 44px; height: 52px; text-align: center; font-size: 20px; border-radius: 8px; border: 1px solid var(--border-color); }
.error { color: var(--color-danger); font-size: 13px; margin: -4px 0 12px; }
</style>
