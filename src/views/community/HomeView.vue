<script setup>
import { usePostsStore } from '@/stores/posts'
import CreatePost from '@/components/CreatePost.vue'
import PostCard from '@/components/PostCard.vue'
import PostSkeleton from '@/components/PostSkeleton.vue'
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/services/api'
import { useSettingsStore } from '@/stores/settings'

const store = usePostsStore()
const route = useRoute()
const router = useRouter()
const t = useSettingsStore().t
const tagLabel = tag => (tag === 'All Topics' ? t('home.allTopics') : tag)
const roleLabel = role => t('role.' + role)
// Top Mentors shows the real highest-reputation members with their own profile photos.
const mentors = ref([])
const isLoading = ref(true)
const activeTag = ref('All Topics')

onMounted(() => {
  api('/leaderboard?page=1&per_page=3').then(res => { mentors.value = res.data || [] }).catch(() => {})
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

// The navbar search sets ?q=; match it against the post text, title, author and topic.
const searchQuery = computed(() => String(route.query.q || '').trim())
const clearSearch = () => router.push({ path: '/' })

const filteredPosts = computed(() => {
  let posts = activeTag.value === 'All Topics' ? store.posts : store.posts.filter(post => post.tag === activeTag.value)
  const q = searchQuery.value.toLowerCase()
  if (q) {
    posts = posts.filter(post => [post.content, post.title, post.author?.name, post.tag, post.codeSnippet]
      .some(field => field && String(field).toLowerCase().includes(q)))
  }
  return posts
})
</script>

<template>
  <main class="home-view">
    <div class="layout-grid">

      <!-- Left Sidebar (Filters) -->
      <aside class="left-sidebar" :aria-label="t('home.topics')">
        <nav class="sidebar-card glass-panel">
          <h2 class="card-title">{{ t('home.topics') }}</h2>
          <ul class="topic-list">
            <li v-for="tag in tags" :key="tag">
              <button
                :class="['topic-item', { active: activeTag === tag }]"
                :aria-pressed="activeTag === tag"
                @click="activeTag = tag"
              >
                {{ tagLabel(tag) }}
              </button>
            </li>
          </ul>
        </nav>

        <footer class="sidebar-links">
          <div class="sidebar-links-row">
            <a href="#">{{ t('home.about') }}</a>
            <a href="#">{{ t('home.help') }}</a>
            <a href="#">{{ t('home.privacy') }}</a>
            <a href="#">{{ t('home.terms') }}</a>
          </div>
          <p>© 2026 Bcommunity</p>
        </footer>
      </aside>

      <!-- Main Feed -->
      <div class="feed-column">
        <!-- Topics as chips on tablets/phones without the left sidebar -->
        <div class="mobile-topics" role="group" :aria-label="t('home.topics')">
          <button
            v-for="tag in tags"
            :key="'mob-'+tag"
            :class="['mobile-topic', { active: activeTag === tag }]"
            :aria-pressed="activeTag === tag"
            @click="activeTag = tag"
          >
            {{ tagLabel(tag) }}
          </button>
        </div>

        <CreatePost v-if="store.currentUser" />
        <RouterLink v-else to="/auth" class="btn btn-primary">{{ t('home.signInToPost') }}</RouterLink>

        <div v-if="searchQuery" class="search-summary">
          <span>{{ t(filteredPosts.length === 1 ? 'home.resultsOne' : 'home.resultsMany', { count: filteredPosts.length }) }} “<strong>{{ searchQuery }}</strong>”</span>
          <button class="clear-search" @click="clearSearch">{{ t('home.clear') }}</button>
        </div>

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
            <p v-if="!filteredPosts.length" class="feed-empty glass-panel">
              {{ searchQuery ? t('home.noMatch') : t('home.noPosts') }}
            </p>
          </template>
        </div>
      </div>

      <!-- Right Sidebar -->
      <aside class="right-sidebar" :aria-label="t('home.highlights')">
        <section class="sidebar-card glass-panel">
          <h2 class="card-title">{{ t('home.topMentors') }}</h2>
          <ul class="row-list">
            <li v-for="m in mentors" :key="m.id" class="widget-row">
              <button class="row-main" :aria-label="t('home.openProfile', { name: m.name })" @click="router.push(`/profile/${m.id}`)">
                <img :src="m.avatar" :alt="m.name" class="widget-avatar" />
                <span class="widget-info">
                  <span class="widget-name-line">
                    <span class="widget-name">{{ m.name }}</span>
                    <span v-if="m.profileRole" class="level-badge" :class="'level-' + m.profileRole.toLowerCase()">{{ roleLabel(m.profileRole) }}</span>
                  </span>
                  <span class="widget-sub">{{ t('home.reputation', { n: m.reputation }) }}</span>
                </span>
              </button>
              <button class="row-action" :title="t('home.askMentor')" :aria-label="t('home.askMentor')" @click="router.push('/mentorship')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              </button>
            </li>
            <li v-if="!mentors.length" class="widget-sub">{{ t('home.noMentors') }}</li>
          </ul>
          <button class="link-btn" @click="router.push('/leaderboard')">{{ t('home.viewLeaderboard') }}</button>
        </section>

        <section class="sidebar-card glass-panel">
          <h2 class="card-title">{{ t('home.resources') }}</h2>
          <ul class="row-list">
            <li>
              <a class="row-main resource-link" href="https://vuejs.org/guide/introduction.html" target="_blank" rel="noopener">
                <span class="widget-icon" style="background: #41b883;">
                  <svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M2 3h20v2H2V3zm2 4h16v12H4V7zm2 2v8h12V9H6zm2 2h8v2H8v-2z"/></svg>
                </span>
                <span class="widget-info">
                  <span class="widget-name">Vue.js Docs</span>
                  <span class="widget-sub">{{ t('home.vueDocs') }}</span>
                </span>
              </a>
            </li>
            <li>
              <a class="row-main resource-link" href="https://javascript.info/" target="_blank" rel="noopener">
                <span class="widget-icon" style="background: #f7df1e;">
                  <svg viewBox="0 0 24 24" fill="black" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M4 22V2h16v20H4zm2-2h12V4H6v16zm2-4v2h8v-2H8zm0-4v2h8v-2H8z"/></svg>
                </span>
                <span class="widget-info">
                  <span class="widget-name">JS Tutorial</span>
                  <span class="widget-sub">JavaScript Info</span>
                </span>
              </a>
            </li>
          </ul>
          <button class="link-btn" @click="router.push('/knowledge')">{{ t('home.viewResources') }}</button>
        </section>

        <section class="sidebar-card glass-panel">
          <h2 class="card-title card-title-flat">{{ t('home.ads') }} <span class="card-title-note">{{ t('home.optional') }}</span></h2>
        </section>
      </aside>

    </div>
  </main>
</template>

<style scoped>
.home-view {
  padding: 0 24px 40px;
}

/* Centered three columns: topics · feed · highlights. */
.layout-grid {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 220px minmax(0, 680px) 290px;
  justify-content: center;
  gap: 24px;
  align-items: start;
}

.left-sidebar,
.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: calc(var(--navbar-height, 64px) + 24px);
}

/* Shared sidebar card */
.sidebar-card {
  padding: 18px;
}

.card-title {
  font-size: 15.5px;
  font-weight: 700;
  color: var(--ink-strong, #0f172a);
  letter-spacing: -0.01em;
  margin: 0 0 10px;
}

.card-title-flat { margin: 0; }
.card-title-note { font-weight: 400; color: var(--ink-400, #94a3b8); font-size: 12.5px; }

/* Topics */
.topic-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 0 -6px;
}

.topic-item {
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: none;
  color: var(--ink-600, #475569);
  font-weight: 500;
  font-size: 14.5px;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
}

.topic-item:hover {
  background: var(--tint, #f6f5fb);
  color: var(--ink-strong, #0f172a);
}

.topic-item.active {
  background: var(--brand-soft);
  color: var(--brand-ink, #6d28d9);
  font-weight: 600;
}

.sidebar-links {
  padding: 0 6px;
  font-size: 12.5px;
  color: var(--ink-400, #94a3b8);
}

.sidebar-links-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  margin-bottom: 6px;
}

.sidebar-links a {
  color: var(--ink-500, #64748b);
  text-decoration: none;
  border-radius: 4px;
}

.sidebar-links a:hover {
  color: var(--brand);
}

/* Feed Column */
.feed-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.feed {
  display: flex;
  flex-direction: column;
}

.feed-empty {
  padding: 28px;
  text-align: center;
  color: var(--ink-500, #64748b);
}

.search-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 2px 12px;
  font-size: 14px;
  color: var(--ink-600, #475569);
}

.clear-search {
  border: none;
  background: var(--brand-soft);
  color: var(--brand-ink, #6d28d9);
  font-weight: 600;
  font-size: 13px;
  padding: 5px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.clear-search:hover { background: var(--tint, #ede9fe); }

/* Topic chips for tablets and phones */
.mobile-topics {
  display: none;
  gap: 8px;
  margin-bottom: 12px;
  overflow-x: auto;
  padding: 2px 2px 4px;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.mobile-topics::-webkit-scrollbar { display: none; }

.mobile-topic {
  flex-shrink: 0;
  padding: 7px 14px;
  border-radius: 999px;
  background: var(--surface, #ffffff);
  border: 1px solid var(--surface-3, #ebe9f5);
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink-600, #475569);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.mobile-topic:hover { border-color: var(--tint-strong, #ddd6fe); color: var(--ink-strong, #0f172a); }

.mobile-topic.active {
  background: var(--brand);
  border-color: var(--brand);
  color: #ffffff;
}

/* Right sidebar rows */
.row-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 0 -8px 6px;
}

.widget-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.row-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 8px;
  border: none;
  border-radius: 10px;
  background: none;
  text-align: left;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: background 0.15s ease;
}

.row-main:hover { background: var(--tint, #f6f5fb); }
.row-main:hover .widget-name { color: var(--brand); }

.widget-avatar, .widget-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
}

.widget-avatar { object-fit: cover; background: var(--tint, #ede9fe); }

.widget-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border-radius: 10px;
}

.widget-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.widget-name-line {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.widget-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--ink-strong, #0f172a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.15s ease;
}

.widget-sub {
  font-size: 12.5px;
  color: var(--ink-500, #64748b);
}

.row-list > .widget-sub { padding: 4px 8px; }

.level-badge {
  flex-shrink: 0;
  padding: 0 6px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
  background: var(--surface-3, #f1f5f9);
  color: var(--ink-600, #475569);
}

.level-senior { background: var(--tint-green, #ecfdf3); color: var(--green-ink, #047857); }
.level-beginner { background: var(--tint, #eef2ff); color: var(--indigo-ink, #4f46e5); }
.level-teacher { background: var(--tint-amber, #fef6e7); color: var(--amber-ink, #b45309); }

.row-action {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: none;
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.row-action:hover { background: var(--brand-soft); }

.row-action svg {
  width: 15px;
  height: 15px;
}

.link-btn {
  display: block;
  margin: 0 auto;
  background: none;
  border: none;
  color: var(--brand-ink, #6d28d9);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.link-btn:hover { background: var(--brand-soft); }

/* Tablet: topics + feed. */
@media (max-width: 1199px) {
  .layout-grid {
    grid-template-columns: 220px minmax(0, 680px);
  }

  .right-sidebar { display: none; }
}

/* Phone: one full-width column. */
@media (max-width: 767px) {
  .home-view {
    padding: 12px 12px 32px;
  }

  .layout-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
  }

  .left-sidebar { display: none; }
  .mobile-topics { display: flex; }
}
</style>
