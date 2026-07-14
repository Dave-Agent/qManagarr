<template>
  <div class="flex flex-col gap-2">
    <div class="flex justify-between items-baseline">
      <label class="text-sm text-foreground">{{ label }}</label>
      <span class="font-mono text-sm font-semibold text-primary">{{ currentStep.label }}</span>
    </div>
    <input
      type="range"
      class="w-full h-1.5 rounded-full cursor-pointer appearance-none bg-secondary"
      :min="0"
      :max="steps.length - 1"
      :value="currentIndex"
      @input="onInput"
    />
    <div class="flex justify-between text-xs text-muted-foreground/50 px-0.5">
      <span>{{ steps[0].label }}</span>
      <span>{{ steps[steps.length - 1].label }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: String,
  modelValue: Number,
  steps: Array,
})
const emit = defineEmits(['update:modelValue'])

const currentIndex = computed(() => {
  const exact = props.steps.findIndex(s => s.value === props.modelValue)
  if (exact >= 0) return exact
  let best = 0, bestDiff = Infinity
  props.steps.forEach((s, i) => {
    const diff = Math.abs(s.value - props.modelValue)
    if (diff < bestDiff) { bestDiff = diff; best = i }
  })
  return best
})

const currentStep = computed(() => props.steps[currentIndex.value])

function onInput(e) {
  emit('update:modelValue', props.steps[parseInt(e.target.value)].value)
}
</script>
