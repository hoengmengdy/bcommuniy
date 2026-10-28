import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, apiAction, apiList } from '../services/api.js'
import { createIncomingMessageTracker, playMessageSound } from '../services/message-sound.js'

export const useChatStore = defineStore('chat', () => {
  const activeChatId = ref(null)
  const conversations = ref([])
  const members = ref([])
  let detectIncoming = createIncomingMessageTracker()
  let latestFetch = 0
  for (const event of ['bcommunity-session-expired', 'bcommunity-session-changed']) {
    globalThis.addEventListener?.(event, () => {
      conversations.value = []; members.value = []; activeChatId.value = null
      detectIncoming = createIncomingMessageTracker()
      latestFetch++
    })
  }
  const activeChat = computed(() => conversations.value.find(c => c.id === activeChatId.value))
  const fetchConversations = ({ silent = false } = {}) => {
    const request = ++latestFetch
    const load = async () => {
      const rows = await apiList('/conversations')
      if (request !== latestFetch) return conversations.value
      const incoming = detectIncoming(rows)
      if (incoming && !globalThis.document?.hidden && (globalThis.document?.hasFocus?.() ?? true)) {
        playMessageSound()
      }
      conversations.value = rows.sort((a, b) =>
        (Date.parse(b.time) || 0) - (Date.parse(a.time) || 0) || b.id - a.id)
      if (!conversations.value.some(c => c.id === activeChatId.value)) {
        activeChatId.value = conversations.value[0]?.id ?? null
      }
      return conversations.value
    }
    return silent ? load().catch(() => null) : apiAction(load)
  }
  const fetchMembers = () => apiAction(async () => {
    members.value = await apiList('/members')
    return members.value
  })
  const setActiveChat = id => apiAction(async () => {
    await api('/conversations/' + id + '/read', { method: 'PUT' })
    const chat = (await api('/conversations/' + id)).data
    const index = conversations.value.findIndex(c => c.id === id)
    if (index >= 0) conversations.value[index] = chat
    activeChatId.value = id
    return chat
  })
  const startConversation = participantId => apiAction(async () => {
    const chat = (await api('/conversations', { method: 'POST', body: { participantId } })).data
    await fetchConversations()
    await setActiveChat(chat.id)
    return chat
  })
  // Swap one message in the open conversation for the server's updated copy (reactions, edits).
  const replaceMessage = updated => {
    const messages = activeChat.value?.messages
    const index = messages?.findIndex(m => m.id === updated.id) ?? -1
    if (index >= 0) messages[index] = updated
    return updated
  }
  const reactToMessage = (messageId, emoji) => apiAction(async () =>
    replaceMessage((await api('/messages/' + messageId + '/reaction', { method: 'PUT', body: { emoji } })).data))
  const editMessage = (messageId, text) => apiAction(async () =>
    replaceMessage((await api('/messages/' + messageId, { method: 'PUT', body: { text: text.trim() } })).data))
  const deleteMessage = messageId => apiAction(async () => {
    await api('/messages/' + messageId, { method: 'DELETE' })
    await fetchConversations()
    return true
  })
  const sendMessage = (text, attachment = null, replyToId = null) => apiAction(async () => {
    if (!activeChat.value || (!text.trim() && !attachment)) return null
    const body = { text: text.trim() }
    if (attachment) body.attachment = attachment
    if (replyToId) body.replyToId = replyToId
    const response = await api('/conversations/' + activeChatId.value + '/messages', { method: 'POST', body })
    await fetchConversations()
    return response.data
  })
  return { conversations, members, activeChatId, activeChat, fetchConversations, fetchMembers,
    setActiveChat, startConversation, sendMessage, reactToMessage, editMessage, deleteMessage }
})
