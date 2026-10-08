<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import NotificationsDropdown from './NotificationsDropdown.vue'

const store = usePostsStore()
const showNotifications = ref(false)
const route = useRoute()
const router = useRouter()
const signOut = async () => { if (await store.logout()) await router.push('/auth') }
const notificationWrapperRef = ref(null)

const closeDropdown = (e) => {
  if (showNotifications.value && notificationWrapperRef.value && !notificationWrapperRef.value.contains(e.target)) {
    showNotifications.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

watch(route, () => {
  showNotifications.value = false
})
</script>

<template>
  <nav class="navbar-wrapper">
    <div class="navbar-content">
      
      <!-- Brand -->
      <RouterLink to="/" class="brand">
        <div class="brand-logo">
          <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M228.45,71.16l-96-56a15.82,15.82,0,0,0-16.1,0l-96,55.93A16,16,0,0,0,12.35,85l1.41,100.86a15.94,15.94,0,0,0,7.91,13.78l96,56.09a15.82,15.82,0,0,0,16.1,0l96-56a16,16,0,0,0,7.88-13.82L244,85A15.93,15.93,0,0,0,228.45,71.16ZM128,32.41,203,76.15,128,119.89,53,76.15ZM43.43,94.2l76.57,44.66v84.71l-75.14-43.9ZM136,223.57V138.86l76.57-44.66.42,1.38-1.55,84.1Z"/>
          </svg>
        </div>
        <span class="brand-text">Bcommunity</span>
      </RouterLink>

      <RouterLink to="/questions">Q&amp;A</RouterLink>
      <RouterLink to="/knowledge">Knowledge</RouterLink>
      <RouterLink to="/reviews">Reviews</RouterLink>
      <RouterLink to="/mentorship">Mentors</RouterLink>
      <RouterLink to="/leaderboard">Leaderboard</RouterLink>

      <!-- Search -->
      <div class="search-bar">
        <svg class="search-icon" viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M232.49,215.51,185,168a92.12,92.12,0,1,0-17,17l47.53,47.54a12,12,0,0,0,17-17ZM44,112a68,68,0,1,1,68,68A68.07,68.07,0,0,1,44,112Z"/>
        </svg>
        <input type="text" placeholder="Search" class="search-input" />
      </div>

      <!-- Right Actions -->
      <div class="right-actions">
        <div v-if="store.currentUser" class="notification-wrapper" ref="notificationWrapperRef">
          <button @click="showNotifications = !showNotifications" class="icon-btn" :class="{ 'active-icon': showNotifications }">
            <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M221.8,175.94C216.25,166.38,208,139.33,208,104a80,80,0,1,0-160,0c0,35.34-8.26,62.38-13.81,71.94A16,16,0,0,0,48,200H88.81a40,40,0,0,0,78.38,0H208a16,16,0,0,0,13.8-24.06ZM128,216a24,24,0,0,1-22.62-16h45.24A24,24,0,0,1,128,216Z"/>
            </svg>
          </button>
          <NotificationsDropdown v-if="showNotifications" />
        </div>
        
        <RouterLink to="/messages" class="icon-btn" active-class="active-icon">
          <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M132,24A100.11,100.11,0,0,0,32,124v84a16,16,0,0,0,16,16h84a100,100,0,0,0,0-200Zm-28,112a12,12,0,1,1,12-12A12,12,0,0,1,104,136Zm28,0a12,12,0,1,1,12-12A12,12,0,0,1,132,136Zm28,0a12,12,0,1,1,12-12A12,12,0,0,1,160,136Z"/>
          </svg>
        </RouterLink>
        
        <RouterLink v-if="!store.currentUser" to="/auth" class="btn btn-primary" style="padding: 0.5rem 1.2rem; font-size: 0.85rem; border-radius: 100px; text-decoration: none;">
          Sign In
        </RouterLink>
        
        <RouterLink v-if="store.currentUser?.isAdmin" to="/admin" class="btn">Admin</RouterLink>
        <button v-if="store.currentUser" class="btn" @click="signOut">Sign Out</button>
        <RouterLink v-if="store.currentUser" to="/profile" class="user-profile">
          <img :src="store.currentUser.avatar" alt="User Avatar" class="avatar" />
          <div class="badge">
            <svg viewBox="0 0 256 256" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/>
            </svg>
          </div>
        </RouterLink>
      </div>
      
    </div>
  </nav>
</template>

<style scoped>
.navbar-wrapper {
  position: sticky;
  top: 0;
  z-index: 100;
  width: 100%;
  background: var(--surface-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid var(--surface-border);
  box-shadow: none;
  margin-bottom: 2rem;
  transition: all var(--transition-normal);
}

.navbar-content {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
  gap: 1rem;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  text-decoration: none;
  gap: 0.5rem;
  justify-self: flex-start;
  transition: transform 0.2s ease;
}

.brand:hover {
  transform: scale(1.02);
}

.brand-logo {
  color: #7c3aed;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  font-size: 1.15rem;
  font-weight: 800;
  color: #1a1a1a;
  letter-spacing: -0.02em;
}

/* Search Bar */
.search-bar {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  border-radius: 100px;
  padding: 0.6rem 1.2rem;
  flex: 1;
  max-width: 500px;
  min-width: 200px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  transition: all var(--transition-normal);
  box-shadow: none;
  order: 2;
  margin: 0 1rem;
}

.search-bar:focus-within {
  background: #ffffff;
  border-color: #cbd5e1;
  box-shadow: none;
  transform: translateY(-1px);
}

.search-icon {
  width: 18px;
  height: 18px;
  color: #9ca3af;
  margin-right: 0.6rem;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-family: inherit;
  font-size: 0.95rem;
  color: #1a1a1a;
  width: 100%;
}

.search-input::placeholder {
  color: #9ca3af;
}

/* Right Actions */
.right-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  order: 3;
}

.notification-wrapper {
  position: relative;
}

.icon-btn {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.8);
  color: var(--text-secondary);
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: all var(--transition-normal);
  box-shadow: none;
}

.icon-btn:hover, .active-icon {
  background: #ffffff;
  color: var(--accent-color);
  transform: translateY(-3px);
  border-color: #ffffff;
  box-shadow: none;
}

.icon-btn svg {
  width: 20px;
  height: 20px;
}

.user-profile {
  position: relative;
  margin-left: 0.5rem;
  cursor: pointer;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  background: var(--accent-color);
  border: 2px solid #ffffff;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge svg {
  width: 8px;
  height: 8px;
}

@media (max-width: 1024px) {
  .navbar-content {
    padding: 0.8rem 1.5rem;
  }
}

@media (max-width: 768px) {
  .navbar-wrapper {
    margin-bottom: 0;
  }
  
  .navbar-content {
    padding: 0.8rem 1rem;
    gap: 0.5rem;
  }
  
  .brand {
    order: 1;
    flex-shrink: 0;
  }
  
  .right-actions {
    order: 2;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .search-bar {
    order: 3;
    flex: 1 1 100%;
    max-width: 100%;
    margin: 0.5rem 0 0 0;
  }
}
</style>
