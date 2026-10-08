<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiAction, apiList } from '@/services/api'
import { useChatStore } from '@/stores/chat'
import { usePostsStore } from '@/stores/posts'
const mentors = ref([])
const search = ref('')
const router = useRouter()
const chat = useChatStore()
const posts = usePostsStore()
onMounted(() => apiAction(async () => { mentors.value = await apiList('/mentors') }))
const filteredMentors = computed(() => mentors.value.filter(mentor =>
  (mentor.name + ' ' + mentor.skills.join(' ')).toLowerCase().includes(search.value.toLowerCase())))
async function requestMentor(id) {
  if (!posts.currentUser) return router.push({ name: 'auth', query: { redirect: '/mentorship' } })
  if (await chat.startConversation(id)) await router.push('/messages')
}
</script>

<template>
  <div class="mentorship-container animate-fade-in">
    <div class="header-section">
      <div>
        <h1 class="page-title">Find a Mentor</h1>
        <p class="text-muted">Connect with experienced developers for 1-on-1 guidance.</p>
      </div>
      <button class="btn btn-primary" @click="router.push('/profile')">
        Edit mentoring profile
      </button>
    </div>

    <div class="filters glass-panel">
      <div class="search-box">
        <input v-model="search" type="text" class="input-field search-input" placeholder="Search by skill, e.g., Vue.js..." />
      </div>
      
    </div>

    <div class="mentor-grid">
      <div v-for="mentor in filteredMentors" :key="mentor.id" class="mentor-card glass-panel">
        <div class="mentor-header">
          <div class="avatar-container">
            <img :src="mentor.avatar" alt="Mentor avatar" class="mentor-avatar" />
            
          </div>
          <div class="mentor-info">
            <h3 class="mentor-name">{{ mentor.name }}</h3>
            <p class="mentor-role text-muted">{{ mentor.role }}</p>
          </div>
        </div>
        
        <p class="mentor-bio">
          {{ mentor.bio }}
        </p>
        
        <div class="skills"><span v-for="skill in mentor.skills" :key="skill" class="skill-tag">{{ skill }}</span></div>
        
        <div class="card-footer">
          <span class="text-muted">Reputation: {{ mentor.reputation }}</span>
          <button class="btn btn-secondary btn-sm" :disabled="mentor.id === posts.currentUser?.id" @click="requestMentor(mentor.id)">Request Mentoring</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mentorship-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem 3rem;
}

.page-title {
  font-size: 2rem;
  color: #1a1a1a;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  margin-bottom: 2rem;
  gap: 1rem;
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.filter-options {
  display: flex;
  gap: 1rem;
}

.select-field {
  padding: 0.75rem 1rem;
  min-width: 150px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 16px;
}

.mentor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.mentor-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.mentor-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.avatar-container {
  position: relative;
}

.mentor-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #f1f5f9;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.status-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #9ca3af;
  border: 2px solid white;
}

.status-indicator.online {
  background: #10b981;
}

.mentor-info {
  flex: 1;
}

.mentor-name {
  font-size: 1.15rem;
  margin-bottom: 0.2rem;
}

.mentor-role {
  font-size: 0.9rem;
}

.mentor-bio {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 1.2rem;
  flex: 1;
}

.skills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.skill-tag {
  background: rgba(15, 23, 42, 0.05);
  color: var(--text-primary);
  padding: 0.25rem 0.75rem;
  border-radius: 100px;
  font-size: 0.8rem;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid rgba(0,0,0,0.05);
  padding-top: 1rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.rating-val {
  font-weight: 700;
  font-size: 0.95rem;
}

.review-count {
  font-size: 0.85rem;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box {
    max-width: 100%;
  }
  .filter-options {
    flex-direction: column;
  }
}
</style>
