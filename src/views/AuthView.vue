<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { usePostsStore } from '@/stores/posts'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()
const store = usePostsStore()
const email = ref('')
const password = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    await store.authenticate({ email: email.value, password: password.value })
    password.value = ''
    uiStore.addToast('Signed in successfully!', 'success')
    const redirect = route.query.redirect
    const target = typeof redirect === 'string' && redirect.startsWith('/') &&
      !redirect.startsWith('//') && !redirect.includes('\\') &&
      router.resolve(redirect).name !== 'auth' ? redirect : '/'
    await router.replace(target)
  } catch (error) {
    uiStore.addToast(error.message || 'Unable to reach the API. Start the Flask backend.', 'error')
  } finally { isLoading.value = false }
}
</script>

<template>
  <div class="auth-container">
    <div class="glass-panel auth-panel">
      <div class="auth-header">
        <h1 class="auth-title">Welcome Back</h1>
        <p class="text-muted">Enter your details to access your account</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="input-group">
          <label for="login-email">Email Address</label>
          <input id="login-email" autocomplete="email" type="email" v-model="email" class="input-field" placeholder="hello@example.com" required />
        </div>

        <div class="input-group">
          <label for="login-password">Password</label>
          <input id="login-password" autocomplete="current-password" type="password" v-model="password" minlength="8" maxlength="128" class="input-field" placeholder="••••••••" required />
        </div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="isLoading">
          <span v-if="!isLoading">Sign In</span>
          <span v-else class="loader"></span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped src="../assets/auth.css"></style>
