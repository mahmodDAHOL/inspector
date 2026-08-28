<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-section">
        <div class="logo-box">م</div>
        <h1>{{ $t('login.title') }}</h1>
        <p>{{ $t('login.subtitle') }}</p>
      </div>

      <div v-if="step === 'credentials'">
        <form @submit.prevent="submitCredentials">
          <input v-model="form.username" type="text" placeholder="Username" required />
          <input v-model="form.password" type="password" placeholder="Password" required />
          <button type="submit" class="btn-primary">{{ $t('login.next') }}</button>
        </form>
      </div>

      <div v-else>
        <p>Enter 6-digit code from authenticator</p>
        <div class="otp-inputs">
          <input v-for="i in 6" :key="i" v-model="totpDigits[i-1]" maxlength="1" class="otp-digit" />
        </div>
        <button class="btn-primary" @click="verify">{{ $t('login.verify') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const step = ref('credentials')
const form = reactive({ username: '', password: '' })
const totpDigits = reactive(['', '', '', '', '', ''])

async function submitCredentials() {
  await auth.login(form.username, form.password)
  step.value = 'mfa'
}

async function verify() {
  await auth.verifyTOTP(totpDigits.join(''))
  router.push('/dashboard')
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: var(--bg-body); }
.login-card { background: var(--bg-card); padding: 40px; border-radius: 16px; box-shadow: var(--shadow-lg); width: 100%; max-width: 400px; }
.logo-section { text-align: center; margin-bottom: 24px; }
.logo-box { width: 60px; height: 60px; background: #1B5E5E; color: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; margin: 0 auto 16px; }
input { width: 100%; padding: 12px; margin-bottom: 12px; border: 1px solid var(--border-color); border-radius: 8px; background: transparent; color: var(--text-primary); }
.btn-primary { width: 100%; padding: 12px; background: #1B5E5E; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
.otp-inputs { display: flex; gap: 8px; justify-content: center; margin: 16px 0; }
.otp-digit { width: 44px; height: 52px; text-align: center; font-size: 20px; border-radius: 8px; border: 1px solid var(--border-color); }
</style>
