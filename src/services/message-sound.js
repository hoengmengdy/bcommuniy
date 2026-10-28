import { ref } from 'vue'

const preferenceKey = 'bcommunity-message-sound'
function savedPreference() {
  try { return globalThis.localStorage?.getItem(preferenceKey) === 'on' }
  catch { return false }
}
export const messageSoundEnabled = ref(savedPreference())
let context

// Create/resume from a click or key press to respect mobile autoplay restrictions.
export async function unlockMessageSound() {
  if (!messageSoundEnabled.value) return false
  try {
    const AudioContext = globalThis.AudioContext || globalThis.webkitAudioContext
    if (!AudioContext) return false
    if (!context || context.state === 'closed') context = new AudioContext()
    if (context.state !== 'running') await context.resume()
    return context.state === 'running'
  } catch { return false }
}

export function setMessageSoundEnabled(enabled) {
  messageSoundEnabled.value = enabled
  try { globalThis.localStorage?.setItem(preferenceKey, enabled ? 'on' : 'off') }
  catch { /* Sound still works when the browser blocks storage. */ }
}

export function playMessageSound() {
  if (!messageSoundEnabled.value || context?.state !== 'running') return false
  try {
    const start = context.currentTime
    // A soft two-note chime, generated locally without downloading audio.
    for (const [offset, frequency] of [[0, 740], [0.13, 988]]) {
      const oscillator = context.createOscillator()
      const gain = context.createGain()
      oscillator.type = 'sine'
      oscillator.frequency.value = frequency
      gain.gain.setValueAtTime(0, start + offset)
      gain.gain.linearRampToValueAtTime(0.12, start + offset + 0.015)
      gain.gain.exponentialRampToValueAtTime(0.001, start + offset + 0.22)
      oscillator.connect(gain)
      gain.connect(context.destination)
      oscillator.onended = () => { oscillator.disconnect(); gain.disconnect() }
      oscillator.start(start + offset)
      oscillator.stop(start + offset + 0.24)
    }
    return true
  } catch { return false }
}

// Keep a high-water mark so polling, read receipts and edits cannot repeat a chime.
export function createIncomingMessageTracker() {
  let latestId = null
  return rows => {
    const previous = latestId
    let incoming = false
    let newest = latestId ?? 0
    for (const chat of rows) {
      for (const message of chat.messages || []) {
        newest = Math.max(newest, message.id)
        if (previous !== null && message.id > previous && message.senderId !== 'me'
            && message.status !== 'read') incoming = true
      }
    }
    latestId = newest
    return incoming
  }
}
