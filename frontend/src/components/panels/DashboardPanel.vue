<template>
  <div>
    <h2 class="text-xl font-semibold mb-6">Dashboard</h2>

    <!-- Connection + last run + evaluate now -->
    <div class="flex items-center gap-3 mb-6">
      <span :class="['w-2.5 h-2.5 rounded-full shrink-0', connected ? 'bg-success' : 'bg-error']"></span>
      <span class="text-sm font-medium">{{ connected ? 'Connected' : 'Disconnected' }}</span>
      <span v-if="data?.last_run" class="text-xs text-base-content/40">
        · Last run {{ lastRunAgo }}
      </span>
      <span v-if="refreshing" class="loading loading-spinner loading-xs text-base-content/30"></span>
      <button
        class="btn btn-sm btn-primary ml-auto"
        :class="{ loading: evaluating }"
        :disabled="evaluating"
        @click="evaluateNow"
      >
        {{ evaluating ? 'Evaluating…' : 'Evaluate Now' }}
      </button>
    </div>

    <!-- Stats + purge table side by side on wide screens -->
    <div class="flex flex-col lg:flex-row gap-6 items-start mb-8">

      <!-- 2-column stat grid -->
      <div class="grid grid-cols-2 gap-3 shrink-0">

        <StatCard label="Active"        :value="torrents.length"                  sub="managed torrents"  />
        <StatCard label="All Time"      :value="data?.metrics.all_time_count ?? 0" sub="torrents seen"    />

        <StatCard
          label="Stalled"
          :value="stalledCount"
          sub="in qBittorrent now"
          :highlight="stalledCount > 0 ? 'warning' : null"
        />
        <StatCard
          label="Watch List"
          :value="watchTotal"
          :sub="`${data?.metrics.watch_stall ?? 0} stall · ${data?.metrics.watch_eta ?? 0} ETA`"
          :highlight="watchTotal > 0 ? 'warning' : null"
        />

        <StatCard
          label="Purged (24h)"
          :value="data?.metrics.purged_24h ?? 0"
          sub="torrents removed"
          :highlight="(data?.metrics.purged_24h ?? 0) > 0 ? 'warning' : null"
        />
        <StatCard
          label="Purged (all time)"
          :value="data?.metrics.purged_all_time ?? 0"
          sub="torrents removed"
        />

      </div>

      <!-- Purge breakdown table -->
      <div v-if="data" class="card bg-base-200 shadow-lg shrink-0 w-full lg:w-auto">
        <div class="card-body p-0">
          <table class="table table-sm">
            <thead>
              <tr class="text-xs uppercase tracking-wider text-base-content/50">
                <th>Module</th>
                <th class="text-right">24h</th>
                <th class="text-right">All Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.purge_breakdown" :key="row.module_id">
                <td class="text-sm">{{ row.label }}</td>
                <td class="text-right tabular-nums text-sm">
                  <span :class="row.last_24h > 0 ? 'text-warning font-semibold' : 'text-base-content/30'">
                    {{ row.last_24h }}
                  </span>
                </td>
                <td class="text-right tabular-nums text-sm">{{ row.all_time }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t-2 border-base-300 font-semibold">
                <td class="text-sm">Total</td>
                <td class="text-right tabular-nums text-sm">
                  <span :class="data.metrics.purged_24h > 0 ? 'text-warning' : ''">
                    {{ data.metrics.purged_24h }}
                  </span>
                </td>
                <td class="text-right tabular-nums text-sm">{{ data.metrics.purged_all_time }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

    </div>

    <!-- Active torrents -->
    <div>
      <h3 class="text-base font-semibold mb-3">
        Active Torrents
        <span v-if="torrents.length" class="text-base-content/50 font-normal ml-1">
          ({{ torrents.length }})
        </span>
      </h3>

      <div v-if="torrentError" role="alert" class="alert alert-warning text-sm max-w-lg">
        {{ torrentError }}
      </div>

      <div v-else-if="!torrents.length && !refreshing" class="text-base-content/30 text-sm">
        No active managed torrents.
      </div>

      <div v-else class="overflow-x-auto rounded-lg border border-base-300">
        <table class="table table-sm table-zebra">
          <thead>
            <tr class="text-xs uppercase tracking-wider text-base-content/50">
              <th>Name</th>
              <th>Category</th>
              <th>State</th>
              <th>Progress</th>
              <th>Speed</th>
              <th>Size</th>
              <th class="text-right">Exclude</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in sorted" :key="t.hash">
              <td class="max-w-xs">
                <span class="block truncate" :title="t.name">{{ t.name }}</span>
              </td>
              <td>
                <span v-if="t.category" class="badge badge-ghost badge-sm">{{ t.category }}</span>
                <span v-else class="text-base-content/30">—</span>
              </td>
              <td>
                <span :class="['badge badge-sm', stateClass(t.state)]">{{ stateLabel(t.state) }}</span>
              </td>
              <td>
                <div class="flex items-center gap-2 min-w-28">
                  <progress
                    class="progress progress-primary w-20"
                    :value="Math.round(t.progress * 100)"
                    max="100"
                  ></progress>
                  <span class="text-xs tabular-nums">{{ Math.round(t.progress * 100) }}%</span>
                </div>
              </td>
              <td class="text-xs tabular-nums text-base-content/70">{{ formatSpeed(t.dlspeed) }}</td>
              <td class="text-xs tabular-nums text-base-content/70">{{ formatSize(t.size) }}</td>
              <td class="text-right">
                <div class="tooltip tooltip-left" data-tip="Exclude this torrent from all modules">
                  <input
                    type="checkbox"
                    class="toggle toggle-warning toggle-sm"
                    :checked="excludedHashes.has(t.hash)"
                    @change="toggleExclusion(t, $event.target.checked)"
                  />
                </div>
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
const evaluating   = ref(false)
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

async function evaluateNow() {
  evaluating.value = true
  await fetch('/api/scheduler/run', { method: 'POST' })
  setTimeout(async () => {
    await refresh()
    evaluating.value = false
  }, 4000)
}

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
  downloading: 'badge-info',   metaDL: 'badge-info',     forcedDL: 'badge-info',
  uploading:   'badge-success', seeding: 'badge-success', forcedUP: 'badge-success',
  stalledDL:   'badge-warning', stalledUP: 'badge-warning',
  error:       'badge-error',  missingFiles: 'badge-error', unknown: 'badge-error',
  pausedDL:    'badge-ghost',  pausedUP: 'badge-ghost',  stoppedDL: 'badge-ghost', stoppedUP: 'badge-ghost',
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
const stateClass  = s => STATE_CLASSES[s] ?? 'badge-neutral'
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
