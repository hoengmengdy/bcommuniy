<script setup>
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const ui = useUiStore()

const message = ref('')
const push = ref(true)
const sending = ref(false)
const history = ref([])
const templates = [
  'ប្រព័ន្ធនឹងថែទាំនៅយប់នេះ ម៉ោង 10:00 PM។ សូមអភ័យទោសចំពោះការរំខាន។',
  'Scheduled maintenance tonight at 10:00 PM. Sorry for the interruption.',
  'Welcome to all new members! Please read the community rules before posting.',
  'New event this weekend — check the Events page for details.',
]

const send = async () => {
  const text = message.value.trim()
  if (!text) return
  if (!window.confirm('Send this notification to every active member?')) return
  sending.value = true
  const result = await admin.broadcast(text, push.value)
  sending.value = false
  if (!result) return
  history.value.unshift({ text, ...result })
  ui.addToast(`Sent to ${result.recipients} member(s)`, 'success')
  message.value = ''
}
const formatDate = iso => new Date(iso).toLocaleString()
</script>

<template>
  <div class="adm-page">
    <div class="adm-header">
      <div>
        <h1>Broadcast</h1>
        <p class="text-muted">Send an announcement to every active member's notifications</p>
      </div>
    </div>

    <div class="grid">
      <form class="glass-panel panel adm-form" @submit.prevent="send">
        <label>Message
          <textarea v-model="message" class="input-field" rows="5" maxlength="500" required
            placeholder="Write your announcement…"></textarea>
          <span class="hint">{{ message.length }} / 500</span>
        </label>
        <label class="adm-check">
          <input v-model="push" type="checkbox" />
          Also send a push notification to phones and browsers that allowed it
        </label>
        <div class="adm-form-foot">
          <button type="submit" class="adm-btn primary" :disabled="sending || !message.trim()">
            {{ sending ? 'Sending…' : 'Send to everyone' }}
          </button>
        </div>
      </form>

      <section class="glass-panel panel">
        <h2>Quick templates</h2>
        <button v-for="template in templates" :key="template" type="button" class="template" @click="message = template">
          {{ template }}
        </button>
      </section>
    </div>

    <section v-if="history.length" class="glass-panel panel">
      <h2>Sent this session</h2>
      <div v-for="item in history" :key="item.sentAt + item.text" class="sent">
        <p>{{ item.text }}</p>
        <small class="text-muted">{{ formatDate(item.sentAt) }} · {{ item.recipients }} recipients{{ item.pushed ? ' · push sent' : '' }}</small>
      </div>
    </section>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 3fr 2fr; gap: 1rem; }
.panel { padding: 1.2rem; display: flex; flex-direction: column; gap: 0.6rem; }
.panel h2 { font-size: 1rem; margin: 0 0 0.3rem; }
.template {
  text-align: left; padding: 0.6rem 0.8rem; border-radius: var(--radius-sm); cursor: pointer;
  border: 1px dashed var(--card-border); background: transparent; color: var(--text-primary); font-size: 0.88rem;
}
.template:hover { border-color: var(--accent-color); background: var(--accent-glow); }
.sent { padding: 0.6rem 0; border-bottom: 1px solid var(--card-border); }
.sent p { margin: 0 0 0.2rem; white-space: pre-wrap; }
@media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
</style>
