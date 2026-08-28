<template>
  <div class="bar-chart">
    <div v-for="(value, key) in normalizedData" :key="key" class="bar-row">
      <span class="bar-label">{{ labels[key] || key }}</span>
      <div class="bar-track">
        <div class="bar-fill" :style="{ width: value.percent + '%', background: value.color }"></div>
      </div>
      <span class="bar-value">{{ value.count }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
  // optional key -> CSS color, falls back to the theme primary color
  colors: { type: Object, default: () => ({}) },
  // optional key -> display label
  labels: { type: Object, default: () => ({}) }
})

const normalizedData = computed(() => {
  const entries = Object.entries(props.data || {})
  const max = Math.max(...entries.map(([, v]) => v), 1)
  const result = {}
  entries.forEach(([key, count]) => {
    result[key] = { count, percent: (count / max) * 100, color: props.colors[key] || 'var(--color-primary)' }
  })
  return result
})
</script>

<style scoped>
.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.bar-label { width: 100px; min-width: 100px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 10px; background: var(--bg-muted); border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--color-primary); border-radius: 5px; }
.bar-value { width: 24px; text-align: right; color: var(--text-primary); font-weight: 600; }
</style>
