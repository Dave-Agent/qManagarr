<template>
  <div v-if="meta">
    <h2 class="text-xl font-semibold mb-6">{{ meta.label }}</h2>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

      <!-- Left column: enable + settings -->
      <div class="flex flex-col gap-6">

        <!-- Enable / disable -->
        <div class="card bg-base-200 shadow-lg">
          <div class="card-body">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium">Enable module</p>
                <p class="text-sm text-base-content/50 mt-0.5">{{ meta.description }}</p>
              </div>
              <input
                type="checkbox"
                class="toggle toggle-primary toggle-lg"
                :checked="enabled"
                @change="setEnabled($event.target.checked)"
              />
            </div>
            <div v-if="!enabled" role="alert" class="alert alert-warning text-sm py-2 mt-2">
              This module is disabled — no action will be taken for this rule.
            </div>
          </div>
        </div>

        <!-- Settings -->
        <div v-if="config" class="card bg-base-200 shadow-lg">
      <div class="card-body gap-6">

        <div class="flex items-center justify-between">
          <h3 class="card-title text-base">Settings</h3>
          <button class="btn btn-ghost btn-xs opacity-60" @click="resetDefaults">
            Reset defaults
          </button>
        </div>

        <!-- COMPLETED PURGE -->
        <template v-if="moduleId === 'completed-purge'">
          <StepSlider
            label="Remove completed torrents after"
            v-model="config.purge_delay"
            :steps="TIME_STEPS"
          />
        </template>

        <!-- EXE KILLER -->
        <template v-else-if="moduleId === 'exe-killer'">
          <div class="form-control gap-2">
            <label class="label-text text-sm">Blocked file extensions</label>
            <div class="flex flex-wrap gap-2 min-h-8">
              <div
                v-for="ext in config.bad_extensions"
                :key="ext"
                class="badge badge-primary gap-1 py-3 pr-1 font-mono"
              >
                {{ ext }}
                <button
                  class="btn btn-ghost btn-xs px-1 min-h-0 h-auto hover:text-error"
                  @click="removeExt(ext)"
                >✕</button>
              </div>
              <span v-if="!config.bad_extensions.length" class="text-sm text-base-content/30 italic">
                No extensions — EXE Killer will not block anything.
              </span>
            </div>
            <div class="flex gap-2 mt-1">
              <input
                v-model="newExt"
                type="text"
                placeholder=".exe"
                class="input input-bordered input-sm flex-1 font-mono"
                @keyup.enter="addExt"
              />
              <button class="btn btn-sm btn-primary" :disabled="!newExt.trim()" @click="addExt">
                Add
              </button>
            </div>
          </div>
        </template>

        <!-- ERROR KILLER -->
        <template v-else-if="moduleId === 'error-killer'">
          <div class="form-control gap-3">
            <label class="label-text text-sm">Act on these states</label>
            <div class="flex flex-col gap-2">
              <label
                v-for="state in KNOWN_ERROR_STATES"
                :key="state.value"
                class="flex items-center gap-3 cursor-pointer"
              >
                <input
                  type="checkbox"
                  class="checkbox checkbox-primary checkbox-sm"
                  :checked="config.error_states.includes(state.value)"
                  @change="toggleErrorState(state.value, $event.target.checked)"
                />
                <div>
                  <span class="text-sm font-medium">{{ state.label }}</span>
                  <span class="text-xs text-base-content/50 ml-2">{{ state.description }}</span>
                </div>
              </label>
            </div>
          </div>
        </template>

        <!-- ETA MONITOR -->
        <template v-else-if="moduleId === 'eta-monitor'">
          <StepSlider
            label="Maximum acceptable ETA"
            v-model="config.max_eta_secs"
            :steps="TIME_STEPS"
          />
          <StepSlider
            label="Wait before checking ETA (torrent age)"
            v-model="config.eta_threshold_secs"
            :steps="TIME_STEPS"
          />
          <StepSlider
            label="Grace period — sustained bad ETA before action"
            v-model="config.eta_grace_secs"
            :steps="TIME_STEPS"
          />
          <StepSlider
            label="Minimum speed during bad ETA (below this = stalled)"
            v-model="config.min_active_speed"
            :steps="SPEED_STEPS"
          />
          <StepSlider
            label="Ignore ETA logic above this progress"
            v-model="config.eta_ignore_progress"
            :steps="PROGRESS_STEPS"
          />
        </template>

        <!-- STALL MONITOR -->
        <template v-else-if="moduleId === 'stall-monitor'">
          <StepSlider
            label="Stall check window"
            v-model="config.stall_check_secs"
            :steps="TIME_STEPS"
          />
          <StepSlider
            label="Minimum progress required within window"
            v-model="config.progress_threshold_bytes"
            :steps="SIZE_STEPS"
          />
        </template>

        <!-- Save -->
        <div class="flex items-center gap-3 pt-1 border-t border-base-300">
          <button class="btn btn-primary btn-sm" :disabled="savingConfig" @click="saveConfig">
            {{ savingConfig ? 'Saving…' : 'Save' }}
          </button>
          <span v-if="savedConfig" class="text-sm text-success">Saved!</span>
        </div>

      </div>
    </div>

      </div><!-- end left column -->

      <!-- Right column: description -->
      <div v-if="description" class="card bg-base-200 shadow-lg">
        <div class="card-body">
          <div
            v-html="descriptionHtml"
            class="prose prose-sm max-w-none
                   prose-p:text-base-content/80 prose-p:leading-relaxed
                   prose-strong:text-base-content prose-headings:text-base-content"
          ></div>
        </div>
      </div>

    </div><!-- end grid -->
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
const config        = ref(null)
const description   = ref('')
const savingConfig  = ref(false)
const savedConfig   = ref(false)
const newExt        = ref('')

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
  const res = await fetch(`/api/modules/${props.moduleId}/config`)
  // Temporarily clear saved config so defaults are returned
  await fetch(`/api/modules/${props.moduleId}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  const defaults = await (await fetch(`/api/modules/${props.moduleId}/config`)).json()
  config.value = defaults
}

// EXE Killer helpers
function addExt() {
  let ext = newExt.value.trim()
  if (!ext) return
  if (!ext.startsWith('.')) ext = '.' + ext
  ext = ext.toLowerCase()
  if (!config.value.bad_extensions.includes(ext)) {
    config.value.bad_extensions.push(ext)
  }
  newExt.value = ''
}

function removeExt(ext) {
  config.value.bad_extensions = config.value.bad_extensions.filter(e => e !== ext)
}

// Error Killer helpers
function toggleErrorState(state, checked) {
  if (checked && !config.value.error_states.includes(state)) {
    config.value.error_states.push(state)
  } else if (!checked) {
    config.value.error_states = config.value.error_states.filter(s => s !== state)
  }
}
</script>
