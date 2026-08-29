<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/dashboard" class="logo">
        <img src="/logo.jpg" alt="" class="logo-icon" />
        <span>{{ $t('landing.title') }}</span>
      </router-link>
    </div>
    <div class="header-right">
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? $t('common.lightMode') : $t('common.darkMode')">
        {{ isDark ? '☀️' : '🌙' }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { useThemeStore } from '../stores/theme'

const theme = useThemeStore()
const isDark = theme.isDark

function toggleTheme() { theme.toggle() }
</script>

<style scoped>
.app-header { display: flex; justify-content: space-between; align-items: center; padding: 0 24px; height: 60px; background: var(--bg-card); border-bottom: 1px solid var(--border-color); }
.logo { display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--text-primary); font-weight: 600; }
.logo-icon { width: 36px; height: 36px; background: #ffffff; border-radius: 8px; object-fit: contain; padding: 3px; border: 1px solid var(--border-color); }
.header-right { display: flex; gap: 8px; }
.theme-toggle { padding: 6px 12px; border: 1px solid var(--border-color); background: transparent; border-radius: 6px; cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { border-color: var(--color-primary); color: var(--color-primary); }
</style>
