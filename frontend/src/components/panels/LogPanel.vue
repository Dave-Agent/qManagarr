<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <h2 class="text-xl font-semibold">Activity Log</h2>
      <span v-if="refreshing" class="loading loading-spinner loading-xs text-base-content/30"></span>

      <!-- Filter -->
      <div class="join ml-auto">
        <button
          v-for="f in FILTERS" :key="f.value"
          :class="['btn btn-xs join-item', filter === f.value ? 'btn-neutral' : 'btn-ghost']"
          @click="filter = f.value"
        >{{ f.label }}</button>
      </div>

      <span class="text-xs text-base-content/40">Last 200 · auto-refreshes every 5s</span>
    </div>

    <div v-if="!filtered.length && !refreshing" class="text-base-content/30 text-sm">
      No log entries{{ filter !== 'all' ? ' at this level' : '' }} yet.
    </div>

    <div v-else class="font-mono text-xs space-y-0.5">
      <div
        v-for="entry in filtered"
        :key="entry.id"
        :class="['flex gap-3 px-3 py-1.5 rounded', rowClass(entry.level)]"
      >
        <span class="text-base-content/40 shrink-0 tabular-nums">{{ formatTs(entry.timestamp) }}</span>
        <span :class="['font-semibold shrink-0 w-16', levelClass(entry.level)]">{{ entry.level }}</span>
        <span class="break-all">{{ entry.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const FILTERS = [
  { value: 'all',     label: 'All' },
  { value: 'watch',   label: 'Watch+' },
  { value: 'warning', label: 'Warning+' },
]

const LEVEL_ORDER = { INFO: 0, WATCH: 1, WARNING: 2, ERROR: 3 }

const entries   = ref([])
const filter    = ref('all')
const refreshing = ref(false)
let timer = null

onMounted(async () => {
  await fetchLogs()
  timer = setInterval(fetchLogs, 5000)
})
onUnmounted(() => clearInterval(timer))

async function fetchLogs() {
  refreshing.value = true
  try {
    const res = await fetch('/api/logs')
    entries.value = await res.json()
  } finally {
    refreshing.value = false
  }
}

const minLevel = computed(() => {
  if (filter.value === 'warning') return LEVEL_ORDER.WARNING
  if (filter.value === 'watch')   return LEVEL_ORDER.WATCH
  return LEVEL_ORDER.INFO
})

const filtered = computed(() =>
  entries.value.filter(e => (LEVEL_ORDER[e.level] ?? 0) >= minLevel.value)
)

function formatTs(unix) {
  return new Date(unix * 1000).toLocaleString(undefined, {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  })
}

function levelClass(level) {
  return {
    WATCH:   'text-info',
    WARNING: 'text-warning',
    ERROR:   'text-error',
  }[level] ?? 'text-base-content/40'
}

function rowClass(level) {
  return {
    WATCH:   'bg-info/5',
    WARNING: 'bg-warning/5',
    ERROR:   'bg-error/5',
  }[level] ?? ''
}
</script>
