<template>
  <div class="flex h-screen bg-base-300 overflow-hidden">
    <Sidebar
      :activePanel="activePanel"
      :modules="modules"
      @navigate="activePanel = $event"
      @toggle="toggleModule"
    />
    <main class="flex-1 overflow-auto p-8">
      <DashboardPanel    v-if="activePanel === 'dashboard'" />
      <QBittorrentPanel  v-else-if="activePanel === 'qbittorrent'" />
      <LogPanel          v-else-if="activePanel === 'log'" />
      <ModulePanel
        v-else-if="isModule(activePanel)"
        :moduleId="activePanel"
        :modules="modules"
        @toggle="toggleModule"
      />
      <div v-else class="flex items-center justify-center h-full">
        <span class="text-base-content/30 text-sm">Coming soon</span>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar          from './components/Sidebar.vue'
import DashboardPanel   from './components/panels/DashboardPanel.vue'
import QBittorrentPanel from './components/panels/QBittorrentPanel.vue'
import LogPanel         from './components/panels/LogPanel.vue'
import ModulePanel      from './components/panels/ModulePanel.vue'

const MODULE_IDS  = ['completed-purge', 'exe-killer', 'error-killer', 'eta-monitor', 'stall-monitor']
const activePanel = ref('dashboard')
const modules     = ref([])

onMounted(fetchModules)

async function fetchModules() {
  const res = await fetch('/api/modules')
  modules.value = await res.json()
}

async function toggleModule(id, enabled) {
  const mod = modules.value.find(m => m.id === id)
  if (mod) mod.enabled = enabled  // optimistic update
  await fetch(`/api/modules/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
}

const isModule = panel => MODULE_IDS.includes(panel)
</script>
