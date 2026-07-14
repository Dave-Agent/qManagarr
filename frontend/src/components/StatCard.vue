<template>
  <div class="bg-card border border-border rounded-lg p-4 flex flex-col gap-1 min-w-36">
    <div class="text-xs uppercase tracking-wide text-muted-foreground font-medium">{{ label }}</div>
    <div :class="['text-3xl font-bold tabular-nums', valueClass]">{{ value }}</div>
    <div class="text-xs text-muted-foreground/60">{{ sub }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:     String,
  value:     Number,
  sub:       String,
  highlight: { type: String, default: null },
})

const valueClass = computed(() => ({
  'text-warning':     props.highlight === 'warning',
  'text-destructive': props.highlight === 'error',
  'text-primary':     !props.highlight,
}))
</script>
