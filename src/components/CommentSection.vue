<script setup>
import { ref, computed, nextTick } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'
import CodeBlock from '@/components/CodeBlock.vue'

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const store = usePostsStore()
const uiStore = useUiStore()
const commentText = ref('')
const showCodeInput = ref(false)
const codeSnippet = ref('')
const codeLanguage = ref('javascript')

const canSubmit = computed(() => commentText.value.trim().length > 0 || codeSnippet.value.trim().length > 0)
const replyingTo = ref(null) // { id, author }
const inputRef = ref(null)

const isPostAuthor = computed(() => Boolean(store.currentUser && props.post.author.id === store.currentUser.id))

// Read all comments reactively from store
const reactivePost = computed(() => store.posts.find(p => p.id === props.post.id))
const allComments = computed(() => reactivePost.value?.comments ?? [])

// Top-level comments (no parentId)
const topComments = computed(() => allComments.value.filter(c => !c.parentId))

// Get replies for a given comment id
function getReplies(commentId) {
  return allComments.value.filter(c => c.parentId === commentId)
}

function replyToComment(comment) {
  replyingTo.value = { id: comment.id, author: comment.author }
  commentText.value = ''
  nextTick(() => inputRef.value?.focus())
}

function cancelReply() {
  replyingTo.value = null
  commentText.value = ''
}

async function submitComment() {
  if (canSubmit.value) {
    const text = replyingTo.value
      ? `@${replyingTo.value.author.name} ${commentText.value.trim()}`
      : commentText.value.trim()
    const parentId = replyingTo.value?.id ?? null
    const created = await store.addComment(props.post.id, text, parentId, codeSnippet.value.trim(), codeLanguage.value)
    if (!created) return
    commentText.value = ''
    codeSnippet.value = ''
    showCodeInput.value = false
    replyingTo.value = null
    uiStore.addToast('Comment added!', 'success')
  }
}

function formatTime() {
  return 'today'
}

function formatComment(text) {
  const escaped = text.replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]))
  return escaped.replace(/(@[\w][\w\s]*)/g, '<span class="mention">$1</span>')
}
</script>

<template>
  <div class="comment-section">
    <h3 class="section-title">Comments ({{ topComments.length }})</h3>

    <!-- Comments list -->
    <div class="comments-list">
      <div v-if="topComments.length === 0" class="no-comments">
        Be the first to comment!
      </div>

      <div v-for="comment in topComments" :key="comment.id" class="comment-thread">
        <!-- Top-level comment -->
        <div class="comment" :class="{ 'best-answer': comment.isBestAnswer }">
          <img
            :src="comment.author.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + comment.author.name"
            :alt="comment.author.name"
            class="comment-avatar"
          />
          <div class="comment-content">
            <div class="comment-bubble">
              <span class="comment-author">
                {{ comment.author.name }} 
                <span v-if="comment.author.role" class="author-role-badge">{{ comment.author.role }}</span>
              </span>
              <p class="comment-text" v-html="formatComment(comment.text)"></p>
              <CodeBlock v-if="comment.codeSnippet" :code="comment.codeSnippet" :language="comment.codeLanguage" style="margin-top: 0.5rem;" />
            </div>
            <div class="comment-meta">
              <span class="comment-time">{{ formatTime(comment.timestamp) }}</span>
              <button class="reply-btn" @click="replyToComment(comment)">Reply</button>
              <button v-if="isPostAuthor && !props.post.isSolved && props.post.isQuestion" class="mark-solved-btn" @click="store.markAsSolved(props.post.id, comment.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M20 6L9 17l-5-5"></path></svg>
                Mark as Best Answer
              </button>
              <span v-if="comment.isBestAnswer" class="best-answer-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M20 6L9 17l-5-5"></path></svg>
                Best Answer
              </span>
            </div>
          </div>
        </div>

        <!-- Sub-comments (replies) -->
        <div v-if="getReplies(comment.id).length > 0" class="replies">
          <div v-for="reply in getReplies(comment.id)" :key="reply.id" class="comment reply" :class="{ 'best-answer': reply.isBestAnswer }">
            <img
              :src="reply.author.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + reply.author.name"
              :alt="reply.author.name"
              class="comment-avatar reply-avatar"
            />
            <div class="comment-content">
              <div class="comment-bubble">
                <span class="comment-author">
                  {{ reply.author.name }}
                  <span v-if="reply.author.role" class="author-role-badge">{{ reply.author.role }}</span>
                </span>
                <p class="comment-text" v-html="formatComment(reply.text)"></p>
                <CodeBlock v-if="reply.codeSnippet" :code="reply.codeSnippet" :language="reply.codeLanguage" style="margin-top: 0.5rem;" />
              </div>
              <div class="comment-meta">
                <span class="comment-time">{{ formatTime(reply.timestamp) }}</span>
                <button class="reply-btn" @click="replyToComment(comment)">Reply</button>
                <button v-if="isPostAuthor && !props.post.isSolved && props.post.isQuestion" class="mark-solved-btn" @click="store.markAsSolved(props.post.id, reply.id)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M20 6L9 17l-5-5"></path></svg>
                  Mark as Best Answer
                </button>
                <span v-if="reply.isBestAnswer" class="best-answer-badge">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M20 6L9 17l-5-5"></path></svg>
                  Best Answer
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div v-if="store.currentUser" class="input-area">
      <div v-if="replyingTo" class="replying-banner">
        <span>Replying to <strong>@{{ replyingTo.author.name }}</strong></span>
        <button class="cancel-reply" @click="cancelReply">✕</button>
      </div>
      
      <div v-if="showCodeInput" class="code-input-section">
        <div class="code-header">
          <select v-model="codeLanguage" class="tag-selector">
            <option value="javascript">JavaScript</option>
            <option value="python">Python</option>
            <option value="html">HTML</option>
            <option value="css">CSS</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
          </select>
          <button class="cancel-reply" @click="showCodeInput = false" title="Remove Code">✕</button>
        </div>
        <textarea 
          v-model="codeSnippet" 
          class="code-textarea" 
          placeholder="Paste your code here..."
          rows="4"
        ></textarea>
      </div>

      <div class="add-comment">
        <img :src="store.currentUser.avatar" :alt="store.currentUser.name" class="comment-avatar" />
        <div class="input-wrapper">
          <input
            ref="inputRef"
            v-model="commentText"
            type="text"
            class="comment-input"
            :placeholder="replyingTo ? `Reply to @${replyingTo.author.name}...` : 'Write a comment...'"
            @keyup.enter="submitComment"
          />
          <button class="add-code-btn" @click="showCodeInput = !showCodeInput" title="Add Code Snippet">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
          </button>
          <span class="enter-hint" v-if="canSubmit">Enter ↵</span>
        </div>
        <button class="send-btn" @click="submitComment" :class="{ active: canSubmit }">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comment-section {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding-top: 1rem;
  min-height: 0;
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
}

.comments-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.comment-thread {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Individual comment row */
.comment {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
}

.comment-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.reply-avatar {
  width: 26px;
  height: 26px;
}

.comment-content {
  flex: 1;
}

.comment-bubble {
  background: #f1f5f9;
  border-radius: 14px;
  padding: 0.5rem 0.9rem;
  display: inline-block;
  max-width: 100%;
}

.comment-author {
  font-weight: 700;
  font-size: 0.82rem;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.2rem;
}

.author-role-badge {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 700;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.comment-text {
  font-size: 0.88rem;
  color: #374151;
  margin: 0;
  line-height: 1.4;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.2rem 0.5rem;
}

.comment-time {
  font-size: 0.75rem;
  color: #9ca3af;
}

.reply-btn {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.reply-btn:hover {
  color: #1a1a1a;
}

.mark-solved-btn {
  background: none;
  border: none;
  color: #10b981;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 0.2rem;
  transition: color 0.2s;
}

.mark-solved-btn:hover {
  color: #059669;
}

.best-answer-badge {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  color: #10b981;
  font-size: 0.75rem;
  font-weight: 700;
}

.comment.best-answer .comment-bubble {
  border: 1px solid #10b981;
  background: rgba(16, 185, 129, 0.05);
}

/* Replies indent */
.replies {
  margin-left: 38px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mention {
  color: #7c3aed;
  font-weight: 600;
}

.no-comments {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
  font-size: 0.9rem;
}

/* Input area */
.input-area {
  border-top: 1px solid #f1f5f9;
  padding-top: 0.75rem;
}

.replying-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f5f3ff;
  border: 1px solid #ede9fe;
  border-radius: 8px;
  padding: 0.35rem 0.75rem;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  color: #6b7280;
}

.replying-banner strong {
  color: #7c3aed;
}

.cancel-reply {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}

.cancel-reply:hover {
  color: #374151;
}

.add-comment {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.comment-input {
  width: 100%;
  background: #f1f5f9;
  border: 1.5px solid transparent;
  border-radius: 24px;
  padding: 0.6rem 1rem;
  font-family: inherit;
  font-size: 0.88rem;
  color: #1a1a1a;
  transition: all 0.2s ease;
  outline: none;
}

.comment-input:focus {
  background: #ffffff;
  border-color: #7c3aed;
}

.comment-input::placeholder {
  color: #9ca3af;
}

.enter-hint {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.7rem;
  color: #9ca3af;
  pointer-events: none;
}

.send-btn {
  background: #e2e8f0;
  color: #94a3b8;
  border: none;
  border-radius: 50%;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.send-btn.active {
  background: #7c3aed;
  color: white;
}

.send-btn.active:hover {
  background: #6d28d9;
}

.add-code-btn {
  position: absolute;
  right: 65px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.4rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.add-code-btn:hover {
  background: rgba(0,0,0,0.05);
  color: #7c3aed;
}

.code-input-section {
  margin-bottom: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.75rem;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
}

.tag-selector {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.2rem 0.5rem;
  font-size: 0.8rem;
  color: #475569;
  outline: none;
}

.code-textarea {
  width: 100%;
  background: transparent;
  border: none;
  padding: 0.75rem;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.85rem;
  color: #1a1a1a;
  resize: vertical;
  min-height: 80px;
}

.code-textarea:focus {
  outline: none;
}
</style>
