<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const store = usePostsStore()
const ui = useUiStore()
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (isLoading.value) return
  errorMessage.value = ''
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }
  isLoading.value = true
  try {
    await store.registerAccount({ name: name.value, email: email.value,
      password: password.value, confirmPassword: confirmPassword.value })
    password.value = ''
    confirmPassword.value = ''
    ui.addToast('Account created. Please sign in.', 'success')
    await router.replace({ name: 'auth', query: { redirect: route.query.redirect } })
  } catch (error) {
    errorMessage.value = error.message || 'Unable to create your account. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="glass-panel auth-panel">
      <div class="auth-header">
        <h1 class="auth-title">Create Account</h1>
      </div>
      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="input-group">
          <label for="register-name">Full Name</label>
          <input id="register-name" v-model="name" type="text" autocomplete="name" class="input-field" maxlength="120" required />
        </div>
        <div class="input-group">
          <label for="register-email">Email Address</label>
          <input id="register-email" v-model="email" type="email" autocomplete="email" class="input-field" maxlength="254" required />
        </div>
        <div class="input-group">
          <label for="register-password">Password</label>
          <input id="register-password" v-model="password" type="password" autocomplete="new-password" class="input-field" minlength="8" maxlength="128" required />
        </div>
        <div class="input-group">
          <label for="register-confirm-password">Confirm Password</label>
          <input id="register-confirm-password" v-model="confirmPassword" type="password" autocomplete="new-password" class="input-field" minlength="8" maxlength="128" required />
        </div>
        <p v-if="errorMessage" role="alert" class="form-error">{{ errorMessage }}</p>
        <button type="submit" class="btn btn-primary submit-btn" :disabled="isLoading">
          <span v-if="!isLoading">Create Account</span>
          <span v-else class="loader" aria-label="Creating account"></span>
        </button>
      </form>
      <p class="auth-switch">
        Already have an account?
        <RouterLink :to="{ name: 'auth', query: { redirect: route.query.redirect } }" class="auth-link">Sign In</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped src="../assets/auth.css"></style>
