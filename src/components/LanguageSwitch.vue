<script setup>
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
const options = [
  { value: 'km', label: 'ខ្មែរ', name: 'Khmer' },
  { value: 'en', label: 'EN', name: 'English' },
]
</script>

<template>
  <div class="lang-switch" role="group" :aria-label="settings.t('settings.language')">
    <button
      v-for="option in options"
      :key="option.value"
      :class="['lang-option', { active: settings.lang === option.value }]"
      :aria-pressed="settings.lang === option.value"
      :lang="option.value"
      :title="option.name"
      @click="settings.setLang(option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<style scoped>
.lang-switch {
  display: inline-flex;
  flex-shrink: 0;
  padding: 3px;
  gap: 2px;
  border-radius: 10px;
  background: var(--surface-3, #f1f5f9);
}

.lang-option {
  height: 28px;
  min-width: 38px;
  padding: 0 8px;
  border: none;
  border-radius: 8px;
  background: none;
  color: var(--ink-500, #64748b);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.lang-option:hover { color: var(--ink-strong, #0f172a); }

.lang-option.active {
  background: var(--surface, #ffffff);
  color: var(--brand-ink, #6d28d9);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.12);
}
</style>
