<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import NotificationsDropdown from './NotificationsDropdown.vue'

const store = usePostsStore()
const showNotifications = ref(false)
const route = useRoute()
const router = useRouter()
const signOut = () => store.logout()
const notificationWrapperRef = ref(null)

const showProfileMenu = ref(false)
const profileWrapperRef = ref(null)

// Search filters the home feed through ?q=, so results can be shared and survive a refresh.
const searchText = ref(String(route.query.q || ''))
const showMobileSearch = ref(false)
const mobileSearchInput = ref(null)
function submitSearch() {
  const q = searchText.value.trim()
  router.push({ path: '/', query: q ? { q } : {} })
  showMobileSearch.value = false
}
function toggleMobileSearch() {
  showMobileSearch.value = !showMobileSearch.value
  if (showMobileSearch.value) nextTick(() => mobileSearchInput.value?.focus())
}

const closeDropdown = (e) => {
  if (showNotifications.value && notificationWrapperRef.value && !notificationWrapperRef.value.contains(e.target)) {
    showNotifications.value = false
  }
  if (showProfileMenu.value && profileWrapperRef.value && !profileWrapperRef.value.contains(e.target)) {
    showProfileMenu.value = false
  }
}

// Publish the navbar's real height so full-height pages (Messages) can fill the rest exactly.
const navRef = ref(null)
let resizeObserver
const publishHeight = () => {
  if (navRef.value) document.documentElement.style.setProperty('--navbar-height', navRef.value.offsetHeight + 'px')
}

onMounted(() => {
  document.addEventListener('click', closeDropdown)
  publishHeight()
  resizeObserver = new ResizeObserver(publishHeight)
  resizeObserver.observe(navRef.value)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
  resizeObserver?.disconnect()
})

watch(route, () => {
  showNotifications.value = false
  showProfileMenu.value = false
  searchText.value = String(route.query.q || '')
})
</script>

<template>
  <nav ref="navRef" class="navbar-wrapper" aria-label="Main">
    <div class="navbar-content">

      <!-- Brand -->
      <RouterLink to="/" class="brand" aria-label="Bcommunity home">
        <div class="brand-logo">
          <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M228.45,71.16l-96-56a15.82,15.82,0,0,0-16.1,0l-96,55.93A16,16,0,0,0,12.35,85l1.41,100.86a15.94,15.94,0,0,0,7.91,13.78l96,56.09a15.82,15.82,0,0,0,16.1,0l96-56a16,16,0,0,0,7.88-13.82L244,85A15.93,15.93,0,0,0,228.45,71.16ZM128,32.41,203,76.15,128,119.89,53,76.15ZM43.43,94.2l76.57,44.66v84.71l-75.14-43.9ZM136,223.57V138.86l76.57-44.66.42,1.38-1.55,84.1Z"/>
          </svg>
        </div>
        <span class="brand-text">Bcommunity</span>
      </RouterLink>

      <!-- Search -->
      <form class="search-bar" role="search" @submit.prevent="submitSearch">
        <svg class="search-icon" viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M232.49,215.51,185,168a92.12,92.12,0,1,0-17,17l47.53,47.54a12,12,0,0,0,17-17ZM44,112a68,68,0,1,1,68,68A68.07,68.07,0,0,1,44,112Z"/>
        </svg>
        <input v-model="searchText" type="search" placeholder="Search posts, people, topics" class="search-input"
          aria-label="Search posts" />
      </form>

      <!-- Right Actions -->
      <div class="right-actions">
        <button class="icon-btn mobile-search-btn" :class="{ 'active-icon': showMobileSearch }" aria-label="Search"
          title="Search" :aria-expanded="showMobileSearch" @click="toggleMobileSearch">
          <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M232.49,215.51,185,168a92.12,92.12,0,1,0-17,17l47.53,47.54a12,12,0,0,0,17-17ZM44,112a68,68,0,1,1,68,68A68.07,68.07,0,0,1,44,112Z"/>
          </svg>
        </button>

        <div v-if="store.currentUser" class="notification-wrapper" ref="notificationWrapperRef">
          <button @click="showNotifications = !showNotifications" class="icon-btn" :class="{ 'active-icon': showNotifications }"
            aria-label="Notifications" title="Notifications" :aria-expanded="showNotifications">
            <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M221.8,175.94C216.25,166.38,208,139.33,208,104a80,80,0,1,0-160,0c0,35.34-8.26,62.38-13.81,71.94A16,16,0,0,0,48,200H88.81a40,40,0,0,0,78.38,0H208a16,16,0,0,0,13.8-24.06ZM128,216a24,24,0,0,1-22.62-16h45.24A24,24,0,0,1,128,216Z"/>
            </svg>
          </button>
          <NotificationsDropdown v-if="showNotifications" />
        </div>

        <RouterLink to="/messages" class="icon-btn" active-class="active-icon" aria-label="Messages" title="Messages">
          <svg viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M132,24A100.11,100.11,0,0,0,32,124v84a16,16,0,0,0,16,16h84a100,100,0,0,0,0-200Zm-28,112a12,12,0,1,1,12-12A12,12,0,0,1,104,136Zm28,0a12,12,0,1,1,12-12A12,12,0,0,1,132,136Zm28,0a12,12,0,1,1,12-12A12,12,0,0,1,160,136Z"/>
          </svg>
        </RouterLink>

        <RouterLink v-if="!store.currentUser" to="/auth" class="btn btn-primary sign-in-btn">
          Sign In
        </RouterLink>

        <div v-if="store.currentUser" class="profile-wrapper" ref="profileWrapperRef">
          <button class="user-profile" aria-label="Account menu" :aria-expanded="showProfileMenu"
            @click="showProfileMenu = !showProfileMenu">
            <img :src="store.currentUser.avatar" :alt="store.currentUser.name" class="avatar" />
            <div class="badge" aria-hidden="true">
              <svg viewBox="0 0 256 256" fill="white" xmlns="http://www.w3.org/2000/svg">
                <path d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/>
              </svg>
            </div>
          </button>
          <div v-if="showProfileMenu" class="profile-menu" role="menu">
            <div class="profile-menu-header">
              <img :src="store.currentUser.avatar" alt="" class="avatar" />
              <div class="profile-menu-who">
                <strong>{{ store.currentUser.name }}</strong>
                <span>{{ store.currentUser.email }}</span>
              </div>
            </div>
            <RouterLink to="/profile" class="profile-menu-item" role="menuitem">👤 My Profile</RouterLink>
            <RouterLink v-if="store.currentUser.isAdmin" to="/admin" class="profile-menu-item" role="menuitem">🛠️ Admin</RouterLink>
            <button class="profile-menu-item sign-out" role="menuitem" @click="signOut">🚪 Sign Out</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Phone search row -->
    <form v-if="showMobileSearch" class="mobile-search" role="search" @submit.prevent="submitSearch">
      <input ref="mobileSearchInput" v-model="searchText" type="search" placeholder="Search posts, people, topics"
        class="search-input" aria-label="Search posts" />
      <button type="submit" class="mobile-search-go">Search</button>
    </form>
  </nav>
</template>

<style scoped>
.navbar-wrapper {
  position: sticky;
  top: 0;
  z-index: 100;
  width: 100%;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: saturate(180%) blur(12px);
  -webkit-backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  margin-bottom: 24px;
}

.navbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 24px;
  max-width: 1360px;
  margin: 0 auto;
  gap: 16px;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  text-decoration: none;
  gap: 8px;
  flex-shrink: 0;
  border-radius: 8px;
}

.brand-logo {
  color: var(--brand);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-logo svg {
  width: 100%;
  height: 100%;
}

.brand-text {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

/* Search Bar */
.search-bar {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 480px;
  height: 40px;
  background: #F7F7FA;
  border: 1px solid #ececf2;
  border-radius: 12px;
  padding: 0 14px;
  transition: all 0.15s ease;
}

.search-bar:hover { border-color: #e0deeb; }

.search-bar:focus-within {
  background: #ffffff;
  border-color: #c4b5fd;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
}

.search-icon {
  width: 17px;
  height: 17px;
  color: #94a3b8;
  margin-right: 10px;
  flex-shrink: 0;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 14.5px;
  color: #0f172a;
  width: 100%;
}

.search-input::placeholder { color: #94a3b8; }

/* Right Actions */
.right-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.notification-wrapper {
  position: relative;
}

.icon-btn {
  background: transparent;
  border: none;
  color: #64748b;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background: #f4f2fb;
  color: var(--brand);
}

.active-icon {
  background: var(--brand-soft);
  color: var(--brand);
}

.icon-btn svg {
  width: 21px;
  height: 21px;
}

.mobile-search-btn { display: none; }

.sign-in-btn {
  padding: 0.5rem 1.2rem;
  font-size: 0.85rem;
  border-radius: 10px;
  text-decoration: none;
}

.profile-wrapper {
  position: relative;
  display: flex;
}

.user-profile {
  position: relative;
  margin-left: 6px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
  display: flex;
  border-radius: 50%;
  transition: box-shadow 0.15s ease;
}

.user-profile:hover { box-shadow: 0 0 0 3px #ede9fe; }

.profile-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 240px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.14);
  padding: 0.4rem;
  z-index: 200;
  animation: menuFade 0.15s ease-out;
}

@keyframes menuFade {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.profile-menu-header {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 0.75rem 0.8rem;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 0.3rem;
}

.profile-menu-header .avatar {
  width: 40px;
  height: 40px;
}

.profile-menu-who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.profile-menu-who strong {
  font-size: 0.95rem;
  color: #111827;
}

.profile-menu-who span {
  font-size: 0.78rem;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-menu-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.75rem 0.75rem;
  border: none;
  border-radius: 10px;
  background: none;
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  text-decoration: none;
  text-align: left;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
  transition: background 0.15s ease;
}

.profile-menu-item:hover,
.profile-menu-item.router-link-active {
  background: #f5f3ff;
  color: #6d28d9;
}

.profile-menu-item.sign-out { color: #dc2626; }
.profile-menu-item.sign-out:hover { background: #fef2f2; }

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
  background: #ede9fe;
}

.badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  background: var(--brand);
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

.mobile-search {
  display: none;
}

@media (max-width: 1024px) {
  .navbar-content { padding: 0 16px; }
}

@media (max-width: 767px) {
  .navbar-wrapper {
    margin-bottom: 0;
    padding-top: env(safe-area-inset-top);
  }

  /* Phones: logo, then search icon, notifications, messages and profile. */
  .navbar-content {
    height: 56px;
    padding: 0 12px;
    gap: 8px;
  }

  .search-bar { display: none; }
  .mobile-search-btn { display: flex; }

  .right-actions { gap: 2px; }

  .icon-btn {
    width: 42px;
    height: 42px;
  }

  .icon-btn svg {
    width: 23px;
    height: 23px;
  }

  /* Let the notifications panel position against the whole navbar, not the small bell. */
  .notification-wrapper { position: static; }

  .user-profile { margin-left: 4px; }

  .profile-menu { width: min(260px, calc(100vw - 1.5rem)); }

  .mobile-search {
    display: flex;
    gap: 8px;
    padding: 0 12px 10px;
  }

  .mobile-search .search-input {
    flex: 1;
    height: 40px;
    background: #F7F7FA;
    border: 1px solid #ececf2;
    border-radius: 12px;
    padding: 0 14px;
    font-size: 16px; /* 16px stops iOS from zooming in on focus. */
  }

  .mobile-search .search-input:focus { background: #fff; border-color: #c4b5fd; }

  .mobile-search-go {
    height: 40px;
    padding: 0 14px;
    border: none;
    border-radius: 12px;
    background: var(--brand);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
  }
}

@media (max-width: 359px) {
  .brand-text { display: none; }
}
</style>
