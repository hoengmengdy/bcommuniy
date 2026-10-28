<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import ToastNotification from '@/components/ToastNotification.vue'
import { usePostsStore } from '@/stores/posts'
import { useChatStore } from '@/stores/chat'
import { unlockMessageSound } from '@/services/message-sound'

const route = useRoute()
const store = usePostsStore()
const chatStore = useChatStore()
const canViewPage = computed(() => route.meta.public === true || Boolean(store.currentUser))
const showNavbar = computed(() => store.currentUser && route.meta.public !== true && !route.meta.requiresAdmin)

// Listen for messages throughout the signed-in app, including while reading the feed.
let refreshTimer
let refreshing = false
async function refreshChats() {
  if (!store.currentUser || document.hidden || refreshing) return
  refreshing = true
  try { await chatStore.fetchConversations({ silent: true }) }
  finally { refreshing = false }
}
watch(() => store.currentUser?.id, id => {
  clearInterval(refreshTimer)
  if (id) {
    refreshChats()
    refreshTimer = setInterval(refreshChats, 2000)
  }
}, { immediate: true })
onMounted(() => {
  document.addEventListener('pointerdown', unlockMessageSound)
  document.addEventListener('keydown', unlockMessageSound)
  document.addEventListener('visibilitychange', refreshChats)
  window.addEventListener('focus', refreshChats)
})
onUnmounted(() => {
  clearInterval(refreshTimer)
  document.removeEventListener('pointerdown', unlockMessageSound)
  document.removeEventListener('keydown', unlockMessageSound)
  document.removeEventListener('visibilitychange', refreshChats)
  window.removeEventListener('focus', refreshChats)
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
