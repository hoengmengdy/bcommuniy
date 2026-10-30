<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { enablePush, turnOffPush, needsHomeScreenInstall, pushEnabled, pushSupported } from '@/services/push'

const state = ref('loading')
const busy = ref(false)
const error = ref('')
let disposed = false

async function refresh() {
  try {
    let next
    if (needsHomeScreenInstall()) next = 'install'
    else if (!pushSupported()) next = 'unsupported'
    else if (Notification.permission === 'denied') next = 'denied'
    else next = await pushEnabled() ? 'on' : 'off'
    if (!disposed) state.value = next
  } catch {
    if (!disposed) {
      state.value = 'off'
      error.value = 'មិនអាចពិនិត្យការជូនដំណឹងបាន។ សូមព្យាយាមម្ដងទៀត។'
    }
  }
}

async function toggle() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    // Call directly from the tap so iPhone can show its permission prompt.
    if (state.value === 'on') await turnOffPush()
    else await enablePush()
  } catch (cause) {
    error.value = cause.message || 'មិនអាចប្ដូរការជូនដំណឹងបាន។ សូមព្យាយាមម្ដងទៀត។'
  } finally {
    await refresh()
    busy.value = false
  }
}

function refreshWhenVisible() {
  if (!document.hidden && !busy.value) refresh()
}
onMounted(() => {
  refresh()
  document.addEventListener('visibilitychange', refreshWhenVisible)
  window.addEventListener('focus', refreshWhenVisible)
})
onUnmounted(() => {
  disposed = true
  document.removeEventListener('visibilitychange', refreshWhenVisible)
  window.removeEventListener('focus', refreshWhenVisible)
})
</script>

<template>
  <section class="notification-settings glass-panel" aria-labelledby="profile-notifications-title">
    <h2 id="profile-notifications-title">ការជូនដំណឹងសារ</h2>
    <p>ទទួល notification ពេលមានគេឆាតមក ឬបង្ហោះអ្វីថ្មី ទោះបិទ app ឬចាក់សោទូរស័ព្ទ។</p>

    <div v-if="state === 'install'" class="notification-help">
      នៅលើ iPhone៖ បើក website ក្នុង Safari → Share → Add to Home Screen។
      បើក Bcommunity ពី Home Screen រួចចូល Profile នេះដើម្បីបើកការជូនដំណឹង។
    </div>
    <p v-else-if="state === 'unsupported'" class="notification-help">
      Browser នេះមិនគាំទ្រ push notification ទេ។ សូមប្រើ browser ដែលគាំទ្រ ឬបន្ថែម app ទៅ Home Screen។
    </p>
    <p v-else-if="state === 'denied'" class="notification-help">
      ការជូនដំណឹងត្រូវបានបិទដោយទូរស័ព្ទ។ សូមអនុញ្ញាត Notifications សម្រាប់ Bcommunity ក្នុង Settings រួចត្រឡប់មកវិញ។
    </p>
    <button v-else class="notification-toggle" type="button" role="switch"
      :aria-checked="state === 'on'" :disabled="busy || state === 'loading'" @click="toggle">
      <span>{{ busy ? 'កំពុងប្ដូរ…' : state === 'loading' ? 'កំពុងពិនិត្យ…' : state === 'on' ? 'បិទការជូនដំណឹង' : 'បើកការជូនដំណឹង' }}</span>
      <span class="switch-track" :class="{ enabled: state === 'on' }" aria-hidden="true"><span /></span>
    </button>
    <p v-if="state === 'on'" class="notification-status" role="status">បានបើកការជូនដំណឹងលើឧបករណ៍នេះ។</p>
    <p v-if="error" class="notification-error" role="alert">{{ error }}</p>
    <p class="notification-note">សំឡេង និងការអានសារចេញជាសំឡេង អាស្រ័យលើការកំណត់ និងការគាំទ្ររបស់ទូរស័ព្ទ។</p>
  </section>
</template>

<style scoped>
.notification-settings { padding: 1.25rem; margin-bottom: 1.5rem; }
h2 { margin: 0 0 0.75rem; font-size: 1.1rem; color: var(--ink-strong, #0f172a); }
p { color: var(--ink-600, #475569); font-size: 0.88rem; line-height: 1.7; margin: 0.75rem 0; }
.notification-toggle { display: flex; align-items: center; justify-content: space-between; gap: 1rem; width: 100%; padding: 0.85rem; border: 1px solid var(--tint-strong, #ddd6fe); border-radius: 12px; background: var(--tint, #f5f3ff); color: var(--brand-ink, #5b21b6); font: inherit; cursor: pointer; text-align: left; }
.notification-toggle:focus-visible { outline: 3px solid #7c3aed; outline-offset: 3px; }
.notification-toggle:disabled { opacity: 0.6; cursor: wait; }
.switch-track { display: flex; align-items: center; flex-shrink: 0; width: 44px; height: 26px; padding: 3px; box-sizing: border-box; border-radius: 20px; background: var(--ink-400, #94a3b8); }
.switch-track span { width: 20px; height: 20px; background: var(--surface, white); border-radius: 50%; transition: transform 0.15s; }
.switch-track.enabled { background: #16a34a; }
.switch-track.enabled span { transform: translateX(18px); }
.notification-help { border-radius: 10px; padding: 0.8rem; background: var(--surface-3, #f1f5f9); color: var(--ink-700, #334155); font-size: 0.85rem; line-height: 1.8; }
.notification-status { color: #15803d; }
.notification-error { color: var(--red-ink, #b91c1c); overflow-wrap: anywhere; }
.notification-note { font-size: 0.8rem; color: var(--ink-500, #64748b); margin-bottom: 0; }
</style>
