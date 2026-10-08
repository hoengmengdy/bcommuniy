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
      component: () => import('../views/AuthView.vue'),
    },
    {
      path: '/admin',
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
    }
  ],
})


router.beforeEach(async to => {
  const store = usePostsStore()
  await store.initialize()
  const protectedPage = ['/profile', '/messages'].includes(to.path) || to.path.startsWith('/admin')
  if (protectedPage && !store.currentUser) {
    return { name: 'auth', query: { redirect: to.fullPath } }
  }
  if (to.path.startsWith('/admin') && !store.currentUser?.isAdmin) return '/'
})

export default router
