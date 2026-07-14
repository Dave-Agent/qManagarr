<template>
  <div v-if="meta">
    <h2 class="text-xl font-semibold text-foreground mb-6">{{ meta.label }}</h2>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

      <!-- Left column -->
      <div class="flex flex-col gap-6">

        <!-- Enable / disable -->
        <div class="bg-card border border-border rounded-lg p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-foreground">Enable module</p>
              <p class="text-sm text-muted-foreground mt-0.5">{{ meta.description }}</p>
            </div>
            <button
              role="switch"
              :aria-checked="enabled"
              :class="[
                'relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                enabled ? 'bg-primary' : 'bg-muted'
              ]"
              @click="setEnabled(!enabled)"
            >
              <span :class="[
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform duration-150',
                enabled ? 'translate-x-5' : 'translate-x-0'
              ]" />
            </button>
          </div>
          <div v-if="!enabled" class="mt-4 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2.5 text-sm text-warning">
            This module is disabled — no action will be taken.
          </div>
        </div>

        <!-- Settings -->
        <div v-if="config" class="bg-card border border-border rounded-lg p-5 flex flex-col gap-6">

          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-foreground">Settings</h3>
            <button class="text-xs text-muted-foreground hover:text-foreground transition-colors" @click="resetDefaults">
              Reset defaults
            </button>
          </div>

          <!-- COMPLETED PURGE -->
          <template v-if="moduleId === 'completed-purge'">
            <StepSlider label="Remove completed torrents after" v-model="config.purge_delay" :steps="TIME_STEPS" />
          </template>

          <!-- EXE KILLER -->
          <template v-else-if="moduleId === 'exe-killer'">
            <div class="flex flex-col gap-2">
              <label class="text-sm text-foreground">Blocked file extensions</label>
              <div class="flex flex-wrap gap-2 min-h-8">
                <div
                  v-for="ext in config.bad_extensions" :key="ext"
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-primary/15 text-primary text-xs font-mono border border-primary/25"
                >
                  {{ ext }}
                  <button class="hover:text-destructive transition-colors ml-0.5" @click="removeExt(ext)">✕</button>
                </div>
                <span v-if="!config.bad_extensions.length" class="text-sm text-muted-foreground italic">
                  No extensions — EXE Killer will not block anything.
                </span>
              </div>
              <div class="flex gap-2 mt-1">
                <input
                  v-model="newExt"
                  type="text"
                  placeholder=".exe"
                  class="flex-1 h-8 rounded-md border border-input bg-background px-3 text-sm font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                  @keyup.enter="addExt"
                />
                <button
                  :disabled="!newExt.trim()"
                  class="h-8 px-3 rounded-md bg-primary text-primary-foreground text-sm font-medium transition-colors hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed"
                  @click="addExt"
                >Add</button>
              </div>
            </div>
          </template>

          <!-- ERROR KILLER -->
          <template v-else-if="moduleId === 'error-killer'">
            <div class="flex flex-col gap-3">
              <label class="text-sm text-foreground">Act on these states</label>
              <div class="flex flex-col gap-2.5">
                <label v-for="state in KNOWN_ERROR_STATES" :key="state.value" class="flex items-center gap-3 cursor-pointer group">
                  <button
                    role="checkbox"
                    :aria-checked="config.error_states.includes(state.value)"
                    :class="[
                      'h-4 w-4 rounded border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring flex items-center justify-center',
                      config.error_states.includes(state.value)
                        ? 'bg-primary border-primary'
                        : 'bg-background border-input hover:border-primary/50'
                    ]"
                    @click="toggleErrorState(state.value, !config.error_states.includes(state.value))"
                  >
                    <svg v-if="config.error_states.includes(state.value)" class="h-3 w-3 text-primary-foreground" fill="none" viewBox="0 0 12 12">
                      <path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <div>
                    <span class="text-sm font-medium text-foreground font-mono">{{ state.label }}</span>
                    <span class="text-xs text-muted-foreground ml-2">{{ state.description }}</span>
                  </div>
                </label>
              </div>
            </div>
          </template>

          <!-- ETA MONITOR -->
          <template v-else-if="moduleId === 'eta-monitor'">
            <StepSlider label="Maximum acceptable ETA"                         v-model="config.max_eta_secs"          :steps="TIME_STEPS" />
            <StepSlider label="Wait before checking ETA (torrent age)"         v-model="config.eta_threshold_secs"    :steps="TIME_STEPS" />
            <StepSlider label="Grace period — sustained bad ETA before action" v-model="config.eta_grace_secs"        :steps="TIME_STEPS" />
            <StepSlider label="Minimum speed during bad ETA"                   v-model="config.min_active_speed"      :steps="SPEED_STEPS" />
            <StepSlider label="Ignore ETA logic above this progress"           v-model="config.eta_ignore_progress"   :steps="PROGRESS_STEPS" />
          </template>

          <!-- STALL MONITOR -->
          <template v-else-if="moduleId === 'stall-monitor'">
            <StepSlider label="Stall check window"                      v-model="config.stall_check_secs"         :steps="TIME_STEPS" />
            <StepSlider label="Minimum progress required within window" v-model="config.progress_threshold_bytes" :steps="SIZE_STEPS" />
          </template>

          <!-- Save -->
          <div class="flex items-center gap-3 pt-1 border-t border-border">
            <button
              :disabled="savingConfig"
              class="h-8 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium transition-colors hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="saveConfig"
            >{{ savingConfig ? 'Saving…' : 'Save' }}</button>
            <span v-if="savedConfig" class="text-sm text-success">Saved!</span>
          </div>

        </div>
      </div>

      <!-- Right column: description -->
      <div v-if="description" class="bg-card border border-border rounded-lg p-5">
        <div
          v-html="descriptionHtml"
          class="prose prose-sm prose-invert max-w-none
                 prose-p:text-muted-foreground prose-p:leading-relaxed
                 prose-strong:text-foreground prose-headings:text-foreground"
        ></div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { marked } from 'marked'
import StepSlider from '../StepSlider.vue'
import { TIME_STEPS, SPEED_STEPS, SIZE_STEPS, PROGRESS_STEPS } from '../../sliderSteps.js'

const props = defineProps({
  moduleId: String,
  modules: { type: Array, default: () => [] },
})
const emit = defineEmits(['toggle'])

const MODULE_META = {
  'completed-purge': {
    label: 'Completed Purge',
    description: 'Removes completed torrents from qBittorrent after a configurable delay, keeping the queue clean.',
  },
  'exe-killer': {
    label: 'EXE Killer',
    description: 'Detects and purges torrents containing executable files as a security measure.',
  },
  'error-killer': {
    label: 'Error Killer',
    description: 'Purges torrents stuck in error, missing files, or unregistered states.',
  },
  'eta-monitor': {
    label: 'ETA Monitor',
    description: 'Monitors torrents with a sustained bad ETA and low speed, purging them after a grace period.',
  },
  'stall-monitor': {
    label: 'Stall Monitor',
    description: 'Purges torrents that have not made meaningful progress within the check window.',
  },
}

const KNOWN_ERROR_STATES = [
  { value: 'error',        label: 'error',        description: 'General torrent error' },
  { value: 'missingFiles', label: 'missingFiles',  description: 'Download files cannot be found' },
  { value: 'unregistered', label: 'unregistered',  description: 'Torrent not registered with tracker' },
]

const meta    = computed(() => MODULE_META[props.moduleId])
const enabled = computed(() => {
  const mod = props.modules.find(m => m.id === props.moduleId)
  return mod ? mod.enabled : true
})
const config       = ref(null)
const description  = ref('')
const savingConfig = ref(false)
const savedConfig  = ref(false)
const newExt       = ref('')

const descriptionHtml = computed(() => marked(description.value))

onMounted(loadModule)
watch(() => props.moduleId, loadModule)

async function loadModule() {
  config.value = null
  description.value = ''
  savedConfig.value = false
  const [cfgRes, descRes] = await Promise.all([
    fetch(`/api/modules/${props.moduleId}/config`),
    fetch(`/api/modules/${props.moduleId}/description`),
  ])
  config.value = await cfgRes.json()
  description.value = (await descRes.json()).content
}

function setEnabled(value) {
  emit('toggle', props.moduleId, value)
}

async function saveConfig() {
  savingConfig.value = true
  savedConfig.value = false
  await fetch(`/api/modules/${props.moduleId}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config.value),
  })
  savingConfig.value = false
  savedConfig.value = true
  setTimeout(() => (savedConfig.value = false), 3000)
}

async function resetDefaults() {
  await fetch(`/api/modules/${props.moduleId}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  const defaults = await (await fetch(`/api/modules/${props.moduleId}/config`)).json()
  config.value = defaults
}

function addExt() {
  let ext = newExt.value.trim()
  if (!ext) return
  if (!ext.startsWith('.')) ext = '.' + ext
  ext = ext.toLowerCase()
  if (!config.value.bad_extensions.includes(ext)) config.value.bad_extensions.push(ext)
  newExt.value = ''
}

function removeExt(ext) {
  config.value.bad_extensions = config.value.bad_extensions.filter(e => e !== ext)
}

function toggleErrorState(state, checked) {
  if (checked && !config.value.error_states.includes(state)) {
    config.value.error_states.push(state)
  } else if (!checked) {
    config.value.error_states = config.value.error_states.filter(s => s !== state)
  }
}
</script>
