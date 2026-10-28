import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createPinia, setActivePinia } from 'pinia'
import { sharePost } from '../../src/utils/share.js'
import { usePostsStore } from '../../src/stores/posts.js'
import { useChatStore } from '../../src/stores/chat.js'
import { setToken } from '../../src/services/api.js'

const response = data => new Response(JSON.stringify({ data }))

test('sharing supports native share, clipboard, HTTP fallback, and manual copy', async () => {
  const originals = Object.fromEntries(['window', 'navigator', 'document'].map(key =>
    [key, Object.getOwnPropertyDescriptor(globalThis, key)]))
  let copied, prompted, removed = false
  const navigator = {}
  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: navigator })
  globalThis.window = { location: { origin: 'http://localhost:5173' }, prompt: (_, url) => { prompted = url } }
  globalThis.document = {
    body: { appendChild() {} },
    createElement: () => ({ style: {}, focus() {}, select() {}, setSelectionRange() {}, remove() { removed = true } }),
    execCommand: () => true,
  }
  try {
    navigator.share = async data => { copied = data.url }
    assert.equal(await sharePost({ id: 7 }), 'shared')
    assert.equal(copied, 'http://localhost:5173/post/7')
    navigator.share = async () => { throw { name: 'AbortError' } }
    assert.equal(await sharePost({ id: 7 }), null)
    navigator.share = async () => { throw { name: 'NotAllowedError' } }
    navigator.clipboard = { writeText: async url => { copied = url } }
    assert.equal(await sharePost({ id: 8 }), 'copied')
    assert.equal(copied, 'http://localhost:5173/post/8')
    delete navigator.clipboard
    assert.equal(await sharePost({ id: 7 }), 'copied')
    assert.equal(removed, true)
    document.execCommand = () => { throw new Error('Denied') }
    assert.equal(await sharePost({ id: 7 }), null)
    assert.equal(prompted, 'http://localhost:5173/post/7')
  } finally {
    for (const [key, descriptor] of Object.entries(originals)) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor)
      else delete globalThis[key]
    }
  }
})

test('like updates immediately, ignores duplicate taps, toggles back, and rolls back failures', async () => {
  const originalFetch = globalThis.fetch
  setActivePinia(createPinia())
  setToken('test')
  const store = usePostsStore()
  store.currentUser = { id: 1 }
  store.posts = [{ id: 7, likes: 0, likedBy: [] }]
  let finish, method
  globalThis.fetch = (_, options) => {
    method = options.method
    return new Promise(resolve => { finish = resolve })
  }
  try {
    const pending = store.likePost(7)
    assert.equal(store.isLiked(store.posts[0]), true)
    assert.equal(store.posts[0].likes, 1)
    assert.equal(await store.likePost(7), null)
    assert.equal(method, 'POST')
    finish(response({ id: 7, likes: 1, likedBy: [1] }))
    await pending
    const unlike = store.likePost(7)
    assert.equal(store.isLiked(store.posts[0]), false)
    assert.equal(method, 'DELETE')
    finish(response({ id: 7, likes: 0, likedBy: [] }))
    await unlike
    globalThis.fetch = async () => { throw new Error('Offline') }
    assert.equal(await store.likePost(7), null)
    assert.equal(store.isLiked(store.posts[0]), false)
    assert.equal(store.posts[0].likes, 0)
  } finally {
    globalThis.fetch = originalFetch
    setToken('')
  }
})

test('incoming messages move the chat to the top without switching the open conversation', async () => {
  const originalFetch = globalThis.fetch
  setActivePinia(createPinia())
  setToken('test')
  const store = useChatStore()
  let rows = [{ id: 1, time: '2026-10-28T09:00:00Z' }, { id: 2, time: '2026-10-28T10:00:00Z' }]
  globalThis.fetch = async () => response(rows)
  try {
    await store.fetchConversations()
    assert.deepEqual(store.conversations.map(c => c.id), [2, 1])
    store.activeChatId = 2
    rows = [{ id: 2, time: '2026-10-28T10:00:00Z' }, { id: 1, time: '2026-10-28T11:00:00Z', unread: 1 }]
    await store.fetchConversations()
    assert.deepEqual(store.conversations.map(c => c.id), [1, 2])
    assert.equal(store.conversations[0].unread, 1)
    assert.equal(store.activeChatId, 2)
  } finally {
    globalThis.fetch = originalFetch
    setToken('')
  }
})
