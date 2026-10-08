<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import ToastNotification from '@/components/ToastNotification.vue'

const route = useRoute()
const showNavbar = computed(() => !route.path.startsWith('/admin'))
</script>

<template>
  <div class="app-wrapper">
    <div v-if="showNavbar" class="nav-container">
      <Navbar />
    </div>
    <main class="main-content">
      <RouterView />
    </main>
    <ToastNotification />
  </div>
</template>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav-container {
  width: 100%;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
