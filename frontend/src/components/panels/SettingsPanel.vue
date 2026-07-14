<template>
  <div>
    <h2 class="text-xl font-semibold text-foreground mb-6">Settings</h2>

    <!-- Connection -->
    <div class="bg-card border border-border rounded-lg p-5 max-w-lg mb-6">
      <h3 class="font-semibold text-foreground mb-5">qBittorrent Connection</h3>

      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-foreground">Host URL</label>
          <input v-model="form.host" type="text" placeholder="http://localhost:8080"
            class="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring w-full" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-foreground">Username</label>
          <input v-model="form.username" type="text" placeholder="admin"
            class="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring w-full" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-foreground">Password</label>
          <input v-model="form.password" type="password" placeholder="••••••••"
            class="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring w-full" />
        </div>

        <div class="flex gap-3 pt-1">
          <button
            :disabled="saving"
            class="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium transition-colors hover:bg-primary/90 disabled:opacity-40"
            @click="save"
          >{{ saving ? 'Saving…' : 'Save' }}</button>
          <button
            :disabled="testing"
            class="h-9 px-4 rounded-md border border-input bg-background text-sm text-foreground font-medium transition-colors hover:bg-secondary/50 disabled:opacity-40"
            @click="testConnection"
          >{{ testing ? 'Testing…' : 'Test Connection' }}</button>
        </div>

        <div v-if="saveStatus" class="flex items-center gap-2 rounded-lg border border-success/30 bg-success/10 px-3 py-2.5 text-sm text-success">
          Settings saved.
        </div>
        <div v-if="testResult" :class="[
          'flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm',
          testResult.success
            ? 'border-success/30 bg-success/10 text-success'
            : 'border-destructive/30 bg-destructive/10 text-destructive'
        ]">
          {{ testResult.message }}
        </div>
      </div>
    </div>

    <!-- Scheduler -->
    <div class="bg-card border border-border rounded-lg p-5 max-w-lg mb-6">
      <h3 class="font-semibold text-foreground mb-5">Scheduler</h3>
      <div class="flex flex-col gap-4">
        <StepSlider label="Evaluate every" v-model="intervalSecs" :steps="INTERVAL_STEPS" />
        <div class="flex items-center gap-3 pt-1 border-t border-border">
          <button
            :disabled="savingInterval"
            class="h-8 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium transition-colors hover:bg-primary/90 disabled:opacity-40"
            @click="saveInterval"
          >{{ savingInterval ? 'Saving…' : 'Save' }}</button>
          <span v-if="savedInterval" class="text-sm text-success">Saved!</span>
        </div>
      </div>
    </div>

    <!-- Managed Categories -->
    <div class="bg-card border border-border rounded-lg p-5 max-w-lg">
      <h3 class="font-semibold text-foreground mb-2">Managed Categories</h3>
      <p class="text-sm text-muted-foreground mb-4">
        Only torrents in these categories are managed. The dashboard torrent list is also filtered to these categories.
      </p>

      <div class="flex flex-wrap gap-2 min-h-8 mb-3">
        <div v-for="cat in categories" :key="cat"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-primary/15 text-primary text-xs font-medium border border-primary/25"
        >
          {{ cat }}
          <button class="hover:text-destructive transition-colors ml-0.5" @click="removeCategory(cat)">✕</button>
        </div>
        <span v-if="!categories.length" class="text-sm text-muted-foreground italic">
          No categories — all torrents will be ignored.
        </span>
      </div>

      <div class="flex gap-2">
        <input
          v-model="newCat"
          type="text"
          placeholder="e.g. radarr-4k"
          class="flex-1 h-8 rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          @keyup.enter="addCategory"
        />
        <button
          :disabled="!newCat.trim()"
          class="h-8 px-3 rounded-md bg-primary text-primary-foreground text-sm font-medium transition-colors hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed"
          @click="addCategory"
        >Add</button>
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

const form           = ref({ host: '', username: '', password: '' })
const saving         = ref(false)
const testing        = ref(false)
const saveStatus     = ref(false)
const testResult     = ref(null)
const categories     = ref([])
const newCat         = ref('')
const intervalSecs   = ref(900)
const savingInterval = ref(false)
const savedInterval  = ref(false)

onMounted(async () => {
  const [connRes, catRes, intRes] = await Promise.all([
    fetch('/api/settings/qbittorrent'),
    fetch('/api/settings/categories'),
    fetch('/api/scheduler/interval'),
  ])
  form.value         = await connRes.json()
  categories.value   = (await catRes.json()).categories
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
  savingInterval.value = true; savedInterval.value = false
  await fetch('/api/scheduler/interval', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ interval_secs: intervalSecs.value }),
  })
  savingInterval.value = false; savedInterval.value = true
  setTimeout(() => (savedInterval.value = false), 3000)
}
</script>
