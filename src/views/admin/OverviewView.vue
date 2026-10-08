<script setup>
import { computed, onMounted } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useUsersStore } from '@/stores/users'

const postsStore = usePostsStore()
const usersStore = useUsersStore()

onMounted(() => usersStore.fetchUsers())

const totalUsers = computed(() => usersStore.users.length)
const totalPosts = computed(() => postsStore.posts.length)
const totalLikes = computed(() => postsStore.posts.reduce((acc, post) => acc + post.likes, 0))
const totalComments = computed(() => postsStore.posts.reduce((acc, post) => acc + post.comments.length, 0))

const recentActivity = computed(() => {
  return postsStore.posts.slice(0, 5)
})
</script>

<template>
  <div class="dashboard-overview animate-fade-in">
    <div class="overview-header">
      <h1>Dashboard Overview</h1>
      <p class="text-muted">High-level summary of your community</p>
    </div>
    
    <div class="stats-grid">
      <div class="stat-card glass-panel">
        <div class="stat-icon users-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
        </div>
        <div class="stat-details">
          <h3>Total Users</h3>
          <p class="stat-number">{{ totalUsers }}</p>
        </div>
      </div>
      
      <div class="stat-card glass-panel">
        <div class="stat-icon posts-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <div class="stat-details">
          <h3>Total Posts</h3>
          <p class="stat-number">{{ totalPosts }}</p>
        </div>
      </div>
      
      <div class="stat-card glass-panel">
        <div class="stat-icon likes-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
          </svg>
        </div>
        <div class="stat-details">
          <h3>Total Likes</h3>
          <p class="stat-number">{{ totalLikes }}</p>
        </div>
      </div>
      
      <div class="stat-card glass-panel">
        <div class="stat-icon comments-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
        </div>
        <div class="stat-details">
          <h3>Comments</h3>
          <p class="stat-number">{{ totalComments }}</p>
        </div>
      </div>
    </div>
    
    <div class="recent-activity-section glass-panel">
      <h2>Recent Posts Activity</h2>
      <div class="activity-list">
        <div v-for="post in recentActivity" :key="post.id" class="activity-item">
          <img :src="post.author.avatar" alt="avatar" class="activity-avatar" />
          <div class="activity-content">
            <p><strong>{{ post.author.name }}</strong> posted in <span class="tag-badge">{{ post.tag }}</span></p>
            <p class="text-muted activity-preview">{{ post.content }}</p>
          </div>
          <div class="activity-meta">
            <span class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {{ post.likes }}
            </span>
            <span class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
              </svg>
              {{ post.comments.length }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-header h1 {
  font-size: 2rem;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.users-icon {
  background: rgba(99, 102, 241, 0.15);
  color: #4f46e5;
}

.posts-icon {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.likes-icon {
  background: rgba(236, 72, 153, 0.15);
  color: #db2777;
}

.comments-icon {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.stat-details h3 {
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-weight: 600;
  margin: 0;
}

.stat-number {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
}

.recent-activity-section {
  padding: 2rem;
}

.recent-activity-section h2 {
  font-size: 1.4rem;
  margin-bottom: 1.5rem;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: all var(--transition-fast);
}

.activity-item:hover {
  background: rgba(255, 255, 255, 0.7);
  transform: translateX(4px);
}

.activity-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f1f5f9;
}

.activity-content {
  flex: 1;
  min-width: 0; /* allows truncation */
}

.activity-content p {
  margin: 0;
  line-height: 1.4;
}

.activity-preview {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-badge {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  color: #4f46e5;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.activity-meta {
  display: flex;
  gap: 1rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

@media (max-width: 768px) {
  .dashboard-overview {
    gap: 1.5rem;
  }
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  .recent-activity-section {
    padding: 1rem;
  }
  .activity-item {
    padding: 0.8rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
  }
  .activity-avatar {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
