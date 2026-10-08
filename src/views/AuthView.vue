<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { usePostsStore } from '@/stores/posts'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()
const store = usePostsStore()
const isLogin = ref(true)
const name = ref('')
const email = ref('')
const password = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  if (isLoading.value) return
  isLoading.value = true
  try {
    await store.authenticate(isLogin.value ? 'login' : 'register', {
      email: email.value, password: password.value, ...(!isLogin.value ? { name: name.value } : {}),
    })
    password.value = ''
    uiStore.addToast(isLogin.value ? 'Signed in successfully!' : 'Account created!', 'success')
    const target = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
      ? route.query.redirect : '/'
    await router.push(target)
  } catch (error) {
    uiStore.addToast(error.message || 'Unable to reach the API. Start the Flask backend.', 'error')
  } finally { isLoading.value = false }
}
</script>

<template>
  <div class="auth-container">
    <div class="glass-panel auth-panel">
      <div class="auth-header">
        <h1 class="auth-title">{{ isLogin ? "Welcome Back" : "Create an Account" }}</h1>
        <p class="text-muted">Enter your details to access your account</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div v-if="!isLogin" class="input-group">
          <label>Display Name</label>
          <input v-model="name" type="text" class="input-field" maxlength="120" required />
        </div>
        <div class="input-group">
          <label>Email Address</label>
          <input type="email" v-model="email" class="input-field" placeholder="hello@example.com" required />
        </div>

        <div class="input-group">
          <label>Password</label>
          <input type="password" v-model="password" minlength="8" maxlength="128" class="input-field" placeholder="••••••••" required />
        </div>

        <div class="forgot-password">
          <button type="button" class="btn" @click="isLogin = !isLogin">
            {{ isLogin ? 'Create an account' : 'Already have an account? Sign in' }}
          </button>
        </div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="isLoading">
          <span v-if="!isLoading">{{ isLogin ? "Sign In" : "Register" }}</span>
          <span v-else class="loader"></span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
  padding: 2rem;
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.auth-panel {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.4);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-title {
  font-size: 2.2rem;
  background: var(--accent-gradient);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
  font-weight: 800;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-left: 0.2rem;
}

.input-field {
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.input-field:focus {
  background: #ffffff;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 4px var(--accent-glow);
  outline: none;
}

.forgot-password {
  text-align: right;
  font-size: 0.85rem;
  margin-top: -0.5rem;
}

.forgot-password a {
  color: var(--accent-color);
  text-decoration: none;
  font-weight: 600;
  transition: opacity var(--transition-fast);
}

.forgot-password a:hover {
  opacity: 0.8;
}

.submit-btn {
  margin-top: 1rem;
  width: 100%;
  padding: 1.1rem;
  border-radius: var(--radius-md);
  font-size: 1.05rem;
  height: 54px;
}

.auth-footer {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.toggle-btn {
  background: none;
  border: none;
  color: var(--accent-color);
  font-weight: 700;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
  margin-left: 0.5rem;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.loader {
  border: 3px solid rgba(255,255,255,0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
