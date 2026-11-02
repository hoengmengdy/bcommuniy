const STORAGE_KEY = 'bcommunity-incoming-message-voice'
const AUDIO_URL = '/audio/incoming-message-km.mp3'

let player

function getPlayer() {
  if (!player && typeof Audio !== 'undefined') {
    player = new Audio(AUDIO_URL)
    player.preload = 'auto'
  }
  return player
}

export function incomingMessageVoiceSupported() {
  return Boolean(getPlayer()?.canPlayType('audio/mpeg').trim())
}

export function incomingMessageVoiceEnabled() {
  return globalThis.localStorage?.getItem(STORAGE_KEY) === 'true'
}

export async function enableIncomingMessageVoice() {
  const audio = getPlayer()
  if (!audio || !incomingMessageVoiceSupported()) {
    throw new Error('ឧបករណ៍នេះមិនគាំទ្រការចាក់សំឡេងនេះទេ។')
  }

  audio.currentTime = 0
  await audio.play()
  globalThis.localStorage.setItem(STORAGE_KEY, 'true')
  return true
}

export function disableIncomingMessageVoice() {
  globalThis.localStorage.setItem(STORAGE_KEY, 'false')
  getPlayer()?.pause()
}

export async function playIncomingMessageVoice() {
  if (!incomingMessageVoiceEnabled()) return false

  const audio = getPlayer()
  if (!audio || !incomingMessageVoiceSupported()) {
    disableIncomingMessageVoice()
    globalThis.dispatchEvent(new Event('bcommunity-incoming-voice-disabled'))
    throw new Error('ឧបករណ៍នេះមិនគាំទ្រការចាក់សំឡេងនេះទេ។')
  }

  try {
    audio.currentTime = 0
    await audio.play()
    return true
  } catch (error) {
    disableIncomingMessageVoice()
    globalThis.dispatchEvent(new Event('bcommunity-incoming-voice-disabled'))
    throw error
  }
}

export function snapshotChatMessages(conversations) {
  const snapshot = new Map()
  for (const conversation of conversations) {
    for (const message of conversation.messages || []) {
      snapshot.set(`${conversation.id}:${message.id}`, message)
    }
  }
  return snapshot
}

export function hasNewIncomingMessages(previous, current) {
  for (const [id, message] of current) {
    if (!previous.has(id) && message.senderId !== 'me') return true
  }
  return false
}
