<template>
  <div class="landing-page" :dir="locale === 'ar' ? 'rtl' : 'ltr'">
    <button class="lang-toggle" @click="toggleLocale">
      {{ locale === 'ar' ? 'English' : 'العربية' }}
    </button>

    <div class="hero">
      <img src="/logo.jpg" alt="" class="logo-box" />
      <h1 class="app-title">{{ $t('landing.title') }}</h1>
      <p class="app-subtitle">{{ $t('landing.subtitle') }}</p>
      <h2>{{ $t('landing.welcome') }}</h2>
      <p class="description">{{ $t('landing.description') }}</p>
      <router-link to="/login" class="cta-button">
        {{ $t('landing.login') }}
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

function toggleLocale() {
  const next = locale.value === 'ar' ? 'en' : 'ar'
  locale.value = next
  localStorage.setItem('locale', next)
  document.documentElement.setAttribute('lang', next)
  document.documentElement.setAttribute('dir', next === 'ar' ? 'rtl' : 'ltr')
}
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #1B5E5E 0%, #123f3f 100%);
  padding: 40px 20px;
  position: relative;
}

.lang-toggle {
  position: absolute;
  top: 24px;
  inset-inline-end: 24px;
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.lang-toggle:hover {
  background: rgba(255, 255, 255, 0.12);
}

.hero {
  max-width: 560px;
  text-align: center;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 48px 40px;
  backdrop-filter: blur(6px);
}

.logo-box {
  width: 88px;
  height: 88px;
  background: #ffffff;
  border-radius: 18px;
  object-fit: contain;
  padding: 8px;
  margin: 0 auto 20px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
}

.app-title {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px;
}

.app-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 32px;
}

.hero h2 {
  font-size: 30px;
  color: #ffffff;
  margin-bottom: 14px;
}

.description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.7;
  margin-bottom: 28px;
}

.cta-button {
  display: inline-block;
  padding: 14px 36px;
  background: #A68B6A;
  color: #ffffff;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 600;
  transition: background 0.2s;
}

.cta-button:hover {
  background: #8f7658;
}
</style>
