<template>
  <div class="form-control gap-1">
    <div class="flex justify-between items-baseline">
      <label class="label-text text-sm">{{ label }}</label>
      <span class="font-mono text-sm font-semibold text-primary">{{ currentStep.label }}</span>
    </div>
    <input
      type="range"
      class="range range-primary range-sm"
      :min="0"
      :max="steps.length - 1"
      :value="currentIndex"
      @input="onInput"
    />
    <div class="flex justify-between text-xs text-base-content/30 px-0.5">
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
  steps: Array,   // [{ label: string, value: number }]
})

const emit = defineEmits(['update:modelValue'])

const currentIndex = computed(() => {
  const exact = props.steps.findIndex(s => s.value === props.modelValue)
  if (exact >= 0) return exact
  // Snap to closest step for values that don't match exactly
  let best = 0
  let bestDiff = Infinity
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
