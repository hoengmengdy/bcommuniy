<template>
  <div class="code-review-container animate-fade-in">
    <div class="header-section">
      <div>
        <h1 class="page-title">Code Reviews</h1>
        <p class="text-muted">Submit your code for peer review or help others improve theirs.</p>
      </div>
      <button class="btn btn-primary" @click="showForm = !showForm">
        <svg viewBox="0 0 256 256" fill="currentColor" width="18" height="18" style="margin-right: 8px;">
          <path d="M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z"></path>
        </svg>
        Request Review
      </button>
    </div>

    <form v-if="showForm" class="glass-panel" @submit.prevent="requestReview" style="padding: 1rem; margin-bottom: 1rem;">
      <input v-model="title" class="input-field" placeholder="Review title" required />
      <input v-model="language" class="input-field" placeholder="Code language" required />
      <textarea v-model="code" class="input-field" placeholder="Code to review" required></textarea>
      <button class="btn btn-primary" type="submit">Publish review request</button>
    </form>
    <div class="filters glass-panel">
      <div class="tabs">
        <button v-for="tab in ['Needs Review', 'My Requests', 'Completed']" :key="tab" class="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button>
      </div>
      <div class="search-box">
        <input v-model="search" type="text" class="input-field search-input" placeholder="Search by language, framework..." />
      </div>
    </div>

    <div class="review-grid">
      <div v-for="review in filteredReviews" :key="review.id" class="review-card glass-panel">
        <div class="card-header">
          <div class="language-badge" >
            {{ review.codeLanguage }}
          </div>
          <span class="status-badge" :class="review.comments.length > 0 ? 'status-reviewed' : 'status-pending'">
            {{ review.comments.length > 0 ? 'Reviewed' : 'Pending' }}
          </span>
        </div>
        
        <h3 class="review-title">
          <RouterLink :to="'/post/' + review.id">{{ review.title }}</RouterLink>
        </h3>
        
        <CodeBlock :code="review.codeSnippet || review.content" :language="review.codeLanguage" />
        
        <div class="card-footer">
          <div class="meta">
            <img :src="review.author.avatar" alt="avatar" class="author-avatar" />
            <span class="author-name">{{ review.author.name }}</span>
          </div>
          <RouterLink :to="'/post/' + review.id" class="btn btn-secondary btn-sm">View Code</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, apiAction, apiList } from '@/services/api'
import { usePostsStore } from '@/stores/posts'
import CodeBlock from '@/components/CodeBlock.vue'
const reviews = ref([])
const posts = usePostsStore()
const activeTab = ref('Needs Review')
const search = ref('')
const showForm = ref(false)
const title = ref('')
const code = ref('')
const language = ref('javascript')
async function load() { reviews.value = await apiList('/reviews') }
onMounted(() => apiAction(load))
const filteredReviews = computed(() => reviews.value.filter(review =>
  (activeTab.value !== 'My Requests' || review.author.id === posts.currentUser?.id) &&
  (activeTab.value !== 'Needs Review' || review.comments.length === 0) &&
  (activeTab.value !== 'Completed' || review.comments.length > 0) &&
  (review.title + ' ' + review.codeLanguage).toLowerCase().includes(search.value.toLowerCase())))
const requestReview = () => apiAction(async () => {
  await api('/reviews', { method: 'POST', body: {
    title: title.value, codeSnippet: code.value, codeLanguage: language.value,
  } })
  showForm.value = false
  title.value = ''; code.value = ''
  await load()
  return true
})
</script>

<style scoped>
.code-review-container {
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
  padding: 0.5rem;
  margin-bottom: 2rem;
  border-radius: var(--radius-lg);
}

.tabs {
  display: flex;
  gap: 0.5rem;
}

.tab {
  background: transparent;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: rgba(255, 255, 255, 0.5);
  color: var(--text-primary);
}

.tab.active {
  background: white;
  color: var(--accent-color);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.search-box {
  width: 300px;
}

.search-input {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.review-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.language-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.lang-vue { background: rgba(65, 184, 131, 0.15); color: #2c3e50; }
.lang-react { background: rgba(97, 218, 251, 0.15); color: #007bc4; }
.lang-python { background: rgba(55, 118, 171, 0.15); color: #3776ab; }
.lang-go { background: rgba(0, 173, 216, 0.15); color: #00add8; }
.lang-js { background: rgba(247, 223, 30, 0.2); color: #b5a000; }
.lang-rust { background: rgba(222, 165, 132, 0.2); color: #b86236; }

.status-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 100px;
}

.status-pending {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.status-reviewed {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.review-title {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.review-title a {
  color: var(--text-primary);
  text-decoration: none;
}

.review-title a:hover {
  color: var(--accent-color);
}

.code-preview {
  background: #282c34;
  border-radius: var(--radius-sm);
  padding: 1rem;
  margin-bottom: 1.5rem;
  overflow: hidden;
  flex: 1;
}

.code-preview code {
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
  color: #abb2bf;
  white-space: pre-wrap;
  display: block;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.btn-sm {
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
}

.meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f1f5f9;
}

.author-name {
  color: var(--text-secondary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  .filters {
    flex-direction: column;
    gap: 1rem;
  }
  .search-box {
    width: 100%;
  }
  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
