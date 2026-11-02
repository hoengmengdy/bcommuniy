<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { enablePush, turnOffPush, needsHomeScreenInstall, pushEnabled, pushSupported } from '@/services/push'
import {
  disableIncomingMessageVoice,
  enableIncomingMessageVoice,
  incomingMessageVoiceEnabled,
  incomingMessageVoiceSupported,
} from '@/services/incomingMessageVoice'

const state = ref('loading')
const busy = ref(false)
const error = ref('')
const voiceState = ref('loading')
const voiceBusy = ref(false)
const voiceError = ref('')
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

function refreshVoiceState() {
  if (disposed) return
  voiceState.value = incomingMessageVoiceSupported()
    ? incomingMessageVoiceEnabled() ? 'on' : 'off'
    : 'unsupported'
}

async function toggleVoice() {
  if (voiceBusy.value || voiceState.value === 'unsupported') return
  voiceBusy.value = true
  voiceError.value = ''
  try {
    if (voiceState.value === 'on') {
      disableIncomingMessageVoice()
      voiceState.value = 'off'
    } else {
      await enableIncomingMessageVoice()
      voiceState.value = 'on'
    }
  } catch {
    voiceState.value = 'off'
    voiceError.value = 'មិនអាចចាក់សាកសំឡេងបានទេ។ សូមពិនិត្យសំឡេងទូរស័ព្ទ ហើយព្យាយាមម្ដងទៀត។'
  } finally {
    voiceBusy.value = false
  }
}

function voiceWasDisabled() {
  voiceState.value = 'off'
  voiceError.value = 'សំឡេងមិនអាចចាក់បាន ដូច្នេះការកំណត់នេះត្រូវបានបិទ។'
}

function refreshWhenVisible() {
  if (!document.hidden && !busy.value) refresh()
}
onMounted(() => {
  refresh()
  refreshVoiceState()
  document.addEventListener('visibilitychange', refreshWhenVisible)
  window.addEventListener('focus', refreshWhenVisible)
  window.addEventListener('bcommunity-incoming-voice-disabled', voiceWasDisabled)
})
onUnmounted(() => {
  disposed = true
  document.removeEventListener('visibilitychange', refreshWhenVisible)
  window.removeEventListener('focus', refreshWhenVisible)
  window.removeEventListener('bcommunity-incoming-voice-disabled', voiceWasDisabled)
})
</script>

<template>
  <section class="notification-settings glass-panel" aria-labelledby="profile-notifications-title">
    <h2 id="profile-notifications-title">ការជូនដំណឹងសារ</h2>
    <p>បើកការជូនដំណឹងពេលមានគេឆាតមក ឬបង្ហោះអ្វីថ្មី ទោះបិទ app ឬចាក់សោទូរស័ព្ទ។</p>

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
      aria-label="ការជូនដំណឹងសារ" :aria-checked="state === 'on'"
      :disabled="busy || state === 'loading'" @click="toggle">
      <span>{{ busy ? 'កំពុងប្ដូរ…' : state === 'loading' ? 'កំពុងពិនិត្យ…' : state === 'on' ? 'បិទការជូនដំណឹង' : 'បើកការជូនដំណឹង' }}</span>
      <span class="switch-track" :class="{ enabled: state === 'on' }" aria-hidden="true"><span /></span>
    </button>
    <p v-if="state === 'on'" class="notification-status" role="status">បានបើកការជូនដំណឹងលើឧបករណ៍នេះ។</p>
    <p v-if="error" class="notification-error" role="alert">{{ error }}</p>
    <p class="notification-note">សំឡេង notification ពេល app បិទ អាស្រ័យលើការកំណត់របស់ទូរស័ព្ទ។</p>

    <h3 class="voice-title">សំឡេងនិយាយពេល app បើក</h3>
    <p>ចាក់សំឡេងខ្មែរ «មានគេឆាតមក» ពេល app បើក។ ប៉ះបើកដើម្បីសាកសំឡេងម្តង។</p>
    <p v-if="voiceState === 'unsupported'" class="notification-help">
      Browser នេះមិនអាចចាក់ឯកសារសំឡេងខ្មែរបានទេ ដូច្នេះមិនអាចបើកមុខងារនេះបាន។
    </p>
    <button v-else class="notification-toggle" type="button" role="switch"
      aria-label="សំឡេងនិយាយ" :aria-checked="voiceState === 'on'"
      :disabled="voiceBusy || voiceState === 'loading'" @click="toggleVoice">
      <span>{{ voiceBusy ? 'កំពុងសាកសំឡេង…' : voiceState === 'loading' ? 'កំពុងពិនិត្យ…' : voiceState === 'on' ? 'បិទសំឡេងនិយាយ' : 'បើកសំឡេងនិយាយ' }}</span>
      <span class="switch-track" :class="{ enabled: voiceState === 'on' }" aria-hidden="true"><span /></span>
    </button>
    <p v-if="voiceState === 'on'" class="notification-status" role="status">បានបើកសំឡេងនិយាយលើឧបករណ៍នេះ។</p>
    <p v-if="voiceError" class="notification-error" role="alert">{{ voiceError }}</p>
  </section>
</template>

<style scoped>
.notification-settings { padding: 1.25rem; margin-bottom: 1.5rem; }
h2 { margin: 0 0 0.75rem; font-size: 1.1rem; color: var(--ink-strong, #0f172a); }
h3.voice-title { margin: 1.5rem 0 0.5rem; font-size: 1rem; color: var(--ink-strong, #0f172a); }
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
