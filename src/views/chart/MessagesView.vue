<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watchEffect } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import { upload } from '@vercel/blob/client'
import { authHeaders } from '@/services/api'
import { chatTime } from '@/utils/time'
import { useRoute } from 'vue-router'
import { enablePush, needsHomeScreenInstall, pushEnabled, pushSupported } from '@/services/push'

const store = useChatStore()
const postStore = usePostsStore()
const selectedMember = ref('')
const availableMembers = computed(() => store.members.filter(member => member.id !== postStore.currentUser?.id))
async function startChat() {
  if (!selectedMember.value) return
  const chat = await store.startConversation(Number(selectedMember.value))
  if (chat) { selectedMember.value = ''; mobileView.value = 'thread' }
}
const uiStore = useUiStore()
const chatContainer = ref(null)
const inputMessage = ref('')
const isTyping = computed(() => inputMessage.value.trim().length > 0)
const searchQuery = ref('')
const mobileView = ref('list') // 'list' | 'thread'

const filteredConversations = computed(() => {
  if (!searchQuery.value) return store.conversations
  const query = searchQuery.value.toLowerCase()
  return store.conversations.filter(chat => 
    chat.name.toLowerCase().includes(query) || 
    chat.lastMessage.toLowerCase().includes(query)
  )
})

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

async function handleSend() {
  const text = inputMessage.value.trim()
  if (!text) return
  showEmojiPicker.value = false
  if (editingMsg.value) {
    if (text !== editingMsg.value.text && !await store.editMessage(editingMsg.value.id, text)) return
    cancelCompose()
    return
  }
  const sent = await store.sendMessage(text, null, replyingTo.value?.id)
  if (!sent) return
  cancelCompose()
  nextTick(() => scrollToBottom())
}

// ── Messenger-style message actions: press and hold (or right-click) a message ──
const REACTIONS = ['❤️', '😆', '😮', '😢', '😡', '👍']
const EMOJIS = ['😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😎', '🤩', '🥳', '😉', '🙂', '🤔', '🤗', '😴', '😅',
  '😭', '😢', '😡', '😱', '🙏', '👍', '👎', '👏', '🙌', '💪', '🤝', '👋', '✌️', '👌', '❤️', '💔',
  '🔥', '✨', '🎉', '💯', '⭐', '🌸', '🌹', '☕', '🍻', '🍕', '🎂', '⚽', '🎮', '💻', '📚', '🚀']
const actionMsg = ref(null)
const reactionPickerOpen = ref(false)
const replyingTo = ref(null)
const editingMsg = ref(null)
const showEmojiPicker = ref(false)
const messageInput = ref(null)
let pressTimer

function pressStart(msg) {
  clearTimeout(pressTimer)
  pressTimer = setTimeout(() => openActions(msg), 450)
}
function pressEnd() {
  clearTimeout(pressTimer)
}
function openActions(msg) {
  showEmojiPicker.value = false
  reactionPickerOpen.value = false
  actionMsg.value = msg
  navigator.vibrate?.(10)
}
function closeActions() {
  actionMsg.value = null
  reactionPickerOpen.value = false
}

async function react(msg, emoji) {
  closeActions()
  const mine = msg.reactions?.find(r => r.mine)?.emoji
  await store.reactToMessage(msg.id, mine === emoji ? null : emoji)
}

function startReply(msg) {
  closeActions()
  editingMsg.value = null
  replyingTo.value = msg
  nextTick(() => messageInput.value?.focus())
}

function startEdit(msg) {
  closeActions()
  replyingTo.value = null
  editingMsg.value = msg
  inputMessage.value = msg.text
  nextTick(() => messageInput.value?.focus())
}

async function copyMessage(msg) {
  closeActions()
  try {
    await navigator.clipboard.writeText(msg.text)
    uiStore.addToast('Copied', 'success')
  } catch {
    uiStore.addToast('Could not copy on this device.', 'error')
  }
}

async function removeMessage(msg) {
  closeActions()
  if (!window.confirm('Delete this message for everyone?')) return
  if (await store.deleteMessage(msg.id)) uiStore.addToast('Message deleted', 'success')
}

function cancelCompose() {
  replyingTo.value = null
  editingMsg.value = null
  inputMessage.value = ''
}

function replyPreview(msg) {
  return msg.text || (msg.type === 'video' ? '🎬 Video' : msg.type === 'image' ? '📷 Photo' : 'Message')
}

// Insert an emoji at the cursor so people can mix emoji and text.
function insertEmoji(emoji) {
  const input = messageInput.value
  const start = input?.selectionStart ?? inputMessage.value.length
  const end = input?.selectionEnd ?? start
  inputMessage.value = inputMessage.value.slice(0, start) + emoji + inputMessage.value.slice(end)
  nextTick(() => input?.setSelectionRange(start + emoji.length, start + emoji.length))
}

async function selectChat(id) {
  if (!await store.setActiveChat(id)) return
  mobileView.value = 'thread'
  nextTick(() => scrollToBottom())
}

// Photos and videos upload straight to Vercel Blob, then the message stores the file's URL.
const fileInput = ref(null)
const uploadProgress = ref(null) // null when idle, 0-100 while uploading
const MEDIA_LIMITS = { image: 10 * 1024 * 1024, video: 50 * 1024 * 1024 }
const VIDEO_EXT = { 'video/mp4': 'mp4', 'video/quicktime': 'mov', 'video/webm': 'webm', 'video/3gpp': '3gp' }

function openMedia(url) {
  window.open(url, '_blank', 'noopener')
}

function formatSize(bytes) {
  return bytes >= 1024 * 1024 ? (bytes / 1024 / 1024).toFixed(1) + ' MB' : Math.ceil(bytes / 1024) + ' KB'
}

async function handleFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || !store.activeChat) return
  const kind = file.type.startsWith('video/') ? 'video' : file.type.startsWith('image/') ? 'image' : null
  if (!kind) return uiStore.addToast('Please choose a photo or video.', 'error')
  if (file.size > MEDIA_LIMITS[kind]) {
    return uiStore.addToast(`${kind === 'video' ? 'Videos' : 'Photos'} can be up to ${formatSize(MEDIA_LIMITS[kind])}.`, 'error')
  }
  const ext = kind === 'video' ? VIDEO_EXT[file.type] || 'mp4' : (file.type.split('/')[1] || 'jpg').replace('jpeg', 'jpg')
  uploadProgress.value = 0
  try {
    const blob = await upload(`chat/${kind}-${Date.now()}.${ext}`, file, {
      access: 'public',
      handleUploadUrl: '/api/media/upload',
      headers: authHeaders(),
      onUploadProgress: ({ percentage }) => { uploadProgress.value = Math.round(percentage) },
    })
    const sent = await store.sendMessage(editingMsg.value ? '' : inputMessage.value,
      { name: file.name.slice(0, 240) || kind, size: formatSize(file.size), url: blob.url, kind }, replyingTo.value?.id)
    if (!sent) return
    cancelCompose()
    nextTick(() => scrollToBottom())
  } catch {
    uiStore.addToast('Upload failed. Please try again.', 'error')
  } finally {
    uploadProgress.value = null
  }
}

function backToList() {
  mobileView.value = 'list'
}

// Lock-screen notifications: 'install' (iPhone Safari, needs Home Screen app), 'off', 'on' or 'unsupported'.
const pushState = ref('unsupported')
const pushBusy = ref(false)
async function refreshPushState() {
  if (needsHomeScreenInstall()) pushState.value = 'install'
  else if (!pushSupported()) pushState.value = 'unsupported'
  else pushState.value = (await pushEnabled()) ? 'on' : 'off'
}
async function turnOnPush() {
  pushBusy.value = true
  try {
    await enablePush()
    pushState.value = 'on'
    uiStore.addToast('Notifications are on 🔔', 'success')
  } catch (error) {
    uiStore.addToast(error.message || 'Could not turn on notifications.', 'error')
  } finally {
    pushBusy.value = false
  }
}

// Tapping the person in the chat header opens their profile.
const otherProfilePath = computed(() => {
  const otherId = store.activeChat?.participantIds?.find(id => id !== postStore.currentUser?.id)
  return otherId ? `/profile/${otherId}` : '/profile'
})

const route = useRoute()
let refreshTimer
let refreshInProgress = false
let disposed = false
async function refreshChats() {
  if (document.hidden || refreshInProgress || disposed) return
  refreshInProgress = true
  try {
    await store.fetchConversations()
  } finally {
    refreshInProgress = false
  }
}
onMounted(async () => {
  refreshPushState()
  await Promise.all([store.fetchConversations(), store.fetchMembers()])
  // Opened from a notification: jump straight into that conversation.
  const fromNotification = Number(route.query.c)
  if (store.conversations.some(c => c.id === fromNotification)) {
    store.activeChatId = fromNotification
    mobileView.value = 'thread'
  }
  if (store.activeChatId) await store.setActiveChat(store.activeChatId)
  scrollToBottom()
  if (disposed) return
  refreshTimer = setInterval(refreshChats, 2000)
  document.addEventListener('visibilitychange', refreshChats)
  window.addEventListener('focus', refreshChats)
})
onUnmounted(() => {
  disposed = true
  clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', refreshChats)
  window.removeEventListener('focus', refreshChats)
})

// iOS Safari keeps the page full height when the keyboard opens and scrolls everything up instead.
// Pin the app to the visible area (visualViewport) so the header and input stay put above the keyboard.
const root = document.documentElement
function syncViewport() {
  const vv = window.visualViewport
  if (!vv) return
  root.style.setProperty('--vv-height', vv.height + 'px')
  root.style.setProperty('--vv-top', vv.offsetTop + 'px')
  const keyboardOpen = window.innerHeight - vv.height > 120
  if (keyboardOpen && !root.classList.contains('keyboard-open')) nextTick(scrollToBottom)
  root.classList.toggle('keyboard-open', keyboardOpen)
}
// Messenger-style: on phones an open conversation takes the whole screen (back arrow + name on top).
watchEffect(() => root.classList.toggle('chat-thread-open', mobileView.value === 'thread' && Boolean(store.activeChat)))
onMounted(() => {
  root.classList.add('chat-locked')
  syncViewport()
  window.visualViewport?.addEventListener('resize', syncViewport)
  window.visualViewport?.addEventListener('scroll', syncViewport)
})
onUnmounted(() => {
  window.visualViewport?.removeEventListener('resize', syncViewport)
  window.visualViewport?.removeEventListener('scroll', syncViewport)
  root.classList.remove('chat-locked', 'keyboard-open', 'chat-thread-open')
  root.style.removeProperty('--vv-height')
  root.style.removeProperty('--vv-top')
})
</script>

<template>
  <div class="messages-layout animate-fade-in">
    <div class="chat-wrapper">

      <!-- Left Sidebar -->
      <div class="chat-sidebar" :class="{ 'hidden-mobile': mobileView === 'thread' }">
        <div class="sidebar-header">
          <h2 class="sidebar-title">Messages</h2>
          <div class="new-chat-row">
            <select v-model="selectedMember" aria-label="Choose a member" class="member-select"
              :disabled="availableMembers.length === 0">
              <option value="">{{ availableMembers.length ? 'Choose a member' : 'No other members yet' }}</option>
              <option v-for="member in availableMembers" :key="member.id" :value="member.id">{{ member.name }}</option>
            </select>
            <button class="new-chat-btn" :disabled="!selectedMember" @click="startChat">New chat</button>
          </div>
          <button v-if="pushState === 'off'" class="push-banner" :disabled="pushBusy" @click="turnOnPush">
            🔔 {{ pushBusy ? 'Turning on…' : 'Turn on message notifications' }}
          </button>
          <p v-else-if="pushState === 'install'" class="push-banner push-hint">
            🔔 To get message notifications on iPhone: tap <strong>Share</strong> →
            <strong>Add to Home Screen</strong>, then open Bcommunity from your Home Screen.
          </p>
        </div>

        <div class="search-container">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="Search conversations..." class="search-input" />
        </div>

        <div class="conversation-list">
          <div v-if="filteredConversations.length === 0" class="no-results-msg">
            <template v-if="searchQuery">No conversations found for "{{ searchQuery }}"</template>
            <template v-else>No conversations yet. Choose a member above to start one.</template>
          </div>
          <div
            v-for="chat in filteredConversations"
            :key="chat.id"
            :class="['conversation-item', { active: chat.id === store.activeChatId }]"
            @click="selectChat(chat.id)"
          >
            <div class="avatar-wrapper">
              <img :src="chat.avatar" :alt="chat.name" class="conv-avatar" />
              <span class="online-dot"></span>
            </div>
            <div class="chat-summary">
              <div class="chat-top">
                <span class="chat-name">{{ chat.name }}</span>
                <span class="chat-time">{{ chatTime(chat.time) }}</span>
              </div>
              <div class="chat-bottom">
                <span class="chat-preview">{{ chat.lastMessage }}</span>
                <span v-if="chat.unread > 0" class="unread-badge">{{ chat.unread }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Thread -->
      <div class="chat-thread" v-if="store.activeChat" :class="{ 'hidden-mobile': mobileView === 'list' }">
        <!-- Header -->
        <div class="thread-header">
          <div class="thread-user-info">
            <button class="back-btn-mobile" @click="backToList">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
              </svg>
            </button>
            <RouterLink :to="otherProfilePath" class="thread-profile-link">
              <div class="avatar-wrapper-sm">
                <img :src="store.activeChat.avatar" alt="Avatar" class="thread-avatar" />
                <span class="online-dot"></span>
              </div>
              <div class="thread-details">
                <span class="thread-name">{{ store.activeChat.name }}</span>
                <span class="thread-status">
                  <span class="status-dot"></span>
                  Community member
                </span>
              </div>
            </RouterLink>
          </div>
          <div class="thread-actions">
            <button class="action-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <circle cx="12" cy="12" r="1"></circle>
                <circle cx="19" cy="12" r="1"></circle>
                <circle cx="5" cy="12" r="1"></circle>
              </svg>
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div class="thread-messages" ref="chatContainer">
          <div
            v-for="msg in store.activeChat.messages"
            :key="msg.id"
            :class="['message-group', msg.senderId === 'me' ? 'me' : 'them']"
          >
            <!-- Them -->
            <template v-if="msg.senderId !== 'me'">
              <div class="message-row">
                <img :src="store.activeChat.avatar" alt="Avatar" class="msg-avatar" />
                <div>
                  <div v-if="msg.replyTo" class="reply-quote">↩︎ {{ msg.replyTo.senderName }}: {{ replyPreview(msg.replyTo) }}</div>
                  <div class="pressable" @contextmenu.prevent="openActions(msg)" @touchstart.passive="pressStart(msg)"
                    @touchend="pressEnd" @touchmove.passive="pressEnd" @touchcancel="pressEnd">
                    <img v-if="msg.attachment?.kind === 'image'" :src="msg.attachment.url" :alt="msg.attachment.name"
                      class="chat-media" loading="lazy" @click="openMedia(msg.attachment.url)" />
                    <video v-else-if="msg.attachment?.kind === 'video'" :src="msg.attachment.url" class="chat-media"
                      controls playsinline preload="metadata"></video>
                    <div v-if="msg.text" class="bubble bubble-them">{{ msg.text }}</div>
                  </div>
                  <div v-if="msg.reactions?.length" class="reaction-row">
                    <button v-for="r in msg.reactions" :key="r.emoji" class="reaction-chip" :class="{ mine: r.mine }"
                      @click="react(msg, r.emoji)">{{ r.emoji }}<span v-if="r.count > 1">{{ r.count }}</span></button>
                  </div>
                  <span class="msg-time">{{ chatTime(msg.time) }}<template v-if="msg.edited"> · Edited</template></span>
                </div>
              </div>
            </template>

            <!-- Me -->
            <template v-else>
              <div class="message-row-me">
                <div>
                  <div v-if="msg.replyTo" class="reply-quote reply-quote-me">↩︎ {{ msg.replyTo.senderName }}: {{ replyPreview(msg.replyTo) }}</div>
                  <div class="pressable" @contextmenu.prevent="openActions(msg)" @touchstart.passive="pressStart(msg)"
                    @touchend="pressEnd" @touchmove.passive="pressEnd" @touchcancel="pressEnd">
                  <img v-if="msg.attachment?.kind === 'image'" :src="msg.attachment.url" :alt="msg.attachment.name"
                    class="chat-media chat-media-me" loading="lazy" @click="openMedia(msg.attachment.url)" />
                  <video v-else-if="msg.attachment?.kind === 'video'" :src="msg.attachment.url" class="chat-media chat-media-me"
                    controls playsinline preload="metadata"></video>
                  <div v-if="msg.text || (msg.attachment && !msg.attachment.url)" class="bubble bubble-me">
                    {{ msg.text }}
                    <div v-if="msg.attachment && !msg.attachment.url" class="attachment-card">
                      <div class="attachment-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                        </svg>
                      </div>
                      <div class="attachment-info">
                        <span class="attachment-name">{{ msg.attachment.name }}</span>
                        <span class="attachment-size">{{ msg.attachment.size }}</span>
                      </div>
                    </div>
                  </div>
                  </div>
                  <div v-if="msg.reactions?.length" class="reaction-row reaction-row-me">
                    <button v-for="r in msg.reactions" :key="r.emoji" class="reaction-chip" :class="{ mine: r.mine }"
                      @click="react(msg, r.emoji)">{{ r.emoji }}<span v-if="r.count > 1">{{ r.count }}</span></button>
                  </div>
                  <div class="msg-time-me">
                    <template v-if="msg.edited">Edited · </template>{{ chatTime(msg.time) }}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="12" height="12">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Replying / editing banner -->
        <div v-if="replyingTo || editingMsg" class="compose-banner">
          <div class="compose-banner-text">
            <strong>{{ editingMsg ? '✏️ Editing message' : '↩︎ Replying to ' + (replyingTo.senderId === 'me' ? 'yourself' : store.activeChat.name) }}</strong>
            <span>{{ replyPreview(editingMsg || replyingTo) }}</span>
          </div>
          <button class="compose-cancel" aria-label="Cancel" @click="cancelCompose">✕</button>
        </div>

        <!-- Emoji picker -->
        <div v-if="showEmojiPicker" class="emoji-panel" role="listbox" aria-label="Emoji">
          <button v-for="e in EMOJIS" :key="e" class="emoji-cell" @click="insertEmoji(e)">{{ e }}</button>
        </div>

        <!-- Input -->
        <div class="thread-input">
          <input ref="fileInput" type="file" accept="image/*,video/*" hidden @change="handleFile" />
          <button class="tool-btn" title="Send photo or video" aria-label="Send photo or video"
            :disabled="uploadProgress !== null" @click="fileInput.click()">
            <span v-if="uploadProgress !== null" class="upload-progress">{{ uploadProgress }}%</span>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </button>
          <button class="tool-btn emoji-btn" :class="{ active: showEmojiPicker }" title="Emoji" aria-label="Emoji"
            @click="showEmojiPicker = !showEmojiPicker">😊</button>
          <div class="input-wrap">
            <input
              ref="messageInput"
              type="text"
              v-model="inputMessage"
              placeholder="Type a message..."
              class="chat-input"
              @keyup.enter="handleSend"
            />
          </div>
          <button class="send-btn" @click="handleSend" :class="{ active: isTyping }">
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div class="empty-state" v-else>
        <div class="empty-icon">💬</div>
        <h3>Your Messages</h3>
        <p>Select a conversation to start chatting</p>
      </div>

      <!-- Press-and-hold menu: reactions + Reply / Copy / Edit / Delete -->
      <Teleport to="body">
        <div v-if="actionMsg" class="msg-actions-overlay" @click.self="closeActions">
          <div class="msg-actions" :class="{ mine: actionMsg.senderId === 'me' }">
            <div class="reaction-bar">
              <button v-for="e in REACTIONS" :key="e" class="reaction-option"
                :class="{ picked: actionMsg.reactions?.some(r => r.mine && r.emoji === e) }"
                :aria-label="'React ' + e" @click="react(actionMsg, e)">{{ e }}</button>
              <button class="reaction-option more" aria-label="More reactions"
                @click="reactionPickerOpen = !reactionPickerOpen">＋</button>
            </div>
            <div v-if="reactionPickerOpen" class="emoji-panel reaction-more">
              <button v-for="e in EMOJIS" :key="e" class="emoji-cell" @click="react(actionMsg, e)">{{ e }}</button>
            </div>
            <div class="action-preview" :class="actionMsg.senderId === 'me' ? 'bubble bubble-me' : 'bubble bubble-them'">
              {{ replyPreview(actionMsg) }}
            </div>
            <div class="action-menu" role="menu">
              <button v-if="actionMsg.senderId === 'me' && actionMsg.type === 'text'" role="menuitem" @click="startEdit(actionMsg)">
                Edit <span>✏️</span>
              </button>
              <button role="menuitem" @click="startReply(actionMsg)">Reply <span>↩︎</span></button>
              <button v-if="actionMsg.text" role="menuitem" @click="copyMessage(actionMsg)">Copy <span>📋</span></button>
              <button v-if="actionMsg.senderId === 'me'" role="menuitem" class="danger" @click="removeMessage(actionMsg)">
                Delete <span>🗑️</span>
              </button>
            </div>
          </div>
        </div>
      </Teleport>

    </div>
  </div>
</template>

<style scoped>
.messages-layout {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem 1.5rem 1rem;
  /* Fill exactly what the navbar leaves; dvh tracks iOS Safari's visible area. */
  height: calc(100vh - var(--navbar-height, 72px) - 2rem);
  height: calc(100dvh - var(--navbar-height, 72px) - 2rem);
  display: flex;
}

.chat-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
  background: #ffffff;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

/* ─── Sidebar ─── */
.chat-sidebar {
  width: 320px;
  flex-shrink: 0;
  border-right: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.sidebar-header {
  padding: 1.5rem 1.25rem 0.75rem;
}

.sidebar-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
}

.new-chat-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.push-banner {
  display: block;
  width: 100%;
  margin-top: 0.75rem;
  padding: 0.65rem 0.85rem;
  border: 1px solid #ddd6fe;
  border-radius: 12px;
  background: #f5f3ff;
  color: #5b21b6;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  text-align: left;
  line-height: 1.4;
  cursor: pointer;
}

.push-banner:disabled { opacity: 0.6; cursor: wait; }

.push-hint {
  font-weight: 500;
  cursor: default;
}

.member-select {
  flex: 1;
  min-width: 0;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.6rem 0.75rem;
  font-family: inherit;
  font-size: 0.85rem;
  color: #1a1a1a;
  outline: none;
  cursor: pointer;
}

.member-select:focus {
  border-color: #7c3aed;
  background: #fff;
}

.member-select:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.new-chat-btn {
  flex-shrink: 0;
  border: none;
  border-radius: 12px;
  padding: 0.6rem 1rem;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  cursor: pointer;
  transition: opacity 0.2s;
}

.new-chat-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.search-container {
  padding: 0 1rem 1rem;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 1.85rem;
  top: 50%;
  transform: translateY(-50%);
  width: 15px;
  height: 15px;
  color: #94a3b8;
}

.search-input {
  width: 100%;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.65rem 1rem 0.65rem 2.2rem;
  font-family: inherit;
  font-size: 0.85rem;
  color: #1a1a1a;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #7c3aed;
  background: #fff;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.75rem 1rem;
  scrollbar-width: none;
}
.conversation-list::-webkit-scrollbar { display: none; }

.no-results-msg {
  text-align: center;
  padding: 2rem 1rem;
  color: #94a3b8;
  font-size: 0.9rem;
}

.conversation-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 0.75rem;
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.15s;
  align-items: center;
}

.conversation-item:hover { background: #f8fafc; }
.conversation-item.active { background: #f5f3ff; }

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.conv-avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  object-fit: cover;
}

.online-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 11px;
  height: 11px;
  background: #10b981;
  border-radius: 50%;
  border: 2px solid #fff;
}

.chat-summary {
  flex: 1;
  min-width: 0;
}

.chat-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.chat-name {
  font-weight: 700;
  font-size: 0.88rem;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-time {
  font-size: 0.7rem;
  color: #94a3b8;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.chat-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-preview {
  font-size: 0.8rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-badge {
  background: #7c3aed;
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

/* ─── Thread ─── */
.chat-thread {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  min-width: 0;
}

.thread-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #ffffff;
  border-bottom: 1px solid #f1f5f9;
}

.thread-user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.thread-profile-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: inherit;
  text-decoration: none;
}

.back-btn-mobile {
  display: none;
  background: none;
  border: none;
  padding: 0.2rem;
  margin-left: -0.2rem;
  color: #64748b;
  cursor: pointer;
}

.avatar-wrapper-sm {
  position: relative;
  flex-shrink: 0;
}

.thread-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.thread-details {
  display: flex;
  flex-direction: column;
}

.thread-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: #0f172a;
}

.thread-status {
  font-size: 0.75rem;
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.status-dot {
  width: 7px;
  height: 7px;
  background: #10b981;
  border-radius: 50%;
}

.thread-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: #f1f5f9;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn:hover { background: #e2e8f0; }

/* ─── Messages ─── */
.thread-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  scrollbar-width: thin;
  scrollbar-color: #e2e8f0 transparent;
}

.message-group { display: flex; flex-direction: column; }
.message-group.them { align-self: flex-start; max-width: 72%; }
.message-group.me { align-self: flex-end; max-width: 72%; }

.message-row {
  display: flex;
  gap: 0.6rem;
  align-items: flex-end;
}

.message-row-me {
  display: flex;
  justify-content: flex-end;
}

.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  margin-bottom: 18px;
}

.bubble {
  padding: 0.7rem 1rem;
  border-radius: 18px;
  font-size: 0.9rem;
  line-height: 1.5;
  word-break: break-word;
}

.bubble-them {
  background: #ffffff;
  color: #1a1a1a;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
}

.bubble-me {
  background: #7c3aed;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.msg-time {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 4px;
  padding-left: 0.25rem;
  display: block;
}

.msg-time-me {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 4px;
  padding-right: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
}

/* ─── Press-and-hold, reactions, replies, emoji ─── */
.pressable {
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  user-select: none;
}

.reply-quote {
  font-size: 0.75rem;
  color: #64748b;
  background: #eef2f7;
  border-left: 3px solid #a78bfa;
  border-radius: 10px;
  padding: 0.35rem 0.6rem;
  margin-bottom: 3px;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reply-quote-me {
  margin-left: auto;
}

.reaction-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: -6px;
  position: relative;
  z-index: 1;
}

.reaction-row-me {
  justify-content: flex-end;
}

.reaction-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 1px 7px;
  font-size: 0.95rem;
  line-height: 1.4;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
  cursor: pointer;
}

.reaction-chip span {
  font-size: 0.72rem;
  font-weight: 700;
  color: #475569;
}

.reaction-chip.mine {
  background: #ede9fe;
  border-color: #c4b5fd;
}

.emoji-btn {
  font-size: 1.35rem;
  line-height: 1;
}

.emoji-btn.active {
  background: #ede9fe;
}

.compose-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 1rem;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
}

.compose-banner-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  font-size: 0.8rem;
}

.compose-banner-text strong {
  color: #6d28d9;
}

.compose-banner-text span {
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compose-cancel {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: #e2e8f0;
  color: #475569;
  cursor: pointer;
  flex-shrink: 0;
}

.emoji-panel {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 2px;
  max-height: 200px;
  overflow-y: auto;
  padding: 0.5rem;
  background: #ffffff;
  border-top: 1px solid #f1f5f9;
}

.emoji-cell {
  font-size: 1.5rem;
  line-height: 1;
  padding: 0.4rem 0;
  border: none;
  border-radius: 8px;
  background: none;
  cursor: pointer;
}

.emoji-cell:hover,
.emoji-cell:active {
  background: #f1f5f9;
}

.msg-actions-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.25);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  animation: overlayIn 0.15s ease-out;
}

@keyframes overlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.msg-actions {
  width: min(360px, 100%);
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  align-items: flex-start;
}

.msg-actions.mine {
  align-items: flex-end;
}

.reaction-bar {
  display: flex;
  gap: 2px;
  padding: 0.35rem 0.45rem;
  background: #ffffff;
  border-radius: 999px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
}

.reaction-option {
  width: 44px;
  height: 44px;
  font-size: 1.7rem;
  line-height: 1;
  border: none;
  border-radius: 50%;
  background: none;
  cursor: pointer;
  transition: transform 0.12s;
}

.reaction-option:active {
  transform: scale(1.25);
}

.reaction-option.picked {
  background: #ede9fe;
}

.reaction-option.more {
  font-size: 1.3rem;
  color: #475569;
  background: #f1f5f9;
}

.reaction-more {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
}

.action-preview {
  max-width: 85%;
  max-height: 30vh;
  overflow: hidden;
}

.action-menu {
  width: 230px;
  background: #f8fafc;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
}

.action-menu button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0.85rem 1rem;
  border: none;
  border-bottom: 1px solid #e2e8f0;
  background: none;
  font-family: inherit;
  font-size: 1rem;
  color: #111827;
  text-align: left;
  cursor: pointer;
}

.action-menu button:last-child {
  border-bottom: none;
}

.action-menu button:active {
  background: #e2e8f0;
}

.action-menu button.danger {
  color: #dc2626;
}

/* Photo / video messages */
.chat-media {
  display: block;
  max-width: min(280px, 65vw);
  max-height: 360px;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  background: #e2e8f0;
  object-fit: cover;
  cursor: pointer;
  margin-bottom: 4px;
}

.chat-media-me {
  margin-left: auto;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 4px;
}

video.chat-media { cursor: default; background: #000; }

.upload-progress {
  font-size: 0.7rem;
  font-weight: 700;
  color: #7c3aed;
}

/* Attachment */
.attachment-card {
  margin-top: 0.75rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 12px;
  padding: 0.6rem 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.attachment-icon {
  width: 34px;
  height: 34px;
  background: rgba(255,255,255,0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.attachment-info { display: flex; flex-direction: column; }
.attachment-name { font-weight: 600; font-size: 0.82rem; color: white; }
.attachment-size { font-size: 0.72rem; color: rgba(255,255,255,0.7); }

/* ─── Input ─── */
.thread-input {
  padding: 1rem 1.25rem;
  background: #ffffff;
  border-top: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tool-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, color 0.2s;
}

.tool-btn:hover {
  background: #f1f5f9;
  color: #7c3aed;
}

.input-wrap { flex: 1; }

.chat-input {
  width: 100%;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 24px;
  padding: 0.7rem 1.25rem;
  font-family: inherit;
  font-size: 0.9rem;
  color: #1a1a1a;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
}

.chat-input:focus {
  border-color: #7c3aed;
  background: #ffffff;
}

.chat-input::placeholder { color: #94a3b8; }

.send-btn {
  background: #e2e8f0;
  color: #94a3b8;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.send-btn.active {
  background: #7c3aed;
  color: #ffffff;
}

.send-btn.active:hover { background: #6d28d9; }

/* ─── Empty State ─── */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  background: #f8fafc;
  gap: 0.5rem;
}

.empty-icon { font-size: 3rem; margin-bottom: 0.5rem; }
.empty-state h3 { font-size: 1.1rem; color: #374151; margin: 0; }
.empty-state p { font-size: 0.88rem; margin: 0; }

@media (max-width: 768px) {
  .messages-layout {
    padding: 0;
    height: calc(100vh - var(--navbar-height, 64px));
    height: calc(100dvh - var(--navbar-height, 64px));
  }
  /* Keep the input above the iPhone home indicator, and at 16px so iOS doesn't zoom on focus. */
  .thread-input {
    padding: 0.6rem 0.6rem calc(0.6rem + env(safe-area-inset-bottom));
    gap: 0.35rem;
  }
  .chat-input,
  .search-input,
  .member-select {
    font-size: 16px;
  }
  /* Bigger touch targets for the chat buttons. */
  .tool-btn {
    width: 46px;
    height: 46px;
    color: #64748b;
  }
  .tool-btn svg {
    width: 26px;
    height: 26px;
  }
  .chat-input {
    min-height: 48px;
    padding: 0.7rem 1rem;
  }
  .send-btn {
    width: 50px;
    height: 50px;
  }
  .send-btn svg {
    width: 22px;
    height: 22px;
  }
  .chat-wrapper {
    border-radius: 0;
    border: none;
  }
  .chat-sidebar {
    width: 100%;
    border-right: none;
  }
  .chat-thread {
    width: 100%;
  }
  
  .chat-sidebar.hidden-mobile,
  .chat-thread.hidden-mobile {
    display: none !important;
  }
  
  .back-btn-mobile {
    display: block;
  }
}
</style>

<style>
/* While Messages is open on a phone, the app is pinned to the visible area above the keyboard
   (sizes come from visualViewport in syncViewport), so nothing scrolls or jumps when typing. */
@media (max-width: 768px) {
  html.chat-locked,
  html.chat-locked body {
    overflow: hidden;
    overscroll-behavior: none;
  }
  html.chat-locked .app-wrapper {
    position: fixed;
    left: 0;
    right: 0;
    top: var(--vv-top, 0px);
    height: var(--vv-height, 100dvh);
    min-height: 0;
  }
  html.chat-locked .main-content {
    min-height: 0;
  }
  html.chat-locked .messages-layout {
    flex: 1;
    min-height: 0;
    height: auto;
  }
  html.chat-thread-open .nav-container {
    display: none;
  }
  html.chat-thread-open .thread-header {
    padding: calc(0.6rem + env(safe-area-inset-top)) 0.75rem 0.6rem;
  }
  /* The home indicator is hidden behind the keyboard, so drop its extra padding. */
  html.keyboard-open .thread-input {
    padding-bottom: 0.6rem;
  }
}
</style>
