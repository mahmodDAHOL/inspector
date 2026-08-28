<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo">
        <div class="logo-icon">م</div>
        <span>Inspection Portal</span>
      </div>
    </div>
    <div class="header-right">
      <button @click="toggleTheme">{{ isDark ? '☀️' : '🌙' }}</button>
      <button @click="toggleLang">{{ locale === 'ar' ? 'EN' : 'AR' }}</button>
      <button @click="logout">Logout</button>
    </div>
  </header>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useThemeStore } from '../stores/theme'
import { useAuthStore } from '../stores/auth'

const { locale } = useI18n()
const theme = useThemeStore()
const auth = useAuthStore()
const isDark = theme.isDark

function toggleTheme() { theme.toggle() }
function toggleLang() {
  locale.value = locale.value === 'ar' ? 'en' : 'ar'
  localStorage.setItem('locale', locale.value)
  document.documentElement.dir = locale.value === 'ar' ? 'rtl' : 'ltr'
}
function logout() { auth.logout() }
</script>

<style scoped>
.app-header { display: flex; justify-content: space-between; align-items: center; padding: 0 20px; height: 60px; background: var(--bg-card); border-bottom: 1px solid var(--border-color); }
.logo { display: flex; align-items: center; gap: 10px; }
.logo-icon { width: 36px; height: 36px; background: #1B5E5E; color: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
.header-right { display: flex; gap: 8px; }
button { padding: 6px 12px; border: 1px solid var(--border-color); background: transparent; border-radius: 6px; cursor: pointer; color: var(--text-secondary); }
</style>
