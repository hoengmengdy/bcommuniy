<template>
  <div class="post-skeleton">
    <!-- Header -->
    <div class="post-header">
      <div class="author-block">
        <div class="skeleton-avatar"></div>
        <div class="author-info">
          <div class="skeleton-text skeleton-name"></div>
          <div class="skeleton-text skeleton-time"></div>
        </div>
      </div>
    </div>
    
    <!-- Content Text -->
    <div class="skeleton-text skeleton-content-1"></div>
    <div class="skeleton-text skeleton-content-2"></div>
    <div class="skeleton-text skeleton-content-3"></div>
    
    <!-- Image -->
    <div class="skeleton-image"></div>
    
    <!-- Actions -->
    <div class="post-actions">
      <div class="skeleton-btn"></div>
      <div class="skeleton-btn"></div>
      <div class="skeleton-btn"></div>
    </div>
  </div>
</template>

<style scoped>
.post-skeleton {
  background: #ffffff;
  border: 1px solid var(--surface-border, #e2e8f0);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background-color: #e2e8f0;
  animation: pulse 1.5s infinite ease-in-out;
}

.post-header {
  margin-bottom: 1rem;
}

.author-block {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.skeleton-text {
  height: 12px;
  background-color: #e2e8f0;
  border-radius: 4px;
  animation: pulse 1.5s infinite ease-in-out;
}

.skeleton-name { width: 120px; }
.skeleton-time { width: 80px; height: 10px; }

.skeleton-content-1 { width: 100%; margin-bottom: 0.5rem; }
.skeleton-content-2 { width: 90%; margin-bottom: 0.5rem; }
.skeleton-content-3 { width: 60%; margin-bottom: 1.2rem; }

.skeleton-image {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  background-color: #e2e8f0;
  margin-bottom: 1.5rem;
  animation: pulse 1.5s infinite ease-in-out;
}

.post-actions {
  display: flex;
  gap: 1.2rem;
}

.skeleton-btn {
  width: 40px;
  height: 20px;
  border-radius: 8px;
  background-color: #e2e8f0;
  animation: pulse 1.5s infinite ease-in-out;
}
</style>
