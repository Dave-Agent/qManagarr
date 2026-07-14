<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <h2 class="text-xl font-semibold text-foreground">Logs</h2>
      <svg v-if="refreshing" class="animate-spin h-3.5 w-3.5 text-muted-foreground/50" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
      </svg>

      <!-- Filter pills -->
      <div class="ml-auto flex items-center gap-1 bg-secondary/50 rounded-lg p-1">
        <button
          v-for="f in FILTERS" :key="f.value"
          :class="[
            'px-3 py-1 rounded-md text-xs font-medium transition-colors',
            filter === f.value
              ? 'bg-card text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          ]"
          @click="filter = f.value"
        >{{ f.label }}</button>
      </div>

      <span class="text-xs text-muted-foreground/50">Last 200 · refreshes every 5s</span>
    </div>

    <div v-if="!filtered.length && !refreshing" class="text-muted-foreground text-sm">
      No log entries{{ filter !== 'all' ? ' at this level' : '' }} yet.
    </div>

    <div v-else class="font-mono text-xs space-y-0.5">
      <div
        v-for="entry in filtered"
        :key="entry.id"
        :class="['flex gap-3 px-3 py-1.5 rounded', rowClass(entry.level)]"
      >
        <span class="text-muted-foreground/50 shrink-0 tabular-nums">{{ formatTs(entry.timestamp) }}</span>
        <span :class="['font-semibold shrink-0 w-16', levelClass(entry.level)]">{{ entry.level }}</span>
        <span class="break-all text-foreground/80">{{ entry.message }}</span>
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

const entries    = ref([])
const filter     = ref('all')
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
  return { WATCH: 'text-info', WARNING: 'text-warning', ERROR: 'text-destructive' }[level] ?? 'text-muted-foreground/40'
}
function rowClass(level) {
  return { WATCH: 'bg-info/5', WARNING: 'bg-warning/5', ERROR: 'bg-destructive/5' }[level] ?? ''
}
</script>
