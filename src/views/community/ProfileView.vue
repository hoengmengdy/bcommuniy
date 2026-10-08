<script setup>
import { computed, ref, onMounted } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'
import PostCard from '@/components/PostCard.vue'
import PostSkeleton from '@/components/PostSkeleton.vue'
import EditProfileModal from '@/components/EditProfileModal.vue'

const store = usePostsStore()
const uiStore = useUiStore()
const isLoading = ref(true)
const showEditModal = ref(false)

async function saveProfile(data) {
  const saved = await store.updateProfile(data.name, data.bio, data.role, data.skills)
  if (!saved) return
  showEditModal.value = false
  uiStore.addToast('Profile updated successfully!', 'success')
}

onMounted(() => {
  setTimeout(() => {
    isLoading.value = false
  }, 800)
})

const userPosts = computed(() => {
  return store.posts.filter(post => post.author.id === store.currentUser.id)
})

const userSkills = computed(() => store.currentUser.skills || [])

const userBadges = [
  { icon: '🚀', name: 'New Hire', color: '#10b981' },
  { icon: '🏢', name: 'Platform Team', color: '#3b82f6' }
]
const portfolioProjects = [
  { name: 'Internal Wiki', url: 'wiki.corp.local', description: 'Runbooks for incident response' },
  { name: 'Quarterly Hackathon', url: 'github.com/corp-hack', description: 'Internal deployment tool' }
]
</script>

<template>
  <div v-if="store.currentUser" class="profile-view animate-fade-in">
    <div class="profile-header glass-panel">
      <div class="cover-photo"></div>
      
      <div class="profile-info-wrapper">
        <div class="avatar-container">
          <img :src="store.currentUser.avatar" alt="Avatar" class="profile-avatar" />
        </div>
        
        <div class="profile-actions">
          <button class="btn btn-secondary" @click="showEditModal = true">Edit Profile</button>
        </div>

        <div class="profile-details">
          <h1 class="profile-name">{{ store.currentUser.name }}</h1>
          <p class="profile-bio text-muted">
            {{ store.currentUser.bio }}
          </p>
          
          <div class="badges">
            <div class="badge" style="background-color: rgba(16, 185, 129, 0.15); color: #10b981; border-color: rgba(16, 185, 129, 0.4);">
              <span class="badge-icon">🎓</span>
              <span class="badge-name">{{ store.currentUser.role || 'Beginner' }}</span>
            </div>
            <div v-for="badge in userBadges" :key="badge.name" class="badge" :style="{ backgroundColor: badge.color + '15', color: badge.color, borderColor: badge.color + '40' }">
              <span class="badge-icon">{{ badge.icon }}</span>
              <span class="badge-name">{{ badge.name }}</span>
            </div>
          </div>
          
          <div class="skills-container">
            <span v-for="skill in userSkills" :key="skill" class="skill-tag">{{ skill }}</span>
          </div>
          
          <div class="profile-stats">
            <div class="stat-box">
              <span class="stat-number">{{ userPosts.length }}</span>
              <span class="stat-label">Posts</span>
            </div>
            <div class="stat-box">
              <span class="stat-number">128</span>
              <span class="stat-label">Followers</span>
            </div>
            <div class="stat-box">
              <span class="stat-number">84</span>
              <span class="stat-label">Following</span>
            </div>
            <div class="stat-box">
              <span class="stat-number">{{ store.currentUser.reputation || 0 }}</span>
              <span class="stat-label">Reputation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="profile-layout">
      <!-- Left Column: Portfolio -->
      <div class="sidebar">
        <div class="portfolio-section glass-panel">
          <h2 class="section-title">Portfolio & Links</h2>
          <div class="portfolio-links">
            <a v-for="project in portfolioProjects" :key="project.name" href="#" class="portfolio-item">
              <div class="project-header">
                <span class="project-icon">🔗</span>
                <span class="project-name">{{ project.name }}</span>
              </div>
              <span class="project-desc">{{ project.description }}</span>
            </a>
          </div>
        </div>
      </div>

      <!-- Right Column: Posts -->
      <div class="user-content">
        <h2 class="section-title">Your Posts</h2>
        
        <div v-if="isLoading" class="feed">
          <PostSkeleton v-for="i in 2" :key="i" />
        </div>
        
        <template v-else>
          <div v-if="userPosts.length > 0" class="feed">
            <PostCard 
              v-for="post in userPosts" 
              :key="post.id" 
              :post="post" 
            />
          </div>
          
          <div v-else class="empty-state glass-panel text-muted">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📝</div>
            <h3>No posts yet</h3>
            <p>You haven't posted anything yet. Share your first experience!</p>
          </div>
        </template>
      </div>
    </div>
    
    <EditProfileModal 
      :is-open="showEditModal"
      :initial-name="store.currentUser.name"
      :initial-bio="store.currentUser.bio"
      :initial-role="store.currentUser.role"
      :initial-skills="store.currentUser.skills"
      @close="showEditModal = false"
      @save="saveProfile"
    />
  </div>
</template>

<style scoped>
.profile-view {
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 2rem;
  padding: 0;
}

.cover-photo {
  height: 220px;
  background: 
    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.8) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.8) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.8) 0px, transparent 50%);
  background-color: #1e293b;
  width: 100%;
}

.profile-info-wrapper {
  position: relative;
  padding: 0 2rem 2rem 2rem;
}

.avatar-container {
  position: absolute;
  top: -60px;
  left: 2rem;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 4px solid var(--surface-bg);
  box-shadow: none;
  background: #ffffff;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 1rem;
  margin-bottom: 1rem;
}

.profile-details {
  margin-top: 1rem;
}

.profile-name {
  font-size: 2rem;
  margin-bottom: 0.25rem;
}

.profile-bio {
  max-width: 600px;
  margin-bottom: 1rem;
}

.badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 700;
  border: 1px solid currentColor;
}

.skills-container {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.skill-tag {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(4px);
  color: var(--text-primary);
  padding: 0.4rem 1rem;
  border-radius: 100px;
  font-size: 0.85rem;
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: none;
  transition: all var(--transition-fast);
}

.skill-tag:hover {
  background: white;
  transform: translateY(-1px);
}

.profile-stats {
  display: flex;
  gap: 2rem;
}

.stat-box {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 0.5rem;
}

.stat-number {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.profile-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.portfolio-section {
  padding: 1.5rem;
}

.section-title {
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--glass-border);
  font-size: 1.25rem;
}

.portfolio-links {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.portfolio-item {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: all var(--transition-fast);
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: none;
}

.portfolio-item:hover {
  transform: translateY(-2px);
  background: rgba(255,255,255,0.8);
  box-shadow: none;
}

.project-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.project-name {
  font-weight: 600;
  color: #111827;
}

.project-desc {
  font-size: 0.85rem;
  color: #6b7280;
}

.empty-state {
  padding: 3rem;
  text-align: center;
}

@media (max-width: 768px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
  .cover-photo {
    height: 140px;
  }
  .profile-info-wrapper {
    padding: 0 1rem 1rem 1rem;
  }
  .avatar-container {
    top: -40px;
    left: 1rem;
  }
  .profile-avatar {
    width: 80px;
    height: 80px;
    border-width: 3px;
  }
  .profile-actions {
    padding-top: 0.5rem;
  }
  .profile-name {
    font-size: 1.5rem;
  }
  .profile-stats {
    gap: 1rem;
    flex-wrap: wrap;
  }
  .portfolio-section {
    padding: 1rem;
  }
}
</style>
