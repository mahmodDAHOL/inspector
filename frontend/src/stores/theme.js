import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const current = ref(localStorage.getItem('theme') || 'light')
  const isDark = computed(() => current.value === 'dark')

  function toggle() {
    current.value = current.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', current.value)
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  return { current, isDark, toggle }
})
