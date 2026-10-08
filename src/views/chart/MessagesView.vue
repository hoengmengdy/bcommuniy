<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'

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
  if (inputMessage.value.trim()) {
    const sent = await store.sendMessage(inputMessage.value)
    if (!sent) return
    inputMessage.value = ''
    uiStore.addToast('Message sent', 'success')
    nextTick(() => scrollToBottom())
  }
}

async function selectChat(id) {
  if (!await store.setActiveChat(id)) return
  mobileView.value = 'thread'
  nextTick(() => scrollToBottom())
}

function backToList() {
  mobileView.value = 'list'
}

let refreshTimer
onMounted(async () => {
  await Promise.all([store.fetchConversations(), store.fetchMembers()])
  if (store.activeChatId) await store.setActiveChat(store.activeChatId)
  scrollToBottom()
  refreshTimer = setInterval(async () => {
    if (document.hidden) return
    await store.fetchConversations()
  }, 5000)
})
onUnmounted(() => clearInterval(refreshTimer))
</script>

<template>
  <div class="messages-layout animate-fade-in">
    <div class="chat-wrapper">

      <!-- Left Sidebar -->
      <div class="chat-sidebar" :class="{ 'hidden-mobile': mobileView === 'thread' }">
        <div class="sidebar-header">
          <h2 class="sidebar-title">Messages</h2>
          <select v-model="selectedMember" aria-label="Choose a member">
            <option value="">Choose a member</option>
            <option v-for="member in availableMembers" :key="member.id" :value="member.id">{{ member.name }}</option>
          </select>
          <button class="btn" :disabled="!selectedMember" @click="startChat">New chat</button>
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
            No conversations found for "{{ searchQuery }}"
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
                <span class="chat-time">{{ chat.time }}</span>
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
                  <div class="bubble bubble-them">{{ msg.text }}</div>
                  <span class="msg-time">{{ msg.time }}</span>
                </div>
              </div>
            </template>

            <!-- Me -->
            <template v-else>
              <div class="message-row-me">
                <div>
                  <div class="bubble bubble-me">
                    {{ msg.text }}
                    <div v-if="msg.attachment" class="attachment-card">
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
                  <div class="msg-time-me">
                    {{ msg.time }}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="12" height="12">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Input -->
        <div class="thread-input">
          <button class="tool-btn" title="Attach file">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </button>
          <button class="tool-btn" title="Send code snippet">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
          </button>
          <div class="input-wrap">
            <input
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

    </div>
  </div>
</template>

<style scoped>
.messages-layout {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem 1.5rem 1rem;
  height: calc(100vh - 72px);
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
    height: calc(100vh - 64px);
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
