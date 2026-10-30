<script setup>
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
const dark = computed(() => settings.theme === 'dark')
</script>

<template>
  <!-- Night: navy pill, white knob on the left, moon and stars. Day: sky pill, sun knob on the right. -->
  <button
    class="theme-toggle"
    :class="{ dark }"
    role="switch"
    :aria-checked="dark"
    :aria-label="settings.t('settings.darkMode')"
    :title="dark ? settings.t('settings.lightMode') : settings.t('settings.darkMode')"
    @click="settings.toggleTheme()"
  >
    <span class="sky" aria-hidden="true">
      <svg class="moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" fill="#fcd34d"/></svg>
      <span class="star s1">✦</span>
      <span class="star s2">✦</span>
      <span class="star s3">✦</span>
      <span class="cloud"></span>
    </span>
    <span class="knob" aria-hidden="true"></span>
  </button>
</template>

<style scoped>
.theme-toggle {
  position: relative;
  width: 58px;
  height: 30px;
  flex-shrink: 0;
  padding: 0;
  border: 2px solid #ffffff;
  border-radius: 999px;
  background: linear-gradient(135deg, #7dd3fc, #38bdf8);
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12), inset 0 1px 3px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  overflow: hidden;
  transition: background 0.25s ease;
}

.theme-toggle.dark {
  background: linear-gradient(135deg, #1e2a4a, #0f1830);
  border-color: #e5e7eb;
}

.sky {
  position: absolute;
  inset: 0;
}

.moon {
  position: absolute;
  right: 7px;
  top: 5px;
  width: 17px;
  height: 17px;
  opacity: 0;
  transform: translateY(6px);
  transition: all 0.25s ease;
}

.star {
  position: absolute;
  color: #fcd34d;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.25s ease;
}

.s1 { font-size: 7px; left: 30px; top: 5px; }
.s2 { font-size: 5px; left: 26px; top: 15px; }
.s3 { font-size: 6px; left: 36px; top: 17px; }

.cloud {
  position: absolute;
  left: 9px;
  top: 14px;
  width: 16px;
  height: 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 5px -3px 0 1px rgba(255, 255, 255, 0.9);
  transition: opacity 0.25s ease;
}

.knob {
  position: absolute;
  top: 2px;
  left: 30px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fde68a, #f59e0b);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  transition: left 0.25s ease, background 0.25s ease;
}

.dark .knob {
  left: 2px;
  background: radial-gradient(circle at 35% 35%, #ffffff, #e5e7eb);
}

.dark .moon { opacity: 1; transform: none; }
.dark .star { opacity: 1; }
.dark .cloud { opacity: 0; }

.theme-toggle:hover { box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2), inset 0 1px 3px rgba(0, 0, 0, 0.15); }

@media (prefers-reduced-motion: reduce) {
  .theme-toggle, .theme-toggle * { transition: none; }
}
</style>
