<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar glass-panel">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
      </div>
      <nav class="sidebar-nav">
        <RouterLink to="/admin" exact-active-class="active" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
          Dashboard Overview
        </RouterLink>
        <RouterLink to="/admin/users" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          Manage Users
        </RouterLink>
        <RouterLink to="/" class="nav-item back-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          Back to Community
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
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
  background: rgba(255, 255, 255, 0.5);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-glow);
  color: var(--accent-color);
  border: 1px solid rgba(255, 255, 255, 0.4);
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
    padding: 1rem;
  }
}
</style>
