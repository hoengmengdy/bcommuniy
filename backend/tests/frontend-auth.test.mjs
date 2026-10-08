import assert from 'node:assert/strict'
import { test } from 'node:test'
import { setTimeout as delay } from 'node:timers/promises'
import { createPinia, setActivePinia } from 'pinia'

const values = new Map()
Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: {
  getItem: key => values.get(key) || null,
  setItem: (key, value) => values.set(key, value),
  removeItem: key => values.delete(key),
} })
const { api, expireSession, hasToken, setToken, setSessionExpiry } = await import('../../src/services/api.js')
const { usePostsStore } = await import('../../src/stores/posts.js')
const { useChatStore } = await import('../../src/stores/chat.js')
const { useKnowledgeStore } = await import('../../src/stores/knowledge.js')
const { useOpportunitiesStore } = await import('../../src/stores/opportunities.js')
const { useProjectsStore } = await import('../../src/stores/projects.js')
const { useUsersStore } = await import('../../src/stores/users.js')
const originalFetch = globalThis.fetch
const user = { id: 1, name: 'Member', isAdmin: false }
const response = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json' },
})
function setup() {
  const target = new EventTarget()
  globalThis.addEventListener = target.addEventListener.bind(target)
  globalThis.dispatchEvent = target.dispatchEvent.bind(target)
  setToken('')
  setActivePinia(createPinia())
  return usePostsStore()
}
function seedProtectedStores(store) {
  const chat = useChatStore(), knowledge = useKnowledgeStore(), opportunities = useOpportunitiesStore()
  const projects = useProjectsStore(), users = useUsersStore()
  store.posts = [{ id: 1 }]
  chat.conversations = [{ id: 1 }]; chat.members = [{ id: 1 }]; chat.activeChatId = 1
  knowledge.questions = [{ id: 1 }]; knowledge.articles = [{ id: 1 }]
  opportunities.jobs = [{ id: 1 }]; opportunities.events = [{ id: 1 }]
  projects.members = [{ id: 1 }]; projects.tasks = [{ id: 1 }]
  users.users = [{ id: 1 }]
  return () => {
    assert.equal(store.currentUser, null)
    for (const rows of [store.posts, chat.conversations, chat.members, knowledge.questions,
      knowledge.articles, opportunities.jobs, opportunities.events, projects.members, projects.tasks, users.users]) {
      assert.deepEqual(rows, [])
    }
    assert.equal(chat.activeChatId, null)
    assert.equal(hasToken(), false)
  }
}

test('authentication lifecycle and protected caches', async t => {
  try {
    await t.test('visitors cannot initialize content or call protected APIs', async () => {
      const store = setup()
      globalThis.fetch = () => { throw new Error('Visitors must not fetch protected content') }
      assert.equal(await store.initialize(), false)
      await assert.rejects(api('/posts'), { status: 401 })
      assert.equal(store.currentUser, null)
      assert.deepEqual(store.posts, [])
    })
    await t.test('public registration is unavailable to frontend visitors', async () => {
      const store = setup()
      globalThis.fetch = () => { throw new Error('Removed signup must not call the server') }
      assert.equal(store.registerAccount, undefined)
      await assert.rejects(api('/auth/register', { method: 'POST', body: {} }), { status: 401 })
      assert.equal(store.currentUser, null)
      assert.equal(hasToken(), false)
    })
    await t.test('login and a fresh store restore the server-verified session', async () => {
      const store = setup()
      const expiresAt = Date.now() + 60000
      const requests = []
      globalThis.fetch = async (url, options) => {
        requests.push({ url, options })
        if (url === '/api/auth/login') return response({ data: { user, token: 'valid', expiresAt } })
        assert.equal(options.headers.Authorization, 'Bearer valid')
        if (url === '/api/auth/me') return response({ data: user, meta: { expiresAt } })
        return response({ data: [{ id: 9 }] })
      }
      await store.authenticate({ email: 'member@example.com', password: 'test-password' })
      assert.equal(store.currentUser.id, 1)
      assert.equal(values.get('bcommunity-token-expires-at'), String(expiresAt))
      setActivePinia(createPinia())
      const restored = usePostsStore()
      assert.equal(await restored.initialize(), true)
      assert.equal(restored.currentUser.id, 1)
      assert.deepEqual(restored.posts, [{ id: 9 }])
      assert.ok(requests.some(request => request.url === '/api/auth/me'))
    })
    await t.test('logout removes access and every cache before the server responds', async () => {
      const store = setup()
      setToken('valid', Date.now() + 60000)
      store.currentUser = user
      const assertCleared = seedProtectedStores(store)
      let finishLogout
      globalThis.fetch = () => new Promise(resolve => { finishLogout = resolve })
      const pending = store.logout()
      assertCleared()
      finishLogout(response({ data: { message: 'Signed out' } }))
      assert.equal(await pending, true)
    })
    await t.test('failed logout still blocks access', async () => {
      const store = setup()
      setToken('valid', Date.now() + 60000)
      store.currentUser = user
      const assertCleared = seedProtectedStores(store)
      globalThis.fetch = async () => { throw new Error('Offline') }
      assert.equal(await store.logout(), null)
      assertCleared()
    })
    await t.test('idle expiry removes content without another API request', async () => {
      const store = setup()
      setToken('valid', Date.now() + 30)
      store.currentUser = user
      const assertCleared = seedProtectedStores(store)
      await delay(60)
      assertCleared()
    })
    await t.test('expired persisted sessions are rejected synchronously', () => {
      const store = setup()
      setToken('valid', Date.now() + 60000)
      store.currentUser = user
      setSessionExpiry(Date.now() - 1)
      assert.equal(hasToken(), false)
      assert.equal(store.currentUser, null)
    })
    await t.test('a non-JSON 401 still clears protected data', async () => {
      const store = setup()
      setToken('valid', Date.now() + 60000)
      store.currentUser = user
      const assertCleared = seedProtectedStores(store)
      globalThis.fetch = async () => new Response('Unauthorized', { status: 401 })
      await assert.rejects(api('/posts'))
      assertCleared()
    })
    await t.test('late requests cannot refill caches after logout', async () => {
      const store = setup()
      setToken('old', Date.now() + 60000)
      store.currentUser = user
      let finishRequest
      globalThis.fetch = () => new Promise(resolve => { finishRequest = resolve })
      const pending = store.fetchPosts()
      expireSession()
      finishRequest(response({ data: [{ id: 99, content: 'private' }] }))
      await assert.rejects(pending, { code: 'SESSION_CHANGED' })
      assert.deepEqual(store.posts, [])
    })
    await t.test('an old unauthorized response cannot sign out a newer session', async () => {
      const store = setup()
      setToken('old', Date.now() + 60000)
      let finishRequest
      globalThis.fetch = () => new Promise(resolve => { finishRequest = resolve })
      const pending = api('/posts')
      setToken('new', Date.now() + 60000)
      store.currentUser = { ...user, id: 2 }
      finishRequest(response({ error: { message: 'Expired' } }, 401))
      await assert.rejects(pending, { code: 'SESSION_CHANGED' })
      assert.equal(hasToken(), true)
      assert.equal(store.currentUser.id, 2)
    })
    await t.test('unverifiable sessions fail closed', async () => {
      const store = setup()
      setToken('valid', Date.now() + 60000)
      store.currentUser = user
      globalThis.fetch = async () => { throw new Error('Offline') }
      assert.equal(await store.validateSession(), false)
      assert.equal(store.currentUser, null)
      assert.equal(hasToken(), false)
    })
  } finally {
    expireSession()
    globalThis.fetch = originalFetch
  }
})
