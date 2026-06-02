<template>
  <aside class="w-56 bg-base-200 flex flex-col border-r border-base-300 shrink-0">

    <div class="px-4 py-3 border-b border-base-300 flex items-center gap-2">
      <img src="../assets/logo1sqr.png" alt="qManagarr" class="h-8 w-8 object-contain shrink-0" />
      <h1 class="text-lg font-bold text-primary tracking-wide">qManagarr</h1>
    </div>

    <nav class="flex-1 overflow-y-auto py-2 px-2">
      <ul class="menu menu-sm gap-0.5 p-0">

        <li>
          <a :class="{ active: activePanel === 'dashboard' }" class="cursor-pointer" @click="$emit('navigate', 'dashboard')">
            Dashboard
          </a>
        </li>

        <li>
          <a :class="{ active: activePanel === 'qbittorrent' }" class="cursor-pointer" @click="$emit('navigate', 'qbittorrent')">
            qBittorrent
          </a>
        </li>

        <li class="menu-title pt-4 pb-1 px-2 text-xs uppercase tracking-wider opacity-50">
          Modules
        </li>

        <li v-for="mod in MODULES" :key="mod.id" class="relative">
          <a
            :class="[{ active: activePanel === mod.id }, !moduleEnabled(mod.id) ? 'opacity-40' : '']"
            class="pr-12 cursor-pointer"
            @click="$emit('navigate', mod.id)"
          >
            {{ mod.label }}
          </a>
          <div class="absolute right-3 top-1/2 -translate-y-1/2 z-10">
            <input
              type="checkbox"
              class="toggle toggle-xs toggle-primary"
              :checked="moduleEnabled(mod.id)"
              @change="$emit('toggle', mod.id, $event.target.checked)"
              @click.stop
            />
          </div>
        </li>

        <li class="pt-4">
          <a :class="{ active: activePanel === 'log' }" class="cursor-pointer" @click="$emit('navigate', 'log')">
            Log
          </a>
        </li>

      </ul>
    </nav>

    <div class="px-4 py-2 border-t border-base-300 text-xs text-base-content/30">
      v0.8.0
    </div>

  </aside>
</template>

<script setup>
const props = defineProps({
  activePanel: String,
  modules: { type: Array, default: () => [] },
})
defineEmits(['navigate', 'toggle'])

const MODULES = [
  { id: 'completed-purge', label: 'Completed Purge' },
  { id: 'exe-killer',      label: 'EXE Killer' },
  { id: 'error-killer',    label: 'Error Killer' },
  { id: 'eta-monitor',     label: 'ETA Monitor' },
  { id: 'stall-monitor',   label: 'Stall Monitor' },
]

function moduleEnabled(id) {
  const mod = props.modules.find(m => m.id === id)
  return mod ? mod.enabled : true
}
</script>
