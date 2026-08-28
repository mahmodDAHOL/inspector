<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo">
        <div class="logo-icon">م</div>
        <span>Inspection Portal</span>
      </router-link>
    </div>
    <div class="header-right">
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Light mode' : 'Dark mode'">
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
.logo-icon { width: 36px; height: 36px; background: var(--color-primary); color: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
.header-right { display: flex; gap: 8px; }
.theme-toggle { padding: 6px 12px; border: 1px solid var(--border-color); background: transparent; border-radius: 6px; cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { border-color: var(--color-primary); color: var(--color-primary); }
</style>
