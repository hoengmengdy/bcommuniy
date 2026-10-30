<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'
import CodeBlock from '@/components/CodeBlock.vue'
import { timeAgo } from '@/utils/time'
import { sharePost } from '@/utils/share'
import SendPostModal from '@/components/SendPostModal.vue'
import { renderRichText } from '@/utils/richText'

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const store = usePostsStore()
const uiStore = useUiStore()
const router = useRouter()
const route = useRoute()

// ⋮ menu: only the author (or an admin) sees it, to delete a post made by mistake.
const showMenu = ref(false)
const menuRef = ref(null)
const deleting = ref(false)
const canDelete = computed(() => store.canDelete(props.post.author))
const closeMenu = event => {
  if (showMenu.value && menuRef.value && !menuRef.value.contains(event.target)) showMenu.value = false
}
onMounted(() => document.addEventListener('click', closeMenu))
onUnmounted(() => document.removeEventListener('click', closeMenu))

async function deletePost() {
  showMenu.value = false
  if (!window.confirm('Delete this post? This cannot be undone.')) return
  deleting.value = true
  const deleted = await store.deletePost(props.post.id)
  deleting.value = false
  if (!deleted) return
  uiStore.addToast('Post deleted', 'success')
  if (route.path.startsWith('/post/')) router.push('/')
}

const formattedTime = computed(() => timeAgo(props.post.timestamp) || 'Just now')

// Heart is an outline until you like the post, then solid red.
const liked = computed(() => store.isLiked(props.post))
const showSend = ref(false)
async function share() {
  try {
    if (await sharePost(props.post) === 'copied') uiStore.addToast('Link copied', 'success')
  } catch {
    uiStore.addToast('Could not share on this device.', 'error')
  }
}

// Plain text and pasted HTML both render as safe, formatted HTML.
const formattedContent = computed(() => renderRichText(props.post.content))
const roleClass = computed(() => 'role-' + String(props.post.author.role || '').toLowerCase())

function viewPost(event) {
  if (event && event.target.closest('a')) {
    return
  }
  router.push(`/post/${props.post.id}`)
}
</script>

<template>
  <article class="post-card glass-panel" @click="viewPost">
    <!-- Header -->
    <header class="post-header">
      <button class="author-block" :aria-label="`Open ${post.author.name}'s profile`"
        @click.stop="router.push(`/profile/${post.author.id}`)">
        <img :src="post.author.avatar" :alt="post.author.name" class="avatar" />
        <span class="author-info">
          <span class="author-line">
            <span class="author-name">{{ post.author.name }}</span>
            <span v-if="post.author.role" class="role-badge" :class="roleClass">{{ post.author.role }}</span>
          </span>
          <span class="post-meta">
            <time :datetime="post.timestamp">{{ formattedTime }}</time>
            <template v-if="post.tag"><span class="meta-dot" aria-hidden="true">·</span><span class="post-tag">{{ post.tag }}</span></template>
          </span>
        </span>
      </button>
      <div v-if="canDelete" ref="menuRef" class="post-menu-wrap" @click.stop>
        <button class="more-btn" aria-label="Post options" title="More" :aria-expanded="showMenu" :disabled="deleting"
          @click="showMenu = !showMenu">
          <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M128,72a16,16,0,1,0-16-16A16,16,0,0,0,128,72Zm0,40a16,16,0,1,0,16,16A16,16,0,0,0,128,112Zm0,72a16,16,0,1,0,16,16A16,16,0,0,0,128,184Z"/>
          </svg>
        </button>
        <div v-if="showMenu" class="post-menu" role="menu">
          <button class="post-menu-item danger" role="menuitem" @click="deletePost">🗑️ Delete post</button>
        </div>
      </div>
    </header>

    <!-- Content Text -->
    <div v-if="post.content" class="post-text rich-text" v-html="formattedContent"></div>

    <!-- Code Snippet -->
    <CodeBlock
      v-if="post.codeSnippet"
      :code="post.codeSnippet"
      :language="post.codeLanguage"
    />

    <!-- Project / Repo Card -->
    <a v-if="post.projectUrl" :href="post.projectUrl" target="_blank" rel="noopener" class="repo-card" @click.stop>
      <div class="repo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24" aria-hidden="true"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
      </div>
      <div class="repo-details">
        <span class="repo-url">{{ post.projectUrl.replace('https://', '').replace('http://', '') }}</span>
        <span class="repo-desc">Click to view project</span>
      </div>
      <svg class="external-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
    </a>

    <!-- Image -->
    <div v-if="post.image" class="post-image-container">
      <img :src="post.image" class="post-image" :alt="`Image shared by ${post.author.name}`" loading="lazy" />
    </div>

    <!-- Actions -->
    <footer class="post-actions" @click.stop>
      <button class="action-btn like-btn" :class="{ liked }" :aria-pressed="liked"
        :aria-label="liked ? 'Unlike' : 'Like'" :title="liked ? 'Unlike' : 'Like'" @click="store.likePost(post.id)">
        <svg class="action-icon heart" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor"
          stroke-width="2" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        <span class="count">{{ post.likes || 0 }}</span>
      </button>
      <button class="action-btn" aria-label="Comments" title="Comment" @click="viewPost">
        <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
        </svg>
        <span class="count">{{ post.comments?.length || 0 }}</span>
      </button>
      <button class="action-btn" aria-label="Share" title="Share" @click="share">
        <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7"></path>
          <polyline points="16 6 12 2 8 6"></polyline>
          <line x1="12" y1="2" x2="12" y2="15"></line>
        </svg>
        <span class="action-label">Share</span>
      </button>
      <button class="action-btn" aria-label="Send to a member" title="Send to a member" @click="showSend = true">
        <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
        <span class="action-label">Send</span>
      </button>
    </footer>
    <SendPostModal v-if="showSend" :post="post" @close="showSend = false" />
  </article>
</template>

<style scoped>
.post-card {
  padding: 20px 22px 12px;
  margin-bottom: 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.author-block {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  background: none;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  color: inherit;
  border-radius: 10px;
}

.author-block:hover .author-name {
  color: var(--brand);
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background: #ede9fe;
}

.author-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.author-line {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}

.author-name {
  font-size: 15.5px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.15s ease;
}

/* Small, calm role badges. */
.role-badge {
  flex-shrink: 0;
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 1.6;
  background: #f1f5f9;
  color: #475569;
}

.role-senior { background: #ecfdf3; color: #047857; }
.role-beginner { background: #eef2ff; color: #4f46e5; }
.role-teacher { background: #fef6e7; color: #b45309; }
.role-admin { background: #f3f0ff; color: #6d28d9; }

.post-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  font-size: 12.5px;
  color: #64748b;
}

.meta-dot { color: #cbd5e1; }

.post-tag {
  background: var(--brand-soft);
  color: #6d28d9;
  padding: 0 6px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.more-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: -4px -6px 0 0;
  transition: all 0.15s ease;
}

.more-btn:hover { background: #f4f4f8; color: #475569; }

.more-btn svg {
  width: 20px;
  height: 20px;
}

.post-menu-wrap {
  position: relative;
  flex-shrink: 0;
}

.post-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 180px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
  padding: 0.35rem;
  z-index: 50;
}

.post-menu-item {
  display: block;
  width: 100%;
  padding: 0.7rem 0.8rem;
  border: none;
  border-radius: 8px;
  background: none;
  font-size: 0.92rem;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.post-menu-item.danger { color: #dc2626; }
.post-menu-item.danger:hover { background: #fef2f2; }

.post-text {
  margin: 0 0 0.9rem;
}

.post-image-container {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 0.9rem;
  background: #f1f5f9;
}

.post-image {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
}

/* One balanced row of actions. */
.post-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0 -10px;
  padding-top: 6px;
  border-top: 1px solid #f1f2f6;
}

.action-btn {
  background: none;
  border: none;
  height: 36px;
  padding: 0 10px;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #f5f3ff;
  color: var(--brand);
}

.action-btn:active { transform: scale(0.97); }

.action-icon {
  width: 19px;
  height: 19px;
  flex-shrink: 0;
}

.like-btn.liked,
.like-btn.liked:hover { color: #ef4444; }
.like-btn.liked:hover { background: #fef2f2; }
.like-btn.liked .heart { animation: heartPop 0.25s ease-out; }

@keyframes heartPop {
  50% { transform: scale(1.25); }
}

.count { font-variant-numeric: tabular-nums; }

.repo-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border: 1px solid #ececf3;
  border-radius: 12px;
  background: #fafafd;
  text-decoration: none;
  margin-bottom: 0.9rem;
  transition: all 0.15s ease;
  position: relative;
}

.repo-card:hover { background: #f5f3ff; border-color: #ddd6fe; }

.repo-icon {
  background: #ffffff;
  padding: 0.6rem;
  border-radius: 8px;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.repo-details { display: flex; flex-direction: column; min-width: 0; }

.repo-url {
  font-weight: 600;
  color: #047857;
  font-size: 0.92rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.repo-desc { font-size: 0.8rem; color: #64748b; }

.external-icon {
  position: absolute;
  right: 1rem;
  top: 1rem;
  color: #9ca3af;
}

@media (max-width: 767px) {
  .post-card {
    padding: 16px 14px 8px;
    margin-bottom: 12px;
  }

  .avatar { width: 40px; height: 40px; }
  .post-actions { margin: 0 -6px; }
  /* Icons only on phones so the row never wraps. */
  .action-label { display: none; }
}
</style>
