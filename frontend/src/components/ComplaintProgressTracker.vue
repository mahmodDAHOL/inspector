<template>
  <div class="progress-tracker">
    <div class="tracker-top">
      <h3 class="tracker-title">{{ $t('complaint.progressTitle') }}</h3>
      <div class="tracker-chips">
        <span v-if="overdue" class="chip chip-danger">⚠ {{ $t('complaint.overdue') }}</span>
        <span class="chip" :class="assigneeName ? 'chip-neutral' : 'chip-muted'">
          {{ assigneeName || $t('complaint.unassigned') }}
        </span>
        <span class="chip chip-muted">{{ elapsedLabel }}</span>
      </div>
    </div>

    <div class="stepper" role="list" :aria-label="$t('complaint.progressTitle')">
      <div class="stepper-track">
        <div class="stepper-fill" :class="fillClass" :style="{ width: fillPercent + '%' }"></div>
      </div>
      <div class="stepper-nodes">
        <div
          v-for="(stage, i) in stages"
          :key="stage.key"
          class="node"
          :class="{ done: i < activeIndex, active: i === activeIndex, danger: stage.key === 'escalated' }"
          role="listitem"
        >
          <span class="node-dot">
            <span v-if="i < activeIndex" class="node-check">✓</span>
          </span>
          <span class="node-label">{{ stage.label }}</span>
        </div>
      </div>
    </div>

    <p v-if="isEscalated" class="escalated-note">⚠ {{ $t('complaint.status.escalated') }} — {{ $t('complaint.priority.urgent') }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  status: { type: String, required: true },
  createdAt: { type: String, default: null },
  closedAt: { type: String, default: null },
  firstResponseAt: { type: String, default: null },
  assigneeName: { type: String, default: null },
})

const { t } = useI18n()

// Escalated renders as a heightened variant of "under investigation" rather than
// a separate pipeline stop — it is a lateral urgency flag, not a forward stage.
const stages = computed(() => [
  { key: 'received', label: t('complaint.status.received') },
  { key: 'under_investigation', label: props.status === 'escalated' ? t('complaint.status.escalated') : t('complaint.status.under_investigation') },
  { key: 'closed', label: t('complaint.status.closed') },
])

const activeIndex = computed(() => {
  if (props.status === 'closed') return 2
  if (props.status === 'under_investigation' || props.status === 'escalated') return 1
  return 0
})

const isEscalated = computed(() => props.status === 'escalated')

const fillPercent = computed(() => [20, 58, 100][activeIndex.value])

const fillClass = computed(() => {
  if (props.status === 'closed') return 'success'
  if (props.status === 'escalated') return 'danger'
  if (props.status === 'under_investigation') return 'warning'
  return 'info'
})

function daysBetween(a, b) {
  return Math.max(0, Math.floor((b - a) / 86400000))
}

const elapsedLabel = computed(() => {
  if (!props.createdAt) return ''
  const created = new Date(props.createdAt)
  if (props.status === 'closed' && props.closedAt) {
    const n = daysBetween(created, new Date(props.closedAt))
    return n <= 1 ? t('complaint.resolvedInOne') : t('complaint.resolvedIn', { n })
  }
  const n = daysBetween(created, new Date())
  return n <= 1 ? t('complaint.dayOpen') : `${n} ${t('complaint.daysOpen')}`
})

const overdue = computed(() => {
  if (props.status === 'closed' || !props.createdAt) return false
  return daysBetween(new Date(props.createdAt), new Date()) > 7
})
</script>

<style scoped>
.progress-tracker {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 18px 20px 20px;
  margin-bottom: 20px;
}
.tracker-top { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
.tracker-title { margin: 0; font-size: 15px; color: var(--text-primary); }
.tracker-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { font-size: 12px; padding: 4px 10px; border-radius: 999px; white-space: nowrap; }
.chip-neutral { background: rgba(59,126,161,0.12); color: var(--color-info); }
.chip-muted { background: var(--bg-muted); color: var(--text-tertiary); }
.chip-danger { background: rgba(184,84,80,0.12); color: var(--color-danger); font-weight: 600; }

.stepper { position: relative; padding: 0 4px; }
.stepper-track {
  position: absolute;
  inset-inline: 20px;
  top: 9px;
  height: 4px;
  background: var(--bg-muted);
  border-radius: 2px;
  overflow: hidden;
}
.stepper-fill { height: 100%; border-radius: 2px; transition: width 0.4s ease; }
.stepper-fill.info { background: var(--color-info); }
.stepper-fill.warning { background: var(--color-warning); }
.stepper-fill.danger { background: var(--color-danger); }
.stepper-fill.success { background: var(--color-success); }

.stepper-nodes { display: flex; justify-content: space-between; position: relative; }
.node { display: flex; flex-direction: column; align-items: center; gap: 8px; width: 33%; }
.node-dot {
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--bg-muted);
  border: 2px solid var(--border-color);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: #fff;
  transition: background 0.3s, border-color 0.3s;
}
.node.done .node-dot { background: var(--color-success); border-color: var(--color-success); }
.node.active .node-dot { border-color: var(--color-primary); box-shadow: 0 0 0 4px rgba(27,94,94,0.15); }
.node.active.danger .node-dot { border-color: var(--color-danger); background: var(--color-danger); box-shadow: 0 0 0 4px rgba(184,84,80,0.15); }
.node-label { font-size: 12.5px; color: var(--text-tertiary); text-align: center; }
.node.active .node-label { color: var(--text-primary); font-weight: 600; }
.node.done .node-label { color: var(--text-secondary); }

.escalated-note { margin: 14px 2px 0; font-size: 12.5px; color: var(--color-danger); font-weight: 600; }

@media (max-width: 560px) {
  .node-label { font-size: 11px; }
}
</style>
