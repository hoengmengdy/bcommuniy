<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import CodeBlock from '@/components/CodeBlock.vue'
import CommentSection from '@/components/CommentSection.vue'

const route = useRoute()
const router = useRouter()
const store = usePostsStore()

const post = computed(() => {
  return store.getPostById(Number(route.params.id))
})

const formattedTime = computed(() => {
  if (!post.value) return ''
  return 'today'
})
</script>

<template>
  <div class="post-detail-view animate-fade-in">
    <div class="detail-container">
      <button class="back-btn" @click="router.back()">
        &larr; Back to Feed
      </button>
      
      <div v-if="post" class="post-grid">
        <!-- Left: Content + Image -->
        <div class="post-left">
          <!-- Always show content text -->
          <div class="post-content-area">
            <h2 v-if="post.title">{{ post.title }}</h2><p class="post-text">{{ post.content }}</p><CodeBlock v-if="post.codeSnippet" :code="post.codeSnippet" :language="post.codeLanguage" />
          </div>

          <!-- Image always shown when available -->
          <div v-if="post.image" class="post-image-container">
            <img :src="post.image" class="post-image" alt="Post Image" />
          </div>

          <!-- Actions below image -->
          <div class="post-actions">
            <div class="action-group-left">
              <button class="action-btn" @click="store.likePost(post.id)">
                <svg class="action-icon" style="color: #ef4444;" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
                <span class="count">{{ post.likes || 0 }} Likes</span>
              </button>
              <button class="action-btn">
                <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                </svg>
                <span class="count">{{ post.comments?.length || 0 }} Comments</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Author info + Comments -->
        <div class="post-right">
          <div class="post-header">
            <div class="author-block">
              <img :src="post.author.avatar" alt="Avatar" class="avatar" />
              <div class="author-info">
                <span class="author-name">{{ post.author.name }}</span>
                <span class="timestamp">{{ formattedTime }}</span>
              </div>
            </div>
            <button class="more-btn">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="12" r="2"></circle>
                <circle cx="12" cy="12" r="2"></circle>
                <circle cx="19" cy="12" r="2"></circle>
              </svg>
            </button>
          </div>

          <CommentSection :post="post" />
        </div>
      </div>
      
      <div v-else class="not-found">
        <h2>Post not found</h2>
        <p>The post you are looking for does not exist or has been removed.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.post-detail-view {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 0 1rem;
}

.detail-container {
  width: 100%;
  max-width: 1100px;
  display: flex;
  flex-direction: column;
}

.back-btn {
  background: none;
  border: none;
  color: #3b82f6;
  font-weight: 600;
  font-size: 0.95rem;
  padding: 0.8rem 0;
  cursor: pointer;
  align-self: flex-start;
  margin-bottom: 1.5rem;
  transition: color 0.2s ease;
}

.back-btn:hover {
  color: #2563eb;
}

/* Two-column grid */
.post-grid {
  display: grid;
  grid-template-columns: 1fr 480px;
  gap: 1.5rem;
  align-items: start;
}

/* Left column */
.post-left {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
}

.post-image-container {
  width: 100%;
  background: #f0f0f0;
}

.post-image {
  width: 100%;
  height: auto;
  max-height: 520px;
  object-fit: cover;
  display: block;
}

.post-container-flat {
  padding: 1.5rem;
}

.post-content-area {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.post-actions {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 1rem 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.action-group-left {
  display: flex;
  gap: 2rem;
}

.action-btn {
  background: none;
  border: none;
  padding: 0.4rem 0.6rem;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.action-icon {
  width: 20px;
  height: 20px;
}

.count {
  font-size: 0.95rem;
  font-weight: 500;
}

/* Right column */
.post-right {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 80px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.author-block {
  display: flex;
  align-items: center;
  gap: 0.75rem;
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
  font-weight: 700;
  font-size: 1rem;
  color: #1a1a1a;
}

.timestamp {
  font-size: 0.8rem;
  color: #9ca3af;
  margin-top: 2px;
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
  color: #374151;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
}

.not-found {
  text-align: center;
  padding: 4rem 2rem;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

@media (max-width: 768px) {
  .post-grid {
    grid-template-columns: 1fr;
  }
  .post-right {
    position: static;
    max-height: none;
    padding: 1rem;
  }
  .post-container-flat {
    padding: 1rem;
  }
  .post-content-area {
    padding: 1rem;
  }
  .post-actions {
    padding: 0.8rem 1rem;
  }
  .not-found {
    padding: 2rem 1rem;
  }
}
</style>
