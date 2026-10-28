<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, apiAction, apiList } from '@/services/api'
import { timeAgo } from '@/utils/time'
const notifications = ref([])
const router = useRouter()
const openNotification = notification => {
  if (notification.type === 'message') router.push('/messages')
}
onMounted(() => apiAction(async () => { notifications.value = await apiList('/notifications') }))
const markAllAsRead = () => apiAction(async () => {
  await api('/notifications/read', { method: 'PUT' })
  notifications.value.forEach(notification => { notification.isRead = true })
  return true
})
</script>

<template>
  <div class="notifications-dropdown">
    <div class="header">
      <h2>Notifications</h2>
      <button @click="markAllAsRead" class="mark-read-btn">Mark all as read</button>
    </div>

    <div class="notifications-list">
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        class="notification-item"
        :class="{ 'unread': !notification.isRead }"
        @click="openNotification(notification)"
      >
        <img :src="notification.user.avatar" alt="Avatar" class="avatar" />
        
        <div class="notification-content">
          <div class="content-header">
            <span class="user-name">{{ notification.user.name }}</span> 
            <span class="time">{{ timeAgo(notification.time) }}</span>
          </div>
          <p class="notification-text">{{ notification.content }}</p>
        </div>
      </div>
      
      <div v-if="notifications.length === 0" class="empty-state">
        <p>No new notifications.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notifications-dropdown {
  position: absolute;
  top: calc(100% + 12px);
  right: -6px;
  width: 360px;
  /* Solid, not frosted: a blur nested inside the frosted navbar renders see-through on iOS. */
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.14);
  overflow: hidden;
  z-index: 200;
  transform-origin: top right;
  animation: dropdownFade 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes dropdownFade {
  from { opacity: 0; transform: scale(0.96) translateY(-8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.25rem 0.75rem 1.25rem;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

h2 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
}

.mark-read-btn {
  background: none;
  border: none;
  color: #7c3aed;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  transition: opacity 0.2s;
  font-size: 0.85rem;
}

.mark-read-btn:hover {
  opacity: 0.7;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  max-height: 360px;
  overflow-y: auto;
  padding: 0.5rem;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  padding: 0.8rem 1rem;
  border-radius: 10px;
  transition: background 0.2s;
  cursor: pointer;
}

.notification-item:hover {
  background: rgba(0,0,0,0.02);
}

.notification-item.unread {
  background: rgba(124, 58, 237, 0.03);
  position: relative;
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 15%;
  height: 70%;
  width: 3px;
  background: #7c3aed;
  border-radius: 0 4px 4px 0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.1rem;
}

.notification-text {
  color: #4b5563;
  margin: 0;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-name {
  font-weight: 600;
  color: #111827;
  font-size: 0.9rem;
}

.time {
  font-size: 0.75rem;
  color: #9ca3af;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #9ca3af;
  font-size: 0.9rem;
}

/* Phones: span the screen under the navbar instead of hanging off the bell (which overflowed left). */
@media (max-width: 768px) {
  .notifications-dropdown {
    top: calc(100% + 6px);
    left: 0.75rem;
    right: 0.75rem;
    width: auto;
    transform-origin: top center;
  }

  .notifications-list {
    max-height: min(65vh, 480px);
  }

  .notification-item {
    padding: 0.85rem 0.75rem;
  }

  .avatar {
    width: 42px;
    height: 42px;
    flex-shrink: 0;
  }

  .user-name { font-size: 0.95rem; }
  .notification-text { font-size: 0.9rem; }
}
</style>
