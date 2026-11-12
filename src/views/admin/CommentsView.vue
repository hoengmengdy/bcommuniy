<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { plainText, useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const ui = useUiStore()
const loading = ref(true)
onMounted(async () => {
  await admin.fetchComments()
  loading.value = false
})

const search = ref('')
const typeFilter = ref('all')
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return admin.comments.filter(comment => {
    if (typeFilter.value === 'replies' && !comment.parentId) return false
    if (typeFilter.value === 'top' && comment.parentId) return false
    if (typeFilter.value === 'best' && !comment.isBestAnswer) return false
    if (typeFilter.value === 'code' && !comment.codeSnippet) return false
    return !q || [comment.text, comment.author?.name, comment.postTitle].some(v => String(v || '').toLowerCase().includes(q))
  })
})

const removeComment = async comment => {
  if (!window.confirm(`Delete this comment by ${comment.author.name} and its replies?`)) return
  if (await admin.deleteComment(comment.id)) {
    ui.addToast('Comment deleted', 'success')
    await admin.fetchComments()
  }
}
const formatDate = iso => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <div class="adm-page">
    <div class="adm-header">
      <div>
        <h1>Comments</h1>
        <p class="text-muted">Every comment and reply, newest first</p>
      </div>
      <button class="adm-btn" @click="admin.fetchComments()">Refresh</button>
    </div>

    <div class="glass-panel adm-toolbar">
      <input v-model="search" type="search" class="input-field adm-search" placeholder="Search comment, author or post…" aria-label="Search comments" />
      <select v-model="typeFilter" class="input-field" aria-label="Filter comments">
        <option value="all">All comments</option>
        <option value="top">Top-level only</option>
        <option value="replies">Replies only</option>
        <option value="best">Accepted answers</option>
        <option value="code">With code</option>
      </select>
      <span class="adm-count">{{ filtered.length }} of {{ admin.comments.length }} comments</span>
    </div>

    <div class="comment-list">
      <article v-for="comment in filtered" :key="comment.id" class="glass-panel comment">
        <div class="comment-head">
          <RouterLink :to="`/profile/${comment.author.id}`" class="adm-user who">
            <img :src="comment.author.avatar" alt="" />
            <div><strong>{{ comment.author.name }}</strong><small>{{ formatDate(comment.timestamp) }}</small></div>
          </RouterLink>
          <div class="adm-actions">
            <span v-if="comment.parentId" class="adm-badge">Reply</span>
            <span v-if="comment.isBestAnswer" class="adm-badge green">Accepted answer</span>
            <RouterLink :to="`/post/${comment.postId}`" class="adm-btn">Open post</RouterLink>
            <button class="adm-btn danger" @click="removeComment(comment)">Delete</button>
          </div>
        </div>
        <p class="comment-text">{{ plainText(comment.text) || '—' }}</p>
        <pre v-if="comment.codeSnippet" class="comment-code">{{ comment.codeSnippet }}</pre>
        <p class="on-post text-muted">on “{{ plainText(comment.postTitle) || 'Untitled post' }}”</p>
      </article>
      <div v-if="loading" class="glass-panel adm-empty">Loading comments…</div>
      <div v-else-if="!filtered.length" class="glass-panel adm-empty">No comments match.</div>
    </div>
  </div>
</template>

<style scoped>
.comment-list { display: flex; flex-direction: column; gap: 0.75rem; }
.comment { padding: 1rem 1.2rem; }
.comment-head { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.who { text-decoration: none; color: inherit; }
.who img { width: 32px; height: 32px; }
.comment-text { margin: 0.7rem 0 0.3rem; white-space: pre-wrap; overflow-wrap: anywhere; }
.comment-code {
  margin: 0.4rem 0; padding: 0.6rem 0.8rem; border-radius: var(--radius-sm); font-size: 0.8rem;
  background: rgba(15, 23, 42, 0.06); max-height: 160px; overflow: auto;
}
.on-post { font-size: 0.82rem; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
