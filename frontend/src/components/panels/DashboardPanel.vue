<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <h2 class="text-xl font-semibold text-foreground">Dashboard</h2>
      <svg v-if="refreshing" class="animate-spin h-3.5 w-3.5 text-muted-foreground/50" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
      </svg>
      <div class="ml-auto flex items-center gap-2.5">
        <div :class="['w-2 h-2 rounded-full', connected ? 'bg-success' : 'bg-destructive']"></div>
        <span class="text-sm text-foreground font-medium">{{ connected ? 'Connected' : 'Disconnected' }}</span>
        <span v-if="data?.last_run" class="text-xs text-muted-foreground">· Last run {{ lastRunAgo }}</span>
      </div>
    </div>

    <!-- Stats + purge table -->
    <div class="flex flex-col lg:flex-row gap-6 items-start mb-8">

      <div class="grid grid-cols-2 gap-3 shrink-0">
        <StatCard label="Active"            :value="torrents.length"                     sub="managed torrents" />
        <StatCard label="All Time"          :value="data?.metrics.all_time_count ?? 0"   sub="torrents seen" />
        <StatCard label="Stalled"           :value="stalledCount"                        sub="in qBittorrent now"  :highlight="stalledCount > 0 ? 'warning' : null" />
        <StatCard label="Watch List"        :value="watchTotal"                          :sub="`${data?.metrics.watch_stall ?? 0} stall · ${data?.metrics.watch_eta ?? 0} ETA`" :highlight="watchTotal > 0 ? 'warning' : null" />
        <StatCard label="Purged (24h)"      :value="data?.metrics.purged_24h ?? 0"       sub="torrents removed"   :highlight="(data?.metrics.purged_24h ?? 0) > 0 ? 'warning' : null" />
        <StatCard label="Purged (all time)" :value="data?.metrics.purged_all_time ?? 0"  sub="torrents removed" />
      </div>

      <div v-if="data" class="overflow-x-auto rounded-lg border border-border shrink-0 w-full lg:w-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border">
              <th class="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Module</th>
              <th class="px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">24h</th>
              <th class="px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">All Time</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="row in data.purge_breakdown" :key="row.module_id" class="hover:bg-secondary/20 transition-colors">
              <td class="px-4 py-2 text-sm text-foreground">{{ row.label }}</td>
              <td class="px-4 py-2 text-right tabular-nums text-sm">
                <span :class="row.last_24h > 0 ? 'text-warning font-semibold' : 'text-muted-foreground/40'">{{ row.last_24h }}</span>
              </td>
              <td class="px-4 py-2 text-right tabular-nums text-sm text-muted-foreground">{{ row.all_time }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t-2 border-border font-semibold">
              <td class="px-4 py-2 text-sm text-foreground">Total</td>
              <td class="px-4 py-2 text-right tabular-nums text-sm">
                <span :class="data.metrics.purged_24h > 0 ? 'text-warning' : 'text-muted-foreground'">{{ data.metrics.purged_24h }}</span>
              </td>
              <td class="px-4 py-2 text-right tabular-nums text-sm text-muted-foreground">{{ data.metrics.purged_all_time }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

    </div>

    <!-- Active torrents -->
    <div>
      <h3 class="text-base font-semibold text-foreground mb-3">
        Active Torrents
        <span v-if="torrents.length" class="text-muted-foreground font-normal ml-1 text-sm">({{ torrents.length }})</span>
      </h3>

      <div v-if="torrentError" class="flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning mb-4">
        {{ torrentError }}
      </div>

      <div v-else-if="!torrents.length && !refreshing" class="text-muted-foreground text-sm">
        No active managed torrents.
      </div>

      <div v-else class="overflow-x-auto rounded-lg border border-border">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border bg-card/50">
              <th class="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Name</th>
              <th class="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Category</th>
              <th class="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">State</th>
              <th class="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Progress</th>
              <th class="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Speed</th>
              <th class="px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Size</th>
              <th class="px-3 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">Exclude</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="t in sorted" :key="t.hash" class="hover:bg-secondary/20 transition-colors">
              <td class="px-3 py-2 max-w-xs">
                <span class="block truncate text-foreground" :title="t.name">{{ t.name }}</span>
              </td>
              <td class="px-3 py-2">
                <span v-if="t.category" class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-secondary text-secondary-foreground font-medium">{{ t.category }}</span>
                <span v-else class="text-muted-foreground/40">—</span>
              </td>
              <td class="px-3 py-2">
                <span :class="['inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', stateClass(t.state)]">{{ stateLabel(t.state) }}</span>
              </td>
              <td class="px-3 py-2">
                <div class="flex items-center gap-2 min-w-28">
                  <div class="w-20 bg-secondary rounded-full h-1.5">
                    <div class="bg-primary h-1.5 rounded-full transition-all" :style="{ width: `${Math.round(t.progress * 100)}%` }"></div>
                  </div>
                  <span class="text-xs tabular-nums text-muted-foreground w-8">{{ Math.round(t.progress * 100) }}%</span>
                </div>
              </td>
              <td class="px-3 py-2 text-xs tabular-nums text-muted-foreground">{{ formatSpeed(t.dlspeed) }}</td>
              <td class="px-3 py-2 text-xs tabular-nums text-muted-foreground">{{ formatSize(t.size) }}</td>
              <td class="px-3 py-2 text-right">
                <button
                  role="switch"
                  :aria-checked="excludedHashes.has(t.hash)"
                  title="Exclude this torrent from all modules"
                  :class="[
                    'relative inline-flex h-4 w-7 shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none',
                    excludedHashes.has(t.hash) ? 'bg-warning-orange' : 'bg-muted'
                  ]"
                  @click="toggleExclusion(t, !excludedHashes.has(t.hash))"
                >
                  <span :class="[
                    'pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow transition-transform duration-150',
                    excludedHashes.has(t.hash) ? 'translate-x-3' : 'translate-x-0'
                  ]" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import StatCard from '../StatCard.vue'

const data         = ref(null)
const torrents     = ref([])
const exclusions   = ref([])
const torrentError = ref(null)
const refreshing   = ref(false)
let timer = null

onMounted(async () => {
  await refresh()
  timer = setInterval(refresh, 10000)
})
onUnmounted(() => clearInterval(timer))

async function refresh() {
  refreshing.value = true
  try {
    const [dashRes, torRes, exRes] = await Promise.all([
      fetch('/api/dashboard'),
      fetch('/api/torrents'),
      fetch('/api/exclusions'),
    ])
    data.value = await dashRes.json()
    exclusions.value = await exRes.json()
    if (torRes.ok) {
      torrents.value = await torRes.json()
      torrentError.value = null
    } else {
      const d = await torRes.json()
      torrentError.value = d.detail || 'Failed to load torrents'
      torrents.value = []
    }
  } catch {
    torrentError.value = 'Could not reach the backend'
  } finally {
    refreshing.value = false
  }
}

const excludedHashes = computed(() => new Set(exclusions.value.map(e => e.hash)))

async function toggleExclusion(torrent, exclude) {
  if (exclude) {
    const res = await fetch('/api/exclusions', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hash: torrent.hash, name: torrent.name }),
    })
    exclusions.value = await res.json()
  } else {
    const res = await fetch(`/api/exclusions/${torrent.hash}`, { method: 'DELETE' })
    exclusions.value = await res.json()
  }
}

const connected  = computed(() => data.value?.connection?.connected ?? false)
const watchTotal = computed(() =>
  (data.value?.metrics.watch_stall ?? 0) + (data.value?.metrics.watch_eta ?? 0)
)
const stalledCount = computed(() =>
  torrents.value.filter(t => t.state === 'stalledDL' || t.state === 'stalledUP').length
)
const lastRunAgo = computed(() => {
  if (!data.value?.last_run) return ''
  const secs = Math.floor(Date.now() / 1000) - data.value.last_run
  if (secs < 60)   return `${secs}s ago`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  return `${Math.floor(secs / 3600)}h ago`
})
const sorted = computed(() =>
  [...torrents.value].sort((a, b) => a.name.localeCompare(b.name))
)

const STATE_CLASSES = {
  downloading:  'bg-info/15 text-info',
  metaDL:       'bg-info/15 text-info',
  forcedDL:     'bg-info/15 text-info',
  uploading:    'bg-success/15 text-success',
  seeding:      'bg-success/15 text-success',
  forcedUP:     'bg-success/15 text-success',
  stalledDL:    'bg-warning/15 text-warning',
  stalledUP:    'bg-warning/15 text-warning',
  error:        'bg-destructive/15 text-destructive',
  missingFiles: 'bg-destructive/15 text-destructive',
  unknown:      'bg-destructive/15 text-destructive',
  pausedDL:     'bg-secondary text-muted-foreground',
  pausedUP:     'bg-secondary text-muted-foreground',
  stoppedDL:    'bg-secondary text-muted-foreground',
  stoppedUP:    'bg-secondary text-muted-foreground',
  queuedDL:     'bg-secondary text-muted-foreground',
  queuedUP:     'bg-secondary text-muted-foreground',
  checkingDL:   'bg-secondary text-muted-foreground',
  checkingUP:   'bg-secondary text-muted-foreground',
  allocating:   'bg-secondary text-muted-foreground',
}
const STATE_LABELS = {
  downloading: 'Downloading', metaDL: 'Getting info',  forcedDL: 'Downloading',
  uploading:   'Seeding',     seeding: 'Seeding',       forcedUP: 'Seeding',
  stalledDL:   'Stalled',     stalledUP: 'Stalled',
  error:       'Error',       missingFiles: 'Missing files', unknown: 'Unknown',
  pausedDL:    'Paused',      pausedUP: 'Paused',      stoppedDL: 'Stopped', stoppedUP: 'Stopped',
  queuedDL:    'Queued',      queuedUP: 'Queued',      checkingDL: 'Checking', checkingUP: 'Checking',
  allocating:  'Allocating',
}
const stateClass  = s => STATE_CLASSES[s] ?? 'bg-secondary text-muted-foreground'
const stateLabel  = s => STATE_LABELS[s]  ?? s
const formatSpeed = bps => {
  if (!bps || bps < 1024) return '—'
  if (bps < 1024 ** 2) return `${(bps / 1024).toFixed(0)} KB/s`
  return `${(bps / 1024 ** 2).toFixed(1)} MB/s`
}
const formatSize = bytes => {
  if (!bytes) return '—'
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(0)} KB`
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(0)} MB`
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`
}
</script>
