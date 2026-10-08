<script setup>
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
</script>

<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div 
        v-for="toast in uiStore.toasts" 
        :key="toast.id" 
        :class="['toast-message', `toast-${toast.type}`]"
      >
        <span v-if="toast.type === 'success'" class="toast-icon">✅</span>
        <span v-else-if="toast.type === 'error'" class="toast-icon">❌</span>
        <span v-else class="toast-icon">ℹ️</span>
        {{ toast.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 9999;
  pointer-events: none; /* Let clicks pass through to UI below */
}

.toast-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #ffffff;
  color: #1a1a1a;
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  box-shadow: none;
  font-weight: 600;
  font-size: 0.9rem;
  min-width: 200px;
}

.toast-success {
  border-left: 4px solid #10b981;
}

.toast-error {
  border-left: 4px solid #ef4444;
}

.toast-info {
  border-left: 4px solid #3b82f6;
}

/* Vue Transition styles for "toast" */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
</style>
