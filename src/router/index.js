import { createRouter, createWebHistory } from 'vue-router'
import { usePostsStore } from '../stores/posts.js'
import CommunityHomeView from '../views/community/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/questions', component: () => import('../views/community/QnAView.vue') },
    { path: '/knowledge', component: () => import('../views/community/KnowledgeBaseView.vue') },
    { path: '/reviews', component: () => import('../views/community/CodeReviewView.vue') },
    { path: '/mentorship', component: () => import('../views/community/MentorshipView.vue') },
    { path: '/leaderboard', component: () => import('../views/community/LeaderboardView.vue') },
    {
      path: '/',
      name: 'community',
      component: CommunityHomeView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/community/ProfileView.vue'),
    },
    {
      path: '/post/:id',
      name: 'post-detail',
      component: () => import('../views/community/PostDetailView.vue'),
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('../views/chart/MessagesView.vue'),
    },
    {
      path: '/auth',
      name: 'auth',
      meta: { public: true },
      component: () => import('../views/AuthView.vue'),
    },
    {
      path: '/register',
      alias: ['/signup', '/create-account'],
      name: 'register',
      meta: { public: true },
      component: () => import('../views/RegisterView.vue'),
    },
    {
      path: '/admin',
      meta: { requiresAdmin: true },
      component: () => import('../views/admin/AdminLayout.vue'),
      children: [
        {
          path: '',
          name: 'admin-overview',
          component: () => import('../views/admin/OverviewView.vue')
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/admin/UsersView.vue')
        }
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})


router.beforeEach(async to => {
  // Only the login and registration screens are public. New routes are protected
  // automatically, including direct URLs and browser history navigation.
  if (to.meta.public === true) return
  const store = usePostsStore()
  if (!await store.validateSession()) {
    return { name: 'auth', query: { redirect: to.fullPath }, replace: true }
  }
  if (to.meta.requiresAdmin && !store.currentUser?.isAdmin) return '/'
  await store.initialize()
  if (!store.currentUser) return { name: 'auth', query: { redirect: to.fullPath }, replace: true }
})

globalThis.addEventListener?.('bcommunity-session-expired', () => {
  const route = router.currentRoute.value
  if (route.meta.public !== true) {
    void router.replace({ name: 'auth', query: { redirect: route.fullPath } })
  }
})

// Recheck server-side revocation when returning to a tab, and while it stays open.
function revalidateSession() {
  const store = usePostsStore()
  if (store.currentUser) void store.validateSession()
}
globalThis.addEventListener?.('focus', revalidateSession)
globalThis.addEventListener?.('pageshow', revalidateSession)
globalThis.document?.addEventListener('visibilitychange', () => {
  if (!document.hidden) revalidateSession()
})
const sessionCheck = setInterval(() => {
  if (!globalThis.document?.hidden) revalidateSession()
}, 30000)
sessionCheck.unref?.()

export default router
