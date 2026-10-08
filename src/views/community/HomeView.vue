<script setup>
import { usePostsStore } from '@/stores/posts'
import CreatePost from '@/components/CreatePost.vue'
import PostCard from '@/components/PostCard.vue'
import PostSkeleton from '@/components/PostSkeleton.vue'
import { ref, onMounted, computed } from 'vue'

const store = usePostsStore()
const isLoading = ref(true)
const activeTag = ref('All Topics')

onMounted(() => {
  setTimeout(() => {
    isLoading.value = false
  }, 800)
})

const tags = [
  'All Topics',
  '#General',
  '#Bug',
  '#Review',
  '#Hardware',
  '#Software'
]

const filteredPosts = computed(() => {
  if (activeTag.value === 'All Topics') return store.posts
  return store.posts.filter(post => post.tag === activeTag.value)
})
</script>

<template>
  <main class="home-view animate-fade-in">
    <div class="layout-grid">
      
      <!-- Left Sidebar (Filters) -->
      <aside class="left-sidebar">
        <div class="sidebar-block glass-panel" style="padding: 1.5rem;">
          <h3 class="block-title">Topics</h3>
          <ul class="skill-list">
            <li 
              v-for="tag in tags" 
              :key="tag"
              :class="['skill-item', { active: activeTag === tag }]"
              @click="activeTag = tag"
            >
              {{ tag }}
            </li>
          </ul>
        </div>
        
        <div class="sidebar-links">
          <a href="#">About</a> · 
          <a href="#">Help Center</a> · 
          <a href="#">Privacy</a> · 
          <a href="#">Terms</a>
          <p>© 2026 Bcommunity</p>
        </div>
      </aside>

      <!-- Main Feed -->
      <div class="feed-column">
        <!-- Mobile Topics (Visible only on small screens) -->
        <div class="mobile-topics">
          <ul class="mobile-skill-list">
            <li 
              v-for="tag in tags" 
              :key="'mob-'+tag"
              :class="['mobile-skill-item', { active: activeTag === tag }]"
              @click="activeTag = tag"
            >
              {{ tag }}
            </li>
          </ul>
        </div>

        <CreatePost v-if="store.currentUser" />
        <RouterLink v-else to="/auth" class="btn btn-primary">Sign in to post</RouterLink>
        
    
        
        <div class="feed">
          <template v-if="isLoading">
            <PostSkeleton v-for="i in 3" :key="i" />
          </template>
          <template v-else>
            <PostCard 
              v-for="post in filteredPosts" 
              :key="post.id" 
              :post="post" 
            />
          </template>
        </div>
      </div>
      
      <!-- Right Sidebar -->
      <aside class="right-sidebar">
        <!-- Suggestions Widget -->
        <div class="sidebar-widget glass-panel">
          <h3 class="widget-title">Top Mentors</h3>
          <div class="suggestion-list">
            <div class="suggestion-item">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Teacher1" alt="Avatar" class="widget-avatar" />
              <div class="widget-info">
                <span class="widget-name">David (Teacher)</span>
                <span class="widget-sub">Reputation: 3200</span>
              </div>
              <button class="follow-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              </button>
            </div>
            
            <div class="suggestion-item">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Senior1" alt="Avatar" class="widget-avatar" />
              <div class="widget-info">
                <span class="widget-name">Sarah (Senior Dev)</span>
                <span class="widget-sub">Reputation: 1450</span>
              </div>
              <button class="follow-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              </button>
            </div>
            
            <div class="suggestion-item">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Senior2" alt="Avatar" class="widget-avatar" />
              <div class="widget-info">
                <span class="widget-name">Michael (DBA)</span>
                <span class="widget-sub">Reputation: 980</span>
              </div>
              <button class="follow-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              </button>
            </div>
          </div>
          <button class="link-btn">View Leaderboard</button>
        </div>
        
        <!-- Popular Pages Widget -->
        <div class="sidebar-widget glass-panel">
          <h3 class="widget-title">Useful Resources</h3>
          <div class="suggestion-list">
            <div class="suggestion-item">
              <div class="widget-icon" style="background: #41b883;">
                <svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M2 3h20v2H2V3zm2 4h16v12H4V7zm2 2v8h12V9H6zm2 2h8v2H8v-2z"/></svg>
              </div>
              <div class="widget-info">
                <span class="widget-name">Vue.js Docs</span>
                <span class="widget-sub">Official Documentation</span>
              </div>
            </div>
            
            <div class="suggestion-item">
              <div class="widget-icon" style="background: #f7df1e;">
                <svg viewBox="0 0 24 24" fill="black" xmlns="http://www.w3.org/2000/svg"><path d="M4 22V2h16v20H4zm2-2h12V4H6v16zm2-4v2h8v-2H8zm0-4v2h8v-2H8z"/></svg>
              </div>
              <div class="widget-info">
                <span class="widget-name">JS Tutorial</span>
                <span class="widget-sub">JavaScript Info</span>
              </div>
            </div>
          </div>
          <button class="link-btn">View all resources</button>
        </div>
        
        <div class="sidebar-widget glass-panel">
          <h3 class="widget-title" style="margin-bottom: 0;">Advertising <span style="font-weight: 400; color:#9ca3af; font-size: 0.8rem;">(optional)</span></h3>
        </div>
      </aside>
      
    </div>
  </main>
</template>

<style scoped>
.home-view {
  display: flex;
  justify-content: center;
  padding: 0 1rem;
}

.layout-grid {
  width: 100%;
  max-width: 1200px;
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 300px;
  gap: 2rem;
  align-items: start;
}

/* Left Sidebar */
.left-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: sticky;
  top: 90px;
}

.skill-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skill-item {
  padding: 0.6rem 0.8rem;
  border-radius: 8px;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  position: relative;
  transition: all var(--transition-fast);
}

.skill-item:hover {
  background: rgba(255,255,255,0.6);
  color: var(--text-primary);
}

.skill-item.active {
  color: var(--accent-color);
  font-weight: 700;
  background: var(--accent-glow);
}



.sidebar-links {
  padding: 0 0.5rem;
  font-size: 0.8rem;
  color: #9ca3af;
  line-height: 1.8;
}

.sidebar-links a {
  color: #9ca3af;
  text-decoration: none;
}

.sidebar-links a:hover {
  text-decoration: underline;
}

/* Feed Column */
.feed-column {
  display: flex;
  flex-direction: column;
}

.feed-sort {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 1rem;
  padding-right: 0.5rem;
  cursor: pointer;
}

.feed-sort strong {
  color: #1a1a1a;
}

.feed {
  display: flex;
  flex-direction: column;
}

/* Mobile Topics */
.mobile-topics {
  display: none;
  margin-bottom: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.mobile-topics::-webkit-scrollbar {
  display: none;
}

.mobile-skill-list {
  display: flex;
  gap: 0.5rem;
  list-style: none;
  padding: 0 0.2rem;
  margin: 0;
  white-space: nowrap;
}

.mobile-skill-item {
  padding: 0.4rem 1rem;
  border-radius: 20px;
  background: rgba(255,255,255,0.5);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.8);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.mobile-skill-item.active {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

/* Right Sidebar */
.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: sticky;
  top: 90px;
}

.sidebar-widget {
  padding: 1.5rem;
}

.widget-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.widget-avatar, .widget-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
}

.widget-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}

.widget-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.widget-name {
  font-weight: 700;
  font-size: 0.85rem;
  color: #1a1a1a;
}

.widget-sub {
  font-size: 0.75rem;
  color: #9ca3af;
}

.follow-btn {
  background: none;
  border: 1px solid rgba(255,255,255,0.8);
  background: rgba(255,255,255,0.4);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-color);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: none;
}

.follow-btn:hover {
  background: #ffffff;
  transform: translateY(-2px);
  box-shadow: none;
}

.follow-btn svg {
  width: 14px;
  height: 14px;
}

.link-btn {
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  width: 100%;
  text-align: center;
  margin-top: 0.5rem;
}

@media (max-width: 1024px) {
  .layout-grid {
    grid-template-columns: 240px minmax(0, 1fr);
  }
  .right-sidebar {
    display: none;
  }
}

@media (max-width: 768px) {
  .layout-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 1rem;
  }
  .left-sidebar {
    display: none;
  }
  .mobile-topics {
    display: block;
  }
  .home-view {
    padding: 0 0.5rem;
  }
}
</style>
