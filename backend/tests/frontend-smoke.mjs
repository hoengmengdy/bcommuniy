// Run via npm run test:auth:browser for isolated servers and administrator-provisioned test accounts.
// Standalone runs need FRONTEND_ORIGIN, SMOKE_ADMIN_EMAIL, and SMOKE_ADMIN_PASSWORD.
import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { createPinia, setActivePinia } from 'pinia'

const origin = process.env.FRONTEND_ORIGIN || 'http://127.0.0.1:5173'
const values = new Map()
Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: {
  getItem: key => values.get(key) || null,
  setItem: (key, value) => values.set(key, value),
  removeItem: key => values.delete(key),
} })
const target = new EventTarget()
globalThis.addEventListener = target.addEventListener.bind(target)
globalThis.dispatchEvent = target.dispatchEvent.bind(target)
const originalFetch = globalThis.fetch.bind(globalThis)
globalThis.fetch = (url, options) => originalFetch(new URL(url, origin), options)
setActivePinia(createPinia())

const { usePostsStore } = await import('../../src/stores/posts.js')
const { useChatStore } = await import('../../src/stores/chat.js')
const { useProjectsStore } = await import('../../src/stores/projects.js')
const { useKnowledgeStore } = await import('../../src/stores/knowledge.js')
const { useOpportunitiesStore } = await import('../../src/stores/opportunities.js')
const { api } = await import('../../src/services/api.js')

const store = usePostsStore()
const chat = useChatStore()
const projects = useProjectsStore()
const knowledge = useKnowledgeStore()
const opportunities = useOpportunitiesStore()
const suffix = randomUUID()
const accounts = []
let administratorToken = ''
const bob = { name: 'Smoke Bob', email: 'bob-' + suffix + '@example.com', password: randomUUID() }
const alice = { name: 'Smoke Alice', email: 'alice-' + suffix + '@example.com', password: randomUUID() }

try {
  await assert.rejects(api('/posts'), { status: 401 })
  await store.initialize()
  assert.ok(process.env.SMOKE_ADMIN_EMAIL && process.env.SMOKE_ADMIN_PASSWORD,
    'Use npm run test:auth:browser, or configure a test administrator for this smoke test.')
  const administrator = await originalFetch(origin + '/api/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: process.env.SMOKE_ADMIN_EMAIL, password: process.env.SMOKE_ADMIN_PASSWORD }),
  })
  assert.equal(administrator.status, 200, 'Test administrator login')
  administratorToken = (await administrator.json()).data.token
  for (const credentials of [bob, alice]) {
    const created = await originalFetch(origin + '/api/users', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + administratorToken },
      body: JSON.stringify(credentials),
    })
    assert.equal(created.status, 201, 'Test accounts are created only by an authenticated administrator')
    accounts.push((await created.json()).data.id)
  }
  let user = await store.authenticate({ email: bob.email, password: bob.password })
  assert.equal((await api('/health')).data.database, 'connected')
  const bobId = user.id
  user = await store.authenticate({ email: alice.email, password: alice.password })
  const aliceId = user.id
  const profile = await store.updateProfile('Smoke Alice Updated', 'Persistent bio', 'Teacher', ['Python'])
  assert.equal(profile.bio, 'Persistent bio')
  assert.equal(profile.isAdmin, false)
  const post = await store.addPost('Live proxy question', '#Q&A', 'print(1)', 'python', true)
  assert.ok(post?.id)
  await store.authenticate({ email: bob.email, password: bob.password })
  const comment = await store.addComment(post.id, 'A live answer')
  assert.ok(comment?.id)
  assert.equal((await store.likePost(post.id)).likes, 1)
  assert.ok(await chat.fetchMembers())
  const conversation = await chat.startConversation(aliceId)
  assert.ok(conversation?.id)
  assert.ok(await chat.sendMessage('Hello through the frontend store'))
  await store.authenticate({ email: alice.email, password: alice.password })
  assert.equal(chat.conversations.length, 0, 'Session changes clear private cached conversations')
  assert.ok(await chat.fetchConversations())
  assert.ok(chat.conversations.some(item => item.id === conversation.id && item.unread === 1))
  assert.ok(await chat.setActiveChat(conversation.id))
  assert.equal(chat.activeChat.messages[0].senderId, bobId)
  assert.equal(chat.activeChat.unread, 0)
  assert.ok(await chat.sendMessage('Reply from Alice'))
  assert.ok((await store.markAsSolved(post.id, comment.id)).isSolved)
  assert.ok(await projects.load())
  const task = await projects.addTask({ title: 'Live task', description: 'Proxy test', assigneeId: bobId, status: 'todo' })
  assert.ok(task?.id)
  assert.equal((await projects.updateTaskStatus(task.id, 'done')).status, 'done')
  assert.ok(await knowledge.load())
  const question = await knowledge.addQuestion({ title: 'Live Q&A', content: 'Body', tags: ['vue'] })
  assert.ok(question?.id)
  assert.ok(await opportunities.load())
  assert.ok(Array.isArray(opportunities.jobs))
  const article = (await api('/articles', { method: 'POST', body: { title: 'Live article', content: 'Content' } })).data
  assert.equal((await api('/articles/' + article.id + '/like', { method: 'POST' })).data.likes, 1)
  assert.ok((await api('/notifications')).data.length > 0)
  await store.fetchPosts()
  assert.ok(store.posts.find(item => item.id === post.id)?.isSolved)
  assert.ok(await store.logout())
  assert.equal(store.currentUser, null)
  assert.equal(chat.conversations.length, 0)
  console.log('PASS: real Pinia stores -> Vite /api proxy -> Flask -> SQLite persistence.')
  console.log('Verified existing-account login, profile, posts, comments, likes, accepted answers, private chat, tasks, articles, opportunities, notifications, and logout.')
} finally {
  for (const account of accounts.reverse()) {
    const response = await originalFetch(origin + '/api/users/' + account, {
      method: 'DELETE', headers: { Authorization: 'Bearer ' + administratorToken },
    })
    assert.equal(response.status, 200, 'Temporary account cleanup')
  }
  if (administratorToken) await originalFetch(origin + '/api/auth/logout', {
    method: 'POST', headers: { Authorization: 'Bearer ' + administratorToken },
  })
  console.log('Temporary test accounts and their related data removed.')
}
