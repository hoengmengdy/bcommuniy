<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { usePostsStore } from '@/stores/posts'
import { downloadCsv, plainText, useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const ui = useUiStore()
const communityPosts = usePostsStore()

const loading = ref(true)
onMounted(async () => {
  await admin.fetchPosts()
  loading.value = false
})

const search = ref('')
const typeFilter = ref('all')
const tagFilter = ref('all')
const sort = ref('newest')

const tags = computed(() => [...new Set(admin.posts.map(post => post.tag))].sort())
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  const rows = admin.posts.filter(post => {
    if (typeFilter.value === 'questions' && !post.isQuestion) return false
    if (typeFilter.value === 'unsolved' && !(post.isQuestion && !post.isSolved)) return false
    if (typeFilter.value === 'posts' && post.isQuestion) return false
    if (typeFilter.value === 'code' && !post.codeSnippet) return false
    if (typeFilter.value === 'images' && !post.image) return false
    if (tagFilter.value !== 'all' && post.tag !== tagFilter.value) return false
    return !q || [post.title, plainText(post.content), post.author?.name].some(v => String(v || '').toLowerCase().includes(q))
  })
  const by = {
    newest: (a, b) => new Date(b.timestamp) - new Date(a.timestamp),
    oldest: (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
    likes: (a, b) => b.likes - a.likes,
    comments: (a, b) => b.comments.length - a.comments.length,
  }
  return rows.sort(by[sort.value])
})

const selected = ref(new Set())
const allSelected = computed(() => filtered.value.length > 0 && filtered.value.every(p => selected.value.has(p.id)))
const toggle = id => {
  const next = new Set(selected.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selected.value = next
}
const toggleAll = () => { selected.value = allSelected.value ? new Set() : new Set(filtered.value.map(p => p.id)) }

// Keep the community feed in sync so deleted posts vanish there too.
const forgetInFeed = ids => {
  const gone = new Set(ids)
  communityPosts.posts = communityPosts.posts.filter(post => !gone.has(post.id))
}

const bulkDelete = async () => {
  const ids = [...selected.value]
  if (!ids.length || !window.confirm(`Delete ${ids.length} post(s) with all their comments and likes?`)) return
  const result = await admin.bulkDeletePosts(ids)
  if (!result) return
  forgetInFeed(ids)
  selected.value = new Set()
  ui.addToast(`${result.affected} post(s) deleted`, 'success')
}
const removePost = async post => {
  if (!window.confirm(`Delete this post by ${post.author.name}?`)) return
  if (await admin.deletePost(post.id)) {
    forgetInFeed([post.id])
    ui.addToast('Post deleted', 'success')
  }
}
const solve = async post => {
  const updated = await admin.toggleSolved(post.id)
  if (updated) ui.addToast(updated.isSolved ? 'Marked as solved' : 'Marked as unsolved', 'success')
}

const preview = post => post.title || plainText(post.content) || (post.codeSnippet ? '💻 Code snippet' : post.image ? '📷 Photo' : '—')
const exportCsv = () => downloadCsv(`posts-${new Date().toISOString().slice(0, 10)}.csv`, filtered.value.map(p => ({
  id: p.id, author: p.author.name, title: p.title, content: plainText(p.content), tag: p.tag,
  question: p.isQuestion, solved: p.isSolved, likes: p.likes, comments: p.comments.length, created: p.timestamp })))
const formatDate = iso => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <div class="adm-page">
    <div class="adm-header">
      <div>
        <h1>Posts</h1>
        <p class="text-muted">Moderate every post, question and code review</p>
      </div>
      <div class="adm-actions">
        <button class="adm-btn" :disabled="!filtered.length" @click="exportCsv">Export CSV</button>
        <button class="adm-btn" @click="admin.fetchPosts()">Refresh</button>
      </div>
    </div>

    <div class="glass-panel adm-toolbar">
      <input v-model="search" type="search" class="input-field adm-search" placeholder="Search title, content or author…" aria-label="Search posts" />
      <select v-model="typeFilter" class="input-field" aria-label="Filter by type">
        <option value="all">All types</option>
        <option value="posts">Posts only</option>
        <option value="questions">Questions</option>
        <option value="unsolved">Unsolved questions</option>
        <option value="code">With code</option>
        <option value="images">With images</option>
      </select>
      <select v-model="tagFilter" class="input-field" aria-label="Filter by tag">
        <option value="all">All tags</option>
        <option v-for="tag in tags" :key="tag" :value="tag">{{ tag }}</option>
      </select>
      <select v-model="sort" class="input-field" aria-label="Sort">
        <option value="newest">Newest</option>
        <option value="oldest">Oldest</option>
        <option value="likes">Most liked</option>
        <option value="comments">Most comments</option>
      </select>
      <span class="adm-count">{{ filtered.length }} of {{ admin.posts.length }} posts</span>
    </div>

    <div v-if="selected.size" class="adm-bulkbar">
      <span>{{ selected.size }} selected</span>
      <button class="adm-btn danger" @click="bulkDelete">Delete selected</button>
      <button class="adm-btn" @click="selected = new Set()">Clear</button>
    </div>

    <div class="glass-panel adm-table-wrap">
      <table class="adm-table">
        <thead>
          <tr>
            <th><input type="checkbox" :checked="allSelected" @change="toggleAll" aria-label="Select all" /></th>
            <th>Post</th>
            <th>Author</th>
            <th>Tag</th>
            <th class="num">Likes</th>
            <th class="num">Comments</th>
            <th>Posted</th>
            <th class="num">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="post in filtered" :key="post.id" :class="{ selected: selected.has(post.id) }">
            <td><input type="checkbox" :checked="selected.has(post.id)" @change="toggle(post.id)" :aria-label="`Select post ${post.id}`" /></td>
            <td>
              <div class="adm-clip"><strong>{{ preview(post) }}</strong></div>
              <div class="flags">
                <span v-if="post.isQuestion" class="adm-badge" :class="post.isSolved ? 'green' : 'amber'">
                  {{ post.isSolved ? 'Solved' : 'Open question' }}
                </span>
                <span v-if="post.codeSnippet" class="adm-badge">Code</span>
                <span v-if="post.image" class="adm-badge">Image</span>
              </div>
            </td>
            <td>
              <RouterLink :to="`/profile/${post.author.id}`" class="adm-user author-link">
                <img :src="post.author.avatar" alt="" /><span>{{ post.author.name }}</span>
              </RouterLink>
            </td>
            <td><span class="adm-badge indigo">{{ post.tag }}</span></td>
            <td class="num">{{ post.likes }}</td>
            <td class="num">{{ post.comments.length }}</td>
            <td class="nowrap text-muted">{{ formatDate(post.timestamp) }}</td>
            <td>
              <div class="adm-cell-actions">
                <RouterLink :to="`/post/${post.id}`" class="adm-icon-btn" title="Open post" aria-label="Open post">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6"/><path d="M10 14 21 3"/></svg>
                </RouterLink>
                <button v-if="post.isQuestion" class="adm-icon-btn" :title="post.isSolved ? 'Mark unsolved' : 'Mark solved'"
                  :aria-label="post.isSolved ? 'Mark unsolved' : 'Mark solved'" @click="solve(post)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/></svg>
                </button>
                <button class="adm-icon-btn danger" title="Delete post" aria-label="Delete post" @click="removePost(post)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="adm-empty">Loading posts…</div>
      <div v-else-if="!filtered.length" class="adm-empty">No posts match these filters.</div>
    </div>
  </div>
</template>

<style scoped>
.flags { display: flex; gap: 0.3rem; margin-top: 0.25rem; flex-wrap: wrap; }
.author-link { text-decoration: none; color: inherit; white-space: nowrap; }
.author-link img { width: 28px; height: 28px; }
.author-link:hover span { color: var(--accent-color); }
</style>
