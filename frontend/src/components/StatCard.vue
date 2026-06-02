<template>
  <div class="bg-base-200 rounded-box shadow p-4 flex flex-col gap-1 min-w-36">
    <div class="text-xs uppercase tracking-wide text-base-content/50">{{ label }}</div>
    <div :class="['text-3xl font-bold tabular-nums', valueClass]">{{ value }}</div>
    <div class="text-xs text-base-content/40">{{ sub }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:     String,
  value:     Number,
  sub:       String,
  highlight: { type: String, default: null },  // 'warning' | 'error' | null
})

const valueClass = computed(() => ({
  'text-warning': props.highlight === 'warning',
  'text-error':   props.highlight === 'error',
  'text-primary': !props.highlight,
}))
</script>
