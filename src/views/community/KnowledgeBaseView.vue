<script setup>
import { onMounted } from 'vue'
import { useKnowledgeStore } from '@/stores/knowledge'
const store = useKnowledgeStore()
onMounted(() => store.load())
</script>

<template>
  <div class="knowledge-container animate-fade-in">
    <div class="header-section">
      <div class="text-center">
        <h1 class="page-title">Knowledge Base</h1>
        <p class="text-muted">Tutorials, guides, and common error solutions from the community.</p>
        <div class="search-box mt-4">
          <input type="text" class="input-field search-input" placeholder="Search for errors, concepts, or guides..." />
        </div>
      </div>
    </div>

    <div class="categories-section">
      <h2 class="section-title">Categories</h2>
      <div class="categories-grid">
        <div class="category-card glass-panel">
          <div class="icon-wrapper bg-blue">
            <svg viewBox="0 0 256 256" fill="currentColor"><path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM40,56H216V88H40ZM216,200H40V104H216V200ZM176,144a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,144Zm0,32a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,176Z"></path></svg>
          </div>
          <h3>Tutorials & Guides</h3>
          <p class="text-muted">Step-by-step learning paths.</p>
        </div>
        <div class="category-card glass-panel">
          <div class="icon-wrapper bg-red">
            <svg viewBox="0 0 256 256" fill="currentColor"><path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm-8,56a8,8,0,0,1,16,0v56a8,8,0,0,1-16,0Zm8,104a12,12,0,1,1,12-12A12,12,0,0,1,128,184Z"></path></svg>
          </div>
          <h3>Common Errors</h3>
          <p class="text-muted">Solutions to frequent bugs.</p>
        </div>
        <div class="category-card glass-panel">
          <div class="icon-wrapper bg-purple">
            <svg viewBox="0 0 256 256" fill="currentColor"><path d="M240,94c0,70-103.79,126.66-108.21,129a8,8,0,0,1-7.58,0C119.79,220.66,16,164,16,94A62.07,62.07,0,0,1,78,32c20.65,0,38.73,8.88,50,23.89C139.27,40.88,157.35,32,178,32A62.07,62.07,0,0,1,240,94Z"></path></svg>
          </div>
          <h3>Best Practices</h3>
          <p class="text-muted">Write cleaner, better code.</p>
        </div>
      </div>
    </div>

    <div class="articles-section">
      <div class="section-header">
        <h2 class="section-title">Latest Articles</h2>
        <a href="#" class="view-all">View All</a>
      </div>
      
      <div class="article-list">
        <div v-for="article in store.articles" :key="article.id" class="article-item glass-panel">
          <img v-if="article.coverImage" :src="article.coverImage" alt="cover" class="article-cover" />
          <div class="article-content">
            <div class="article-meta text-muted">
              <span class="category-tag" style="text-transform: capitalize;">{{ article.tags[0] }}</span>
              <span>•</span>
              <span>{{ article.readTime }}</span>
            </div>
            <h3 class="article-title">
              <a href="#">{{ article.title }}</a>
            </h3>
            <p class="article-excerpt text-muted">
              {{ article.excerpt }}
            </p>
            <div class="article-author">
              <img :src="article.author.avatar" alt="author" class="author-avatar" />
              <span class="author-name">{{ article.author.name }}</span>
              <span class="publish-date text-muted">{{ article.createdAt }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.knowledge-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 2rem 3rem;
}

.header-section {
  padding: 3rem 0;
  display: flex;
  justify-content: center;
}

.text-center {
  text-align: center;
  max-width: 600px;
  width: 100%;
}

.page-title {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.search-box {
  width: 100%;
  position: relative;
}

.search-input {
  padding: 1rem 1.5rem;
  font-size: 1.1rem;
  border-radius: 100px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.categories-section {
  margin-bottom: 4rem;
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.category-card {
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.icon-wrapper svg {
  width: 32px;
  height: 32px;
  color: white;
}

.bg-blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.bg-red { background: linear-gradient(135deg, #ef4444, #dc2626); }
.bg-purple { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

.category-card h3 {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.view-all {
  color: var(--accent-color);
  font-weight: 600;
  text-decoration: none;
}

.view-all:hover {
  text-decoration: underline;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.article-item {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
  align-items: center;
}

.article-cover {
  width: 240px;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.article-item:hover {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .article-item {
    flex-direction: column;
    align-items: stretch;
  }
  .article-cover {
    width: 100%;
    height: 180px;
  }
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.category-tag {
  color: var(--accent-color);
  font-weight: 600;
}

.article-title {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
}

.article-title a {
  color: var(--text-primary);
  text-decoration: none;
}

.article-title a:hover {
  color: var(--accent-color);
}

.article-excerpt {
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.article-author {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.author-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e2e8f0;
}

.author-name {
  font-weight: 600;
  color: #1a1a1a;
}
</style>
