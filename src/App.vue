<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import ToastNotification from '@/components/ToastNotification.vue'
import { usePostsStore } from '@/stores/posts'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import {
  hasNewIncomingMessages,
  incomingMessageVoiceEnabled,
  playIncomingMessageVoice,
  snapshotChatMessages,
} from '@/services/incomingMessageVoice'

const route = useRoute()
const store = usePostsStore()
const chatStore = useChatStore()
const uiStore = useUiStore()
const canViewPage = computed(() => route.meta.public === true || Boolean(store.currentUser))
const showNavbar = computed(() => store.currentUser && route.meta.public !== true && !route.meta.requiresAdmin)

let chatRefreshTimer
let chatRefreshInProgress = false
let knownMessages = null
let disposed = false

// The messages screen refreshes conversations itself; elsewhere poll more gently.
const CHAT_POLL_MS = 4000

async function refreshIncomingMessages() {
  const userId = store.currentUser?.id
  if (disposed || document.hidden || !userId || chatRefreshInProgress || route.name === 'messages') return
  chatRefreshInProgress = true
  try {
    await chatStore.fetchConversations()
  } finally {
    chatRefreshInProgress = false
  }
}

// Announce new incoming messages whichever screen refreshed the conversations.
watch(() => chatStore.conversations, async conversations => {
  const userId = store.currentUser?.id
  if (!userId || !Array.isArray(conversations)) return
  // Sign-in and sign-out clear the list; an empty list must not become the baseline,
  // or every existing message would sound as new once the real list arrives.
  if (!knownMessages && !conversations.length) return
  const currentMessages = snapshotChatMessages(conversations)
  const previous = knownMessages
  knownMessages = currentMessages
  if (previous && hasNewIncomingMessages(previous, currentMessages) && incomingMessageVoiceEnabled()) {
    try {
      await playIncomingMessageVoice()
    } catch {
      uiStore.addToast('សំឡេងមិនអាចចាក់បានទេ។ សំឡេងនិយាយត្រូវបានបិទ។', 'error')
    }
  }
})

function refreshWhenVisible() {
  if (!document.hidden) refreshIncomingMessages()
}

watch(() => store.currentUser?.id ?? null, userId => {
  knownMessages = null
  if (userId) refreshIncomingMessages()
}, { immediate: true })

onMounted(() => {
  chatRefreshTimer = setInterval(refreshIncomingMessages, CHAT_POLL_MS)
  document.addEventListener('visibilitychange', refreshWhenVisible)
  window.addEventListener('focus', refreshWhenVisible)
})

onUnmounted(() => {
  disposed = true
  clearInterval(chatRefreshTimer)
  document.removeEventListener('visibilitychange', refreshWhenVisible)
  window.removeEventListener('focus', refreshWhenVisible)
})

// Installed phone apps keep the old page in memory for days; reload when a new version is deployed.
const currentBundle = document.querySelector('script[type="module"][src*="/assets/index-"]')?.getAttribute('src')
async function checkForUpdate() {
  if (document.visibilityState !== 'visible' || !currentBundle) return
  try {
    const html = await (await fetch('/', { cache: 'no-store' })).text()
    if (html.includes('/assets/index-') && !html.includes(currentBundle)) location.reload()
  } catch {
    // Offline or a transient error: try again next time the app comes back to the foreground.
  }
}
document.addEventListener('visibilitychange', checkForUpdate)
</script>

<template>
  <div class="app-wrapper">
    <div v-if="showNavbar" class="nav-container">
      <Navbar />
    </div>
    <main class="main-content">
      <RouterView v-if="canViewPage" />
    </main>
    <ToastNotification />
  </div>
</template>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav-container {
  width: 100%;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
