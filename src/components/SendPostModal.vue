<script setup>
import { computed, onMounted, ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'
import { postSnippet, postUrl } from '@/utils/share'

// "Send" a post to another member as a chat message containing its link.
const props = defineProps({ post: { type: Object, required: true } })
const emit = defineEmits(['close'])

const chatStore = useChatStore()
const postStore = usePostsStore()
const uiStore = useUiStore()
const search = ref('')
const sendingTo = ref(null)

onMounted(() => chatStore.fetchMembers())

const members = computed(() => chatStore.members
  .filter(member => member.id !== postStore.currentUser?.id)
  .filter(member => member.name.toLowerCase().includes(search.value.trim().toLowerCase())))

async function sendTo(member) {
  sendingTo.value = member.id
  const chat = await chatStore.startConversation(member.id)
  const sent = chat && await chatStore.sendMessage(`📌 ${postSnippet(props.post)}\n${postUrl(props.post)}`)
  sendingTo.value = null
  if (!sent) return
  uiStore.addToast(`Sent to ${member.name}`, 'success')
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div class="send-overlay" @click.self="emit('close')">
      <div class="send-sheet" role="dialog" aria-label="Send post">
        <div class="send-header">
          <h3>Send to…</h3>
          <button class="send-close" aria-label="Close" @click="emit('close')">✕</button>
        </div>
        <input v-model="search" class="send-search" type="search" placeholder="Search members" />
        <div class="send-list">
          <button v-for="member in members" :key="member.id" class="send-row" :disabled="sendingTo !== null"
            @click="sendTo(member)">
            <img :src="member.avatar" alt="" class="send-avatar" />
            <span class="send-name">{{ member.name }}</span>
            <span class="send-action">{{ sendingTo === member.id ? 'Sending…' : 'Send' }}</span>
          </button>
          <p v-if="!members.length" class="send-empty">No members found.</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.send-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.send-sheet {
  width: min(480px, 100%);
  max-height: 75vh;
  display: flex;
  flex-direction: column;
  background: var(--surface, #ffffff);
  border-radius: 20px 20px 0 0;
  padding: 1rem 1rem calc(1rem + env(safe-area-inset-bottom));
  box-shadow: 0 -10px 30px rgba(15, 23, 42, 0.15);
  animation: sheetUp 0.2s ease-out;
}

@media (min-width: 769px) {
  .send-overlay { align-items: center; }
  .send-sheet { border-radius: 20px; }
}

@keyframes sheetUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.send-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.send-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.send-close {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: var(--surface-3, #f1f5f9);
  cursor: pointer;
}

.send-search {
  width: 100%;
  padding: 0.7rem 1rem;
  border: 1px solid var(--line, #e2e8f0);
  border-radius: 12px;
  font-family: inherit;
  font-size: 16px;
  margin-bottom: 0.5rem;
  outline: none;
}

.send-list {
  overflow-y: auto;
}

.send-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.6rem 0.25rem;
  border: none;
  background: none;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
}

.send-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.send-name {
  flex: 1;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--ink-strong, #111827);
}

.send-action {
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  background: #7c3aed;
  color: #ffffff;
  font-size: 0.8rem;
  font-weight: 700;
}

.send-empty {
  text-align: center;
  color: var(--ink-400, #94a3b8);
}
</style>
