import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import { createIncomingMessageTracker, messageSoundEnabled, setMessageSoundEnabled,
  unlockMessageSound, playMessageSound } from '../../src/services/message-sound.js'

const message = (id, senderId = 2, status = 'sent') => ({ id, senderId, status })

test('sound detects only newly received unread messages, once per refresh batch', () => {
  const detect = createIncomingMessageTracker()
  assert.equal(detect([{ messages: [message(10)] }]), false, 'old inbox is silent')
  assert.equal(detect([{ messages: [message(10), message(11, 'me')] }]), false)
  assert.equal(detect([{ messages: [message(10), message(12)] }]), true)
  assert.equal(detect([{ messages: [message(10), message(12)] }]), false, 'polls do not repeat')
  assert.equal(detect([{ messages: [message(12, 2, 'read')] }]), false)
  assert.equal(detect([{ messages: [message(13, 2, 'read')] }]), false)
  assert.equal(detect([{ messages: [message(13, 2, 'read'), message(14), message(15)] }]), true)
  assert.equal(detect([]), false)
  assert.equal(detect([{ messages: [message(10)] }]), false, 'deleting messages cannot rewind the tracker')
  assert.equal(createIncomingMessageTracker()([{ messages: [message(100)] }]), false, 'new sessions start silently')
  const empty = createIncomingMessageTracker()
  assert.equal(empty([]), false)
  assert.equal(empty([{ messages: [message(1)] }]), true, 'first incoming chat after an empty inbox')
})

test('chime requires enabling and unlocking audio, and mute persists', async () => {
  const originalAudio = globalThis.AudioContext
  const originalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage')
  const preferences = new Map()
  const notes = []
  let audio
  globalThis.AudioContext = class {
    constructor() { audio = this; this.state = 'suspended'; this.currentTime = 1 }
    async resume() { this.state = 'running' }
    createOscillator() {
      const node = { frequency: {}, connect() {}, disconnect() {}, start() {}, stop() {} }
      notes.push(node)
      return node
    }
    createGain() { return { gain: { setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {}, disconnect() {} } }
  }
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: {
    setItem: (key, value) => preferences.set(key, value),
  } })
  try {
    setMessageSoundEnabled(false)
    assert.equal(await unlockMessageSound(), false)
    assert.equal(playMessageSound(), false)
    setMessageSoundEnabled(true)
    assert.equal(playMessageSound(), false, 'cannot play before browser gesture')
    assert.equal(await unlockMessageSound(), true)
    assert.equal(playMessageSound(), true)
    assert.deepEqual(notes.map(n => n.frequency.value), [740, 988])
    audio.state = 'suspended'
    assert.equal(playMessageSound(), false, 'interrupted audio does not throw')
    assert.equal(await unlockMessageSound(), true, 'next gesture resumes interrupted audio')
    setMessageSoundEnabled(false)
    assert.equal(messageSoundEnabled.value, false)
    assert.equal(preferences.get('bcommunity-message-sound'), 'off')
    assert.equal(playMessageSound(), false)
  } finally {
    globalThis.AudioContext = originalAudio
    if (originalStorage) Object.defineProperty(globalThis, 'localStorage', originalStorage)
    else delete globalThis.localStorage
  }
})

test('foreground push avoids a second sound, while background pushes allow device sound', async () => {
  const code = await readFile(new URL('../../public/sw.js', import.meta.url), 'utf8')
  for (const [windows, silent] of [
    [[{ visibilityState: 'visible', focused: true }], true],
    [[{ visibilityState: 'hidden', focused: false }], false],
    [[], false],
  ]) {
    const events = {}
    let options, pending
    const self = {
      addEventListener: (name, handler) => { events[name] = handler },
      clients: { matchAll: async () => windows },
      registration: { showNotification: async (_, opts) => { options = opts } },
    }
    vm.runInNewContext(code, { self })
    events.push({ data: { json: () => ({ title: 'New message', body: 'Hello' }) }, waitUntil: promise => { pending = promise } })
    await pending
    assert.equal(options.silent, silent)
  }
})
