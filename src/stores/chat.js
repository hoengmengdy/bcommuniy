import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, apiAction, apiList } from '../services/api.js'

export const useChatStore = defineStore('chat', () => {
  const activeChatId = ref(null)
  const conversations = ref([])
  const members = ref([])
  for (const event of ['bcommunity-session-expired', 'bcommunity-session-changed']) {
    globalThis.addEventListener?.(event, () => {
      conversations.value = []; members.value = []; activeChatId.value = null
    })
  }
  const activeChat = computed(() => conversations.value.find(c => c.id === activeChatId.value))
  const fetchConversations = () => apiAction(async () => {
    conversations.value = await apiList('/conversations')
    if (!conversations.value.some(c => c.id === activeChatId.value)) {
      activeChatId.value = conversations.value[0]?.id ?? null
    }
    return conversations.value
  })
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
  const sendMessage = text => apiAction(async () => {
    if (!activeChat.value || !text.trim()) return null
    const response = await api('/conversations/' + activeChatId.value + '/messages',
      { method: 'POST', body: { text: text.trim() } })
    await fetchConversations()
    return response.data
  })
  return { conversations, members, activeChatId, activeChat, fetchConversations, fetchMembers,
    setActiveChat, startConversation, sendMessage }
})
