<template>
  <aside class="w-60 bg-sidebar flex flex-col border-r border-border shrink-0">

    <!-- Header -->
    <div class="px-4 py-4 flex items-center gap-2.5 border-b border-border">
      <img src="../assets/logo1sqr.png" alt="qManagarr" class="h-7 w-7 object-contain shrink-0 rounded" />
      <h1 class="text-sm font-semibold text-foreground tracking-wide">qManagarr</h1>
    </div>

    <!-- Main nav -->
    <nav class="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">

      <button :class="navItemClass(activePanel === 'dashboard')" @click="$emit('navigate', 'dashboard')">
        <LayoutDashboard class="h-4 w-4 shrink-0" />
        <span>Dashboard</span>
      </button>

      <!-- Modules section label -->
      <div class="mt-5 mb-1.5 px-2">
        <span class="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">Modules</span>
      </div>

      <div v-for="mod in MODULES" :key="mod.id" class="flex items-center gap-1">
        <button
          :class="[navItemClass(activePanel === mod.id), 'flex-1', !moduleEnabled(mod.id) ? 'opacity-40' : '']"
          @click="$emit('navigate', mod.id)"
        >
          <component :is="mod.icon" class="h-4 w-4 shrink-0" />
          <span class="flex-1 text-left truncate">{{ mod.label }}</span>
        </button>
        <!-- Toggle switch -->
        <button
          role="switch"
          :aria-checked="moduleEnabled(mod.id)"
          :title="moduleEnabled(mod.id) ? 'Disable module' : 'Enable module'"
          :class="[
            'relative inline-flex h-4 w-7 shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            moduleEnabled(mod.id) ? 'bg-primary' : 'bg-muted'
          ]"
          @click.stop="$emit('toggle', mod.id, !moduleEnabled(mod.id))"
        >
          <span :class="[
            'pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow transition-transform duration-150',
            moduleEnabled(mod.id) ? 'translate-x-3' : 'translate-x-0'
          ]" />
        </button>
      </div>

    </nav>

    <!-- System section (pinned to bottom) -->
    <div class="px-2 pt-3 pb-2 border-t border-border flex flex-col gap-0.5">
      <div class="mb-1.5 px-2">
        <span class="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">System</span>
      </div>
      <button :class="navItemClass(activePanel === 'logs')" @click="$emit('navigate', 'logs')">
        <ScrollText class="h-4 w-4 shrink-0" />
        <span>Logs</span>
      </button>
      <button :class="navItemClass(activePanel === 'settings')" @click="$emit('navigate', 'settings')">
        <Settings2 class="h-4 w-4 shrink-0" />
        <span>Settings</span>
      </button>
    </div>

    <!-- Version -->
    <div class="px-4 py-2.5 border-t border-border">
      <span class="text-[10px] text-muted-foreground/40">{{ version }}</span>
    </div>

  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  LayoutDashboard, CheckCircle2, ShieldX, AlertCircle,
  Clock, Activity, ScrollText, Settings2,
} from 'lucide-vue-next'

const version = ref('—')
onMounted(async () => {
  try {
    const res = await fetch('/api/settings/version')
    version.value = (await res.json()).version
  } catch { /* leave as — */ }
})

const props = defineProps({
  activePanel: String,
  modules: { type: Array, default: () => [] },
})
defineEmits(['navigate', 'toggle'])

const MODULES = [
  { id: 'completed-purge', label: 'Completed Purge', icon: CheckCircle2 },
  { id: 'exe-killer',      label: 'EXE Killer',      icon: ShieldX },
  { id: 'error-killer',   label: 'Error Killer',    icon: AlertCircle },
  { id: 'eta-monitor',    label: 'ETA Monitor',     icon: Clock },
  { id: 'stall-monitor',  label: 'Stall Monitor',   icon: Activity },
]

function navItemClass(active) {
  return [
    'w-full flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-colors text-left',
    active
      ? 'bg-secondary text-primary font-medium'
      : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground',
  ]
}

function moduleEnabled(id) {
  const mod = props.modules.find(m => m.id === id)
  return mod ? mod.enabled : true
}
</script>
