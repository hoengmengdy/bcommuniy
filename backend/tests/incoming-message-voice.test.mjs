import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
import {
  disableIncomingMessageVoice,
  enableIncomingMessageVoice,
  hasNewIncomingMessages,
  incomingMessageVoiceEnabled,
  incomingMessageVoiceSupported,
  playIncomingMessageVoice,
  snapshotChatMessages,
} from '../../src/services/incomingMessageVoice.js'

test('Khmer incoming-message recording is supported, user-tested, and disabled on playback failure', async () => {
  const originals = Object.fromEntries(['Audio', 'localStorage', 'dispatchEvent'].map(key =>
    [key, Object.getOwnPropertyDescriptor(globalThis, key)]))
  const settings = new Map()
  let failPlayback = false
  let player
  let disabledEvent = false
  class FakeAudio {
    constructor(url) {
      this.url = url
      player = this
    }
    canPlayType(type) { return type === 'audio/mpeg' ? 'probably' : '' }
    async play() {
      if (failPlayback) throw new Error('Playback blocked')
    }
    pause() {}
  }
  Object.defineProperty(globalThis, 'Audio', { configurable: true, value: FakeAudio })
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: {
    getItem: key => settings.get(key) ?? null,
    setItem: (key, value) => settings.set(key, value),
  } })
  Object.defineProperty(globalThis, 'dispatchEvent', { configurable: true, value: event => {
    if (event.type === 'bcommunity-incoming-voice-disabled') disabledEvent = true
  } })
  try {
    assert.equal(incomingMessageVoiceSupported(), true)
    assert.equal(player.url, '/audio/incoming-message-km.mp3')
    assert.equal(incomingMessageVoiceEnabled(), false)
    failPlayback = true
    await assert.rejects(enableIncomingMessageVoice(), /Playback blocked/)
    assert.equal(incomingMessageVoiceEnabled(), false)
    failPlayback = false
    await enableIncomingMessageVoice()
    assert.equal(incomingMessageVoiceEnabled(), true)
    await playIncomingMessageVoice()

    failPlayback = true
    await assert.rejects(playIncomingMessageVoice(), /Playback blocked/)
    assert.equal(incomingMessageVoiceEnabled(), false)
    assert.equal(disabledEvent, true)

    failPlayback = false
    await enableIncomingMessageVoice()
    disableIncomingMessageVoice()
    assert.equal(incomingMessageVoiceEnabled(), false)

    const transcript = await readFile(new URL('../../public/audio/incoming-message-km.vtt', import.meta.url), 'utf8')
    assert.match(transcript, /មានគេឆាតមក/)
  } finally {
    for (const [key, descriptor] of Object.entries(originals)) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor)
      else delete globalThis[key]
    }
  }
})

test('chat polling only treats newly seen messages from other people as incoming', () => {
  const before = snapshotChatMessages([{ id: 4, messages: [
    { id: 1, senderId: 'me' },
    { id: 2, senderId: 7 },
  ] }])
  const unchanged = snapshotChatMessages([{ id: 4, messages: [
    { id: 1, senderId: 'me' },
    { id: 2, senderId: 7 },
  ] }])
  const withOwnReply = snapshotChatMessages([{ id: 4, messages: [
    { id: 1, senderId: 'me' },
    { id: 2, senderId: 7 },
    { id: 3, senderId: 'me' },
  ] }])
  const withIncoming = snapshotChatMessages([{ id: 4, messages: [
    { id: 1, senderId: 'me' },
    { id: 2, senderId: 7 },
    { id: 3, senderId: 9 },
  ] }])

  assert.equal(hasNewIncomingMessages(before, unchanged), false)
  assert.equal(hasNewIncomingMessages(before, withOwnReply), false)
  assert.equal(hasNewIncomingMessages(before, withIncoming), true)
})
