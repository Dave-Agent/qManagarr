<template>
  <div>
    <h2 class="text-xl font-semibold mb-6">qBittorrent</h2>

    <!-- Connection settings -->
    <div class="card bg-base-200 shadow-lg max-w-lg">
      <div class="card-body gap-5">

        <h3 class="card-title text-base">Connection</h3>

        <div class="form-control">
          <label class="label pb-1"><span class="label-text">Host URL</span></label>
          <input v-model="form.host" type="text" placeholder="http://localhost:8080" class="input input-bordered w-full" />
        </div>
        <div class="form-control">
          <label class="label pb-1"><span class="label-text">Username</span></label>
          <input v-model="form.username" type="text" placeholder="admin" class="input input-bordered w-full" />
        </div>
        <div class="form-control">
          <label class="label pb-1"><span class="label-text">Password</span></label>
          <input v-model="form.password" type="password" placeholder="••••••••" class="input input-bordered w-full" />
        </div>

        <div class="flex gap-3 pt-1">
          <button class="btn btn-primary" :disabled="saving" @click="save">{{ saving ? 'Saving…' : 'Save' }}</button>
          <button class="btn btn-ghost" :disabled="testing" @click="testConnection">{{ testing ? 'Testing…' : 'Test Connection' }}</button>
        </div>

        <div v-if="saveStatus" role="alert" class="alert alert-success py-2 text-sm">Settings saved.</div>
        <div v-if="testResult" role="alert" :class="['alert py-2 text-sm', testResult.success ? 'alert-success' : 'alert-error']">
          {{ testResult.message }}
        </div>

      </div>
    </div>

    <!-- Scheduler -->
    <div class="card bg-base-200 shadow-lg max-w-lg mt-6">
      <div class="card-body gap-4">
        <h3 class="card-title text-base">Scheduler</h3>
        <StepSlider label="Evaluate every" v-model="intervalSecs" :steps="INTERVAL_STEPS" />
        <div class="flex items-center gap-3">
          <button class="btn btn-primary btn-sm" :disabled="savingInterval" @click="saveInterval">
            {{ savingInterval ? 'Saving…' : 'Save' }}
          </button>
          <span v-if="savedInterval" class="text-sm text-success">Saved!</span>
        </div>
      </div>
    </div>

    <!-- Managed Categories -->
    <div class="card bg-base-200 shadow-lg max-w-lg mt-6">
      <div class="card-body gap-4">

        <h3 class="card-title text-base">Managed Categories</h3>
        <p class="text-sm text-base-content/50">
          Only torrents in these categories are managed. The dashboard torrent list is also filtered to these categories.
        </p>

        <div class="flex flex-wrap gap-2 min-h-8">
          <div v-for="cat in categories" :key="cat" class="badge badge-primary gap-1 py-3 pr-1">
            {{ cat }}
            <button class="btn btn-ghost btn-xs px-1 min-h-0 h-auto hover:text-error" @click="removeCategory(cat)">✕</button>
          </div>
          <span v-if="!categories.length" class="text-sm text-base-content/30 italic">
            No categories — all torrents will be ignored.
          </span>
        </div>

        <div class="flex gap-2">
          <input v-model="newCat" type="text" placeholder="e.g. radarr-4k" class="input input-bordered input-sm flex-1" @keyup.enter="addCategory" />
          <button class="btn btn-sm btn-primary" :disabled="!newCat.trim()" @click="addCategory">Add</button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StepSlider from '../StepSlider.vue'

const INTERVAL_STEPS = [
  { label: '5m',  value: 300 },
  { label: '10m', value: 600 },
  { label: '15m', value: 900 },
  { label: '30m', value: 1800 },
  { label: '1h',  value: 3600 },
  { label: '2h',  value: 7200 },
  { label: '4h',  value: 14400 },
  { label: '6h',  value: 21600 },
  { label: '12h', value: 43200 },
  { label: '24h', value: 86400 },
]

const form       = ref({ host: '', username: '', password: '' })
const saving     = ref(false)
const testing    = ref(false)
const saveStatus = ref(false)
const testResult = ref(null)
const categories    = ref([])
const newCat        = ref('')
const intervalSecs  = ref(900)
const savingInterval = ref(false)
const savedInterval  = ref(false)

onMounted(async () => {
  const [connRes, catRes, intRes] = await Promise.all([
    fetch('/api/settings/qbittorrent'),
    fetch('/api/settings/categories'),
    fetch('/api/scheduler/interval'),
  ])
  form.value       = await connRes.json()
  categories.value = (await catRes.json()).categories
  intervalSecs.value = (await intRes.json()).interval_secs
})

async function save() {
  saving.value = true; saveStatus.value = false; testResult.value = null
  await fetch('/api/settings/qbittorrent', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form.value),
  })
  saving.value = false; saveStatus.value = true
  setTimeout(() => (saveStatus.value = false), 3000)
}

async function testConnection() {
  testing.value = true; testResult.value = null
  const res = await fetch('/api/settings/qbittorrent/test', { method: 'POST' })
  testResult.value = await res.json()
  testing.value = false
}

async function saveCategories() {
  await fetch('/api/settings/categories', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ categories: categories.value }),
  })
}
function addCategory() {
  const cat = newCat.value.trim()
  if (!cat || categories.value.includes(cat)) return
  categories.value.push(cat); newCat.value = ''
  saveCategories()
}
function removeCategory(cat) {
  categories.value = categories.value.filter(c => c !== cat)
  saveCategories()
}

async function saveInterval() {
  savingInterval.value = true
  savedInterval.value = false
  await fetch('/api/scheduler/interval', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ interval_secs: intervalSecs.value }),
  })
  savingInterval.value = false
  savedInterval.value = true
  setTimeout(() => (savedInterval.value = false), 3000)
}
</script>
