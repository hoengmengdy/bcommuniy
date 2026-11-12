<script setup>
import { RouterView, RouterLink } from 'vue-router'
import './admin.css'

// Each entry is one admin tool; icons are inline SVG path data.
const links = [
  { to: '/admin', label: 'Dashboard', exact: true, icon: ['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M14 14h7v7h-7z', 'M3 14h7v7H3z'] },
  { to: '/admin/users', label: 'Users', icon: ['M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2', 'M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z', 'M23 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'] },
  { to: '/admin/posts', label: 'Posts', icon: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z', 'M14 2v6h6', 'M16 13H8', 'M16 17H8'] },
  { to: '/admin/comments', label: 'Comments', icon: ['M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'] },
  { to: '/admin/content', label: 'Articles, Jobs & Events', icon: ['M4 19.5A2.5 2.5 0 0 1 6.5 17H20', 'M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'] },
  { to: '/admin/broadcast', label: 'Broadcast', icon: ['M3 11l18-5v12L3 14v-3z', 'M11.6 16.8a3 3 0 1 1-5.8-1.6'] },
]
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar glass-panel">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
      </div>
      <nav class="sidebar-nav" aria-label="Admin tools">
        <RouterLink v-for="link in links" :key="link.to" :to="link.to" class="nav-item"
          :exact-active-class="link.exact ? 'active' : undefined" :active-class="link.exact ? '' : 'active'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
            stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <path v-for="d in link.icon" :key="d" :d="d" />
          </svg>
          <span>{{ link.label }}</span>
        </RouterLink>
        <RouterLink to="/" class="nav-item back-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon" aria-hidden="true">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          <span>Back to Community</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="admin-main animate-fade-in">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  flex: 1;
  gap: 2rem;
  padding: 2rem;
}

.admin-sidebar {
  width: 280px;
  flex-shrink: 0;
  height: calc(100vh - 4rem);
  padding: 1.5rem;
  position: sticky;
  top: 2rem;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgb(var(--surface-rgb, 255 255 255) / 0.4);
}

.sidebar-header h2 {
  font-size: 1.4rem;
  background: var(--accent-gradient);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.8rem 1rem;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  background: rgb(var(--surface-rgb, 255 255 255) / 0.5);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-glow);
  color: var(--accent-color);
  border: 1px solid rgb(var(--surface-rgb, 255 255 255) / 0.4);
}

.back-link {
  margin-top: auto;
  color: #ef4444;
}

.back-link:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.admin-main {
  flex: 1;
  min-width: 0;
  padding-bottom: 2rem;
}

@media (max-width: 768px) {
  .admin-layout {
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }
  .admin-sidebar {
    width: 100%;
    position: static;
    height: auto;
    padding: 0.75rem;
  }
  .sidebar-header { display: none; }
  .sidebar-nav {
    flex-direction: row;
    overflow-x: auto;
    gap: 0.3rem;
  }
  .nav-item {
    white-space: nowrap;
    padding: 0.55rem 0.8rem;
    font-size: 0.85rem;
  }
  .back-link { margin-top: 0; }
}
</style>
