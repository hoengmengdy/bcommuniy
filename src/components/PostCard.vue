<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import CodeBlock from '@/components/CodeBlock.vue'

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const store = usePostsStore()
const router = useRouter()

const formattedTime = computed(() => {
  if (props.post.timestamp) {
    return '2 hours ago' // Mocking time for UI match
  }
  return 'Just now'
})

const formattedContent = computed(() => {
  if (!props.post.content) return ''
  
  const escapeHTML = (str) => str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  )
  let text = escapeHTML(props.post.content)
  
  const urlRegex = /(https?:\/\/[^\s]+)/g
  text = text.replace(urlRegex, '<a href="$1" target="_blank" class="post-link">$1</a>')
  
  text = text.replace(/\n/g, '<br>')
  
  return text
})

function viewPost(event) {
  if (event && event.target.closest('a')) {
    return
  }
  router.push(`/post/${props.post.id}`)
}
</script>

<template>
  <div class="post-card glass-panel" @click="viewPost">
    <!-- Header -->
    <div class="post-header">
      <div class="author-block">
        <img :src="post.author.avatar" alt="Avatar" class="avatar" />
        <div class="author-info">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <h3 class="author-name">{{ post.author.name }}</h3>
            <span v-if="post.author.role" class="author-role">{{ post.author.role }}</span>
          </div>
          <span class="post-time">
            {{ formattedTime }}
            <span v-if="post.tag" class="post-tag">{{ post.tag }}</span>
          </span>
        </div>
      </div>
      <button class="icon-btn more-btn">
        <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M128,72a16,16,0,1,0-16-16A16,16,0,0,0,128,72Zm0,40a16,16,0,1,0,16,16A16,16,0,0,0,128,112Zm0,72a16,16,0,1,0,16,16A16,16,0,0,0,128,184Z"/>
        </svg>
      </button>
    </div>
    
    <!-- Content Text -->
    <p v-if="post.content" class="post-text" v-html="formattedContent"></p>
    
    <!-- Code Snippet -->
    <CodeBlock 
      v-if="post.codeSnippet" 
      :code="post.codeSnippet" 
      :language="post.codeLanguage" 
    />
    
    <!-- Project / Repo Card -->
    <a v-if="post.projectUrl" :href="post.projectUrl" target="_blank" class="repo-card" @click.stop>
      <div class="repo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
      </div>
      <div class="repo-details">
        <span class="repo-url">{{ post.projectUrl.replace('https://', '').replace('http://', '') }}</span>
        <span class="repo-desc">Click to view project</span>
      </div>
      <svg class="external-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
    </a>

    <!-- Image -->
    <div v-if="post.image" class="post-image-container">
      <img :src="post.image" class="post-image" alt="Post Image" />
    </div>
    
    <!-- Actions -->
    <div class="post-actions" @click.stop>
      <div class="action-group-left">
        <button class="action-btn" @click="store.likePost(post.id)">
          <svg class="action-icon" style="color: #ef4444;" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
          <span class="count">{{ post.likes || 0 }}</span>
        </button>
        <button class="action-btn" @click="viewPost">
          <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
          <span class="count">{{ post.comments?.length || 0 }}</span>
        </button>
        <button class="action-btn">
          <svg class="action-icon" viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M237.66,106.34l-80,80A8,8,0,0,1,144,180.69V136c-51.52,0-91.82,18.06-118,52.88A8,8,0,0,1,14.61,185C27.46,128.84,65.65,88,144,88V43.31a8,8,0,0,1,13.66-5.65l80,80A8,8,0,0,1,237.66,106.34ZM160,157.37V184l56-56-56-56V98.63a8,8,0,0,1-8,8C78.47,106.63,44.75,138,32.22,185.34C58.11,152,95.53,130.63,152,130.63A8,8,0,0,1,160,138.63Z"/>
          </svg>
        </button>
      </div>
      <button class="action-btn">
        <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.post-card {
  padding: 1.5rem;
  margin-bottom: 2rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.post-card:hover {
  border-color: rgba(255, 255, 255, 1);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.author-block {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  margin: 0;
  font-size: 1rem;
  color: #1a1a1a;
}

.author-role {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.post-time {
  font-size: 0.85rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.post-tag {
  background: #f1f5f9;
  color: #475569;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.more-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.5rem;
}

.more-btn svg {
  width: 20px;
  height: 20px;
}

.post-text {
  font-size: 0.95rem;
  color: #4b5563;
  line-height: 1.5;
  margin: 0 0 1.2rem 0;
}

.post-text :deep(.post-link) {
  color: #3b82f6;
  text-decoration: none;
  word-break: break-all;
}

.post-text :deep(.post-link:hover) {
  text-decoration: underline;
}

.post-image-container {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1.5rem;
  background: #f0f0f0;
}

.post-image {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
}

.post-image-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
}

.post-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-group-left {
  display: flex;
  gap: 1.2rem;
}

.action-btn {
  background: none;
  border: none;
  padding: 0.4rem 0.6rem;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255,255,255,0.8);
  color: var(--accent-color);
  transform: translateY(-2px);
  box-shadow: none;
}

.action-icon {
  width: 20px;
  height: 20px;
}

.count {
  font-size: 0.9rem;
  font-weight: 500;
}

.repo-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  background: rgba(255,255,255,0.4);
  backdrop-filter: blur(4px);
  text-decoration: none;
  margin-bottom: 1.5rem;
  transition: all 0.2s ease;
  position: relative;
}

.repo-card:hover {
  background: rgba(255,255,255,0.8);
  transform: translateY(-2px);
}

.repo-icon {
  background: rgba(0,0,0,0.05);
  padding: 0.75rem;
  border-radius: 8px;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.repo-details {
  display: flex;
  flex-direction: column;
}

.repo-url {
  font-weight: 600;
  color: #10b981;
  font-size: 0.95rem;
  margin-bottom: 0.2rem;
}

.repo-desc {
  font-size: 0.8rem;
  color: #64748b;
}

.external-icon {
  position: absolute;
  right: 1rem;
  top: 1rem;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .post-card {
    padding: 1rem;
  }
}
</style>
